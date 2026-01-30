import abc
from typing import Literal

import requests
from agentlib import Agent, AgentVariable, BaseModule, BaseModuleConfig
from filip.custom_types import AnyMqttUrl
from filip.models.base import FiwareHeader
from filip.models.ngsi_v2 import ContextEntity
from filip.models.ngsi_v2.iot import Device, DeviceAttribute
from filip.models.ngsi_v2.subscriptions import (
    AttrsFormat,
    Http,
    Mqtt,
    Notification,
    Subject,
    Subscription,
)
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    FilePath,
    field_validator,
    model_validator,
)

from juniconnlib_core.data_models.basic_models import CredentialsConfig
from juniconnlib_core.utils.keycloak_oauth import KeycloakConfig
from juniconnlib_core.utils.keycloak_ocb import OAuthContextBroker
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases
from juniconnlib_core.utils.mqtt import fill_topic_pattern
from juniconnlib_core.utils.validators import (
    check_keycloak_config,
    check_mqtt_credentials,
    check_mqtt_topic,
)


class SubscriptionAttributeConfiguration(BaseModel):
    """A container class to store configuration on how the attributes are
    to be handled in the subscriptions"""

    subscribe_specific_attributes: list[str] = Field(
        default_factory=list,
        description="A list of specific attributes to add to the subscription",
        examples=["['temperature', 'humidity']", "['temperatureSetpoint']"],
    )
    subscribe_all_attributes: bool = Field(
        description="A flag that just adds all attributes to the subscription",
    )
    subscribe_dynamic_attributes: bool = Field(
        description="A flag to indicate if attributes that are considered "
        '"dynamic" are added to the subscription. In case of '
        "ContextEntity this is true for all attributes, for "
        "Device this only adds instances DeviceAttribute",
    )
    subscribe_isCommand_metadata: bool = Field(
        description="A flag to indicate if attributes with the 'isCommand'"
        "set to True should be included in the subscription",
    )


class FiwareSubscriptionFactoryConfig(BaseModuleConfig):
    """General subscription config shared between all subscription modules"""

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
    # TODO (sa.johnen): Might want to name this "module" instead of "global"
    global_subscription_config: SubscriptionAttributeConfiguration = Field(
        description="The global configuration for the specific instance "
        "of the module on how attributes in subscriptions "
        "are handled.",
        examples=[
            '{"subscribe_specific_attributes": [], '
            '"subscribe_all_attributes": True, '
            '"subscribe_dynamic_attributes": True, '
            '"subscribe_isCommand_metadata": True}',
        ],
    )
    entity_type_subscription_config: (
        dict[str, SubscriptionAttributeConfiguration] | None
    ) = Field(
        default={},
        description="Configuration for how attributes are handled in "
        "subscriptions that overwrites `gloabl_subscription_"
        "configuration` config on a type by type basis. Type "
        "refers to the `type` field incase of ContextEntity and "
        "`entity_type` for Device. The key of the dict is the type"
        " and the value is a configuration according to "
        "`gloabl_subscription_configuration`",
        examples=["{Sensor:  {...}, Actuator: {...}, AnotherType: {...}}"],
    )
    check_oauth_config = model_validator(mode="after")(check_keycloak_config)


class FiwareHttpSubscriptionConfig(FiwareSubscriptionFactoryConfig):
    """Specific Configuration for HTTP subscriptions."""

    url: AnyHttpUrl = Field(
        title="Host for a FIWARE Subscription with HTTP Notification",
        description="Complete url, including port and scheme",
        examples=["https://awesome-url.com:8001"],
    )


