from itertools import cycle
from typing import Any, Dict, List

from agentlib.core import Agent, AgentVariable, BaseModule, BaseModuleConfig
from pydantic import Field, ValidationError, field_validator

from juniconnlib_core.utils.logging import create_logger_for_module


class SendConfig(BaseModuleConfig):
    delay: float = Field(
        default=0,
        ge=0,
        description="Time delay to tick down before a value "
        "should be send (again)",
    )
    values: List[dict[str, Any]] = Field(
        None,
        description="Variable to be send. Should have keys "
        "'value' and 'alias'",
        examples=[
            '[{"value": ..., "alias": ...}, ' '{"value": ..., "alias": ...}]'
        ],
    )
    repeat: bool = Field(
        False,
        description="Decision if messages should be send "
        "repeatedly. Cycles through the list of "
        "values.",
    )

    @field_validator("values")
    def check_keys(cls, values):
        for val in values:
            if "value" not in val and "alias" not in val:
                raise ValidationError(
                    "Provide 'value' and 'alias' for every "
                    "variable to be send"
                )
        return values


class DebugSender(BaseModule):
    """General sending type module that can be used for debugging purposes.
    It sends a list of `values` to the agent broker with a given `delay`"""

    config: SendConfig

    def __init__(self, config: Dict, agent: Agent):
        super().__init__(config=config, agent=agent)
        # overwrite the logger of agent liv modules, since it has a fixed formatter
        self.logger = create_logger_for_module(self)

        self.loop = True
        if self.config.repeat:
            self.vals = cycle(self.config.values)
        else:
            self.vals = iter(self.config.values)

    def process(self):
        while True:
            # try getting a value. If the iterator is exhausted
            try:
                val = next(self.vals)
                self.logger.debug(f"Sending {val}")
            except StopIteration:
                self.logger.debug("All values have been sent")
                yield self.env.event()

            var = AgentVariable(**val, name="DevVar", source=self.source)
            self.agent.data_broker.send_variable(var)
            yield self.env.timeout(5)

    def terminate(self):
        self.loop = False
        self.logger.info(f"Terminated {self.__class__.__name__}")

    def register_callbacks(self):
        """No callback necessary."""
        ...
        #  self.agent.data_broker.register_callback()


class DebugListener(BaseModule):
    """This module ist meant for debugging and development purposes.
    It logs any variable on the broker on level DEBUG"""

    config: BaseModuleConfig

    def __init__(self, config: Dict, agent: Agent):
        super().__init__(config=config, agent=agent)
        # overwrite the logger of agent liv modules, since it has a fixed formatter
        self.logger = create_logger_for_module(self)

    def process(self):
        yield self.env.event()

    def terminate(self):
        self.logger.info(f"Terminated {self.__class__.__name__}")

    def register_callbacks(self):
        """Registers a simple callback that logs ALL variables on the broker as
        debug message."""
        self.agent.data_broker.register_callback(
            callback=lambda var: self.logger.debug(var)
        )
