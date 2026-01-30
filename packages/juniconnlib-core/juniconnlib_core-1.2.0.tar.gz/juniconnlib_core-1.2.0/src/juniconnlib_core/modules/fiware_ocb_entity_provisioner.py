from datetime import datetime

from agentlib import Agent, AgentVariable
from agentlib.core import BaseModule, BaseModuleConfig
from filip.models import FiwareHeader
from filip.models.ngsi_v2.base import NamedMetadata
from filip.models.ngsi_v2.context import (
    ContextEntity,
    DataType,
    NamedContextAttribute,
)
from filip.utils import convert_datetime_to_iso_8601_with_z_suffix
from pydantic import AnyHttpUrl, Field
from requests import RequestException

from juniconnlib_core.utils.keycloak_oauth import KeycloakConfig
from juniconnlib_core.utils.keycloak_ocb import OAuthContextBroker
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases


class OCBEntityProvisionerConfig(BaseModuleConfig):
    """Configuration class for the :class:`FiwareOCBEntityProvisioner`"""

    fiware_header: FiwareHeader = Field(
        title="FIWARE Header",
        description="The corresponding FIWARE service and service path for the data",
    )
    location_fiware_header: FiwareHeader | None = Field(
        default=None,
        title="Location FIWARE Header",
        description="Meta information about the location of each device. Used to check if"
        " related locations exist",
    )
    cb_url: AnyHttpUrl = Field(
        title="Context Broker URL",
        description="Url of the FIWARE's Context Broker",
    )
    use_keycloak_oauth_cb: bool = Field(
        default=False,
        title="Use Keycloak Identity Management for Orion Context Broker",
        description="Flag whether to use the Keycloak JWT token for "
        "the FIWARE Orion Context Broker",
    )
    keycloak_config_cb: KeycloakConfig | None = None
    add_timestamps: bool = Field(
        default=True,
        title="Add TimeInstant attribute",
        description="Flag wether to add TimeInstant to each"
        " entity attribute and to global entity",
    )


