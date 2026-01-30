"""
General Fiware Provisioner Class Provisions Fiware Devices and Service
Groups.
"""

from queue import Queue

from agentlib.core import Agent, AgentVariable, BaseModule, BaseModuleConfig
from filip.models import FiwareHeader
from filip.models.base import DataType
from filip.models.ngsi_v2.iot import Device, ServiceGroup
from pydantic import AnyHttpUrl, Field, model_validator
from requests.exceptions import HTTPError

from juniconnlib_core.utils.keycloak_iota import OAuthIoTAgentClient
from juniconnlib_core.utils.keycloak_oauth import KeycloakConfig
from juniconnlib_core.utils.keycloak_ocb import OAuthContextBroker
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases


class FiwareIotaDeviceProvisionerConfig(BaseModuleConfig):
    """Config Parameters for the Fiware Provisioner."""

    iota_url: AnyHttpUrl = Field(
        title="IoT Agent", description="Host of the IoT Agent."
    )
    cb_url: AnyHttpUrl = Field(
        title="ContextBroker Client",
        description="URL of the Orion Context Broker Client",
    )
    device_fiware_header: FiwareHeader = Field(
        title="FIWARE Header",
        description="Meta information for FIWARE's multi tenancy mechanism.",
    )
    location_fiware_header: FiwareHeader | None = Field(
        default=None,
        title="Location FIWARE Header",
        description="Meta information about the location of each device",
    )
    use_keycloak_oauth_cb: bool = Field(
        default=False,
        title="Use Keycloak Identity Management for Orion Context Broker",
        description="Flag whether to use the Keycloak JWT token for "
        "the FIWARE Orion Context Broker",
    )
    keycloak_config_cb: KeycloakConfig | None = None
    use_keycloak_oauth_iota: bool = Field(
        default=False,
        title="Use Keycloak Identity Management for IoT Agent",
        description="Flag whether to use the Keycloak JWT token for "
        "the FIWARE IoT Agent",
    )
    keycloak_config_iota: KeycloakConfig | None = None
    wait_time: int = Field(
        default=3,
        title="Wait time in seconds",
        description="Time to wait for new incoming devices before pushing "
        "them to the iotagent",
    )
    max_package_size: int = Field(
        default=20,
        title="Maximal number of devices to be provisioned at once",
        description="Maximum number of devices to be send to the iotagent in "
        "one request",
    )
    device_request_limit: int = Field(
        default=20,
        title="Maximal number of devices to be requested from the iota at once",
        description="Maximum number of devices to be requested from the iotagent in "
        "one request",
    )

    @model_validator(mode="after")
    def check_keycloak_configs(self):
        if self.use_keycloak_oauth_cb and not self.keycloak_config_cb:
            raise ValueError(
                "Keycloak oauth for the Orion Context Broker "
                "should be used but the corresponding keycloak configuration is missing!"
            )
        if self.use_keycloak_oauth_iota and not self.keycloak_config_iota:
            raise ValueError(
                "Keycloak oauth for the FIWARE IoT agent should be used but "
                "the corresponding keycloak configuration is missing!"
            )
        return self

    class Config:
        """Pydantic internal model settings."""

        # pylint: disable=too-few-public-methods
        extra = "forbid"


