import csv
import logging
import re
from enum import Enum
from typing import Dict, Union, get_args

from filip.models.base import DataType
from filip.models.ngsi_v2.context import ContextAttribute, ContextEntity
from pydantic_core import ValidationError
from requests import RequestException
from requests.exceptions import HTTPError

from juniconnlib_core.data_models.fiware_models import (
    Building,
    BuildingNumber,
    Room,
    Wing,
)
from juniconnlib_core.utils.keycloak_oauth import KeycloakConfig
from juniconnlib_core.utils.keycloak_ocb import OAuthContextBroker


class LocationReference(str, Enum):
    REF_BUILDING = "refBuilding"
    REF_WING = "refWing"
    REF_ROOM = "refRoom"


class LocationProvisioner:
    """Superclass for all location provisioners."""

    # TODO: (Why) do we need these type definitions?
    BUILDING_ENTITY_TYPE = "Building"
    WING_ENTITY_TYPE = "Wing"
    ROOM_ENTITY_TYPE = "Room"

    REFRESH_TOKEN_MAX_ATTEMPTS = 3

    def __init__(
        self, fiware_header, ocb_url, *, keycloak_config: KeycloakConfig = None
    ):
        """Constructor of :class:`LocationProvisioner`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            ocb_url (str): URL of the context broker

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloak configuration for
                the according service
        """
        self.logger = logging.getLogger(
            f"({self.__class__.__module__}.{self.__class__.__name__})"
        )
        self.oauth_ocb_client = OAuthContextBroker(
            fiware_header=fiware_header,
            ocb_url=ocb_url,
            keycloak_config=keycloak_config,
        )

        # make underlying functions more easily available
        self._get_entity = self.oauth_ocb_client.get_entity
        self._get_entity_list = self.oauth_ocb_client.get_entity_list
        self._post_entity = self.oauth_ocb_client.post_entity
        self._delete_entity = self.oauth_ocb_client.delete_entity


