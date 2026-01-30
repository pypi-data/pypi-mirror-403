from agentlib.utils.plugin_import import ModuleImport

import juniconnlib_core._version as package_version
from juniconnlib_core.modules import (
    devtools,
    fiware_iota_communicators,
    fiware_iota_device_provisioner,
    fiware_ocb_communicators,
    fiware_ocb_entity_provisioner,
    fiware_subscriptions,
    influxdb_writer,
    json_schema_parser,
)

version = package_version.version
__version__ = package_version.__version__
__version_tuple__ = package_version.__version_tuple__
version_tuple = package_version.version_tuple

__all__ = [
    "__version__",
    "__version_tuple__",
    "version",
    "version_tuple",
    "MODULE_TYPES",
]


# This property MODULE_TYPES has to exist with exactly this name, so that the plugin
# is usable in the agentlib

MODULE_TYPES = {
    "json_schema_parser": ModuleImport(
        import_path="juniconnlib_core.modules.json_schema_parser",
        class_name=json_schema_parser.GeneralJsonSchemaParser.__name__,
    ),
    "mqtt_communicator_send_to_iota": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_iota_communicators",
        class_name=fiware_iota_communicators.MQTTCommunicatorSendToIoTA.__name__,
    ),
    "mqtt_communicator_receive_from_iota": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_iota_communicators",
        class_name=fiware_iota_communicators.MQTTCommunicatorReceiveFromIoTA.__name__,
    ),
    "debug_listener": ModuleImport(
        import_path="juniconnlib_core.modules.devtools",
        class_name=devtools.DebugListener.__name__,
    ),
    "debug_sender": ModuleImport(
        import_path="juniconnlib_core.modules.devtools",
        class_name=devtools.DebugSender.__name__,
    ),
    "fiware_iota_device_provisioner": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_iota_device_provisioner",
        class_name=fiware_iota_device_provisioner.FiwareIoTADeviceProvisioner.__name__,
    ),
    "influxdb_writer": ModuleImport(
        import_path="juniconnlib_core.modules.influxdb_writer",
        class_name=influxdb_writer.InfluxdbWriter.__name__,
    ),
    "fiware_ocb_entity_provisioner": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_ocb_entity_provisioner",
        class_name=fiware_ocb_entity_provisioner.FiwareOCBEntityProvisioner.__name__,
    ),
    "fiware_mqtt_subscription_handler": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_subscriptions",
        class_name=fiware_subscriptions.FiwareMQTTSubscriptionHandler.__name__,
    ),
    "fiware_http_subscription_handler": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_subscriptions",
        class_name=fiware_subscriptions.FiwareHTTPSubscriptionHandler.__name__,
    ),
    "mqtt_communicator_receive_from_ocb": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_ocb_communicators",
        class_name=fiware_ocb_communicators.MQTTCommunicatorReceiveFromOCB.__name__,
    ),
    "http_communicator_send_to_ocb": ModuleImport(
        import_path="juniconnlib_core.modules.fiware_ocb_communicators",
        class_name=fiware_ocb_communicators.HTTPCommunicatorSendToOCB.__name__,
    ),
}
