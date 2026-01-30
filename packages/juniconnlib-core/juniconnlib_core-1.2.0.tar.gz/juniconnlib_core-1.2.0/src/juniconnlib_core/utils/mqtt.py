import logging
import re
from typing import TypeVar

from agentlib import BaseModule
from paho.mqtt.client import Client
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCodes

FORBIDDEN_CHARACTERS = "<>=();"

_logger = logging.getLogger(__name__)

ClientType = TypeVar("ClientType", Client, BaseModule)
"""Type definition for the MQTT-Client"""


def fill_topic_pattern(pattern: str, **kwargs):
    """Replaces placeholders in a pattern string with provided keyword
    arguments.

    This function searches for placeholders in the given pattern string,
    formatted as `${key}`, and replaces them with corresponding values from
    the provided keyword arguments. Keyword arguments not in the pattern are
    ignored. A warning is given in case not all placeholders could be replaced

    Args:
        pattern (str): The pattern string containing placeholders.

    Kwargs:
        **: Key-value pairs where the key corresponds to a placeholder
            in the pattern.

    Returns:
        str: The pattern string with placeholders replaced by their
        respective values.

    Example:
        >>> fill_topic_pattern("Hello, ${name}!", name="Alice")
        'Hello, Alice!'

        >>> fill_topic_pattern("The ${animal} jumps over the ${object}.", animal="fox", object="fence")
        'The fox jumps over the fence.'

        >>> fill_topic_pattern("No replacement here.", unused="value")
        'No replacement here.'
    """

    def replacer(match):
        key = match.group(1)  # Extract the key inside ${...}
        return kwargs.get(
            key, match.group(0)
        )  # Replace if found, else keep original

    # Use regex to replace all occurrences of ${key}
    pattern = re.sub(r"\$\{([^}]+)\}", replacer, pattern)

    # Check for remaining placeholders
    if re.search(r"\$\{[^}]+\}", pattern):
        logging.warning(
            "Unmatched placeholders remaining in the string: %s", pattern
        )

    return pattern


def extract_from_topic(pattern: str, topic: str) -> dict | None:
    """Extracts named values from an MQTT topic string based on a pattern with
    placeholders and MQTT wildcards.

    Wildcard rules:
        - ${var}    : named single-level match
        - ${var}+   : named single-level match (same as ${var})
        - ${var}#   : named multi-level match
        - +         : anonymous single-level wildcard (not captured)
        - #         : anonymous multi-level wildcard

    Notes:
        - `${var}#` and `#` can only appear at the **start or end** of the
        pattern.
        - The rest of the pattern must align to topic segments exactly.

    Args:
        pattern (str): MQTT-style pattern with named and unnamed wildcards.
        topic (str): The actual MQTT topic to extract from.

    Returns:
        dict | None: Extracted named values if matched, else None.

    Examples:
        >>> extract_from_topic("devices/${device}", "devices/sensor1")
        {'device': 'sensor1'}

        >>> extract_from_topic("home/${room}+/${device}", "home/kitchen/light")
        {'room': 'kitchen', 'device': 'light'}

        >>> extract_from_topic("${prefix}#/status", "foo/bar/baz/status")
        {'prefix': 'foo/bar/baz'}

        >>> extract_from_topic("devices/${path}#", "devices/x/y/z")
        {'path': 'x/y/z'}

        >>> extract_from_topic("#", "a/b/c")
        {}

        >>> extract_from_topic("logs/+/+/info", "logs/foo/bar/info")
        {}
    """
    # Check for invalid `#` or `${var}#` in the middle
    hash_matches = list(re.finditer(r"(\$\{[^}]+\}#|#)", pattern))
    for m in hash_matches:
        start, end = m.span()
        if start != 0 and end != len(pattern):
            logging.warning(
                "Multi-level wildcard (#) must be at start or end of pattern."
            )
            return None

    def replacer(match):
        name, suffix = match.group(1), match.group(2)
        if suffix == "#":
            return f"(?P<{name}>([^/]+/)*[^/]+)"  # multi-level (at end only)
        return f"(?P<{name}>[^/]+)"  # single-level (default or +)

    # Replace named variables
    regex = re.sub(r"\$\{([^}]+)\}([+#]?)", replacer, pattern)

    # Replace unnamed wildcards (we don’t capture them)
    regex = regex.replace("+", "[^/]+")
    regex = regex.replace("#", ".+")

    full_regex = f"^{regex}$"
    match = re.match(full_regex, topic)
    if not match:
        return None
    return match.groupdict()


def mqtt_connect_callback(
    client: ClientType,
    userdata,
    flags: dict,
    code: int | ReasonCodes,
    properties: Properties = None,
) -> None:
    """A callback for when the MQTT client connects. For the signature look at
    `Client` from `paho.mqtt.client`"""
    if code != 0:
        client.logger.error(f"Connection failed with error code: '{code}'")
    if hasattr(properties, "AssignedClientIdentifier"):
        client._client_id = properties.AssignedClientIdentifier
    client.logger.info("Connected to broker")


def mqtt_subscription_callback(
    client: ClientType, obj, mid, reason_codes, properties
):
    """A callback for when the MQTT client subscribes to a topic.
    For the signature look at `Client` from `paho.mqtt.client`"""
    client.logger.info(
        f"Subscription returned: "
        f"(object: {obj}) (message_id: {mid}) "
        f"(reason codes: {[str(rc) for rc in reason_codes]}"
    )


def mqtt_disconnect_callback(
    client: ClientType,
    userdata,
    flags,
    code: int | ReasonCodes,
    properties: Properties = None,
) -> None:
    """A callback for when the MQTT client disconnects. For the signature look
    at `Client` from `paho.mqtt.client`"""
    client.logger.info(
        f"Disconnected with result code:{code} | "
        f"userdata: {userdata} | properties: {properties}"
    )
