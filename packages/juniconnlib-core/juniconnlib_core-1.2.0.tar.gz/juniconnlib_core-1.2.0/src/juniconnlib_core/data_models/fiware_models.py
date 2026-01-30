import re
from typing import Any, Literal, Type

from filip.models import FiwareHeader
from filip.models.ngsi_v2.context import ContextAttribute, ContextEntity
from pydantic import Field, field_validator


def generate_entity_id(entity_type: str, entity_content: Any) -> str:
    """Generate an entity id based on the entity type and entity content.

    Args:
        entity_type (str): Type of the entity, e.g. Building, Wing, MessdasMeter
        entity_content (Any): Hashable object, e.g. 0970, 0130_W, 0130_W_2001A, etc.

    Returns:
        unique FIWARE entity id based on a SHAKE256 hash of the `entity_content`.
    """
    from hashlib import shake_256

    plain_id = f"{entity_type}_{entity_content}".encode("utf-8")
    hash_id = shake_256(plain_id).hexdigest(16)

    return f"urn:ngsi-ld:{entity_type}:{hash_id}"


def generate_api_key(
    fiware_header: FiwareHeader, entity_type: str, resource: str = "/iot/json"
) -> str:
    """Generate a unique API key based on the FIWARE service, entity type and
    resource.

    Args:
        fiware_header (FiwareHeader): FIWARE header.
        entity_type (str): Type of the entity or more specific device.
        resource (str): Resource of the devices service group (default is "/iot/json").

    Returns:
        Unique API key.
    """
    from hashlib import shake_256

    plain_id = (
        f"{fiware_header.service}_{fiware_header.service_path}_"
        f"{entity_type}_{resource}"
    ).encode("utf-8")
    return shake_256(plain_id).hexdigest(16)


class BuildingNumber(ContextAttribute):
    """A string of four numbers to identify a building. The
    :class:`BuildingNumber` is meant to be used as an attribute in a
    `ContextEntity`. The building number should be a string consisting of
    exactly four numbers. For any further usage this formatting of four digits
    is called the "standardized format".

    A certain amount of conversion between incompatible formats is done
    as shown in examples.

    Examples:
        9.7 -> 0970
        10.21 -> 1021
        02.1 -> 0210
    """

    value: str = Field(
        title="Building number",
        description="Building number in the standardized format, e.g. 0970, 1021, etc.",
    )

    @field_validator("value")
    def validate_number(cls, building_number: str) -> str:
        """Validate building number. It must be in the standardized format,
        e.g. 0970, 1021, etc.

        For more information on the standardized format, please take a
        look at :class:juniconnlib_core.data_models.fiware_models.BuildingNumber

        Args:
            building_number: building number to validate.

        Returns:
            str: building number in case of the corrected format.

        Raises:
            ValueError: If building number is not in the
                standard format (four digits).
        """
        number = BuildingNumber.normalize_building_number_format(
            building_number
        )
        if number != building_number:
            raise ValueError(
                "Building number has a wrong format! Expected the "
                "standardized format, e.g. 0970, 1021, etc."
            )
        return building_number

    @classmethod
    def normalize_building_number_format(cls, building_number: str) -> str:
        """Format the supplied `building_number` in the standardized format.

        In practice, the buildings are named similar to: 02.1, 12.15, 09.7
        In the standardized format: 0210, 1215, 0970. Some have 15.83-A,
        so the regex can be a little more complex. It's idempotent if
        building_number is already in standardized format or any other
        format lacking a '.'

        Args:
            building_number (str): e.g. 09.7

        Returns:
            str: The normalized number e.g. 0970
        """
        if re.match(r"^\d{4}(\D*)", building_number):
            return building_number

        parts = building_number.split(".")
        # add leading or trailing zero if necessary
        area_number = re.sub(r"^(\d)$", r"0\g<1>", parts[0])
        part2 = re.sub(r"^(\d)(\D*)$", r"\g<1>0\g<2>", parts[1])

        return f"{area_number}{part2}"


