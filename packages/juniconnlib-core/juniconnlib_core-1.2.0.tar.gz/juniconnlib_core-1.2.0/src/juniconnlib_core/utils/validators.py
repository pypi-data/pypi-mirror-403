from pydantic import BaseModel


def check_mqtt_credentials(cls, obj: BaseModel):
    """A function to be used as model_validator. Validates if a pydantic
    class has both a username and password fields with non None values

    Raises:
        ValueError: If one value is None (both None is allowed)

    Returns:
        BaseModel: The validated model
    """
    if obj.credentials_file and (obj.username or obj.password):
        raise ValueError(
            "Either supply a credentials file XOR username and password"
        )
    if (obj.username is not None and obj.password is None) or (
        obj.password is not None and obj.username is None
    ):
        raise ValueError("Supply username and password")
    return obj


def check_mqtt_topic(cls, value):
    """A function to be used as field_validator. Validates if a string (mainly
    MQTT topics) start with a leading slash

    Raises:
        ValueError: If it does not start with a leading slash
        AttributeError: If `value` is not of type string (or does not
            implement a `str.starts_with` compatible method)

    Returns:
        BaseModel: The validated string
    """
    if value.startswith("/"):
        raise ValueError(
            "MQTT topics should not start with a " "leading slash"
        )
    return value


def check_keycloak_config(cls, value):
    """A function to be used as model_validator. Validates if a model that
    is configured to use Keycloak hold the necessary configuration

    Raises:
        ValueError: If `use_keycloak_oauth` is True and `keycloak_config`
            is missing

    Returns:
        BaseModel: The validated string
    """
    if value.use_keycloak_oauth and not value.keycloak_config:
        raise ValueError(
            "Keycloak oauth for the Orion Context Broker should be used "
            "but the corresponding keycloak configuration is missing!"
        )
    return value