class FiwareMqttSubscriptionConfig(FiwareSubscriptionFactoryConfig):
    """Specific Configuration for MQTT subscriptions."""

    url: str | AnyMqttUrl = Field(
        title="Host for a  FIWARE Subscription with MQTT Notification",
        description="Complete url, including port and scheme of the mqtt broker",
        examples=["mqtt://mqtt-broker:1883"],
    )
    username: str | None = Field(
        default=None,
        title="MQTT Username",
        description="Username for the MQTT Broker",
        validate_default=True,
    )
    password: str | None = Field(
        default=None,
        title="MQTT password",
        description="Password for the MQTT Broker",
        validate_default=True,
    )
    credentials_file: FilePath | None = Field(
        default=None,
        title="Use Credentials file",
        description="A path to a JSON file containing username and password "
        "for the MQTT Broker",
        validate_default=True,
    )
    topic: str = Field(
        title="Host for a  FIWARE Subscription with MQTT Notification",
        description="topic that should be used for sending the NGSI "
        "notification to. Allowed dynamic replacements are:"
        "${id}, ${type}, ${service}, ${service_path}. For "
        "Devices id and type are filled with entity_name "
        "and entity_type",
        examples=["pre/fix/${type}/between/${id}/suffix"],
    )
    qos: Literal[0, 1, 2] = Field(
        title="Quality of Service",
        default=2,
        description="Service Quality level to be used for publish "
        "caused by the subscription",
    )

    valid_credentials = model_validator(mode="after")(check_mqtt_credentials)
    valid_topic = field_validator("topic", mode="after")(check_mqtt_topic)

    @model_validator(mode="after")
    def check_mqtt_configuration(self):
        if (self.url and not self.topic) or (not self.url and self.topic):
            raise ValueError(
                "When using MQTT Notifications, both url "
                "and topic must be defined"
            )
        return self


