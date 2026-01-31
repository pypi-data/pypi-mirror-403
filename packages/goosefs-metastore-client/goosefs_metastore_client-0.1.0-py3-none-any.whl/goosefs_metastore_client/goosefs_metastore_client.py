"""GooseFS Metastore Client main class."""
from typing import List, Dict, Optional, Any
import logging
import uuid

import grpc
from grpc_files.table_master_pb2 import (
    GetAllDatabasesPRequest,
    GetDatabasePRequest,
    GetAllTablesPRequest,
    GetTablePRequest,
    AttachDatabasePRequest,
    DetachDatabasePRequest,
    SyncDatabasePRequest,
    MountTablePRequest,
    UnmountTablePRequest,
    AccessStatPRequest,
    IncrementHotsPRequest,
    GetTableColumnStatisticsPRequest,
    GetPartitionColumnStatisticsPRequest,
    ReadTablePRequest,
    TransformTablePRequest,
    GetTransformJobInfoPRequest,
    Database,
    DbInfo,
    TbInfo,
    TableInfo,
    AccessStatInfo,
    SyncStatus,
)
from grpc_files.table_master_pb2_grpc import TableMasterClientServiceStub
from goosefs_metastore_client.authentication import ChannelAuthenticator, ChannelIdInjector


logger = logging.getLogger(__name__)


