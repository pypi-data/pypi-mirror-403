import logging
import warnings

from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from urllib3.exceptions import ConnectTimeoutError, HTTPError, TimeoutError

logger = logging.getLogger(__name__)


class InfluxDBConnect:
    def __init__(
        self,
        url: str,
        org: str,
        bucket: str,
        token: str,
        timeout: int = 10_000,
        write_batch_size: int = 1,
    ):
        self._url = url
        self._org = org
        self._bucket = bucket
        self._token = token
        self._client = InfluxDBClient(
            url=url,
            token=token,
            org=org,
            timeout=timeout,
            enable_gzip=False,
        )

        if 1 < write_batch_size <= 1000:
            self._write_batch_size = write_batch_size
        else:
            self._write_batch_size = 1
        self._write_batch_data: list[dict] = list()
        self._write_batch_count = 0

        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

        self._query_api = self._client.query_api()

    def _write(self, data):
        self._write_api.write(bucket=self._bucket, org=self._org, record=data)

    def _write_batch(self):
        self._write(self._write_batch_data)
        self._write_batch_data.clear()
        self._write_batch_count = 0

    def write(self, data: dict | list[dict]):
        if self._write_batch_size == 1 or isinstance(data, list):
            self._write(data)
            return

        self._write_batch_data.append(data)
        self._write_batch_count += 1
        if self._write_batch_count >= self._write_batch_size:
            self._write_batch()

    def flush(self):
        if self._write_batch_count >= 1:
            self._write_batch()

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        It will bind this method’s return value to the target(s)
        specified in the `as` clause of the statement.

        return: self instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object and close the connect."""
        self.flush()
        self._write_api.close()
        self._client.close()

    def query(self, q: str):
        warnings.warn(
            "query() 方法已废弃, 使用 query_with_columns() 方法替代", DeprecationWarning
        )
        return self._query_api.query(q)

    def query_with_columns(self, q: str, cs: list[str]) -> list:
        try:
            return self._query_api.query(q).to_values(columns=cs)
        except (InfluxDBError, HTTPError, TimeoutError, ConnectTimeoutError) as e:
            logger.error(f"InfluxDB access error: {e}")
            return []

    def query_data_frame(self, q: str):
        return self._query_api.query_data_frame(q)
