import logging
from math import inf
from typing import Any

from filip.clients.ngsi_v2 import ContextBrokerClient
from filip.models import FiwareHeader
from filip.models.ngsi_v2.context import (
    ContextAttribute,
    ContextEntity,
    NamedContextAttribute,
)
from filip.models.ngsi_v2.subscriptions import Subscription
from filip.utils.cleanup import clear_context_broker
from pydantic import PositiveInt
from requests import RequestException

from juniconnlib_core.utils.keycloak_oauth import (
    KeycloakConfig,
    get_authorisation_header,
    get_keycloak_access_token,
    is_token_invalid,
    refresh_keycloak_access_token,
    should_retry_token_renewal,
)


def oauth_clear_context_broker(
    url: str = None,
    fiware_header: FiwareHeader = None,
    *,
    keycloak_config: KeycloakConfig = None,
):
    """Clear the OCB while using Keycloak OAuth

    Args:
        url (str): URL or the OCB
        fiware_header (FiwareHeader, optional): Service information for FIWARE

    Kwargs:
        keycloak_config (KeycloakConfig): Keycloak configuration for the given
            header
    """
    cb_authorisation_header = {}
    if keycloak_config:
        cb_access_token = get_keycloak_access_token(keycloak_config)
        cb_authorisation_header = get_authorisation_header(cb_access_token)

    cb_client = ContextBrokerClient(
        url=url, fiware_header=fiware_header, headers=cb_authorisation_header
    )
    clear_context_broker(
        url=url, fiware_header=fiware_header, cb_client=cb_client
    )