class GoosefsMetastoreClient:
    """User main interface with the GooseFS Table Master service via gRPC."""

    def __init__(
        self,
        host: str,
        port: int = 9200,
        max_retries: int = 3,
        timeout: int = 30,
        credentials: Optional[grpc.ChannelCredentials] = None,
        authentication_enabled: bool = True,
        username: Optional[str] = None,
        impersonation_user: Optional[str] = None,
    ) -> None:
        """
        Instantiate the client for the given host and port.

        :param host: GooseFS master host
        :param port: GooseFS table master service port (default: 9200)
        :param max_retries: maximum number of retries for failed requests
        :param timeout: timeout in seconds for gRPC calls
        :param credentials: optional gRPC credentials for secure connection
        :param authentication_enabled: whether to enable SASL authentication (default: True)
        :param username: username for authentication (defaults to OS user)
        :param impersonation_user: optional user to impersonate
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.timeout = timeout
        self.credentials = credentials
        self.authentication_enabled = authentication_enabled
        self.username = username
        self.impersonation_user = impersonation_user
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[TableMasterClientServiceStub] = None
        self.channel_id: Optional[uuid.UUID] = None

    def connect(self) -> "GoosefsMetastoreClient":
        """
        Open the gRPC connection to the GooseFS Table Master.

        :return: GoosefsMetastoreClient instance
        """
        address = f"{self.host}:{self.port}"
        
        if self.credentials:
            base_channel = grpc.secure_channel(address, self.credentials)
        else:
            base_channel = grpc.insecure_channel(address)
        
        if self.authentication_enabled:
            self.channel_id = uuid.uuid4()
            logger.info(f"Authenticating with channel ID: {self.channel_id}")
            
            # Authenticate on the base channel (without Channel ID header)
            authenticator = ChannelAuthenticator(
                base_channel,
                self.channel_id,
                username=self.username,
                impersonation_user=self.impersonation_user,
            )
            
            try:
                authenticator.authenticate()
            except Exception as e:
                base_channel.close()
                raise RuntimeError(f"Authentication failed: {e}") from e
            
            # After successful authentication, add Channel ID interceptor
            channel_id_injector = ChannelIdInjector(self.channel_id)
            self.channel = grpc.intercept_channel(base_channel, channel_id_injector)
        else:
            self.channel = base_channel
        
        self.stub = TableMasterClientServiceStub(self.channel)
        logger.info(f"Connected to GooseFS Table Master at {address}")
        
        return self

    def close(self) -> None:
        """Close the gRPC connection."""
        if self.channel:
            self.channel.close()
            logger.info("Closed connection to GooseFS Table Master")

    def __enter__(self) -> "GoosefsMetastoreClient":
        """Handle connection opening when using 'with' block statement."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Handle connection closing after the code inside 'with' block ends."""
        self.close()

    def _call_with_retry(self, func, *args, **kwargs):
        """
        Call a gRPC method with retry logic.

        :param func: the gRPC method to call
        :param args: positional arguments for the method
        :param kwargs: keyword arguments for the method
        :return: the result of the gRPC call
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, timeout=self.timeout, **kwargs)
            except grpc.RpcError as e:
                last_exception = e
                logger.warning(
                    f"gRPC call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    if e.code() in (
                        grpc.StatusCode.UNAVAILABLE,
                        grpc.StatusCode.DEADLINE_EXCEEDED,
                    ):
                        continue
                    else:
                        raise
        
        raise last_exception

    def get_all_databases(self) -> List[DbInfo]:
        """
        Get all databases from the GooseFS catalog.

        :return: list of DbInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetAllDatabasesPRequest()
        response = self._call_with_retry(self.stub.GetAllDatabases, request)
        return list(response.dbInfo)

    def get_database(self, db_name: str) -> Database:
        """
        Get a specific database by name.

        :param db_name: database name
        :return: Database object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.GetDatabase, request)
        return response.db

    def get_all_tables(self, database: str) -> List[TbInfo]:
        """
        Get all tables in a database.

        :param database: database name
        :return: list of TbInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetAllTablesPRequest()
        request.database = database
        response = self._call_with_retry(self.stub.GetAllTables, request)
        return list(response.tbInfo)

    def get_table(self, db_name: str, table_name: str) -> TableInfo:
        """
        Get a specific table.

        :param db_name: database name
        :param table_name: table name
        :return: TableInfo object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        response = self._call_with_retry(self.stub.GetTable, request)
        return response.table_info

    def attach_database(
        self,
        udb_type: str,
        udb_db_name: str,
        db_name: str,
        configuration: Optional[Dict[str, str]] = None,
        ignore_sync_errors: bool = False,
        auto_mount: bool = False,
    ) -> SyncStatus:
        """
        Attach an external database to the GooseFS catalog.

        :param udb_type: underlying database type (e.g., "hive", "glue")
        :param udb_db_name: database name in the underlying database
        :param db_name: database name to use in GooseFS catalog
        :param configuration: configuration parameters for the database
        :param ignore_sync_errors: whether to ignore sync errors
        :param auto_mount: whether to auto-mount tables in the database
        :return: SyncStatus object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = AttachDatabasePRequest()
        request.udb_type = udb_type
        request.udb_db_name = udb_db_name
        request.db_name = db_name
        request.ignore_sync_errors = ignore_sync_errors
        request.auto_mount = auto_mount
        
        if configuration:
            request.attributed.update(configuration)
        
        response = self._call_with_retry(self.stub.AttachDatabase, request)
        return response.sync_status

    def detach_database(self, db_name: str) -> bool:
        """
        Detach a database from the GooseFS catalog.

        :param db_name: database name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = DetachDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.DetachDatabase, request)
        return response.success

    def sync_database(self, db_name: str) -> SyncStatus:
        """
        Sync a database with its underlying database.

        :param db_name: database name
        :return: SyncStatus object
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = SyncDatabasePRequest()
        request.db_name = db_name
        response = self._call_with_retry(self.stub.SyncDatabase, request)
        return response.status

    def mount_table(self, db_name: str, tb_name: str) -> bool:
        """
        Mount a table to GooseFS.

        :param db_name: database name
        :param tb_name: table name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = MountTablePRequest()
        request.dbName = db_name
        request.tbName = tb_name
        response = self._call_with_retry(self.stub.mountTable, request)
        return response.success

    def unmount_table(self, db_name: str, tb_name: str) -> bool:
        """
        Unmount a table from GooseFS.

        :param db_name: database name
        :param tb_name: table name
        :return: True if successful
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = UnmountTablePRequest()
        request.dbName = db_name
        request.tbName = tb_name
        response = self._call_with_retry(self.stub.unmountTable, request)
        return response.success

    def access_stat(self, days: int, top_nums: int) -> List[AccessStatInfo]:
        """
        Get access statistics for tables.

        :param days: number of days to look back
        :param top_nums: number of top results to return
        :return: list of AccessStatInfo objects
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = AccessStatPRequest()
        request.days = days
        request.topNums = top_nums
        response = self._call_with_retry(self.stub.accessStat, request)
        return list(response.accessStatInfo)

    def increment_hots(
        self,
        hive_hots_path_list: Optional[List[Dict[str, str]]] = None,
        presto_hots_path_list: Optional[List[Dict[str, str]]] = None,
        engine_name: Optional[str] = None,
    ) -> None:
        """
        Increment hot statistics for tables.

        :param hive_hots_path_list: list of hive hot paths
        :param presto_hots_path_list: list of presto hot paths
        :param engine_name: engine name
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = IncrementHotsPRequest()
        
        if engine_name:
            request.engine_name = engine_name
        
        self._call_with_retry(self.stub.incrementHots, request)

    def get_table_column_statistics(
        self, db_name: str, table_name: str, col_names: List[str]
    ) -> Any:
        """
        Get column statistics for a table.

        :param db_name: database name
        :param table_name: table name
        :param col_names: list of column names
        :return: column statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTableColumnStatisticsPRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.col_names.extend(col_names)
        response = self._call_with_retry(self.stub.GetTableColumnStatistics, request)
        return list(response.statistics)

    def get_partition_column_statistics(
        self,
        db_name: str,
        table_name: str,
        col_names: List[str],
        part_names: List[str],
    ) -> Any:
        """
        Get partition column statistics.

        :param db_name: database name
        :param table_name: table name
        :param col_names: list of column names
        :param part_names: list of partition names
        :return: partition column statistics
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetPartitionColumnStatisticsPRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.col_names.extend(col_names)
        request.part_names.extend(part_names)
        response = self._call_with_retry(
            self.stub.GetPartitionColumnStatistics, request
        )
        return response.partition_statistics

    def read_table(
        self, db_name: str, table_name: str, constraint: Optional[Any] = None
    ) -> Any:
        """
        Read table partitions with optional constraints.

        :param db_name: database name
        :param table_name: table name
        :param constraint: optional constraint for filtering
        :return: list of partitions
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = ReadTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        
        if constraint:
            request.constraint.CopyFrom(constraint)
        
        response = self._call_with_retry(self.stub.ReadTable, request)
        return list(response.partitions)

    def transform_table(
        self, db_name: str, table_name: str, definition: str
    ) -> int:
        """
        Transform a table with the given definition.

        :param db_name: database name
        :param table_name: table name
        :param definition: transformation definition
        :return: job ID for the transformation
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = TransformTablePRequest()
        request.db_name = db_name
        request.table_name = table_name
        request.definition = definition
        response = self._call_with_retry(self.stub.TransformTable, request)
        return response.job_id

    def get_transform_job_info(self, job_id: Optional[int] = None) -> Any:
        """
        Get information about transformation jobs.

        :param job_id: optional job ID; if not provided, returns all jobs
        :return: list of transformation job info
        """
        if not self.stub:
            raise RuntimeError("Client not connected. Call connect() first or use context manager.")
        
        request = GetTransformJobInfoPRequest()
        
        if job_id is not None:
            request.job_id = job_id
        
        response = self._call_with_retry(self.stub.GetTransformJobInfo, request)
        return list(response.info)