class FiwareOCBEntityProvisioner(BaseModule):
    """This class can receive context entities from Agentlibs Databroker and
    provision or update those entities directly to the OCB"""

    config: OCBEntityProvisionerConfig

    def __init__(self, *, config: dict, agent: Agent):
        """Constructor for the :class:`FiwareOCBEntityProvisioner` module

        Args:
            config (dict): A dict containing configuration parameters as
                defined in :class:`OCBEntityProvisionerConfig`
            agent (agentlib.Agent): The agent for the initialization.
        """
        super().__init__(config=config, agent=agent)
        self.logger = create_logger_for_module(self)
        self._subscribed_entity_types = []
        if self.config.use_keycloak_oauth_cb:
            self.cb_client = OAuthContextBroker(
                ocb_url=self.config.cb_url,
                fiware_header=self.config.fiware_header,
                keycloak_config=self.config.keycloak_config_cb,
            )
            if self.config.location_fiware_header:
                self.cb_location_client = OAuthContextBroker(
                    ocb_url=self.config.cb_url,
                    fiware_header=self.config.location_fiware_header,
                    keycloak_config=self.config.keycloak_config_cb,
                )
        else:
            self.cb_client = OAuthContextBroker(
                ocb_url=self.config.cb_url,
                fiware_header=self.config.fiware_header,
            )
            if self.config.location_fiware_header:
                self.cb_location_client = OAuthContextBroker(
                    ocb_url=self.config.cb_url,
                    fiware_header=self.config.location_fiware_header,
                )

    def register_callbacks(self):
        """Register a callback to handle unprovisioned entities:

        `alias="UnprovisionedContextEntity"` for entities that are not yet
        provisioned at the OCB. The module provisions the device based on
        the configuration

        """
        self.logger.info("Register callback _send_entities_to_ocb_callback")
        alias = Aliases.UNPROVISIONED_CONTEXT_ENTITY
        self.agent.data_broker.register_callback(
            alias=alias,
            source=None,
            callback=self._send_entities_to_ocb_callback,
        )

    def _send_entities_to_ocb_callback(self, variable: AgentVariable):
        """This function checks if the `variable.value` is of type `ContextEntity`
        and posts it to the OCB.

        Before posting a "TimeInstant" metadata is added to all attributes
        of this entity if configured to do so.
        It is also checked whether related entity references do
        exist. If not an error is logged.

        Args:
            variable (AgentVariable): The variable containing an `ContextEntity`

        Returns:
            tuple[ContextEntity, Response]: A tuple containing the entity
                reference and the response of the POST
            ContextEntity: If no response is available it
        """
        entity = variable.value
        response = None
        if not isinstance(entity, ContextEntity):
            self.logger.error(f"Expected ContextEntity but got {type(entity)}")
            return
        self.logger.debug(
            f"_send_entities_to_ocb_callback with entitiy_id={entity.id}"
        )
        try:
            self._check_relationships(entity)
        except ValueError as error:
            self.logger.error(f"Error while checking relationships: {error}")
        if self.config.add_timestamps:
            entity = self.add_timestamps(entity)
        try:
            self.logger.info(f"Post entity with entitiy_id={entity.id}...")
            response = self.cb_client.post_entity(entity, update=True)
        except RequestException as exc:
            self.logger.error(
                msg=f"could not post entity: RequestException: {exc}"
            )
            self.logger.error(f"Entity={entity}")
            return
        # if self.config.create_subscriptions:
        #     self._create_subscriptions(entity)
        self.agent.data_broker.send_variable(
            AgentVariable(
                alias=Aliases.PROVISIONED_CONTEXT_ENTITY,
                value=entity,
                name="ProvisionedContextEntity",
            )
        )
        if response:
            return entity, response
        else:
            return entity

    @staticmethod
    def add_timestamps(entity: ContextEntity) -> ContextEntity:
        """This function adds an attribute 'TimeInstant' of the current
        datetime in ISO8601 format to the entity.

        The same TimeInstant is also added as metadata to each
        attribute.

        Args:
            entity (ContextEntity): The entity to add timestamps to.

        Returns:
            `ContextEntity`: The entity with timestamps added.
        """
        iso8601_datetime = convert_datetime_to_iso_8601_with_z_suffix(
            datetime.now()
        )
        attributes = entity.get_attributes()
        # TODO: This overwrites possible existing TimeInstant metadata
        #  which is unwanted behaviour imo. (sa.johnen)
        time_instant_metadata = NamedMetadata(
            name="TimeInstant", type=DataType.DATETIME, value=iso8601_datetime
        )
        updated_attributes = []
        for attribute in attributes:
            attribute.metadata["TimeInstant"] = time_instant_metadata
            updated_attributes.append(attribute)
        entity.update_attribute(updated_attributes)
        time_instant_attribute = NamedContextAttribute(
            name="TimeInstant", value=iso8601_datetime, type=DataType.DATETIME
        )
        entity.add_attributes([time_instant_attribute])
        return entity

    def _check_relationships(self, entity: ContextEntity) -> None:
        """For each relationship of the entity, this function checks whether
        the corresponding entity exists in the orion context broker.

        Args:
            entity (ContextEntity): The entity to check the relationships of

        Raises:
            ValueError if entity with related ID is not found
        """
        relationships = entity.get_relationships()
        not_found = []
        for relationship in relationships:
            related_entities = relationship.value
            if related_entities is None:
                return
            if not isinstance(related_entities, list):
                related_entities = [related_entities]
            for related_entity_id in related_entities:
                # The entity type is normally included inside the id e.g. type "Room"
                # inside "urn:ngsi-ld:Room:001"
                related_entity_type = related_entity_id.split(":")[2]
                client = self._choose_cb_client_for_entity_type(
                    related_entity_type
                )
                if not client.does_entity_exist(
                    entity_id=related_entity_id,
                    entity_type=related_entity_type,
                ):
                    not_found.append(relationship.value)
        if not_found:
            raise ValueError(
                f"For entity {entity.id} following Relationships were not "
                f"found in OCB: {not_found} "
            )

    def _choose_cb_client_for_entity_type(
        self, entity_type: str
    ) -> OAuthContextBroker:
        """Some entities are stored in a different service and therefore
        another OCB client instance is needed to do requests to this service.

        This method chooses the location client which uses the location
        fiware header for location related entity types.

        Args:
            entity_type (str): The entity type for is to be provisioned

        Returns:
            OAuthContextBroker: The OCB client instance

        Raises:
            AttributeError if cb_location_client was not configured.
        """
        if entity_type in ["Building", "Wing", "Room"]:
            if not self.config.location_fiware_header:
                raise AttributeError(
                    f"Location Fiware Header not configured but location"
                    f"client needed for entity type {entity_type}."
                    f"Add location_fiware_header to config.json"
                )
            return self.cb_location_client
        else:
            return self.cb_client

    def process(self):
        """Yield statement gives back control over simulation flow to event
        manager of environment"""
        yield self.env.event()
