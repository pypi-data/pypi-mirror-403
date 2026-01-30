import datetime
import json
from typing import Any, Literal

from agentlib import Agent, AgentVariable, BaseModule, BaseModuleConfig
from filip.models import FiwareHeader
from filip.models.base import DataType
from filip.models.ngsi_v2.base import Metadata
from filip.models.ngsi_v2.context import ContextAttribute, ContextEntity
from filip.models.ngsi_v2.iot import Device
from paho.mqtt.client import Client, MQTTMessage, MQTTv5
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCodes
from pydantic import AnyHttpUrl, AnyUrl, Field, FilePath, model_validator
from requests import HTTPError

from juniconnlib_core.data_models.basic_models import (
    AttributeUpdate,
    CredentialsConfig,
)
from juniconnlib_core.utils.keycloak_ocb import (
    KeycloakConfig,
    OAuthContextBroker,
)
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases
from juniconnlib_core.utils.mqtt import (
    extract_from_topic,
    fill_topic_pattern,
    mqtt_connect_callback,
    mqtt_disconnect_callback,
    mqtt_subscription_callback,
)
from juniconnlib_core.utils.validators import (
    check_keycloak_config,
    check_mqtt_credentials,
)


class SendToFiwareOCBConfig(BaseModuleConfig):
    """Configuration class for the sending OCB communicator (via HTTP)"""

    cb_url: AnyHttpUrl = Field(
        title="ContextBroker Client",
        description="URL of the Orion Context Broker Client",
    )
    fiware_header: FiwareHeader = Field(
        title="FIWARE Header",
        description="Meta information for FIWARE's multi tenancy mechanism.",
    )
    use_keycloak_oauth: bool = Field(
        default=False,
        title="Use Keycloak Identity Management for Orion Context Broker",
        description="Flag whether to use the Keycloak JWT token for "
        "the FIWARE Orion Context Broker",
    )
    keycloak_config: KeycloakConfig | None = None
    add_timestamp: bool | None = Field(
        default=True,
        title="Add TimeInstant metadata",
        description="Flag whether to add TimeInstant "
        "metadata to the attributes",
    )
    check_oauth_config = model_validator(mode="after")(check_keycloak_config)


