import json
import time
import uuid
from typing import Literal, Union

from agentlib.core import (
    Agent,
    AgentVariable,
    BaseModule,
    BaseModuleConfig,
    Source,
)
from agentlib.core.errors import InitializationError
from filip.clients.mqtt import IoTAMQTTClient
from filip.models.ngsi_v2.iot import Device, ServiceGroup, TransportProtocol
from paho.mqtt.client import MQTTMessage, MQTTv5
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCodes
from pydantic import AnyUrl, Field, FilePath, model_validator

from juniconnlib_core.data_models.basic_models import IotaMqttMessage
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases
from juniconnlib_core.utils.mqtt import (
    mqtt_connect_callback,
    mqtt_disconnect_callback,
    mqtt_subscription_callback,
)
from juniconnlib_core.utils.validators import check_mqtt_credentials


class FiwareMQTTConfig(BaseModuleConfig):
    """Class containing configuration parameters for the MQTT connection."""

    mqtt_url: AnyUrl = Field(
        title="MQTT URL",
        examples=["mqtt://mqtt.example.com:1883"],
        description="host is the hostname or IP address of the remote broker.",
    )

    keepalive: int = Field(
        default=30,
        description="Maximum period in seconds between communications with the "
        "broker. If no other messages are being exchanged, this "
        "controls the rate at which the client will send ping messages "
        "to the broker.",
    )
    qos: int = Field(
        default=2,
        ge=0,
        le=2,
        description="Quality of Service level as defined by the MQTT standard",
    )
    protocol: Literal[3, 4, 5] = Field(
        default=MQTTv5,
        description="Version of the MQTT protocol to be used "
        "(v3.1 = 3; v3.11 = 4; v5 = 5)",
    )
    connection_timeout: float = Field(
        default=10,
        ge=0,
        description="Number of seconds to wait for the initial connection until "
        "throwing an Error.",
    )
    username: str | None = Field(description="MQTT username", default=None)
    password: str | None = Field(description="MQTT password", default=None)
    credentials_file: FilePath | None = (
        Field(
            description="Path to the credentials JSON file, containing 'username' "
            "and 'password' entries",
            default=None,
        ),
    )
    use_tls: bool | None = Field(
        default=True,
        description="Use TLS encryption for MQTT traffic",
    )

    valid_credentials = model_validator(mode="after")(check_mqtt_credentials)