class FiwareSubscriptionHandler(BaseModule, abc.ABC):
    """Base class for modules that are creating subscriptions.
    Common functionality and certain abstract functions are defined here."""

    config: FiwareSubscriptionFactoryConfig

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config=config, agent=agent)
        self._subscriptions = {}
        # overwrite the logger of agentlib modules, since it has a
        # fixed formatter
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

    def register_callbacks(self):
        """The callbacks should be implemented by the subclasses"""
        pass

    def process(self):
        yield self.env.event()

    @abc.abstractmethod
    def _construct_subject(self, **kwargs) -> Subject: ...

    @abc.abstractmethod
    def _construct_notification(self, **kwargs) -> Notification: ...

    def _check_device_variable(self, variable: AgentVariable) -> Device | None:
        """Checks if the content of the AgentVariable is a device and if a
        subscription is already created for the according device type.

        Args:
            variable (AgentVariable): variable containing a `Device`

        Returns:
            Device: If content is device
            None: If `variable.value` is not of type `Device` or
                subscription already exists
        """
        if not isinstance(variable.value, Device):
            return
        # extract the attributes relevant for subscription
        device = variable.value
        # Check if there is a subscription for the according type already
        if device.entity_type in self._subscriptions:
            self.logger.debug(
                f"Subscription for {device.entity_type} already exists"
            )
            return
        return device

    def _check_entity_variable(
        self, variable: AgentVariable
    ) -> ContextEntity | None:
        """Checks if the content of the AgentVariable is an entity and if a
        subscription is already created for the according type.

        Args:
            variable (AgentVariable): variable containing a `ContextEntity`

        Returns:
            ContextEntity: If content is `ContextEntity`
            None: If `variable.value` is not of type device or
                subscription already exists
        """
        if not isinstance(variable.value, ContextEntity):
            return
        # extract the attributes relevant for subscription
        entity = variable.value
        # Check if there is a subscription for the according type already
        if entity.type in self._subscriptions:
            self.logger.debug(f"Subscription for {entity.type} already exists")
            return
        return entity

    def _get_attrs_from_device(self, device: Device) -> list[str] | None:
        """Collects attributes (static and dynamic) from a device, based
        on the module configuration. Type specific configuration is prioritised
        over global config. This function should be independent of the specific
        implementation         of subscription module.

        Args:
            device (Device): Device in question

        Returns:
            None: if variable is either not device or no subscription
                attributes are supplied
            list[str]: a list of attributes to be subscribed to
        """
        try:
            config = self.config.entity_type_subscription_config[
                device.entity_type
            ]
            self.logger.debug(
                "Using specific configuration for %s", device.entity_type
            )
        except KeyError:
            config = self.config.global_subscription_config
            self.logger.debug("Using global subscription config")

        # check first if all attributes are to be used (avoids the logic below)
        if config.subscribe_all_attributes:
            return [
                attr.name
                for attr in device.attributes + device.static_attributes
            ]

        attrs = set()  # using a set to avoid duplicates
        # iterate over all static and dynamic attributes and check
        for attr in device.attributes + device.static_attributes:
            # check if all dynamic attributes are to be used (add if applicable)
            if config.subscribe_dynamic_attributes and isinstance(
                attr, DeviceAttribute
            ):
                attrs.add(attr.name)
            # if attr is not added already, check of the according metadata
            elif (
                config.subscribe_isCommand_metadata
                and "isCommand" in attr.metadata
            ):
                if attr.metadata["isCommand"].value:
                    attrs.add(attr.name)

        # add any specific attributes not yet added
        if config.subscribe_specific_attributes:
            attrs.update(config.subscribe_specific_attributes)

        # We want to make sure the order is always aphabetical so the
        # same device always produces the same list (for comparing
        # against subscriptions from the OCB). As sets are subsject to
        # the hashing seed that is generated every run, the order can
        # change between runs
        return sorted(attrs)

    def _get_attrs_from_entity(
        self, entity: ContextEntity
    ) -> list[str] | None:
        """Collects attributes from a context entity, based
        on the module configuration. Type specific configuration is prioritised
        over global config. Since entities don't differentiate between dynamic
        and static attributes `self.config.subscribe_all_attributes` and
        `self.config.subscribe_dynamic_attributes` are equivalent.
        This function should be independent of the specific implementation
        of subscription module.

        Args:
            entity (ContextEntity): ContextEntity in question

        Returns:
            list[str]: a list of attributes to be subscribed to
            None: if variable is either not an entity or no subscription
                attributes are supplied
        """
        try:
            config = self.config.entity_type_subscription_config[entity.type]
            self.logger.debug(
                "Using specific configuration for %s", entity.type
            )
        except KeyError:
            self.logger.debug("Using global subscription config")
            config = self.config.global_subscription_config

        # check first if all attributes are to be used (avoids the logic below)
        if config.subscribe_all_attributes:
            return [attr.name for attr in entity.get_attributes()]

        attrs = set()  # using a set to avoid duplicates
        # iterate over all static and dynamic attributes and check
        for attr in entity.get_attributes():
            # check if all dynamic attributes are to be used (add if applicable)
            if config.subscribe_dynamic_attributes:
                attrs.add(attr.name)
            # if attr is not added already, check of the according metadata
            elif (
                config.subscribe_isCommand_metadata
                and "isCommand" in attr.metadata
            ):
                if attr.metadata["isCommand"].value:
                    attrs.add(attr.name)

        # add any specific attributes not yet added
        if config.subscribe_specific_attributes:
            attrs.update(config.subscribe_specific_attributes)

        # We want to make sure the order is always aphabetical so the
        # same device always produces the same list (for comparing
        # against subscriptions from the OCB). As sets are subsject to
        # the hashing seed that is generated every run, the order can
        # change between runs
        return sorted(attrs)

    def subscription_factory(
        self,
        subject_params: dict | None = None,
        notification_params: dict | None = None,
        description: str | None = None,
    ) -> Subscription:
        """The factory type function calls the module specific implementations
        of `_construct_notification` and `_construct_subject` to construct
        a `Subscription` isntance.

        Args:
            subject_params (dict, optional): parameters to be passed
                on to `_construct_subject`
            notification_params (dict, optional): parameters to be passed
             on to `_construct_notification`
            description (str, optional): Description for the `Subscription`

        Return:
            Subscription: Constructed subscription
        """
        # Check if there are additional parameters for the construction methods
        if subject_params is None:
            subject_params = {}
        if notification_params is None:
            notification_params = {}
        # call the notification constructor with possible additional args
        notification = self._construct_notification(**notification_params)
        # call subject constructor with possible addition args
        subject = self._construct_subject(**subject_params)
        return Subscription(
            description=description, notification=notification, subject=subject
        )

    def _post_subscription(self, subscription: Subscription, key: str):
        """Posts a `Subscription` to the OCB

        Args:
            subscription (Subscription): Subscription to be posted
            key (str): The key that is to be used to keep track of already
            posted subscriptions (e.g. the fiware type for the
            entity/device in question)
        """
        try:
            id_ = self.cb_client.post_subscription(subscription)
        except requests.RequestException:
            self.logger.error(
                f"Unsuccessful at posting "
                f"subscription: {subscription.description}",
                exc_info=True,
            )
            return

        # if a subscription was posted, just add it to the dict subscriptions
        subscription.id = id_
        self._subscriptions[key] = subscription
        return id_

    # @staticmethod
    def _subject_for_type_and_attrs(
        self, type_: str, attrs: list[str]
    ) -> Subject:
        """A simple function that constructs a Subject for the subscriptions
        (likely to be extended in the future)

        Args:
            type_ (str): The entry for the type in the entities field
            attrs (list[str]): A list of attributes for the condition field

        Returns:
            Subject: The constructed subject (as filip class)
        """
        return Subject.model_validate(
            {
                "entities": [{"idPattern": ".*", "type": type_}],
                "condition": {"attrs": attrs},
            }
        )