class MQTTCommunicatorConfig(BaseModuleConfig):
    """Configuration class for the receiving OCB communicator (via MQTT)"""

    url: AnyUrl = Field(
        title="MQTT URL",
        examples=["mqtt://mqtt.example.com:1883"],
        description="host is the hostname or IP address of the remote broker.",
    )
    topic_subscription_pattern: str = Field(
        default="{type}/cmd",
        description="topic that should be subscribed to, for listening to "
        "messages. MQTT wildcards + and # are supported. One "
        "subscription is created for each unique combination of "
        "replacements. If there are no replacements, only one"
        "topic is subscribed. Both + and # are allowed. Allowed "
        "dynamic replacements are: ${id}, ${type}. For Devices "
        "id and type are filled with entity_name and entity_type",
        examples=["pre/fix/${type}/between/+/suffix"],
    )
    topic_parsing_pattern: str = Field(
        default="{type}/cmd",
        description="Pattern on where and what information is to be extracted "
        "from `topic`. The possible functionality is defined by "
        "`juniconnlib_core.utils.string_manipulation.extract_from_topic`",
        examples=[
            "pre/fix/${type}/between/${id}/suffix",
            "${prefix}#/${type}/in/between/{id}",
        ],
    )
    keepalive: int = Field(
        default=30,
        description="Maximum period in seconds between communications with the "
        "broker. If no other messages are being exchanged, this "
        "controls the rate at which the client will send ping messages "
        "to the broker.",
    )
    qos: Literal[0, 1, 2] = Field(
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
    username: str | None = Field(description="MQTT username", default=None)
    password: str | None = Field(description="MQTT password", default=None)
    credentials_file: FilePath | None = Field(
        description="Path to the credentials JSON file, containing 'username' "
        "and 'password' entries",
        default=None,
    )
    use_tls: bool | None = Field(
        default=True,
        description="Use TLS encryption for MQTT traffic",
    )

    valid_credentials = model_validator(mode="after")(check_mqtt_credentials)


class HTTPCommunicatorSendToOCB(BaseModule):
    """A module that sends NGSIv2 compatible payloads to the OCB of
    previously provisioned entities. Sending data to unprovisioned
    entities is not possible.

    The module infers the FIWARE data type from the python type based on
    :meth:`HTTPCommunicatorSendToOCB._infer_fiware_type_from_value`
    """

    config: SendToFiwareOCBConfig

    def __init__(self, config: dict, agent: Agent):
        """Constructor for the `HTTPCommunicatorSendToOCB` module

        Args:
            Args:
            config (dict): A dict containing configuration parameters as
                defined in :class:`SendToFiwareOCBConfig`
            agent (agentlib.Agent): The agent for the initialization.
        """
        self._entities_identifiers: list[tuple[str, str]] = []
        super().__init__(config=config, agent=agent)
        self.logger = create_logger_for_module(self)
        cb_client_config = {
            "fiware_header": self.config.fiware_header,
            "ocb_url": self.config.cb_url,
            "keycloak_config": (
                self.config.keycloak_config
                if self.config.keycloak_config
                else None
            ),
        }
        self.cb_client = OAuthContextBroker(**cb_client_config)

    def process(self):
        yield self.env.event()

    def register_callbacks(self):
        """Registers two callbacks to the aliases:

        `alias="ProvisionedContextEntity"` for entities that are already
        provisioned at the OCB. Provisioning can be done via
        :class:`FiwareOCBEntityProvisioner`

        `alias="HttpSendToFiware"` for attributes that changed and
        should be sent to the OCB
        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_attr_update,
            alias=Aliases.HTTP_SEND_TO_FIWARE,
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_entity,
            alias=Aliases.PROVISIONED_CONTEXT_ENTITY,
        )

    def _callback_to_attr_update(self, variable: AgentVariable):
        """Callback function that is registered to send out changed attributes"""
        if not isinstance(variable.value, AttributeUpdate):
            return
        value = variable.value
        # If the entity is unknown we can't
        if (
            value.entity_id,
            value.entity_type,
        ) not in self._entities_identifiers:
            self.logger.error(
                "Cannot update attribute value for "
                "ContextEntity not yet provisioned"
            )
            return

        attrs = {}
        for attr_name, attr_value in value.payload.items():
            attr = {
                "value": attr_value,
                "type": self._infer_fiware_type_from_value(attr_value),
                "metadata": {},
            }
            if self.config.add_timestamp:
                try:
                    attr["metadata"]["TimeInstant"] = Metadata(
                        type=DataType.DATETIME,
                        value=value.timestamp.isoformat(
                            timespec="milliseconds"
                        ),
                    )
                except AttributeError:
                    self.logger.error("Could not add timestamp")
            attrs[attr_name] = ContextAttribute.model_validate(attr)
        try:
            self.cb_client.update_or_append_entity_attributes(
                entity_id=value.entity_id,
                entity_type=value.entity_type,
                attrs=attrs,
                append_strict=False,
                forcedUpdate=False,
            )
        except HTTPError:
            self.logger.error("Could not update entity attributes")
        self.logger.info(
            "Successfully updated: %s", (value.entity_id, value.entity_type)
        )

    def _callback_to_entity(self, variable: AgentVariable):
        """Callback to keep track of already provisioned devices"""
        if not isinstance(variable.value, ContextEntity):
            return
        # At the moment it is just supported to work with one FIWARE header,
        # hence it is not necessary to save anything more that id and type
        # of each entity to know if it exists on the OCB
        entity_identifier = (variable.value.id, variable.value.type)
        if entity_identifier not in self._entities_identifiers:
            self._entities_identifiers.append(entity_identifier)
            self.logger.info("Registered %s as provisioned", entity_identifier)
        else:
            self.logger.debug(
                "Entity already registered %s", entity_identifier
            )

    def _infer_fiware_type_from_value(self, value: Any):
        """Maps from a python data type to a fiware type. Falls back to Text.

        Types are mapped as follows:

        - `bool` -> Boolean
        - `int` -> Integer
        - `float` -> Number
        - `str` or `bytes` -> Text
        - `datetime.datetime` -> DateTime
        - `datetime.date` -> Date
        - `datetime.time`-> Time
        - `list` or `tuple` -> Array
        - `dict` -> StructuredValue
        - Anything else falls back to Text

        Args:
            value (Any): Variable from which the FIWARE type shall be derived

        Return:
            DataType: A FIWARE type from the according filip enum
        """
        if isinstance(value, bool):
            return DataType.BOOLEAN
        if isinstance(value, int):
            return DataType.INTEGER
        if isinstance(value, float):
            return DataType.NUMBER
        if isinstance(value, (str, bytes)):
            return DataType.TEXT
        if isinstance(value, datetime.datetime):
            return DataType.DATETIME
        if isinstance(value, datetime.date):
            return DataType.DATE
        if isinstance(value, datetime.time):
            return DataType.TIME
        if isinstance(value, (list, tuple)):
            return DataType.ARRAY
        if isinstance(value, dict):
            return DataType.STRUCTUREDVALUE
        self.logger.warning(
            "Could not infer fiware type from value of type "
            f"{type(value)}. Fallback to Text"
        )
        return DataType.TEXT


class MQTTCommunicatorReceiveFromOCB(BaseModule, Client):
    """Module receives NGSIv2 notifications from MQTT in key-value format"""

    config: MQTTCommunicatorConfig

    def __init__(self, config: dict, agent: Agent):
        """Constructor for the `MQTTCommunicatorReceiveFromOCB` module

        Args:
            Args:
            config (dict): A dict containing configuration parameters as
                defined in :class:`MQTTCommunicatorConfig`
            agent (agentlib.Agent): The agent for the initialization.
        """
        self._subscribed_topics: list[str] = []
        self._entity_identifiers: list[tuple[str, str]] = []
        BaseModule.__init__(self, config=config, agent=agent)
        Client.__init__(self, callback_api_version=CallbackAPIVersion(2))
        self.logger = create_logger_for_module(self)

        # if we have a credentials file, we just fill the username and pass
        if self.config.credentials_file:
            self.logger.debug("Reading credentials from file")
            self._credentials = CredentialsConfig.load_from_file(
                self.config.credentials_file
            )
        elif self.config.username and self.config.password:
            self._credentials = CredentialsConfig(
                username=self.config.username, password=self.config.password
            )
        else:
            # Can't be None, so we need a CredentialsConfig with None values
            self._credentials = CredentialsConfig(username=None, password=None)

        # add callbacks for different mqtt events
        self.on_connect = mqtt_callback_subscribe_on_connect
        self.on_disconnect = mqtt_disconnect_callback
        self.on_subscribe = mqtt_subscription_callback
        self.on_message = mqtt_message_callback

        if self.config.use_tls:
            self.tls_set()
        if self._credentials.username is not None:
            self.username_pw_set(
                username=self._credentials.username,
                password=self._credentials.password,
            )

        self.connect(
            host=self.config.url.host,
            port=int(self.config.url.port),
            keepalive=self.config.keepalive,
        )
        self.loop_start()

    def terminate(self):
        """Disconnect from client and join loop."""
        self.disconnect()
        self.loop_stop()
        BaseModule.terminate(self)

    def process(self):
        """Calls on this module should just happen upon an event."""
        yield self.env.event()

    def register_callbacks(self):
        """Register a callback to handle provisioned devices and entities.
        Registers two callbacks to the aliases:

        `alias="ProvisionedContextEntity"` for entities that are already
        provisioned at the OCB. Provisioning can be done via
        :class:`FiwareOCBEntityProvisioner`

        `alias="ProvisionedDevice"` for devices that are already
        provisioned at the IoTA. Provisioning can be done via
        :class:`FiwareIoTADeviceProvisioner`

        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_device, alias=Aliases.PROVISIONED_DEVICE
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_entity,
            alias=Aliases.PROVISIONED_CONTEXT_ENTITY,
        )

    def _subscribe_topic(self, topic: str):
        """Function that subscribes a specific MQTT topic and checks the
        return code if it was successful

        Args:
            topic (str): Topic to subscribe to

        Raises:
            ConnectionError if subscription was not successful
        """
        if topic in self._subscribed_topics:
            self.logger.debug("Topic already subscribed: %s", topic)
            return

        # subscribe to topic
        code, mid = self.subscribe(topic=topic, qos=self.config.qos)
        if code != 0:
            raise ConnectionError("Could not subscribe to %s", topic)
        self._subscribed_topics.append(topic)

    def _callback_to_entity(self, variable: AgentVariable):
        """Registers the entity in the module and subscribes necessary
        topics."""
        if not isinstance(variable.value, ContextEntity):
            return
        entity = variable.value

        if (entity.id, entity.type) in self._entity_identifiers:
            self.logger.debug(
                "Entity already registered: %s", (entity.id, entity.type)
            )
            return

        topic = fill_topic_pattern(
            pattern=self.config.topic_subscription_pattern,
            id=entity.id,
            type=entity.type,
        )
        self._subscribe_topic(topic)
        # We only append the device after subscription is done
        self._entity_identifiers.append((entity.id, entity.type))

    def _callback_to_device(self, variable: AgentVariable):
        """Registers the device in the module and subscribes necessary
        topics."""
        if not isinstance(variable.value, Device):
            return
        device = variable.value
        # Check if the device was already handled
        if (
            device.entity_name,
            device.entity_type,
        ) in self._entity_identifiers:
            self.logger.debug(
                "Device already registered: %s", device.device_id
            )
            return

        # construct topics
        topic = fill_topic_pattern(
            pattern=self.config.topic_subscription_pattern,
            id=device.entity_name,
            type=device.entity_type,
        )
        self.logger.debug("Subscribing to %s", topic)
        self._subscribe_topic(topic)
        # We only append the device after subscription is done
        self._entity_identifiers.append(
            (device.entity_name, device.entity_type)
        )


