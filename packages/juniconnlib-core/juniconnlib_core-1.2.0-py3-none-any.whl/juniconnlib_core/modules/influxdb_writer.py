import json
from datetime import datetime, timezone

from agentlib.core import Agent, AgentVariable, BaseModule, BaseModuleConfig
from filip.models import FiwareHeader
from influxdb_client import InfluxDBClient, Point, WriteApi, WritePrecision
from pydantic import AnyHttpUrl, Field
from urllib3.exceptions import MaxRetryError

from juniconnlib_core.data_models.basic_models import IotaMqttMessage
from juniconnlib_core.utils.logging import create_logger_for_module
from juniconnlib_core.utils.meta import Aliases


class InfluxdbWriterConfig(BaseModuleConfig):
    """Configuration for the :class:`InfluxdbWriterConfig` module."""

    fiware_header: FiwareHeader = Field(
        title="FIWARE Header",
        description="The corresponding FIWARE service  and service path for the data",
    )
    influxdb_url: AnyHttpUrl = Field(
        title="InfluxDB Url", description="Url of the InfluxDB"
    )
    influxdb_org: str = Field(
        title="InfluxDB Organization",
        description="Organization the data should be written in",
    )
    influxdb_bucket: str = Field(
        title="InfluxDB Bucket",
        description="Bucket the data should be written in",
    )
    credentials_file: str = Field(
        title="InfluxDB Credentials",
        description="JSON File with API token with write access to the bucket and org the data should be written in",
    )
    timestamp_field: str | None = Field(
        title="Timestamp Field",
        description="If provided, this parameter shows where in the payload the timestamp is stored",
    )
    write_precision: str | None = Field(
        title="Write Precision for influxDB data",
        description="Sets the resolution the timestamps should be written to the influxDB",
        default=WritePrecision.S,
    )