class Building(ContextEntity):
    """A data model based `ContextEntity` used as representation of a single
    building as FIWARE entity. It holds a number for the building in addition
    to some other data like area.

    For more information on the standardized format, please take a
    look at :class:juniconnlib_core.data_models.fiware_models.BuildingNumber

    This class is meant to be used in scope of the FZJ campus, but can
    easily be used for buildings outside this scope as well."""

    type: Literal["Building"] = Field(description="Entity type 'Building'")
    number: BuildingNumber | ContextAttribute = Field(
        title="Building number",
        description="Building number in the standardized format, e.g. "
        "0970, 1021, etc. or or `ContextAttribute`",
    )
    area: ContextAttribute = Field(
        description="`ContextAttribute`-object containing the area of the "
        "building in [m^2]"
    )
    year: ContextAttribute = Field(
        description="`ContextAttribute`-object containing the year "
        "of the building."
    )

    @field_validator("number")
    def cast_to_building_number(cls, v):
        """Convert a possible `ContextAttribute` to a `BuildingNumber` instance"""
        if isinstance(v, ContextAttribute):
            v = BuildingNumber(**dict(v))
        return v

    @classmethod
    def generate_building_id(
        cls: Type["Building"], building_number: str
    ) -> "str":
        """Generates a FIWARE building ID from a building number.

        Args:
            building_number (str):  building number in the standardized
                format, e.g. 0970, 1021, etc.

        Returns:
            FIWARE building entity ID.
        """
        entity_content = BuildingNumber.normalize_building_number_format(
            building_number
        )
        return generate_entity_id(
            "Building", entity_content=entity_content
        )  # TODO: should use the type attribute instead of the hardcoded string, but that is not working?

    @field_validator("number", mode="before")
    def convert_from_context_entity(cls, value):
        if isinstance(value, ContextAttribute):
            return value.model_dump()
        return value


class Wing(ContextEntity):
    type: Literal["Wing"] = Field(description="Has to be 'Wing'")
    # _WING_TYPE = 'Wing'
    refBuilding: ContextAttribute = Field(description="number of the building")
    number: ContextAttribute = Field(
        description="letter of the wing, e.g. U, V, W"
    )

    @field_validator("number")
    def validate_number(cls, number: ContextAttribute):
        """Validate building number.

        Args:
            number (ContextAttribute): Wing number as ContextAttribute

        Returns:
            ContextAttribute: building number

        Raises:
            ValueError: In case the value of the ContextAttribute is
                not an uppercase letter
        """
        if not number.value.isupper():
            raise ValueError(
                "Wing number has a wrong format! Expected upper case, e.g. U, V, W etc."
            )
        return number

    @classmethod
    def generate_wing_id(
        cls: Type["Wing"], wing_number: str, building_number: str
    ) -> "str":
        """Generates a FIWARE wing id by hashing a wing letter and building number.

        Args:
            wing_number (str): letter of the wing, e.g. U, V, W
            building_number (str): building number in the standardized

        Returns:
            str: wing entity ID
        """
        normalized_building_number = (
            BuildingNumber.normalize_building_number_format(building_number)
        )
        normalized_wing_number = wing_number.upper()
        wing_entity_content = (
            f"{normalized_building_number}_{normalized_wing_number}"
        )
        return generate_entity_id(
            entity_type="Wing", entity_content=wing_entity_content
        )


class Room(ContextEntity):
    type: Literal["Room"] = Field(description="Has to be 'Room'")
    # _ROOM_TYPE = 'Room'
    refBuilding: ContextAttribute = Field(description="id of the building")
    refWing: ContextAttribute = Field(description="id of the wing")
    number: ContextAttribute = Field(
        description="number of the room, e.g. 300, 4002, 120a"
    )

    @field_validator("number")
    def validate_number(cls, number: ContextAttribute):
        """Room numbers have very different formats, so for now no validation
        is done."""
        return number

    @classmethod
    def generate_room_id(
        cls: Type["Room"],
        room_number: str,
        wing_number: str,
        building_number: str,
    ) -> "str":
        """Generates a FIWARE room id by hashing a room descriptor, wing
        letter and building number.

        Args:
            room_number (str): number of the room, e.g. 300, 4002, 120a
            wing_number (str): number of the wing, e.g. U, V, W
            building_number (str): building number in the standardized format
        """
        normalized_building_number = (
            BuildingNumber.normalize_building_number_format(building_number)
        )
        normalized_wing_number = wing_number.upper()
        normalized_room_number = room_number.upper()
        room_entity_content = f"{normalized_building_number}_{normalized_wing_number}_{normalized_room_number}"
        return generate_entity_id(
            entity_type="Room", entity_content=room_entity_content
        )