def mqtt_message_callback(
    client: MQTTCommunicatorReceiveFromOCB, userdata, message: MQTTMessage
) -> None:
    """Payload is expected to be in NGSI v2 Key-Value Format.

    Example:

    .. code-block:: json

        {
            "subscriptionId": "67dc384b3e806e788c0c5bbd",
            "data": [
                {
                    "id": "Device:001",
                    "type": "Device",
                    "commandAttribute": 39,
                    "anotherCommandAttribute": 39
                }
            ]
        }
    """
    # We try to extract any information from the actual topic, using
    # the supplied parsing string
    topic_info = extract_from_topic(
        topic=message.topic, pattern=client.config.topic_parsing_pattern
    )
    # If the parsing function did not match the pattern
    if topic_info is None:
        client.logger.error(
            "Extracting information from topic failed: %s", message.topic
        )
    # we parse the payload as json
    try:
        payload = json.loads(message.payload)
    except json.JSONDecodeError:
        client.logger.error(
            "Could not decode %s", message.payload.decode(), exc_info=True
        )
        return

    # the data is a list of dicts (in NGSIv2 key-values), iterate over it
    for data in payload["data"]:
        # if id and type are not in data KeyError is raised
        try:
            # Before we try to even do anything else we check if the
            # device/entity is registered in the module
            if (data["id"], data["type"]) not in client._entity_identifiers:
                client.logger.debug(
                    "Received message for unregistered entity: %s",
                    (data["id"], data["type"]),
                )
                continue
            # construct the AttributeUpdate
            var = AttributeUpdate(
                entity_id=data.pop("id"),  # pop so only attrs remain
                entity_type=data.pop("type"),  # pop so only attrs remain
                payload=data,
                additional_data=topic_info,
            )
        # can only be raised with id or type missing
        except KeyError:
            client.logger.error("Missing id or type in payload", exc_info=True)
            continue
        # since id and type have been popped before, everything
        # else is considered an attribute
        if not var.payload:
            client.logger.error("Payload is empty")
            return
        client.logger.info("Received payload on %s: %s", message.topic, data)
        client.agent.data_broker.send_variable(
            AgentVariable(
                value=var,
                alias=Aliases.MQTT_RECEIVED_FROM_FIWARE,
                name="MqttFromOCB",
                source=client.source,
            )
        )


def mqtt_callback_subscribe_on_connect(
    client: Client,
    userdata,
    flags: dict,
    code: int | ReasonCodes,
    properties: Properties = None,
) -> None:
    """The callback for when the client receives a CONNACK response from the server"""
    mqtt_connect_callback(client, userdata, flags, code, properties)
    client.logger.debug("Subscribing to topics")
    if client._subscribed_topics:
        subscription_list = [
            (topic, client.config.qos) for topic in client._subscribed_topics
        ]
        client.subscribe(topic=subscription_list)