class FiwareMQTTSubscriptionHandler(FiwareSubscriptionHandler):
    """Specific Implementation of :class:`FiwareSubscriptionHandler` for
    creating subscriptions with MQTT notifications. Currently, the payload
    format is fixed to key-value, as normalized produces large amounts of
    redundant data, that is somewhat going against to idea of using a
    simple protocol like MQTT.
    """

    config: FiwareMqttSubscriptionConfig

    def __init__(self, config: dict, agent: Agent):
        super().__init__(config=config, agent=agent)
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
            self._credentials = CredentialsConfig(username=None, password=None)

    # If at any point we need a more complex way of creating
    # subjects, we can replace this method
    _construct_subject = FiwareSubscriptionHandler._subject_for_type_and_attrs

    def _construct_notification(
        self, attrs: list[str], topic: str
    ) -> Notification:
        """Specific implementation of for creating an MQTT notifications.

        Args:
            attrs (list[str]): A list of attribute names for to be included
                in the notification
            topic (str): MQTT topic for the notification to be delivered to

        Returns:
            Notification: The constructed notification
        """
        mqtt = Mqtt(
            url=self.config.url,
            topic=topic,
            qos=self.config.qos,
            user=self._credentials.username,
            passwd=self._credentials.password,
        )
        return Notification(
            attrsFormat=AttrsFormat.KEY_VALUES,
            onlyChangedAttrs=True,
            attrs=attrs,
            mqtt=mqtt,
        )

    def register_callbacks(self):
        """Registers two callbacks for the aliases:

        `alias = "ProvisionedDevice": Creates a subscription per `entity_type`

        `alias = "ProvisionedContextEntity": Creates a subscription per `type`

        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_device, alias=Aliases.PROVISIONED_DEVICE
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_entity,
            alias=Aliases.PROVISIONED_CONTEXT_ENTITY,
        )

    def _callback_to_device(self, variable: AgentVariable):
        """Check if a subscription for this type already exists, if not
        construct it and post it.

        Args:
            variable (AgentVariable): variable containing a `Device`
        """
        device = self._check_device_variable(variable)
        if device is None:
            return

        attrs = self._get_attrs_from_device(device=device)
        if not attrs:
            self.logger.debug(
                f"No subscription attributes specified for {device.entity_type}"
            )
            return

        topic = fill_topic_pattern(
            pattern=self.config.topic,
            type=device.entity_type,
            id=device.entity_name,
            service=self.config.fiware_header.service,
            service_path=self.config.fiware_header.service_path,
        )
        subscription = self.subscription_factory(
            description=f"HTTP Subscription for {device.entity_type}",
            subject_params={"type_": device.entity_type, "attrs": attrs},
            notification_params={"attrs": attrs, "topic": topic},
        )
        self._post_subscription(subscription, device.entity_type)

    def _callback_to_entity(self, variable: AgentVariable):
        """Check if a subscription for this type already exists, if not
        construct it and post it.

        Args:
            variable (AgentVariable): variable containing a `ContextEntity`
        """
        entity = self._check_entity_variable(variable)
        if entity is None:
            return

        attrs = self._get_attrs_from_entity(entity=entity)
        if not attrs:
            self.logger.debug(
                f"No subscription attributes specified for {entity.type}"
            )
            return
        topic = fill_topic_pattern(
            pattern=self.config.topic,
            type=entity.type,
            id=entity.id,
            service=self.config.fiware_header.service,
            service_path=self.config.fiware_header.service_path,
        )
        subscription = self.subscription_factory(
            description=f"HTTP Subscription for {entity.type}",
            subject_params={"type_": entity.type, "attrs": attrs},
            notification_params={"attrs": attrs, "topic": topic},
        )
        self._post_subscription(subscription, entity.type)


class FiwareHTTPSubscriptionHandler(FiwareSubscriptionHandler):
    """Specific implementation of :class:`FiwareSubscriptionHandler` for
    creating subscriptions with HTTP notifications"""

    config: FiwareHttpSubscriptionConfig

    # If at any point we need a more complex way of creating
    # subjects, we can replace this method
    _construct_subject = FiwareSubscriptionHandler._subject_for_type_and_attrs

    def _construct_notification(self, attrs: list[str]) -> Notification:
        return Notification(
            onlyChangedAttrs=True,
            attrs=attrs,
            http=Http.model_validate({"url": self.config.url}),
        )

    def process(self):
        yield self.env.event()

    def register_callbacks(self):
        """Registers two callbacks for the aliases:

        `alias = "ProvisionedDevice": Creates a subscription per `entity_type`

        `alias = "ProvisionedContextEntity": Creates a subscription per `type`

        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_device, alias=Aliases.PROVISIONED_DEVICE
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_entity,
            alias=Aliases.PROVISIONED_CONTEXT_ENTITY,
        )

    def _callback_to_device(self, variable: AgentVariable):
        """Check if a subscription for this type already exists, if not
        construct it and post it.

        Args:
            variable (AgentVariable): variable containing a `Device`
        """
        device = self._check_device_variable(variable)
        if device is None:
            return

        attrs = self._get_attrs_from_device(device=device)
        if not attrs:
            self.logger.debug(
                f"No subscription attributes specified for {device.entity_type}"
            )
            return

        subscription = self.subscription_factory(
            description=f"HTTP Subscription for {device.entity_type}",
            subject_params={"type_": device.entity_type, "attrs": attrs},
            notification_params={"attrs": attrs},
        )
        self._post_subscription(subscription, device.entity_type)

    def _callback_to_entity(self, variable: AgentVariable):
        """Check if a subscription for this type already exists, if not
        construct it and post it.

        Args:
            variable (AgentVariable): variable containing a `ContextEntity`"""
        entity = self._check_entity_variable(variable)
        if entity is None:
            return

        attrs = self._get_attrs_from_entity(entity=entity)
        if not attrs:
            self.logger.debug(
                f"No subscription attributes specified for {entity.type}"
            )
            return

        subscription = self.subscription_factory(
            description=f"HTTP Subscription for {entity.type}",
            subject_params={"type_": entity.type, "attrs": attrs},
            notification_params={"attrs": attrs},
        )
        self._post_subscription(subscription, entity.type)