class FiwareIoTADeviceProvisioner(BaseModule):
    """This module is for provisioning `Device` s at the IoT-Agent. The
    functionality of the module includes:

    * Provisioning of `Devices` in batches
    * Checking according References from `StaticDeviceAttributes` on the `OCB`
    * Provisioning `ServiceGroups`
    """

    config: FiwareIotaDeviceProvisionerConfig

    def __init__(self, config: dict, agent: Agent):
        """
        Initialize a FiwareIoTADeviceProvisioner.

        Args:
            config (dict): A dict containing configuration parameters as defined in :class:`FiwareIotaDeviceProvisionerConfig`
            agent (agentlib.Agent): The agent for the initialization.
        """
        super().__init__(config=config, agent=agent)
        # overwrite the logger of agent liv modules, since it has a fixed formatter
        self.logger = create_logger_for_module(self)
        self.stopping_module = False

        if self.config.use_keycloak_oauth_cb:
            self.cb_keycloak_config = self.config.keycloak_config_cb
            self.cb_client = OAuthContextBroker(
                fiware_header=self.config.device_fiware_header,
                ocb_url=self.config.cb_url,
                keycloak_config=self.cb_keycloak_config,
            )
            self.location_cb_client = OAuthContextBroker(
                fiware_header=self.config.location_fiware_header,
                ocb_url=self.config.cb_url,
                keycloak_config=self.cb_keycloak_config,
            )
        else:
            self.cb_client = OAuthContextBroker(
                fiware_header=self.config.device_fiware_header,
                ocb_url=self.config.cb_url,
            )
            self.location_cb_client = OAuthContextBroker(
                fiware_header=self.config.location_fiware_header,
                ocb_url=self.config.cb_url,
            )
        if self.config.use_keycloak_oauth_iota:
            self.iota_keycloak_config = self.config.keycloak_config_iota
            self.iota_client = OAuthIoTAgentClient(
                fiware_header=self.config.device_fiware_header,
                iota_url=self.config.iota_url,
                keycloak_config=self.iota_keycloak_config,
            )
        else:
            self.iota_client = OAuthIoTAgentClient(
                fiware_header=self.config.device_fiware_header,
                iota_url=self.config.iota_url,
            )

        # initialize provisioned_devices-list with existing devices
        # TODO: add pagination (specify limit and offset!)
        self.provisioned_devices = self._get_provisioned_devices()
        # self._subscribed_device_types = []
        self.devices = Queue()

    def register_callbacks(self):
        """
        Registers callback functions for provisioning devices and service
        groups.
        Listens to the variables with aliases:

        `alias = "UnprovisionedDevice"` for devices that are not already
        provisioned to the IoT-Agent. The module collects devices for a few
        seconds before posting in batches

        `alias = "UnprovisionedServiceGroup"` for service groups that are
        not already provisioned to the IoT-Agent . The module will try posting
        them

        Returns:
            None
        """
        # register callback for unprovisioned devices
        self.agent.data_broker.register_callback(
            callback=self._callback_device, alias=Aliases.UNPROVISIONED_DEVICE
        )
        # register callback for unprovisioned service groups
        self.agent.data_broker.register_callback(
            callback=self._callback_service_group,
            alias=Aliases.UNPROVISIONED_SERVICE_GROUP,
        )

    def _callback_device(self, variable: AgentVariable):
        """Checks if the device already exists.

        If not, the _provision_device-method is called to provision the
        device.
        """
        # check if it is a device
        if not isinstance(variable.value, Device):
            self.logger.error("Must be of type Device.")
            return
        self.logger.debug("Received unprovisioned device.")
        device = variable.value
        if self._check_static_attributes(device):
            for attribute in device.attributes:
                # since the filip currently needs an object_id, this is added
                if attribute.object_id is None:
                    attribute.object_id = attribute.name
            self.devices.put(device)
        else:
            self.logger.warning(
                "Some references for this device were not found"
            )

    # def _create_subscriptions(self, device):
    #     """
    #     creates subscriptions to specified attributes
    #     """
    #     device_type = device.entity_type
    #
    #     # check if a subscription was already made for this device type
    #     if device_type not in self._subscribed_device_types:
    #
    #         device_attributes = []
    #         if self.config.subscribe_all_dynamic_attributes:
    #             device_attributes += [attr.name for attr in device.attributes]
    #         if self.config.specified_attribute_subscriptions:
    #             device_attributes += [attr_name for attr_name in
    #                                   self.config.specified_attribute_subscriptions[device_type]
    #                                   if (attr_name in [attr.name for attr in device.attributes]
    #                                   or attr_name in [attr.name for attr in device.static_attributes])
    #                                   and attr_name not in device_attributes]
    #
    #         if device_attributes:
    #
    #             subscription_data = {
    #                 'description': f'Subscription for {device_type} device',
    #                 'subject': {
    #                     'entities': [{'idPattern': '.*', 'type': device_type}],
    #                     'condition': {'attrs': device_attributes}
    #                 },
    #                 'notification': {
    #                     'http': {'url': self.config.subscription_url},
    #                     'attrs': device_attributes,
    #                     'onlyChangedAttrs': True
    #                 }
    #             }
    #             subscription = Subscription(**subscription_data)
    #
    #             self.cb_client.post_subscription(subscription, update=True)
    #
    #             self.logger.info(f'Subscriptions created for {device_type}')
    #             self._subscribed_device_types.append(device_type)
    #         else:
    #             self.logger.debug(f'No subscriptions specified for {device_type}')
    #     else:
    #         self.logger.debug(f'Subscriptions for {device_type} device already exists')

    def _provision_devices(self, devices: list[Device]):
        """Provisions a list of devices on the IOTAgent.

        Args:
            devices (list[Device]: List of Devices to be provisioned
        """
        try:
            self.iota_client.post_devices(devices=devices, update=True)
            self.provisioned_devices += [
                device.device_id for device in devices
            ]
            for device in devices:
                self.logger.info(
                    f" Device {device.device_id} was successfully provisioned/updated in the Batch."
                )
                provisioned_device_var = AgentVariable(
                    value=device,
                    source=self.agent.id,
                    shared=True,
                    name="Device",
                    alias=Aliases.PROVISIONED_DEVICE,
                )
                self.agent.data_broker.send_variable(provisioned_device_var)
        except HTTPError as e:
            self.logger.warning(
                f"Devices could not be provisioned/updated to the IoTAgent ({e.response})."
            )

            self.logger.info("Trying to provision/update devices one by one")
            for device in devices:
                try:
                    self.iota_client.post_device(device=device, update=True)
                    self.logger.info(
                        f"Device {device.device_id} was successfully provisioned."
                    )
                    provisioned_device_var = AgentVariable(
                        value=device,
                        source=self.agent.id,
                        shared=True,
                        name="Device",
                        alias=Aliases.PROVISIONED_DEVICE,
                    )
                    self.agent.data_broker.send_variable(
                        provisioned_device_var
                    )
                except HTTPError as e:
                    try:
                        self.iota_client.get_device(device_id=device.device_id)
                        self.logger.warning(
                            f"Device {device.device_id} could not be updated in the IoTAgent "
                            f"({e.response})."
                        )
                        provisioned_device_var = AgentVariable(
                            value=device,
                            source=self.agent.id,
                            shared=True,
                            name="Device",
                            alias=Aliases.PROVISIONED_DEVICE,
                        )
                        self.agent.data_broker.send_variable(
                            provisioned_device_var
                        )
                    except HTTPError as e:
                        self.logger.error(
                            f"Device {device.device_id} could not be found in the IoTAgent "
                            f"({e.response})."
                        )

    def _check_static_attributes(self, device: Device) -> bool:
        """Checks the static attributes of the device. Especially checks
        if all attributes from type "Relationship" actually exist on ocb.

        Args:
            device (Device): Device to be checked
        """
        unresolved_refs = []
        for static_attr in device.static_attributes:
            # This warning is viable for any stat. attr., not just relations
            if static_attr.value is None:
                self.logger.warning(
                    f"Value of {static_attr.name} "
                    f"for {device.device_id} attribute is None"
                )
                continue
            # Guard clause for any stat. attr. that is not a relationship
            if not static_attr.type == DataType.RELATIONSHIP:
                continue
            # guard clause to prevent nesting of stat attrs via dict
            if isinstance(static_attr.value, dict):
                raise TypeError(
                    f"The value of the relationship {static_attr.name} "
                    f"shouldn't be a dictionary as it creates unnecessary "
                    f"nesting."
                )

            ids = static_attr.value
            # Since the StaticAttributeClass does data validation during
            # runtime, I don't think we receive anything else but list
            # as type for a Sequence
            if not isinstance(ids, list):
                ids = [ids]

            for id_ in ids:
                # not very likely, but still good to catch
                if not isinstance(id_, str):
                    raise TypeError("Relationship values must be a string")
                # choose ocb client to be the location client in case of
                # location reference. Pick device client for anything else
                if static_attr.name in ["refBuilding", "refWing", "refRoom"]:
                    client = self.location_cb_client
                    self.logger.debug("Resolving location reference")
                else:
                    client = self.cb_client
                    self.logger.debug("Resolving device reference")
                # TODO: In the future it might be a good idea to somehow
                #  mark location references instead of checking for the name.
                #  It is a possibility to have e.g. connectedBuilding
                #  or connectedRoom which should not be resolved in the
                #  device but the location service

                try:
                    client.get_entity(entity_id=id_)
                    self.logger.debug(f"Related Entity with id {id_} found.")
                    continue
                except HTTPError as e:
                    unresolved_refs.append(id_)
                    self.logger.error(
                        f"Static Attribute with ID {id_} of type "
                        f"Relationship of the Device {device.device_id} "
                        f"could not be found ({e.response})."
                    )
        # returning here instead of after the first unresolved reference,
        # allows error are logged for each one
        if unresolved_refs:
            return False
        # if nothing failed above or returned with False already, all refs
        # were resolved successfully
        return True

    def _callback_service_group(self, variable: AgentVariable):
        """Provisions a new service group."""
        if not isinstance(variable.value, ServiceGroup):
            raise TypeError("Must be of type Service Group.")
        self.logger.info("Received unprovisioned service group.")
        service_group = variable.value
        # TODO: Check if service group already exists?
        self.iota_client.post_group(service_group, update=True)
        provisioned_service_group = AgentVariable(
            value=service_group,
            source=self.source,
            shared=True,
            name="ServiceGroup",
            alias=Aliases.PROVISIONED_SERVICE_GROUP,
        )
        self.agent.data_broker.send_variable(provisioned_service_group)

    def _get_provisioned_devices(self):
        """Receives a list of devices and returns a list of device IDs."""
        device_ids = []
        offset = 0
        devices = self.iota_client.get_device_list(
            limit=self.config.device_request_limit, offset=offset
        )
        while devices:
            device_ids += [dev.device_id for dev in devices]
            if len(devices) < self.config.device_request_limit:
                return device_ids
            offset += self.config.device_request_limit
            devices = self.iota_client.get_device_list(
                limit=self.config.device_request_limit, offset=offset
            )

        return device_ids

    def process(self):
        """In a loop, take up to max_package_size devices out of the devices-
        queue to process.

        These devices are then provisioned.
        """
        while not self.stopping_module:
            devices = []
            count = 0
            while (
                not self.devices.empty()
                and count < self.config.max_package_size
            ):
                devices.append(self.devices.get())
                count += 1
            if devices:
                self._provision_devices(devices)
            yield self.env.timeout(self.config.wait_time)

    def terminate(self):
        super().terminate()
        self.stopping_module = True