class BuildingProvisioner(LocationProvisioner):
    """Class provisioning Building-entities in FIWARE."""

    def __init__(
        self,
        fiware_header,
        ocb_url,
        file_path_building_data_csv=None,
        *,
        keycloak_config: KeycloakConfig = None,
    ):
        """Constructor of :class:`BuildingProvisioner`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            ocb_url (str): URL of the context broker
            file_path_building_data_csv (str): Path to a csv file containing
                additional information to a building entity (To be removed
                in future releases)

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloak configuration for
                the according service
        """
        super().__init__(
            fiware_header, ocb_url, keycloak_config=keycloak_config
        )
        # initialize building_entities
        self.buildings: Dict[str, Building] = {}
        self.buildings_data: Dict[str, dict] = {}
        if file_path_building_data_csv is not None:
            self.__fill_buildings_data_dict(file_path_building_data_csv)
        building_entities = self.get_building_entities_from_ocb()
        if building_entities:
            for be in building_entities:
                be = self.update_building_if_needed(be)
                self.__add_building_entity(be)

    def __add_building_entity(self, building_entity: ContextEntity) -> None:
        """Updates an internal dict of Building-entities provisioned on the
        OCB.

        Args:
            building_entity (ContextEntity): Building-entity to add

        Returns:
            None
        """
        self.buildings[building_entity.id] = Building(**dict(building_entity))

    def __fill_buildings_data_dict(self, path):
        """Reads from the given path and stores it in self.buildings_data.
        Columns for the csv file ['Building Nr']["Area [m2]"]["Year"].

        Args:
            path: The path to the csv file

        Returns:
            None
        """
        try:
            with open(path, newline="", encoding="utf-8-sig") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=";")
                for building in reader:
                    normalized_building_nr = (
                        BuildingNumber.normalize_building_number_format(
                            building["Building Nr"]
                        )
                    )
                    building_id = Building.generate_building_id(
                        building_number=normalized_building_nr
                    )
                    building_dict = {
                        "area": (
                            None
                            if building["Area [m2]"] == "None"
                            else building["Area [m2]"]
                        ),
                        "year": (
                            None
                            if building["Year"] == "None"
                            else building["Year"]
                        ),
                    }
                    self.buildings_data[building_id] = building_dict
        except FileNotFoundError as e:
            self.logger.warning(
                f"Could not find the File or file not given. Error: {e}"
            )

    def has_building_entity(self, building_nr: str) -> bool:
        """Checks if there is a Building entity with a given building number.

        Args:
            building_nr (str): The building number in normalized format
                (e.g. 0970, 1021, ...)

        Returns:
            bool: If the building entity exists
        """
        building_id = Building.generate_building_id(building_nr)
        return building_id in self.buildings

    def get_building_entities_from_ocb(self) -> list[ContextEntity]:
        """Retrieves entities of type Building from the OCB.

        Returns:
            list[ContextEntity]: Building entities returned by the OCB

        Raises:
            RequestException: Retrieval of entities did not succeed or
                authentication failed
        """
        try:
            return self._get_entity_list(
                entity_types=[LocationProvisioner.BUILDING_ENTITY_TYPE]
            )
        except RequestException as exc:
            self.logger.error(
                f"Could not retrieve building entities from the Orion Context Broker! Error: {exc}"
            )
            raise exc

    def create_new_building_entity_if_does_not_exist(
        self, building_nr: str
    ) -> Building:
        """Check whether the passed building has already been provisioned as a
        FIWARE entity. Create a corresponding FIWARE entity if the building is
        unknown on the server.

        Args:
            building_nr: Number of the building to provision in FIWARE

        Returns:
            Building: instance of Building model class
        """
        # TODO: Should we discard the normalization and just force the right formatting?
        normalized_building_nr = (
            BuildingNumber.normalize_building_number_format(building_nr)
        )
        building_id = Building.generate_building_id(
            building_number=normalized_building_nr
        )
        building_entity = self.buildings.get(building_id)
        if building_entity:
            return building_entity
        # check it on server
        try:
            building_entity = self._get_entity(entity_id=building_id)
            self.logger.info("Found building {} in OCB.".format(building_nr))
            building_entity = self.update_building_if_needed(building_entity)
            self.__add_building_entity(building_entity)
            return building_entity
        except Exception as exc:
            self.logger.warning(
                f"Could not find the building with number {normalized_building_nr} on the server. Error: {exc}"
            )

        building_entity = self.create_new_building(building_nr)
        self.__add_building_entity(building_entity)
        return building_entity

    def update_building_if_needed(
        self, building_entity: ContextEntity
    ) -> Building:
        """Check whether the passed ContextEntity is or can be made into a
        Building. If it can, it will try to update the ContextEntity. If it
        cant it will create a new Building corresponding to the passed building
        number.

        Args:
            building_entity: Building or ContextEntity to be updated if needed

        Returns:
            Building: instance of Building model class
        """
        try:
            building = Building(**dict(building_entity))
            if building.id not in self.buildings_data:
                return building
            return self.update_building(building)
        except ValidationError:
            self.logger.info(
                f"Updating building entity for building number "
                f"{building_entity.get_attribute('number').value} on the server"
            )
            return self.create_new_building(
                building_entity.get_attribute("number").value
            )

    def create_new_building(self, building_nr: str) -> Building:
        """Create FIWARE entity corresponding to the passed building number.

        Args:
            building_nr (str): Number of the building to provision in FIWARE

        Returns:
            instance of Building model class
        """
        normalized_building_nr = (
            BuildingNumber.normalize_building_number_format(building_nr)
        )
        building_id = Building.generate_building_id(
            building_number=normalized_building_nr
        )
        building_number = BuildingNumber(
            type=DataType.TEXT, value=normalized_building_nr
        )
        building_area = ContextAttribute(type=DataType.TEXT, value=None)
        building_year = ContextAttribute(type=DataType.TEXT, value=None)
        if building_id in self.buildings_data:
            building_area.value = self.buildings_data[building_id]["area"]
            building_year.value = self.buildings_data[building_id]["year"]
        building_entity = Building(
            id=building_id,
            type=get_args(Building.model_fields["type"].annotation)[0],
            number=building_number,
            area=building_area,
            year=building_year,
        )
        try:
            response = self._post_entity(entity=building_entity, update=True)
            self.logger.info(
                f"Created building with building number {normalized_building_nr} and ID: {response}"
            )
        except Exception as exc:
            self.logger.error(
                f"Could not provision building entity: {building_entity}. Error occured: {exc}"
            )

        return building_entity

    def update_building(self, building: Building) -> Building:
        """Updates a Building with the data from the file. Only updates with
        values and not None. Does not post if nothing changed.

        Args:
            building (Building): Building to be updated

        Returns:
            Building: Instance of Building
        """
        changed = False
        if (
            self.buildings_data[building.id]["area"]
            and building.area.value
            is not self.buildings_data[building.id]["area"]
        ):
            building.area.value = self.buildings_data[building.id]["area"]
            changed = True
        if (
            self.buildings_data[building.id]["year"]
            and building.year.value
            is not self.buildings_data[building.id]["year"]
        ):
            building.year.value = self.buildings_data[building.id]["year"]
            changed = True
        if changed:
            try:
                response = self._post_entity(entity=building, update=True)
                self.logger.info(
                    f"Created building with building number {building.get_attribute('number').value} and "
                    f"ID: {response}"
                )
            except HTTPError:
                self.logger.error(
                    f"Could not provision building entity: {building}"
                )

        return building