class OAuthContextBroker:
    """This class wraps methods of Filips ContextBrokerClient with keycloak
    authentication."""

    REFRESH_TOKEN_MAX_ATTEMPTS = 3

    def __init__(
        self,
        fiware_header: FiwareHeader,
        ocb_url: str,
        *,
        keycloak_config: KeycloakConfig = None,
    ):
        """Constructor of :class:`OAuthContextBroker`

        Args:
            fiware_header (FiwareHeader): Service information for FIWARE
            ocb_url (str): URL of the OCB

        Kwargs:
            keycloak_config (KeycloakConfig): Keycloack configuration for the
                given service
        """
        self.logger = logging.getLogger(
            f"({self.__class__.__module__}.{self.__class__.__name__})"
        )
        self.fiware_header = fiware_header
        self.cb_url = ocb_url
        self.use_keycloak_oauth = False
        self.cb_authorisation_header = {}
        self.cb_access_token = None
        self.keycloak_config = keycloak_config
        if self.keycloak_config:
            self.use_keycloak_oauth = True
            self.cb_access_token = get_keycloak_access_token(
                self.keycloak_config
            )
            self.cb_authorisation_header = get_authorisation_header(
                self.cb_access_token
            )

        self.cb_client = ContextBrokerClient(
            url=self.cb_url,
            fiware_header=self.fiware_header,
            headers=self.cb_authorisation_header,
        )

    # Context Manager Protocol
    def __enter__(self):
        if not self.cb_client:
            self.cb_client = ContextBrokerClient(
                url=self.cb_url,
                fiware_header=self.fiware_header,
                headers=self.cb_authorisation_header,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cb_client:
            self.cb_client.close()

    def close(self) -> None:
        """Close ContextBrokerClient session and possible underlying Sockets

        Returns:
            None
        """
        if self.cb_client:
            self.cb_client.close()

    def refresh_cb_access_token(self):
        """Refreshes the access token granted by Keycloak OAuth and saves the
        renewed access information to `self.cb_autherisation_header`"""
        self.cb_access_token = refresh_keycloak_access_token(
            keycloak_config=self.keycloak_config,
            access_token=self.cb_access_token,
        )
        self.cb_authorisation_header = get_authorisation_header(
            bearer_token=self.cb_access_token
        )
        self.cb_client.close()
        self.cb_client = ContextBrokerClient(
            url=self.cb_url,
            fiware_header=self.fiware_header,
            headers=self.cb_authorisation_header,
        )

    def refresh_cb_access_token_and_redo_method(self, method, **kwargs):
        """Wrapper function that retries a function or method after
        renewing the access token

        Args:
            method (Callable): The method to call

        Kwargs:
            **: Anything to be passed to `method` when rerunning it
        """
        self.refresh_cb_access_token()
        return method(**kwargs)

    def token_renewal_required(self, err: RequestException):
        # TODO: Check if this can be removed
        if not self.keycloak_config:
            return False
        status_code = err.response.status_code
        if status_code == 401:
            self.logger.info(
                msg=f"Connection error: {err}. Renewing access token..."
            )
            return True

        return False

    def get_entity(self, entity_id: str, counter=1) -> ContextEntity:
        """Gets a single entity from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_id (str): id of the entity to retrieve
            counter (int): Retry counter

        Returns:
            ContextEntity: The entity retrieved

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            entity = self.cb_client.get_entity(entity_id=entity_id)
            return entity
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.get_entity,
                        entity_id=entity_id,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def get_entity_list(
        self, entity_types: list[str], counter=1
    ) -> list[ContextEntity]:
        """Gets a list of entities from the OCB based on the type.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_types (list[str]): type of which to retrieve entities of
            counter (int): Retry counter

        Returns:
            list[ContextEntity]: The entities retrieved

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.cb_client.get_entity_list(entity_types=entity_types)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.get_entity_list,
                        entity_types=entity_types,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def post_entity(
        self, entity: ContextEntity, update: bool, counter=1
    ) -> str | None:
        """Posts a single entity from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity (ContextEntity): The entity to post
            update (bool): If the entity should be updated
            counter (int): Retry counter

        Returns:
            str: `Location` key from the headers dict of the response
            None: If `Location` is not in headers

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            response = self.cb_client.post_entity(entity=entity, update=update)
            return response
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.post_entity,
                        entity=entity,
                        update=update,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc
        except AttributeError as error:
            # Remove this after this behavior is fixed in Filip
            raise RequestException(
                f"Attribute error possibly during handling of "
                f"Requestexception because of Filips error handling "
                f"which tries to access err.response.status_code "
                f"where response is None."
                f"Attribute error message: {error}"
            )

    def delete_entity(
        self, entity_id: str, entity_type: str, counter=1
    ) -> None:
        """deletes a single entity from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_id (str): id of the entity to delete
            entity_type (str): type of the entity to delete
            counter (int): Retry counter

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            self.cb_client.delete_entity(
                entity_id=entity_id, entity_type=entity_type
            )
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.delete_entity,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while deleting location entities. "
                        "Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def post_subscription(
        self, subscription: Subscription, update: bool = False, counter=1
    ) -> str:
        """Posts a single subscription from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            subscription (Subscription): The subscription to post
            update (bool): If the subscription should be updated
            counter (int): Retry counter

        Returns:
            str: The id assigned to the subscription by the OCB

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.cb_client.post_subscription(
                subscription=subscription, update=update
            )
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.post_subscription,
                        subscription=subscription,
                        update=update,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while posting subscription. "
                        "Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def get_subscription_list(
        self, limit: PositiveInt = inf, counter=1
    ) -> list[Subscription]:
        """Gets a list of subscriptions from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            limit (ContextEntity): The number ob subscriptions to return at max
            counter (int): Retry counter

        Returns:
            list[Subscriptions]: The subscriptions found for the FIWARE service

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.cb_client.get_subscription_list(limit=limit)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.get_subscription_list,
                        limit=limit,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token while getting subscription list. "
                        "Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def does_entity_exist(
        self, entity_id: str, entity_type: str, counter=1
    ) -> bool:
        """Check if an entity exists on the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_id (str): id of the entity to check for
            entity_type (str): type of the entity to check for
            counter (int): Retry counter

        Returns:
            bool: True if the entity exists, False otherwise

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.cb_client.does_entity_exist(entity_id, entity_type)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.does_entity_exist,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def get_entity_type(self, entity_type: str, counter=1) -> dict[str, Any]:
        """Get multiple entities of a specific type from the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_type (str): type of which to return entities for
            counter (int): Retry counter

        Returns:
            dict: The entities of the according type

        Raises:
            RequestException: if the retry strategy failed
        """
        try:
            return self.cb_client.get_entity_type(entity_type)
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.get_entity_type,
                        entity_type=entity_type,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def update_or_append_entity_attributes(
        self,
        entity_id: str,
        attrs: list[NamedContextAttribute] | dict[str, ContextAttribute],
        entity_type: str = None,
        append_strict: bool = False,
        forcedUpdate: bool = False,
        counter=1,
    ) -> None:
        """Updates one or more attributes (or appends it if it does not exist
        yet) for a specific entity on the OCB.
        Wraps the non Keycloak compatible version of this function

        Args:
            entity_id (str): id of the entity to update the attribute for
            attrs (list[NamedContextAttribute] | dict[str, ContextAttribute]):
                The attribute(s) in question to be updated
            entity_type (str, optional): type of the entity to update the
                attribute for (just for more precise identification of entity)
            append_strict (bool, optional): Raises an exception if on of attrs
                is already in the entity
            forcedUpdate (bool, optional): Force the update, even if no
                effective change occurred in the attribute
            counter (int): Retry counter

        Raises:
            RequestException: if the retry strategy failed or append_strict
                is True and one of `attrs` does already exists
        """
        try:
            results = self.cb_client.update_or_append_entity_attributes(
                entity_id=entity_id,
                attrs=attrs,
                entity_type=entity_type,
                append_strict=append_strict,
                forcedUpdate=forcedUpdate,
            )
            return results
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.update_or_append_entity_attributes,
                        entity_id=entity_id,
                        attrs=attrs,
                        entity_type=entity_type,
                        append_strict=append_strict,
                        forcedUpdate=forcedUpdate,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc

    def delete_subscription(
        self,
        subscription_id: str,
        counter=1,
    ) -> None:
        """
        Deletes a subscription from a Context Broker
        Args:
            subscription_id: id of the subscription
        """
        try:
            results = self.cb_client.delete_subscription(
                subscription_id=subscription_id,
            )
            return results
        except RequestException as exc:
            if is_token_invalid(err=exc):
                if should_retry_token_renewal(
                    keycloak_config=self.keycloak_config, counter=counter
                ):
                    self.logger.warning(
                        msg=f"Could not connect to the Orion Context Broker {exc}. Renewing access token..."
                    )
                    return self.refresh_cb_access_token_and_redo_method(
                        self.delete_subscription,
                        subscription_id=subscription_id,
                        counter=counter + 1,
                    )
                else:
                    self.logger.error(
                        msg="Could not renew access token. Connection to the Orion Context Broker is "
                        "not possible!"
                    )
            raise exc
