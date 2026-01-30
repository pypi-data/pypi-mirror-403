import json
from typing import Dict, Literal, Optional
from urllib.parse import urlparse

import requests
from agentlib.core import Agent, AgentVariable, BaseModule, BaseModuleConfig
from agentlib.core.errors import ConfigurationError
from fidere import JsonSchemaParser
from fidere.models import NormalizedModel
from pydantic import AnyHttpUrl, ConfigDict, Field, FilePath, field_validator

from juniconnlib_core.data_models.basic_models import JsonSchemaInstance
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases


class JsonSchemaParserConfig(BaseModuleConfig):
    """Config object for the GeneralJsonSchemaParser."""

    url_schema: Dict[str, AnyHttpUrl] | None = Field(
        description="A dict containing the identifier to be used for instancing "
        "this schema later and an url pointing to this schema. The "
        "simplest case would be to use the 'type' as identifier",
        examples=[
            "{'Sensor': 'https://example.org/your/sensor/schema.json',"
            "'Actuator': 'http://example.org/your/actuator/schema.json'}"
        ],
        default={},
    )
    url_instance: Dict[str, AnyHttpUrl] | None = Field(
        description="A dict with the identifier of the corresponding schema and "
        "the url pointing to the instances. Each file contains a "
        "list of instances.",
        examples=[
            "{'Sensor': 'https://example.org/your/sensor/instances.json', "
            "'Actuator': 'http://example.org/your/actuator/instance.json'}"
        ],
        default={},
    )
    path_schema: Dict[str, FilePath] | None = Field(
        description="A dict containing the identifier to be used for instancing "
        "this schema later and a path pointing to this schema. The "
        "simplest case would be to use the 'type' as identifier",
        examples=[
            "{'Sensor': '/path/to/sensor/schema',"
            "'Actuator': './path/to/actuator/schema'}"
        ],
        default={},
    )  # making the default an empty list makes it easier later
    path_instance: Dict[str, FilePath] | None = Field(
        description="A dict with the identifier of the corresponding schema and "
        "the path pointing to the instances. Each file contains a "
        "list of instances.",
        examples=[
            "{'Sensor': '/your/sensor/instances.json', "
            "'Actuator': './your/actuator/instance.json'}"
        ],
        default={},
    )
    raise_for_exception: Optional[bool] = Field(
        default=True,
        description="Define if an exception is raised when a  instance was not "
        "processed into an Entity or Device",
    )
    # TODO (sa.johnen): This should be discussed if it is really necessary.
    #  Are we actually using it for ContextEntities? Maybe make two
    #  versions of this module, one for Devices on for ContextEntities
    parse_to: Literal["Device", "ContextEntity"] = Field(
        default="Device",
        title="Output Object Type",
        description="Either 'Device' or 'ContextEntity'",
    )
    model_config = ConfigDict(use_enum_values=True, validate_default=True)

    @field_validator("url_schema", "url_instance")
    def check_url_status(cls, values: Dict[str, AnyHttpUrl]):
        """Check if a given URL returns a status code in the 200 range."""
        for key, value in values.items():
            res = requests.get(value, allow_redirects=False)
            if not 200 <= res.status_code < 300:
                raise ConfigurationError(
                    f"{value} responded with status code {res}: {res.reason}"
                )
        return values

    @field_validator("path_schema", "path_instance")
    def check_file_path(cls, values: Dict[str, FilePath]):
        """Check if the file exists.

        Content is not validated
        """
        for key, value in values.items():
            if not value.exists():
                raise ConfigurationError(f"{value} does not exist")
            if not value.suffix == ".json":
                raise ConfigurationError(f"{value} is not a JSON file")
        return values

    @field_validator(
        "url_schema",
        "url_instance",
        "path_schema",
        "path_instance",
        mode="after",
    )
    def drop_none_values(cls, value):
        """Cleanup None values to be an empty dict to enforce the default
        value, since Pydantic thinks None as a valid input due to the fields
        being optional."""
        if value is None:
            return {}
        return value