class WingProvisioner(LocationProvisioner):
    """Class provisioning Wing-entities in FIWARE."""

    def __init__(
        self,
        fiware_header,
        ocb_url,
        file_path_building_data_csv=None,
        *,
        keycloak_config: KeycloakConfig = None,
    ):
        """Constructor of :class:`WingProvisioner`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            ocb_url (str): URL of the context broker
            file_path_building_data_csv (str): Path to a csv file containing
                additional information to a building entity (To be removed
                in future releases)

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloak configuration for
                the according service
        """
        super().__init__(
            fiware_header, ocb_url, keycloak_config=keycloak_config
        )
        # a dictionary containing a Building-FIWARE-id as key and a list with building wings as value
        self.wings: Dict[str, Wing] = {}
        wing_entities = self.get_wing_entities_from_ocb()
        if wing_entities:
            for we in wing_entities:
                self.__add_wing_entity(we)
        self.building_provisioner = BuildingProvisioner(
            fiware_header,
            ocb_url,
            file_path_building_data_csv,
            keycloak_config=keycloak_config,
        )

    def __add_wing_entity(self, wing_entity: Union[Wing, dict]):
        """Updates an internal dict of Wing-entities provisioned on the
        OCB.

        Args:
            wing_entity (Union[Wing, dict]): Building-entity to add

        Returns:
            None
        """
        wing = Wing(**dict(wing_entity))
        self.wings[wing.id] = wing

    def get_wing_entities_from_ocb(self) -> list[ContextEntity]:
        """Retrieves entities of type Wing from the OCB.

        Returns:
            list[ContextEntity]: Wing entities returned by the OCB

        Raises:
            RequestException: Retrieval of entities did not succeed or
                authentication failed
        """
        return self._get_entity_list(
            entity_types=[LocationProvisioner.WING_ENTITY_TYPE]
        )

    def has_wing_entity(self, building_nr: str, wing_nr: str):
        """Checks if there is a Wing entity with a given building and
        wing number.

        Args:
            building_nr (str): The building number in normalized format
                (e.g. 0970, 1021, ...)
            wing_nr (str): The wing letter (e.g. U, V, ...)

        Returns:
            bool: If the wing entity exists
        """
        wing_id = Wing.generate_wing_id(
            building_number=building_nr, wing_number=wing_nr
        )
        return wing_id in self.wings

    def create_new_wing_entity_if_does_not_exist(
        self, wing_nr: str, building_nr: str
    ) -> ContextEntity | None:
        """Check whether the wing of the building has been already provisioned
        as a FIWARE entity. Create a corresponding wing FIWARE entity if the
        wing is unknown on the server. If necessary the corresponding building
        entity will be created, too.

        Args:
            wing_nr (str): wing number (e.g. 0970, 1021, ...)
            building_nr (str): building number (e.g. U, V, ...)

        Returns:
            ContextEntity: Wing-instance
        """
        wing_nr = wing_nr.upper()

        wing_id = Wing.generate_wing_id(
            building_number=building_nr, wing_number=wing_nr
        )
        if wing_id in self.wings:
            return self.wings[wing_id]
        try:
            self.logger.info("Getting wing entities from the FIWARE OCB...")
            we = self._get_entity(wing_id)
            self.wings[wing_id] = we
            return we
        except Exception as exc:
            self.logger.warning(
                f"Could not find the wing with number {wing_nr} for building {building_nr} on the server. Error: {exc}"
            )

        # provision wing, but first make sure the building is provisioned
        building_entity = self.building_provisioner.create_new_building_entity_if_does_not_exist(
            building_nr
        )
        building_id = building_entity.id
        self.logger.info(
            "No corresponding wing entity has been found on the FIWARE OCB. Provisioning one..."
        )

        current_wing_entity = Wing(
            id=wing_id,
            type=get_args(Wing.model_fields["type"].annotation)[0],
            number=ContextAttribute(type=DataType.TEXT, value=wing_nr),
            refBuilding=ContextAttribute(
                type=DataType.RELATIONSHIP, value=building_id
            ),
        )
        try:
            response = self._post_entity(
                entity=current_wing_entity, update=True
            )
            self.logger.info(
                f"Created wing with wing number {wing_nr} and ID: {response}"
            )
            self.__add_wing_entity(current_wing_entity)
            return current_wing_entity
        except Exception as exc:
            self.logger.error(
                f"Could not create Wing-entity: {current_wing_entity}. Error occured: {exc}"
            )

        return None


