import logging
from typing import Callable, List

from filip.clients.ngsi_v2 import IoTAClient
from filip.models import FiwareHeader
from filip.models.ngsi_v2.iot import Device, ServiceGroup
from filip.utils.cleanup import clear_iot_agent
from requests import RequestException

from juniconnlib_core.utils.keycloak_oauth import (
    KeycloakConfig,
    get_authorisation_header,
    get_keycloak_access_token,
    is_token_invalid,
    refresh_keycloak_access_token,
    should_retry_token_renewal,
)


def oauth_clear_iota(
    url: str = None,
    fiware_header: FiwareHeader = None,
    *,
    keycloak_config: KeycloakConfig = None,
):
    """Clear the IoT-Agent while using Keycloak OAuth

    Args:
        url (str): URL or the IoTA
        fiware_header (FiwareHeader, optional): Service information for FIWARE

    Kwargs:
        keycloak_config (KeycloakConfig): Keycloak configuration for the given
            header
    """
    iota_authorisation_header = {}
    if keycloak_config:
        iota_access_token = get_keycloak_access_token(keycloak_config)
        iota_authorisation_header = get_authorisation_header(iota_access_token)

    iota_client = IoTAClient(
        url=url, fiware_header=fiware_header, headers=iota_authorisation_header
    )
    clear_iot_agent(iota_client=iota_client)


class OAuthIoTAgentClient:
    """Client for the IoT-Agent, including the possibility to use Keycloak
    for authentication"""

    REFRESH_TOKEN_MAX_ATTEMPTS = 3

    def __init__(
        self,
        fiware_header: FiwareHeader,
        iota_url: str,
        *,
        keycloak_config: KeycloakConfig = None,
    ):
        """Constructor of :class:`OAuthIoTAgentClient`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            iota_url (str): URL of the IoTA

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloack configuration for the
                given service
        """
        self.logger = logging.getLogger(
            f"({self.__class__.__module__}.{self.__class__.__name__})"
        )
        self.fiware_header = fiware_header
        self.iota_url = iota_url
        self.use_keycloak_oauth = False
        self.iota_authorisation_header = {}
        self.iota_access_token = None
        self.keycloak_config = keycloak_config
        if self.keycloak_config:
            self.use_keycloak_oauth = True
            self.iota_access_token = get_keycloak_access_token(
                self.keycloak_config
            )
            self.iota_authorisation_header = get_authorisation_header(
                self.iota_access_token
            )

        self.iota_client = IoTAClient(
            url=self.iota_url,
            fiware_header=self.fiware_header,
            headers=self.iota_authorisation_header,
        )

    # Context Manager Protocol
    def __enter__(self):
        if not self.iota_client:
            self.iota_client = IoTAClient(
                url=self.iota_url,
                fiware_header=self.fiware_header,
                headers=self.iota_authorisation_header,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.iota_client:
            self.iota_client.close()

    def close(self) -> None:
        """Close IoTAClient instance and possible underlying Sockets

        Returns:
            None
        """
        if self.iota_client:
            self.iota_client.close()

    def refresh_iota_access_token(self):
        """Refreshes the access token granted by Keycloak OAuth and saves the
        renewed access information to `self.iota_autherisation_header`"""
        self.iota_access_token = refresh_keycloak_access_token(
            keycloak_config=self.keycloak_config,
            access_token=self.iota_access_token,
        )
        self.iota_authorisation_header = get_authorisation_header(
            bearer_token=self.iota_access_token
        )
        self.iota_client.close()
        self.iota_client = IoTAClient(
            url=self.iota_url,
            fiware_header=self.fiware_header,
            headers=self.iota_authorisation_header,
        )

    def refresh_iota_access_token_and_redo_method(
        self, method: Callable, **kwargs
    ):
        """Wrapper function that retries a function or method after
        renewing the access token

        Args:
            method (Callable): The method to call

        Kwargs:
            **: Anything to be passed to `method` when rerunning it
        """
        self.refresh_iota_access_token()
        return method(**kwargs)

    def post_group(
        self,
        service_group: ServiceGroup,
        update: bool = False,
        counter: int = 1,
    ) -> None:
        """Post a single service group to the IoT-Agent.
        Wraps the non Keycloak compatible version of this function

        Args:
            service_group (ServiceGroup): Service group to post
            update (bool): If the service group should be updated
            counter (int): Retry counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            self.iota_client.post_group(
                service_group=service_group, update=update
            )
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.post_group,
                        service_group=service_group,
                        update=update,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting devices. "
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc

    def post_devices(
        self,
        devices: Device | list[Device],
        update: bool = False,
        counter: int = 1,
    ) -> None:
        """Post one or more devices to the IoT-Agent.
        Wraps the non Keycloak compatible version of this function

        Args:
            devices (Device, list[Device]): Device(s) to post
            update (bool): If the device should be updated
            counter (int): Retry counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            self.iota_client.post_devices(devices=devices, update=update)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.post_devices,
                        devices=devices,
                        update=update,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting devices. "
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc

    def post_device(
        self, device: Device, update: bool = False, counter: int = 1
    ) -> None:
        """Post a single device to the IoT-Agent.
        Wraps the non Keycloak compatible version of this function

        Args:
            device (Device): Device to post
            update (bool): If the service group should be updated
            counter (int): Retry counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            self.iota_client.post_device(device=device, update=update)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.post_device,
                        device=device,
                        update=update,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting devices. "
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc

    def get_device_list(
        self,
        limit: int = None,
        offset: int = None,
        device_ids: str | list[str] = None,
        entity_names: str | list[str] = None,
        entity_types: str | list[str] = None,
        counter: int = 1,
    ) -> List[Device]:
        """Gets one or more devices based on either it's `device_id` or
        information regarding the associated entities.
        Wraps the non Keycloak compatible version of this function

        Args:
            limit (int): Maximum amount of devices to be returned
            offset (int): Offset for pagination
            device_ids (str, list[str]): Id(s) to retrieve specific devices
            entity_names (str, list[str]): Id(s) of entities associated
                with devices to be returned
            entity_types (str, list[str]): Type(s) of entities associated
                with devices to be returned
            counter (int): Retry Counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.iota_client.get_device_list(
                limit=limit,
                offset=offset,
                device_ids=device_ids,
                entity_names=entity_names,
                entity_types=entity_types,
            )
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.get_device_list,
                        limit=limit,
                        offset=offset,
                        device_ids=device_ids,
                        entity_names=entity_names,
                        entity_types=entity_types,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting devices. "
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc

    def get_device(self, device_id: str, counter: int = 1) -> Device:
        """Gets a single device based on its `device_id`.
        Wraps the non Keycloak compatible version of this function

        Args:
            device_id (str, list[str]): Id to a retrieve specific devices
            counter (int): Retry Counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.iota_client.get_device(device_id=device_id)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.get_device,
                        device_id=device_id,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting devices. "
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc

    def get_group_list(self, counter: int = 1):
        """Return a list of all service groups.
        Wraps the non Keycloak compatible version of this function

        Args:
            counter (int): Retry Counter

        Returns:
            None

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.iota_client.get_group_list()
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the IoTAgent {exc}. Renewing access token..."
                    )
                    return self.refresh_iota_access_token_and_redo_method(
                        self.get_group_list(), counter=counter + 1
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token"
                        "Connection to the IoTAgent is "
                        "not possible!"
                    )
            raise exc
