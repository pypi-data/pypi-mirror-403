import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from fidere.models import Identifier
from pydantic import BaseModel, ConfigDict, Field, field_serializer


def timestamp_with_timezone():
    return dt.datetime.now(tz=dt.timezone.utc)


class Location(BaseModel):
    """Representation of a single location.

    It can either identify a specific room together with the building
    and precise wing it is situated in or a specific wing together with
    the according building.

    The class is mainly planned to be used in context of the FZJ campus.
    """

    building: str = Field(
        description="Building number in a standardized format consisting "
        "of just 4"
        "e.g. 2.1 -> 0210, 12.15 -> 1215, 9.7 -> 0970, etc.",
    )
    wing: str = Field(
        description="Building wing, e.g. U, V, Z. The wing is mandatory."
    )
    room: str | None = Field(default=None, description="Room number")

    class Config:
        extra = "ignore"

    @classmethod
    def number2code(cls: Type[BaseModel], building_number: str | int) -> str:
        """This function transforms buildings names like "02.1", "12.15"
        into the standardized format "0210", "1215".

        For more information on the standardized format, please take a
        look at :class:juniconnlib_core.data_models.fiware_models.BuildingNumber

        Args:
            building_number (str, int): number of the building

        Returns:
            building code in the standardized format, e.g. 0210, 1215, 0970
        """
        if re.match(r"^\d{4}(\D*)", building_number):
            return building_number
        # return '{0[0]:0>2}{0[1]:0<2}'.format(building_number.split('.'))
        # simpler to understand is below:
        # (Does the replacement by adding '0' only if after removing ".", we don't have a 4-digit number.)
        # We keep the building wing, if present.
        return re.sub(
            r"^(\d{3})(\D*)$", r"\g<1>0\g<2>", building_number.replace(".", "")
        )


class AttributeUpdate(BaseModel):
    """Representation of an attribute update of a FIWARE entity.

    This is meant to be used as a container for all necessary information
    needed to exchange information on updates for or from FIWARE attributes"""

    entity_id: str = Field(description="FIWARE entity identifier")
    entity_type: str = Field(description="FIWARE entity type")
    payload: dict[str, Any] = Field(description="MQTT payload")
    timestamp: dt.datetime | None = Field(
        description="Timestamp when the attribute update was initiated",
        default_factory=timestamp_with_timezone,
    )
    additional_data: dict[str, Any] | None = Field(
        default={},
        description="Additional data that can be added to the for other "
        "modules to work upon",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    @field_serializer("timestamp")
    def serialize_datetime(self, timestamp: dt.datetime) -> str:
        return timestamp.isoformat(timespec="milliseconds")


class IotaMqttMessage(BaseModel):
    """Contains data for an MQTT message for the IoT agent such as
    topic, payload, etc."""

    device_id: str = Field(description="FIWARE device ID")
    device_type: Optional[str] = Field(
        default=None, description="FIWARE device type"
    )
    apikey: Optional[str] = Field(
        default=None, description="IoT agent API key"
    )
    payload: Dict = Field(description="MQTT payload")

    def topic(self) -> str:
        """Creates a MQTT-topic in the format required by the FIWARE MQTT IoT
        agent.

        Returns:
            MQTT-topic compatible to the requirements of the FIWARE IoT
            agent.
        """
        return f"/json/{self.apikey}/{self.device_id}/attrs"


class CredentialsConfig(BaseModel):
    """Model class for storing username and password (e.g. for use with MQTT)"""

    username: str
    password: str

    @classmethod
    def load_from_file(
        cls: Type[BaseModel], credentials_file: str | Path
    ) -> BaseModel:
        """Loads credentials from a file and returns an instance of
        :class:`CredentialsConfig`

        Args:
            credentials_file (str, Path): path to credentials file. The file
                should be in JSON format and contain at least the keys
                "username" and "password".

        Returns:
            CredentialsConfig: Credentials read from file and validated
        """
        credentials_file = credentials_file
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(
                f"Could not find keycloak credentials file {credentials_file}!"
            )
        with open(credentials_file) as json_input:
            json_data = json.load(json_input)

        return CredentialsConfig.model_validate(json_data)


class JsonSchemaInstance(BaseModel):
    """A JSON schema to be used with the `JsonSchemaParser` module."""

    model_config = ConfigDict(arbitrary_types_allowed=True, allow_extra=False)
    instance: dict[str, Any]
    identifier: Union[str, Identifier]