class MQTTWithIoTA(BaseModule, IoTAMQTTClient):
    """Contains basic functionality for communication with the FIWARE MQTT
    broker.

    Handles initialization and connection of a mqtt client
    with the FIWARE MQTT broker and contains functionality useful for
    both sending data to FIWARE via `SendToFiwareMqtt` and receiving
    data from FIWARE via `GetFromFiwareMqtt`
    """

    config: FiwareMQTTConfig

    def __init__(self, config: dict, agent: Agent):
        BaseModule.__init__(self, config=config, agent=agent)
        IoTAMQTTClient.__init__(
            self,
            protocol=self.config.protocol,
            client_id=f"{agent.id}_"
            f"{self.config.module_id}_"
            f"{str(uuid.uuid4())}",
        )
        # overwrite the logger of agent lib modules, since it has a
        # fixed formatter
        self.logger = create_logger_for_module(self)
        self.create_and_connect_mqtt()
        self.logger.info("Module is fully connected")

    def terminate(self):
        """Disconnect from client and join loop."""
        self.disconnect()
        super().terminate()

    def process(self):
        """Calls on this module should just happen upon an event."""
        yield self.env.event()

    def register_callbacks(self) -> None:
        """Registers callback methods at the data broker.

        Listens to the variables with aliases:

        `alias = "ProvisionedDevice"` for devices that are already
        provisioned to the IoT-Agent

        `alias = "ProvisionedServiceGroup"` for service groups that are
        already provisioned to the IoT-Agent

        Returns:
            None
        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_device,
            source=Source(agent_id=self.agent.id),
            alias=Aliases.PROVISIONED_DEVICE,
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_service_group,
            source=Source(agent_id=self.agent.id),
            alias=Aliases.PROVISIONED_SERVICE_GROUP,
        )

    def _callback_to_device(self, variable: AgentVariable):
        """Upon receiving a device, add it to the MQTT-Client."""
        if isinstance(variable.value, Device):
            device = variable.value
            self.logger.debug(f"Received Device from agent broker: {device}")
            # Necessary since devices received from the IoTAgent may be
            # missing this information
            device.transport = TransportProtocol.MQTT
            try:
                self.add_device(device=device, qos=self.config.qos)
                self.logger.info(
                    f"Device {device.device_id} was added " f"to MQTT client"
                )
            except ValueError:
                self.logger.debug("Device is already added")

    def _callback_to_service_group(self, variable: AgentVariable):
        """Upon receiving a service group, add it to the MQTT-Client."""
        if isinstance(variable.value, ServiceGroup):
            sg = variable.value
            self.logger.debug(f"Received ServiceGroup from agent broker: {sg}")
            try:
                self.add_service_group(service_group=sg)
                self.logger.info(
                    f"Service group {sg.entity_type} was "
                    f"added to MQTT client"
                )
            except ValueError:
                self.logger.debug("ServiceGroup is already added")

    def create_and_connect_mqtt(self) -> None:
        """Helper to configure and connect a mqtt client."""
        if self.config.use_tls:
            self.tls_set()
        if self.config.credentials_file is not None:
            self.logger.debug("Setting password and username from file")
            with open(
                self.config.credentials_file, "r", encoding="utf-8"
            ) as file:
                credentials = json.load(file)
            self.username_pw_set(
                username=credentials["username"],
                password=credentials["password"],
            )
        elif self.config.username is not None:
            self.logger.debug("Setting password and username")
            self.username_pw_set(
                username=self.config.username, password=self.config.password
            )
        else:
            self.logger.warning("No credentials_file provided for MQTT")

        # add callbacks for different mqtt events and versions
        self.on_connect = mqtt_callback_subscribe_on_conntect
        self.on_disconnect = mqtt_disconnect_callback

        # connect to the MQTT broker
        self.connect(
            host=self.config.mqtt_url.host,
            port=int(self.config.mqtt_url.port),
            keepalive=self.config.keepalive,
        )
        self.loop_start()

        self.logger.info(
            "Agent %s waits for mqtt connections to be ready", self.agent.id
        )
        started_wait = time.time()
        while not self.is_connected():
            if time.time() - started_wait > self.config.connection_timeout:
                raise InitializationError("Could not connect to MQTT broker.")

    def reconnect_mqtt_client(self) -> None:
        """Simple routine, that stops the MQTT loop in the background,
        recon."""
        self.logger.info("Trying to reconnect MQTT client")
        self.loop_stop()
        self.reconnect()
        self.loop_start()


class MQTTCommunicatorSendToIoTA(MQTTWithIoTA):
    def __init__(self, config: dict, agent: Agent):
        super().__init__(config=config, agent=agent)

    def __subscribe_commands(self, *args, **kwargs):
        self.logger.info(
            "Skipping any subscription operations for this modules"
        )

    def subscribe(self, *args, **kwargs):
        self.logger.info(
            "Skipping any subscription operations for this modules"
        )

    def register_callbacks(self) -> None:
        """Extends the variables with callbacks from
        :meth:`MQTTWithIoTA.register_callbacks` by:

        `alias = "MqttSendToFiware"` for actual Payload
        (:class:`juniconnlib_core.data_models.basic_models.IotaMqttMessage`)
        to be sent out

        Returns: None
        """
        super().register_callbacks()
        self.agent.data_broker.register_callback(
            callback=self._callback_to_value_from_field,
            source=Source(agent_id=self.agent.id),
            alias=Aliases.MQTT_SEND_TO_FIWARE,
        )

    def _callback_to_value_from_field(self, var: AgentVariable) -> None:
        """Callback to receiving a IotaMqttMessage from the Agent's DataBroker
        and sending it to MQTT."""
        if not isinstance(var.value, IotaMqttMessage):
            return
        self.logger.debug(
            f"Received MQTT message from agent broker: {var.value}"
        )

        # check if the client is connected
        if not self.is_connected():
            self.logger.warning(
                "MQTT client disconnected from the FIWARE MQTT "
                "Broker! Reconnecting..."
            )
            self.reconnect_mqtt_client()

        # publish mqtt message for the FIWARE IOT agent
        try:
            self.publish(
                device_id=var.value.device_id,
                payload=var.value.payload,
                qos=self.config.qos,
            )
            self.logger.info(
                f"published {var.value.device_id}: " f"{var.value.payload}"
            )
        except KeyError:
            self.logger.error(
                f"Cannot publish {var.value.device_id}: "
                f"{var.value.payload}. Likely the Device of the "
                f"corresponding device_id is missing"
            )


class MQTTCommunicatorReceiveFromIoTA(MQTTWithIoTA):
    def __init__(self, config: dict, agent: Agent):
        super().__init__(config=config, agent=agent)
        self.on_message = mqtt_message_callback
        self.on_subscribe = mqtt_subscription_callback

    def register_callbacks(self) -> None:
        """Registers the same callbacks as
        :meth:`MQTTWithIoTA.register_callbacks`"""
        super().register_callbacks()


def mqtt_message_callback(
    client: MQTTCommunicatorReceiveFromIoTA, userdata, message: MQTTMessage
) -> None:
    """Callback to messages on subscribed MQTT topics (commands)"""
    client.logger.info(
        f"Received command from FIWARE MQTT broker: "
        f"{message.payload.decode('utf-8')} "
        f"on topic: {message.topic}"
    )
    # deconstruct topic to get device id
    protocol, apikey, device_id, _ = message.topic.split("/")

    # construct AgentVariable and send it
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError as err:
        client.logger.error(
            f"Unable to decode mqtt payload {message.payload}: {err}"
        )
        payload = None
    else:
        payload = IotaMqttMessage(
            device_id=device_id, apikey=apikey, payload=payload
        )

    if payload is not None:
        client.agent.data_broker.send_variable(
            AgentVariable(
                value=payload,
                source=client.source,
                name=str(message.mid),
                alias=Aliases.MQTT_RECEIVED_FROM_FIWARE,
            )
        )


def mqtt_callback_subscribe_on_conntect(
    client: MQTTWithIoTA,
    userdata,
    flags: dict,
    code: Union[int, ReasonCodes],
    properties: Properties = None,
) -> None:
    """The callback for when the client receives a CONNACK response from the
    server."""
    mqtt_connect_callback(client, userdata, flags, code, properties)
    client.logger.debug("Subscribing to command topics")
    client.subscribe(qos=client.config.qos)