class RoomProvisioner(LocationProvisioner):
    """Class provisioning Room-entities in FIWARE."""

    def __init__(
        self,
        fiware_header,
        ocb_url,
        file_path_building_data_csv=None,
        *,
        keycloak_config: KeycloakConfig = None,
    ):
        """Constructor of :class:`RoomProvisioner`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            ocb_url (str): URL of the context broker
            file_path_building_data_csv (str): Path to a csv file containing
                additional information to a building entity (To be removed
                in future releases)

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloak configuration for
                the according service
        """
        super().__init__(
            fiware_header, ocb_url, keycloak_config=keycloak_config
        )
        self.rooms: Dict[str, Room] = {}  # List of room entities
        room_entities = self.get_room_entities_from_ocb()
        for room_e in room_entities:
            self.__add_room_entity(dict(room_e))
        self.wing_provisioner = WingProvisioner(
            fiware_header,
            ocb_url,
            file_path_building_data_csv,
            keycloak_config=keycloak_config,
        )

    def get_room_entity_from_ocb(self, room_id) -> ContextEntity:
        """Returns a specific 'Room'-Entity from the context broker.

        Args:
            room_id (str): The room for which to get the entity for

        Returns:
            ContextEntity: The room in question
        """
        return self._get_entity(entity_id=room_id)

    def get_room_entities_from_ocb(self) -> list[ContextEntity]:
        """Returns a list of all 'Room'-Entities from the context broker.

        Returns:
            list[ContextEntity]: The rooms in the defined FIWARE service
        """
        return self._get_entity_list(
            entity_types=[LocationProvisioner.ROOM_ENTITY_TYPE]
        )

    def __add_room_entity(self, room_entity: Union[Room, Dict]):
        """Updates an internal dict of Room-entities provisioned on the
        OCB.

        Args:
            room_entity (ContextEntity): Room-entity to add

        Returns:
            None
        """
        room = Room(**dict(room_entity))
        self.rooms[room.id] = room

    def create_new_room_entity_if_does_not_exist(
        self, room_nr: str, wing_nr: str, building_nr: str
    ) -> Room:
        """Check if a room is already provisioned, if not provision it via the
        context broker. This also includes the check for the corresponding wing
        and building, since a room can't be provisioned without a reference to
        the wing- and building-entity. Therefore this functions also checks if
        they already exist and provisions them if necassary.

        Args:
            room_nr (str): room number (e.g. R102, 1004, ...)
            wing_nr (str): wing number (e.g. U, V, ...)
            building_nr (str): building number (e.g. 1021, 0970, ...)

        Returns:
            ContextEntity: Room-instance
        """
        room_nr = room_nr.upper()
        wing_nr = wing_nr.upper()

        # look for the ID of the Entity in the room-list
        room_id = Room.generate_room_id(
            room_number=room_nr,
            wing_number=wing_nr,
            building_number=building_nr,
        )
        if room_id in self.rooms:
            return self.rooms[room_id]
        # room wasnt found in the already saved list, look for it on the contextbroker
        try:
            self.logger.info("Look for room entitiy from the FIWARE OCB...")
            room_fiware = self.get_room_entity_from_ocb(room_id)
            self.__add_room_entity(room_fiware)
            logging.info(
                f"room {room_nr} building {building_nr} wing {wing_nr} already exists "
            )
            return Room(**dict(room_fiware[0]))

        except Exception as exc:
            self.logger.warning(
                f"Could not find room {room_nr}, wing {wing_nr}, building {building_nr} on the server. Error: {exc}"
            )

        # room was not found and has to be created
        self.logger.info(
            "No corresponding room entity has been found on the FIWARE OCB. Provisioning one..."
        )
        # check if wing already exist
        # provisoin wing (wingprovisioner also checks for building)
        wing_entity = (
            self.wing_provisioner.create_new_wing_entity_if_does_not_exist(
                wing_nr, building_nr
            )
        )
        wing_id = wing_entity.id
        building_id = wing_entity.refBuilding.value

        current_room_entity = Room(
            id=room_id,
            type=get_args(Room.model_fields["type"].annotation)[0],
            number=ContextAttribute(type=DataType.TEXT, value=room_nr),
            refWing=ContextAttribute(
                type=DataType.RELATIONSHIP, value=wing_id
            ),
            refBuilding=ContextAttribute(
                type=DataType.RELATIONSHIP, value=building_id
            ),
        )
        try:
            response = self._post_entity(
                entity=current_room_entity, update=True
            )
            self.logger.info(
                f"Created room with room number {room_nr} and ID: {response}"
            )
            self.__add_room_entity(current_room_entity)
            return current_room_entity
        except Exception as exc:
            self.logger.error(
                f"Could not create Room-entity: {current_room_entity}. Error occured: {exc}"
            )

        return None


