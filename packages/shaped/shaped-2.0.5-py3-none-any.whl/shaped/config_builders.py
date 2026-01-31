"""
Fluent builders for constructing Shaped V2 configurations.

This module provides a fluent API for building Engine, Table, and View configurations
using Python objects instead of raw dictionaries or complex model instantiation.
"""

from typing import Any, Dict, List, Optional, Union

from shaped.autogen.models.ai_enrichment_view_config import AIEnrichmentViewConfig
from shaped.autogen.models.amplitude_table_config import AmplitudeTableConfig
from shaped.autogen.models.aws_pinpoint_table_config import AWSPinpointTableConfig
from shaped.autogen.models.big_query_table_config import BigQueryTableConfig
from shaped.autogen.models.clickhouse_table_config import ClickhouseTableConfig
from shaped.autogen.models.custom_table_config import CustomTableConfig
from shaped.autogen.models.data_config import DataConfig
from shaped.autogen.models.data_config_interaction_table import (
    DataConfigInteractionTable,
)
from shaped.autogen.models.deployment_config import DeploymentConfig
from shaped.autogen.models.dynamo_db_table_config import DynamoDBTableConfig
from shaped.autogen.models.engine_config_v2 import EngineConfigV2
from shaped.autogen.models.file_table_config import FileTableConfig
from shaped.autogen.models.iceberg_table_config import IcebergTableConfig

# Other Imports
from shaped.autogen.models.index_config import IndexConfig
from shaped.autogen.models.kafka_table_config import KafkaTableConfig
from shaped.autogen.models.kinesis_table_config import KinesisTableConfig
from shaped.autogen.models.mongo_db_table_config import MongoDBTableConfig
from shaped.autogen.models.mssql_table_config import MSSQLTableConfig
from shaped.autogen.models.my_sql_table_config import MySQLTableConfig

# Table Config Imports
from shaped.autogen.models.postgres_table_config import PostgresTableConfig
from shaped.autogen.models.posthog_table_config import PosthogTableConfig
from shaped.autogen.models.query_definition import QueryDefinition
from shaped.autogen.models.query_table_config import QueryTableConfig
from shaped.autogen.models.rank_query_config import RankQueryConfig
from shaped.autogen.models.redshift_table_config import RedshiftTableConfig
from shaped.autogen.models.reference_table_config import ReferenceTableConfig
from shaped.autogen.models.rudderstack_table_config import RudderstackTableConfig
from shaped.autogen.models.segment_table_config import SegmentTableConfig
from shaped.autogen.models.shopify_table_config import ShopifyTableConfig
from shaped.autogen.models.snowflake_table_config import SnowflakeTableConfig
from shaped.autogen.models.sql_transform_type import SQLTransformType

# View Config Imports
from shaped.autogen.models.sql_view_config import SQLViewConfig
from shaped.autogen.models.training_config import TrainingConfig

# Type aliases for better type hints
TableConfig = Union[
    PostgresTableConfig,
    BigQueryTableConfig,
    SnowflakeTableConfig,
    FileTableConfig,
    AmplitudeTableConfig,
    AWSPinpointTableConfig,
    ClickhouseTableConfig,
    CustomTableConfig,
    DynamoDBTableConfig,
    IcebergTableConfig,
    KafkaTableConfig,
    KinesisTableConfig,
    MongoDBTableConfig,
    MSSQLTableConfig,
    MySQLTableConfig,
    PosthogTableConfig,
    RedshiftTableConfig,
    RudderstackTableConfig,
    SegmentTableConfig,
    ShopifyTableConfig,
]
ViewConfig = Union[SQLViewConfig, AIEnrichmentViewConfig]