class GeneralJsonSchemaParser(BaseModule):
    """Module to parse JSON-Schema models.

    It is configured using
    `JsonSchemaParserConfig`. For details on the config, see the according
    class object.
    """

    config: JsonSchemaParserConfig
    parser: JsonSchemaParser
    __ALIAS: str
    __NAME: str

    def __init__(self, config: dict, agent: Agent):
        """Initializes the module by creating the `JsonSchemaParser`, parsing
        all models in `config.folder_schemas` if not None and instancing based
        on a config.path_instance. Only one schema per entity type is allowed!

        Args:
            config (dict): The configuration for the initialization.
            agent (Agent): The agent for the initialization.
        """
        super().__init__(config=config, agent=agent)
        # overwrite the logger of agentlib modules, since it has a fixed formatter
        self.logger = create_logger_for_module(self)
        self.logger.info("Beginning initialization of JsonSchemaParser module")
        self.parser = JsonSchemaParser()

        # predefine the alias and name used for outgoing Device or ContextEntities
        self.__ALIAS = Aliases(f"Unprovisioned{self.config.parse_to}")
        self.__NAME = f"{self.config.parse_to}fromParser"

        # get the schemas from url and parse them
        for ident, path in self.config.path_schema.items():
            self.logger.info(f"Found schema {ident} at path {path}")
            self.parser.parse_schema(path, NormalizedModel, ident)
        # get the schemas from local paths and parse them
        for ident, url in self.config.url_schema.items():
            self.logger.info(f"Found schema {ident} at url {url}")
            # necessary since parser only work on Path and ParseResult objects
            url = urlparse(str(url))
            self.parser.parse_schema(url, NormalizedModel, ident)

        instances = []
        # get the schemas from urls
        for key, url in self.config.url_instance.items():
            res = requests.get(url, allow_redirects=False)
            instances.extend(res.json())
        # get the schemas from files
        for key, path in self.config.path_instance.items():
            with open(path, "r", encoding="utf-8") as file:
                instances.extend(json.load(file))
        self.logger.info(f"Found {len(instances)} instances in configuration")

        # call the callback by hand since it makes no difference if an
        # instance is received from the broker or doing it like this!
        for instance in instances:
            var = AgentVariable(
                name="InitInstance",
                value=instance,
                source=self.source,
                shared=True,
            )
            self._callback_to_instance(var)

    def process(self):
        yield self.env.event()

    def register_callbacks(self):
        """Registers up to two callbacks based on the configuration

        if `config.instance_from_broker` `True`. It reacts to `AgentVariables`
        with alias `'ContextEntityInstance'` or `'DeviceInstance'` based
        on the parse_to

        if `config.schema_from_broker` is `True`. It reacts to
        AgentVariables` with alias `'JsonSchema'`.

        """
        self.agent.data_broker.register_callback(
            callback=self._callback_to_instance,
            alias=Aliases(f"{self.config.parse_to}Instance"),
        )
        self.agent.data_broker.register_callback(
            callback=self._callback_to_schema, alias="JsonSchema"
        )

    def _callback_to_instance(self, variable: AgentVariable):
        """Callback to receive a DeviceInstance of ContextEntityInstance.

        Args:
            variable (AgentVariable): The variable to be processed. The
                type of the value is either a dict, in which case the 'type'
                or 'entity_type' is used as identifier, or a 'JsonSchemaInstance'
        """
        self.logger.debug("Received Instance")
        if not isinstance(variable.value, (dict, JsonSchemaInstance)):
            msg = (
                "Received an instance of invalid type. Only 'dict' and "
                "'JsonSchemaInstance' is supported"
            )
            self.logger.error(msg)
            if self.config.raise_for_exception:
                raise ValueError(msg)
            return

        instance = variable.value
        if not isinstance(instance, JsonSchemaInstance):
            if self.config.parse_to == "ContextEntity":
                instance = JsonSchemaInstance(
                    instance=instance, identifier=instance["type"]
                )
            if self.config.parse_to == "Device":
                instance = JsonSchemaInstance(
                    instance=instance, identifier=instance["entity_type"]
                )

        result = None
        # create Device is configured to do so
        self.logger.debug(f"Creating {self.config.parse_to} from: {instance}")
        try:
            if self.config.parse_to == "Device":
                result = self.parser.create_device(**instance.model_dump())
            # create ContextEntity is configured to do so
            elif self.config.parse_to == "ContextEntity":
                result = self.parser.create_context_entity(
                    **instance.model_dump()
                )
        except KeyError as err:
            self.logger.error(
                f"Instance was not compatible for creating a "
                f"{self.config.parse_to}. Likely the identifier is unknown or "
                f"used a Device instance to create a ContextEntity or "
                f"vice versa!"
            )
            if self.config.raise_for_exception:
                raise KeyError() from err
            result = None

        # if a result was generated send it out to broker
        if result is not None:
            self.logger.info(f"Created {self.config.parse_to}: {result}")
            var = AgentVariable(
                value=result,
                source=self.source,
                name=self.__NAME,
                alias=self.__ALIAS,
            )
            self.agent.data_broker.send_variable(var)
        else:
            self.logger.warning(
                f"Something went wrong creating a {self.config.parse_to} from: "
                f"{instance}"
            )

    def _callback_to_schema(self, variable: AgentVariable):
        """Convert a callback to a schema and store it in the schema's
        dictionary.

        Args:
            variable (AgentVariable): The variable containing the JSON-Schema.
        """
        raise NotImplementedError(
            "Currently receiving schemas from the broker is no longer "
            "supported. A non hacky implementation based on the most recent "
            "JsonSchemaParser versions is still pending"
        )
        # self.logger.debug('Received JSON-Schema from broker')
        # self.parser.parse_schema(variable.value, model_class=NormalizedModel)