class InfluxdbWriter(BaseModule):
    """A module or writing data directly into an InfluxDB"""

    config: InfluxdbWriterConfig

    def __init__(self, config: dict, agent: Agent):
        """Constructor for the :class:`InfluxdbWriter` module.

        Args:
            config (dict): A dict containing configuration parameters as
                defined in :class:`InfluxDBWriterConfig`
            agent (agentlib.Agent): The agent for the initialization."""

        super().__init__(config=config, agent=agent)
        self.influxdb_client: InfluxDBClient | None = None
        self.write_api: WriteApi | None = None
        self.logger = create_logger_for_module(self)

        # read in the credentials file as JSON
        credentials_file = self.config.credentials_file
        with open(self.config.credentials_file, "r", encoding="utf-8") as file:
            self.logger.debug(
                "reading credentials from {}".format(credentials_file)
            )
            credentials_data: dict[str, str] = json.load(file)
        self.influxdb_api_token = credentials_data["token"]

    def __reconnect_influxdb_client(self):
        """(Re)Connects to the InfluxDB and pings it. If the configured bucket
        does not exist, the function creates it.

        Raises:
            ConnectionError: if the ping is not successful
        """
        if self.influxdb_client and not self.influxdb_client.ping():
            self.__disconnect_from_influxdb()
        try:
            self.influxdb_client = InfluxDBClient(
                url=str(self.config.influxdb_url),
                token=self.influxdb_api_token,
                org=self.config.influxdb_org,
                retries=5,
            )
            if not self.influxdb_client.ping():
                raise ConnectionError("Ping to influxdb failed.")
            self.logger.info(
                f"Connected to InfluxDB at {self.config.influxdb_url}."
            )

        except Exception as e:
            self.logger.error(
                f"Could not set up InfluxDB at {self.config.influxdb_url}: {e}"
            )
            raise e

    def __reconnect_write_api(self):
        """Connects to influxdb and creates a new write_api."""
        self.__reconnect_influxdb_client()
        self.write_api = self.influxdb_client.write_api()

    def check_if_target_bucket_exits(self):
        """Creates the required bucket if it does not exist.

        Raises:
            Exception: if bucket does not exist
        """
        # TODO: Check if the function actually creates the bucket
        self.__reconnect_influxdb_client()
        buckets_api = self.influxdb_client.buckets_api()
        target_bucket = buckets_api.find_bucket_by_name(
            bucket_name=self.config.influxdb_bucket
        )
        if target_bucket is None:
            self.logger.error(
                f'The required bucket "{self.config.influxdb_bucket}" did '
                f"not exist at {self.config.influxdb_url} "
                f"in organization: {self.config.influxdb_org}"
            )
            raise Exception(
                'Bucket "{}" does not exist.'.format(
                    self.config.influxdb_bucket
                )
            )

    def __disconnect_from_influxdb(self):
        """Close the api client and influxdb connection."""
        self.logger.info(
            f"Disconnected from InfluxDB at {self.config.influxdb_url}"
        )
        if self.write_api:
            self.write_api.close()
            self.write_api = None

        if self.influxdb_client:
            self.influxdb_client.close()
            self.influxdb_client = None

    def __write_to_influxdb(self, data_point: Point):
        """Writes the point to the influxDB.

        Raises:
             AttributeError: if write_api is closed or None.
        """
        self.logger.debug(f"Writing Point {data_point} to InfluxDB")
        self.write_api.write(
            bucket=self.config.influxdb_bucket,
            org=self.config.influxdb_org,
            record=data_point,
            write_precision=self.config.write_precision,
        )

    def write_to_influxdb(self, data_point: Point):
        """Writes the point to the influxDB.

        Attempts a single reconnect if connection is closed and no
        other error occurred.

        Args:
            data_point (Point): Point to write to the influxDB

        Raises:
            Exception: Data point couldn't be written
        """
        try:
            self.__write_to_influxdb(data_point)
        except AttributeError as e:
            if self.write_api:
                raise e
            self.logger.debug("Trying to reconnect to InfluxDB")
            self.logger.debug(
                f"Exception assumed due to closed connection: {e}"
            )
            try:
                self.__reconnect_write_api()
                self.__write_to_influxdb(data_point)
            except AttributeError as e:
                self.logger.error(
                    "A connection to InfluxDB cannot be established: {}".format(
                        e
                    )
                )
        except MaxRetryError as e:
            self.logger.error(
                f"MaxRetryError while writing data to InfluxDB {self.influxdb_client.url}: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"Could not write Point {data_point} to InfluxDB: {e}"
            )

    def register_callbacks(self):
        """Registers a single callback:

        `alias = "MqttSendToFiware"`: to write anything that is usually
        written to FIWARE

        """
        self.agent.data_broker.register_callback(
            callback=self._callback_incoming_data,
            alias=Aliases.MQTT_SEND_TO_FIWARE,
        )

    def _callback_incoming_data(self, variable: AgentVariable):
        """Processes incoming message and writes it to the influxDB.

        Args:
            variable (AgentVariable): Variable to write to the influxDB
        """
        if not isinstance(variable.value, IotaMqttMessage):
            return
        self.logger.debug(
            f"Received MQTT message from agent broker: {variable.value}"
        )

        point = self.create_data_point(
            fiware_header=self.config.fiware_header, message=variable.value
        )
        self.write_to_influxdb(point)

    def process(self):
        self.check_if_target_bucket_exits()
        yield self.env.event()

    def terminate(self):
        self.__disconnect_from_influxdb()

    def create_data_point(
        self, fiware_header: FiwareHeader, message: IotaMqttMessage
    ) -> Point:
        """Create a single data point to be written to the InfluxDB

        Args:
            fiware_header (FiwareHeader): fiware service information for
                the bucket
            message (IotaMqttMessage): Attribute data to be written

        Returns:
            Point: the InfluxDB compatible point object
        """
        device_id = message.device_id
        device_type = message.device_type
        timestamp = datetime.now(timezone.utc).isoformat()
        if self.config.timestamp_field:
            try:
                timestamp = message.payload.pop(self.config.timestamp_field)
            except KeyError:
                self.logger.info(
                    f"Entity {device_id} does not have a valid timestamp! Using default timestamp now()"
                )
        point_dict = {
            "measurement": device_type,
            "tags": {
                "device_id": device_id,
                "fiware-service": fiware_header.service,
                "fiware-servicepath": fiware_header.service_path,
            },
            "time": timestamp,
            "fields": {},
        }
        for device_attribute, value in message.payload.items():
            point_dict["fields"][device_attribute] = value

        return Point.from_dict(
            dictionary=point_dict, write_precision=self.config.write_precision
        )

    def delete_from_influxdb(
        self,
        start: str | datetime,
        stop: str | datetime,
        predicate: str,
        bucket: str,
        org: str,
    ):
        """Deletes a certain range of timer series date from the InfluxDB

        Args:
            start (datetime): start date of the range
            stop (datetime): stop date of the range
            predicate (str): predicate syntax for the delete operation
            bucket (str): bucket name from which to delete
            org (str): organization name from which to delete

        Raises:
            MaxRetryError: if delete fails too often
        """
        try:
            self.__reconnect_influxdb_client()
            delete_api = self.influxdb_client.delete_api()
            delete_api.delete(
                start=start,
                stop=stop,
                predicate=predicate,
                bucket=bucket,
                org=org,
            )
        except MaxRetryError as e:
            raise Exception(
                f"MaxRetryError while deleting data of bucket {bucket} from InfluxDB "
                f"{self.influxdb_client.url}"
            ) from e