class Engine:
    """
    Builder for Engine configurations with support for all V2 features.

    Example:
        engine = (Engine("my-engine")
            .interactions("events")
            .users("users")
            .items("items")
            .with_index_config(...)
            .with_training_config(...)
            .with_deployment_config(...)
            .with_query("recommendations", "SELECT * FROM items ORDER BY score DESC"))
    """

    def __init__(self, name: str):
        if not name:
            raise ValueError("Engine name is required")

        self._name = name
        self._description: Optional[str] = None
        self._interactions: Optional[Union[str, Dict[str, Any]]] = None
        self._users: Optional[Union[str, Dict[str, Any]]] = None
        self._items: Optional[Union[str, Dict[str, Any]]] = None
        self._schedule: Optional[str] = None
        self._schema_override: Optional[Dict[str, Any]] = None
        self._compute: Optional[Dict[str, Any]] = None
        self._filters: List[Dict[str, Any]] = []
        self._reference_tables: Dict[str, Any] = {}
        self._tags: Optional[Dict[str, str]] = None
        self._index_config: Optional[IndexConfig] = None
        self._training_config: Dict[str, Any] = {}
        self._deployment_config: Dict[str, Any] = {}
        self._queries: Dict[str, QueryDefinition] = {}

    def description(self, description: str) -> "Engine":
        """Set the engine description."""
        self._description = description
        return self

    def interactions(self, table: Union[str, Dict[str, Any]]) -> "Engine":
        """Set the interactions table configuration."""
        self._interactions = table
        return self

    def users(self, table: Union[str, Dict[str, Any]]) -> "Engine":
        """Set the users table configuration."""
        self._users = table
        return self

    def items(self, table: Union[str, Dict[str, Any]]) -> "Engine":
        """Set the items table configuration."""
        self._items = table
        return self

    def schedule(self, schedule: str) -> "Engine":
        """Set the data refresh schedule."""
        self._schedule = schedule
        return self

    def with_schema_override(self, schema: Dict[str, Any]) -> "Engine":
        """Override the default schema detection with custom schema."""
        self._schema_override = schema
        return self

    def with_compute(self, compute: Dict[str, Any]) -> "Engine":
        """Configure compute resources for data processing."""
        self._compute = compute
        return self

    def add_filter(self, filter_config: Dict[str, Any]) -> "Engine":
        """
        Add a filter configuration.

        Args:
            filter_config: Dictionary containing filter configuration

        Returns:
            The Engine instance for method chaining
        """
        self._filters.append(filter_config)
        return self

    def add_filters(self, *filter_configs: Dict[str, Any]) -> "Engine":
        """
        Add multiple filter configurations at once.

        Args:
            *filter_configs: One or more filter configurations to add

        Returns:
            The Engine instance for method chaining
        """
        self._filters.extend(filter_configs)
        return self

    def add_reference_table(self, name: str, config: Dict[str, Any]) -> "Engine":
        """
        Add a reference table configuration.

        Args:
            name: Name of the reference table
            config: Configuration dictionary for the reference table

        Returns:
            The Engine instance for method chaining
        """
        self._reference_tables[name] = config
        return self

    def add_reference_tables(self, **tables: Dict[str, Any]) -> "Engine":
        """
        Add multiple reference tables at once using keyword arguments.

        Args:
            **tables: Keyword arguments where keys are table names and values are configs

        Returns:
            The Engine instance for method chaining
        """
        self._reference_tables.update(tables)
        return self

    def with_tags(self, **tags: str) -> "Engine":
        """Add tags to the engine configuration."""
        if self._tags is None:
            self._tags = {}
        self._tags.update(tags)
        return self

    def with_index_config(self, config: IndexConfig) -> "Engine":
        """Configure index settings."""
        self._index_config = config
        return self

    def with_training_config(
        self,
        data_split_strategy: Optional[str] = None,
        data_split_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> "Engine":
        """Configure model training settings."""
        if data_split_strategy:
            self._training_config["data_split"] = {
                "strategy": data_split_strategy,
                **(data_split_params or {}),
            }
        self._training_config.update(kwargs)
        return self

    def with_deployment_config(self, **kwargs) -> "Engine":
        """Configure deployment settings."""
        self._deployment_config.update(kwargs)
        return self

    def with_query(self, name: str, query: Union[str, Dict[str, Any]]) -> "Engine":
        """Add a named query definition."""
        if isinstance(query, str):
            # Convert SQL string to a RankQueryConfig
            query_def = QueryDefinition(query=RankQueryConfig(type="rank", sql=query))
        else:
            query_def = QueryDefinition(**query)

        self._queries[name] = query_def
        return self

    def validate(self) -> List[str]:
        """
        Validate the current configuration.

        Returns:
            List of error messages, empty if configuration is valid
        """
        errors = []

        if not self._interactions:
            errors.append("Interactions table is required")

        # Validate reference tables
        for name, config in self._reference_tables.items():
            if not isinstance(config, dict) or not config:
                errors.append(f"Invalid configuration for reference table '{name}'")

        # Validate queries
        for name, query in self._queries.items():
            if not query or not getattr(query, "query", None):
                errors.append(f"Invalid query definition for query '{name}'")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the current configuration is valid.

        Returns:
            True if configuration is valid, False otherwise
        """
        return not bool(self.validate())

    def build(self) -> EngineConfigV2:
        """
        Build the EngineConfigV2 object with all configured settings.

        Returns:
            EngineConfigV2: The built engine configuration

        Raises:
            ValueError: If the configuration is invalid
        """
        # Validate before building
        if errors := self.validate():
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        # Build data configuration
        data_config = DataConfig(
            interaction_table=self._create_data_table(self._interactions),
            user_table=self._create_data_table(self._users) if self._users else None,
            item_table=self._create_data_table(self._items) if self._items else None,
            schedule=self._schedule,
            schema=self._schema_override,
            compute=self._compute,
            filters=self._filters if self._filters else None,
            reference_tables=self._reference_tables if self._reference_tables else None,
        )

        # Build engine config
        config = EngineConfigV2(
            name=self._name,
            description=self._description,
            data=data_config,
            version="v2",
            tags=self._tags,
        )

        # Add optional configurations
        if self._index_config:
            config.index = self._index_config

        if self._training_config:
            config.training = TrainingConfig(**self._training_config)

        if self._deployment_config:
            config.deployment = DeploymentConfig(**self._deployment_config)

        if self._queries:
            config.queries = self._queries

        return config

    def _create_data_table(
        self, table: Union[str, Dict[str, Any], Any]
    ) -> Optional[DataConfigInteractionTable]:
        """
        Create a DataConfigInteractionTable from input.

        Args:
            table: Can be a table name (str), a table config dict, or an existing config object.

        Returns:
            A properly configured DataConfigInteractionTable instance, or None if input is None.

        Raises:
            ValueError: If the input cannot be converted to a valid table configuration.
        """
        if table is None:
            return None

        try:
            if isinstance(table, str):
                # It's a reference to a table by name
                config = ReferenceTableConfig(name=table)
                # Create the DataConfigInteractionTable with the config
                result = DataConfigInteractionTable(actual_instance=config)
                return result

            if isinstance(table, dict):
                # It's a config dictionary
                if table.get("type") == "query":
                    config = QueryTableConfig(**table)
                    result = DataConfigInteractionTable(actual_instance=config)
                    return result
                else:
                    config = ReferenceTableConfig(**table)
                    result = DataConfigInteractionTable(actual_instance=config)
                    return result

            # Check if it's already a DataConfigInteractionTable
            if hasattr(table, "actual_instance") and hasattr(table, "to_dict"):
                return table

            raise ValueError(
                f"Unsupported table configuration type: {type(table).__name__}"
            )

        except Exception as e:
            raise ValueError(f"Failed to create data table: {str(e)}")


class Table:
    """
    Factory methods for Table configurations.
    """

    @staticmethod
    def Postgres(
        name: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        table: str,
        replication_key: str,
        description: Optional[str] = None,
        schema: Optional[str] = None,  # database_schema
        ssl_args: Optional[Dict[str, Any]] = None,
    ) -> PostgresTableConfig:
        """Create a Postgres table configuration."""
        kwargs = {
            "name": name,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "table": table,
            "replication_key": replication_key,
            "description": description,
            "database_schema": schema,
        }
        if ssl_args:
            kwargs.update(ssl_args)
        return PostgresTableConfig(**kwargs)

    @staticmethod
    def BigQuery(
        name: str,
        project_id: str,
        dataset_id: str,
        table_id: str,
        service_account_key: str,
        replication_key: Optional[str] = None,
        description: Optional[str] = None,
    ) -> BigQueryTableConfig:
        """Create a BigQuery table configuration."""
        return BigQueryTableConfig(
            name=name,
            project=project_id,
            dataset=dataset_id,
            table=table_id,
            service_account_keys=service_account_key,
            replication_key=replication_key,
            description=description,
        )

    @staticmethod
    def Snowflake(
        name: str,
        account: str,
        user: str,
        password: str,
        database: str,
        schema: str,
        table: str,
        warehouse: str,
        role: str,
        replication_key: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SnowflakeTableConfig:
        """Create a Snowflake table configuration."""
        return SnowflakeTableConfig(
            name=name,
            account=account,
            user=user,
            password=password,
            database=database,
            schema_name=schema,
            table=table,
            warehouse=warehouse,
            role=role,
            replication_key=replication_key,
            description=description,
        )

    @staticmethod
    def File(
        name: str,
        file_path: str,
        file_type: str = "CSV",
        description: Optional[str] = None,
    ) -> FileTableConfig:
        """Create a File table configuration (for CSV, Parquet, etc)."""
        return FileTableConfig(
            name=name,
            path=file_path,
            mime_type=file_type,
            description=description,
        )

    @staticmethod
    def MySQL(
        name: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        table: str,
        replication_key: str,
        description: Optional[str] = None,
        ssl_args: Optional[Dict[str, Any]] = None,
    ) -> MySQLTableConfig:
        """
        Create a MySQL table configuration.

        Args:
            name: Name of the table configuration
            host: MySQL server hostname or IP
            port: MySQL server port
            user: MySQL username
            password: MySQL password
            database: Name of the database
            table: Name of the table
            replication_key: Column name to use for change data capture
            description: Optional description of the table
            ssl_args: Optional SSL configuration parameters

        Returns:
            MySQLTableConfig: Configured MySQL table configuration
        """
        kwargs = {
            "name": name,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "table": table,
            "replication_key": replication_key,
            "description": description,
        }
        if ssl_args:
            kwargs.update(ssl_args)
        return MySQLTableConfig(**kwargs)

    @staticmethod
    def MSSQL(
        name: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        schema: str,
        table: str,
        replication_key: str,
        description: Optional[str] = None,
        ssl_args: Optional[Dict[str, Any]] = None,
    ) -> MSSQLTableConfig:
        """
        Create a Microsoft SQL Server table configuration.

        Args:
            name: Name of the table configuration
            host: SQL Server hostname or IP
            port: SQL Server port
            user: SQL Server username
            password: SQL Server password
            database: Name of the database
            schema: Database schema name (e.g., 'dbo')
            table: Name of the table
            replication_key: Column name to use for change data capture
            description: Optional description of the table
            ssl_args: Optional SSL configuration parameters

        Returns:
            MSSQLTableConfig: Configured SQL Server table configuration
        """
        kwargs = {
            "name": name,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "schema_name": schema,
            "table": table,
            "replication_key": replication_key,
            "description": description,
        }
        if ssl_args:
            kwargs.update(ssl_args)
        return MSSQLTableConfig(**kwargs)

    @staticmethod
    def MongoDB(
        name: str,
        connection_uri: str,
        database: str,
        collection: str,
        replication_key: str,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> MongoDBTableConfig:
        """
        Create a MongoDB table configuration.

        Args:
            name: Name of the table configuration
            connection_uri: MongoDB connection URI
            database: Name of the database
            collection: Name of the collection
            replication_key: Field name to use for change data capture
            description: Optional description of the table
            **kwargs: Additional MongoDB connection parameters

        Returns:
            MongoDBTableConfig: Configured MongoDB table configuration
        """
        return MongoDBTableConfig(
            name=name,
            connection_uri=connection_uri,
            database=database,
            collection=collection,
            replication_key=replication_key,
            description=description,
            **kwargs,
        )

    @staticmethod
    def Redshift(
        name: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        schema: str,
        table: str,
        replication_key: str,
        description: Optional[str] = None,
        ssl_args: Optional[Dict[str, Any]] = None,
    ) -> RedshiftTableConfig:
        """
        Create an Amazon Redshift table configuration.

        Args:
            name: Name of the table configuration
            host: Redshift cluster endpoint
            port: Redshift port (typically 5439)
            user: Redshift username
            password: Redshift password
            database: Name of the database
            schema: Database schema name
            table: Name of the table
            replication_key: Column name to use for change data capture
            description: Optional description of the table
            ssl_args: Optional SSL configuration parameters

        Returns:
            RedshiftTableConfig: Configured Redshift table configuration
        """
        kwargs = {
            "name": name,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "schema_name": schema,
            "table": table,
            "replication_key": replication_key,
            "description": description,
        }
        if ssl_args:
            kwargs.update(ssl_args)
        return RedshiftTableConfig(**kwargs)


class View:
    """
    Factory methods for View configurations.
    """

    @staticmethod
    def SQL(
        name: str,
        query: str,
        description: Optional[str] = None,
        materialized: bool = False,
    ) -> SQLViewConfig:
        """
        Create a SQL view configuration.
        """
        transform_type = "MATERIALIZED_VIEW" if materialized else "VIEW"

        return SQLViewConfig(
            name=name,
            sql_query=query,
            sql_transform_type=(
                SQLTransformType(transform_type)
                if isinstance(transform_type, str)
                else transform_type
            ),
            description=description,
        )

    @staticmethod
    def AI(
        name: str,
        source_dataset: str,
        source_columns: List[str],
        output_columns: List[str],
        prompt: str,
        description: Optional[str] = None,
    ) -> AIEnrichmentViewConfig:
        """
        Create an AI enrichment view configuration.
        """
        return AIEnrichmentViewConfig(
            name=name,
            source_dataset=source_dataset,
            source_columns=source_columns,
            source_columns_in_output=source_columns,
            enriched_output_columns=output_columns,
            prompt=prompt,
            description=description,
        )
