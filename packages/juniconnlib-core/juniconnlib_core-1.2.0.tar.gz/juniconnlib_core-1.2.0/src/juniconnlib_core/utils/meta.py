from enum import Enum


class Aliases(str, Enum):
    """A simple enum to collect all the different aliases for AgentVariables
    used throughout the modules."""

    PROVISIONED_CONTEXT_ENTITY = "ProvisionedContextEntity"
    PROVISIONED_DEVICE = "ProvisionedDevice"
    PROVISIONED_DEVICES = "ProvisionedDevices"
    PROVISIONED_SERVICE_GROUP = "ProvisionedServiceGroup"
    UNPROVISIONED_CONTEXT_ENTITY = "UnprovisionedContextEntity"
    UNPROVISIONED_DEVICE = "UnprovisionedDevice"
    UNPROVISIONED_DEVICES = "UnprovisionedDevices"
    UNPROVISIONED_SERVICE_GROUP = "UnprovisionedServiceGroup"
    UNPROVISIONED_ADS_DEVICE_IDS = "UnprovisionedAdsDeviceIds"
    UNPROVISIONED_KNX_DEVICE_IDS = "UnprovisionedKnxDeviceIds"
    UNPROVISIONED_ENOCEAN_DEVICE_IDS = "UnprovisionedEnoceanDeviceIds"
    REFRESH_KEYCLOAK_TOKEN = "RefreshKeycloakToken"
    OPCUA_SEND_TO_FIELD = "OpcuaSendToField"
    OPCUA_RECEIVED_FROM_FIELD = "OpcuaReceivedFromField"
    OPCUA_MAPPING = "OpcuaMapping"
    MQTT_SEND_TO_FIWARE = "MqttSendToFiware"
    MQTT_RECEIVED_FROM_FIWARE = "MqttReceivedFromFiware"
    HTTP_SEND_TO_FIWARE = "HttpSendToFiware"
    DEVICE_INSTANCE = "DeviceInstance"
    CONTEXT_ENTITY_INSTANCE = "ContextEntityInstance"