def extract_location_from_waldo_id(location_id) -> tuple[Building, Wing, Room]:
    """Returns building, wing and room as strings for a given WALDO location ID
    (They look like this: B0970U_R300B)

    Args:
        location_id (str): WALDO location ID

    Returns:
        tuple[Building, Wing, Room]: The extracted numbers for Building,
            Wing and Room

    Raises:
        ValueError: Was not able to extract one or more number identifiers
            from `location_id`
    """
    # RE_ROOM_GUID_INDEXED = re.compile(r'^B(\d{4})([A-Z])_R(.+)$')
    RE_ROOM_GUID_NAMED = re.compile(
        r"^B(?P<building_code>\d{4})(?P<building_wing>[A-Z])_R(?P<room_number>.+)$"
    )

    m = RE_ROOM_GUID_NAMED.match(location_id)
    if not m:
        msg = (
            f"Could not match Room {location_id} to "
            f"pattern {RE_ROOM_GUID_NAMED.pattern}"
        )
        logging.error(msg)
        raise ValueError(msg)
    building = m.group("building_code")
    wing = m.group("building_wing")
    room = m.group("room_number")

    return building, wing, room


class CampusDefinitions:
    """The agglomeration of a building stock is called a campus. This campus
    is represented as a building with number 00.00 and the wing 'U'

    This class is meant to be used in scope of the FZJ campus, but can
    easily be used for buildings outside this scope as well."""

    BUILDING = "0000"
    WING = "U"
