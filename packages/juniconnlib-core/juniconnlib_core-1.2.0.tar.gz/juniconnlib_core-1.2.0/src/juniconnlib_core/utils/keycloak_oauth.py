import logging

import requests
from pydantic import AnyUrl, BaseModel, Field
from requests import RequestException

from juniconnlib_core.data_models.basic_models import CredentialsConfig
from juniconnlib_core.utils.logging import add_logging_handler

logger = logging.getLogger(name=__name__)
LOG_LEVEL = logging.INFO
add_logging_handler(logger=logger, level=LOG_LEVEL)


class KeycloakConfig(BaseModel):
    """Configuration necessary for OAuth using Keycloak"""

    keycloak_url: AnyUrl = Field(
        title="Keycloak URL",
        description="The keycloak url to request the JWT token.",
    )

    client_id: str = Field(
        title="Client ID", description="The client ID for authentication"
    )

    credentials_file: str = Field(
        title="Path to the json file containing username and password for the Keycloak instance to use.",
    )

    max_attempts_to_renew_access_token: int = Field(
        default=3,
        title="Max number of attempts to try to renew the access token.",
        description="Max number of attempts to try to renew the access token.",
    )


def get_keycloak_access_token(keycloak_config: KeycloakConfig) -> dict:
    """Calls upon the Keycloak service to retrieve an access token.

    Args:
        keycloak_config (KeycloakConfig): Keycloak configuration

    Returns:
        dict: The response from getting an access token

    Raises:
        HTTPError: If the retrieval fails
    """
    url = keycloak_config.keycloak_url
    credentials_config = CredentialsConfig.load_from_file(
        credentials_file=keycloak_config.credentials_file
    )
    token_data = {
        "client_id": keycloak_config.client_id,
        "username": credentials_config.username,
        "password": credentials_config.password,
        "grant_type": "password",
    }

    token_response = requests.post(url, data=token_data)

    if token_response.status_code != 200:
        token_response.raise_for_status()

    return token_response.json()


def refresh_keycloak_access_token(
    keycloak_config: KeycloakConfig, access_token: dict
) -> dict:
    """Calls upon the Keycloak service to renew an access token. If the
    renewal fails, a single try to retrieve a completely fresh access
    token is done.

    Args:
        keycloak_config (KeycloakConfig): Keycloak configuration
        access_token (dict): Old access token

    Returns:
        dict: The response from getting an access token

    Raises:
        HTTPError: If the retrieval fails
    """
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": get_refresh_token_from_keycloak_access_token(
            access_token=access_token
        ),
        "client_id": keycloak_config.client_id,
    }

    refresh_response = requests.post(
        keycloak_config.keycloak_url, data=refresh_data
    )
    if 200 <= refresh_response.status_code < 300:
        return refresh_response.json()

    else:
        # the refresh token has probably expired, apply for the new one
        return get_keycloak_access_token(keycloak_config)


def get_authorisation_header(bearer_token: dict) -> dict:
    """Gets the authorisation headers that can be added to any requests.

    Args:
        bearer_token (dict): The access token information with at least
        `"access token"` as key, containing the relevant token for
        authorisation.

    Returns:
        dict: Format is `{"authorization": f"Bearer glpscnsjauen1214b2oksd"}
    """
    return {"authorization": f"Bearer {bearer_token['access_token']}"}


def get_refresh_token_from_keycloak_access_token(access_token: dict) -> str:
    """Extracts the refresh token from an access token dict.

    Args:
        access_token (dict): The access token information with at least
        `"refresh_token"` as key, containing the relevant token for
        refreshing.

    Returns:
        str: The refresh token
    """
    return access_token["refresh_token"]


def should_retry_token_renewal(
    keycloak_config: KeycloakConfig, counter: int
) -> bool:
    """Checks if further retry attempts should be done.

    Args:
        keycloak_config (KeycloakConfig): Keycloak configuration
        counter (int): The number of attempts already made to renew
            the access token

    Returns:
        bool: If another attempt should be done or not
    """
    if not keycloak_config:
        return False
    return counter <= keycloak_config.max_attempts_to_renew_access_token


def is_token_invalid(err: RequestException) -> bool:
    """Checks a `RequestException` if a token is invalid.

    Args:
        err (RequestException): The exception to be checked

    Returns:
        bool: False if the token is invalid (No response or status code
            is not 401)
    """
    # If error contains no response, it is not a token error
    if err.response is None:
        return False
    status_code = err.response.status_code
    if status_code == 401:
        return True

    return False
