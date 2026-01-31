import logging
import socket
from typing import Any, Dict, List, Optional, Union

from shaped.autogen.api.engine_api import EngineApi
from shaped.autogen.api.query_api import QueryApi
from shaped.autogen.api.table_api import TableApi
from shaped.autogen.api.view_api import ViewApi
from shaped.autogen.api_client import ApiClient
from shaped.autogen.configuration import Configuration
from shaped.autogen.models.ai_enrichment_view_config import AIEnrichmentViewConfig
from shaped.autogen.models.create_table_response import CreateTableResponse
from shaped.autogen.models.create_view_response import CreateViewResponse
from shaped.autogen.models.delete_engine_response import DeleteEngineResponse
from shaped.autogen.models.delete_table_response import DeleteTableResponse
from shaped.autogen.models.delete_view_response import DeleteViewResponse
from shaped.autogen.models.engine_config_v2 import EngineConfigV2
from shaped.autogen.models.engine_details_response import EngineDetailsResponse
from shaped.autogen.models.list_engines_response import ListEnginesResponse
from shaped.autogen.models.list_tables_response import ListTablesResponse
from shaped.autogen.models.list_views_response import ListViewsResponse
from shaped.autogen.models.parameters_value import ParametersValue
from shaped.autogen.models.query1 import Query1
from shaped.autogen.models.query_request import QueryRequest
from shaped.autogen.models.query_result import QueryResult
from shaped.autogen.models.rank_query_config import RankQueryConfig
from shaped.autogen.models.request import Request as TableRequest
from shaped.autogen.models.request1 import Request1 as ViewRequest
from shaped.autogen.models.response_get_view_details_views_view_name_get import (
    ResponseGetViewDetailsViewsViewNameGet,
)
from shaped.autogen.models.saved_query_info_response import SavedQueryInfoResponse
from shaped.autogen.models.saved_query_list_response import SavedQueryListResponse
from shaped.autogen.models.saved_query_request import SavedQueryRequest
from shaped.autogen.models.setup_engine_response import SetupEngineResponse
from shaped.autogen.models.sql_view_config import SQLViewConfig
from shaped.autogen.models.table_insert_arguments import TableInsertArguments
from shaped.autogen.models.table_insert_response import TableInsertResponse
from shaped.autogen.models.update_table_response import UpdateTableResponse
from shaped.autogen.models.update_view_response import UpdateViewResponse
from shaped.config_builders import Engine
from shaped.query_builder import RankQueryBuilder

# Type aliases for better developer experience.
ViewConfig = Union[SQLViewConfig, AIEnrichmentViewConfig]


class Client:
    """
    Client SDK for Shaped AI V2 API.

    Provides access to all V2 API endpoints: Engine, Table, View, and Query APIs.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.shaped.ai/v2"):
        """
        Initialize the Shaped client.

        Args:
            api_key: Your Shaped API key.
            base_url: Base URL for the API (defaults to V2 endpoint).
        """
        self._api_key = api_key
        self._base_url = base_url
        api_key_dict = {"main": api_key}
        self._configuration = Configuration(api_key=api_key_dict)
        if base_url != "https://api.shaped.ai/v2":
            self._configuration.host = base_url

        # Optimize connection pool for high-performance query endpoints.
        # Increased pool size supports high-throughput scenarios (1k+ qps).
        self._configuration.connection_pool_maxsize = 100

        # Disable retries for query endpoints to minimize latency.
        # Fail fast rather than retry for high-throughput scenarios.
        self._configuration.retries = 0

        # Configure socket options for TCP keep-alive.
        self._configuration.socket_options = [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
        ]

        # HTTP/2 support: With urllib3 >= 2.2.3 and h2 installed,
        # HTTP/2 will be automatically negotiated if the server supports it.
        self._api_client = ApiClient(self._configuration)

        # Enable response compression for high-performance query endpoints.
        # Reduces bandwidth and improves performance for large query results.
        self._api_client.set_default_header("Accept-Encoding", "gzip, deflate")

        # Initialize V2 API instances.
        self._engine_api = EngineApi(self._api_client)
        self._table_api = TableApi(self._api_client)
        self._view_api = ViewApi(self._api_client)
        self._query_api = QueryApi(self._api_client)

        self._logger = logging.getLogger(__name__)
        if not self._logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(console_format)
            self._logger.addHandler(console_handler)
            self._logger.setLevel(logging.INFO)

    def _query_api_call(self, method: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Helper for Query API calls that require headers.

        Args:
            method: The API method to call.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            Result from the API call.
        """
        kwargs.setdefault("_headers", {})["x-api-key"] = self._api_key
        return method(*args, **kwargs)

    # Engine API Methods

    def create_engine(
        self, engine_config: Union[EngineConfigV2, Engine, Dict[str, Any]]
    ) -> SetupEngineResponse:
        """
        Create a new engine.

        Args:
            engine_config: Engine configuration (dict, EngineConfigV2, or Engine builder).

        Returns:
            SetupEngineResponse with engine URL.
        """
        self._logger.debug("Creating engine")

        # Handle Engine builder
        if isinstance(engine_config, Engine):
            engine_config = engine_config.build()

        # Convert dict to EngineConfigV2 to ensure proper model conversion.
        if isinstance(engine_config, dict):
            try:
                engine_config = EngineConfigV2.from_dict(engine_config)
            except Exception:
                # If conversion fails, pass dict as-is and let API handle it.
                pass
        return self._engine_api.post_setup_engine_engines_post(
            x_api_key=self._api_key, engine_config_v2=engine_config
        )

    def update_engine(
        self, engine_config: Union[EngineConfigV2, Engine, Dict[str, Any]]
    ) -> SetupEngineResponse:
        """
        Update an existing engine.

        Args:
            engine_config: Updated engine configuration (dict, EngineConfigV2, or Engine builder).

        Returns:
            SetupEngineResponse.
        """
        self._logger.debug("Updating engine")

        # Handle Engine builder
        if isinstance(engine_config, Engine):
            engine_config = engine_config.build()

        return self._engine_api.patch_update_engine_engines_patch(
            x_api_key=self._api_key, engine_config_v2=engine_config
        )

    def list_engines(self) -> ListEnginesResponse:
        """
        List all engines.

        Returns:
            ListEnginesResponse with list of engines.
        """
        self._logger.debug("Listing engines")
        return self._engine_api.get_engines_engines_get(x_api_key=self._api_key)

    def get_engine(self, engine_name: str) -> EngineDetailsResponse:
        """
        Get details for a specific engine.

        Args:
            engine_name: Name of the engine.

        Returns:
            EngineDetailsResponse with engine details.
        """
        self._logger.debug("Getting engine details for %s", engine_name)
        return self._engine_api.get_engine_details_engines_engine_name_get(
            engine_name=engine_name, x_api_key=self._api_key
        )

    def delete_engine(self, engine_name: str) -> DeleteEngineResponse:
        """
        Delete an engine.

        Args:
            engine_name: Name of the engine to delete.

        Returns:
            DeleteEngineResponse.
        """
        self._logger.debug("Deleting engine %s", engine_name)
        return self._engine_api.delete_engine_engines_engine_name_delete(
            engine_name=engine_name, x_api_key=self._api_key
        )

    # Table API Methods

    def create_table(
        self, table_config: Union[TableRequest, Dict[str, Any]]
    ) -> CreateTableResponse:
        """
        Create a new table.

        Args:
            table_config: Table configuration (one of the TableConfig types) or dict.

        Returns:
            CreateTableResponse.
        """
        self._logger.debug("Creating table")
        # Convert dict to Request if needed
        if isinstance(table_config, dict):
            request = TableRequest.from_dict(table_config)
        elif not isinstance(table_config, TableRequest):
            # Assume it's a specific table config (e.g. PostgresTableConfig)
            # and wrap it in the Request wrapper.
            try:
                request = TableRequest(table_config)
            except Exception:
                # Fallback
                request = table_config
        else:
            request = table_config
        return self._table_api.post_create_table_tables_post(
            x_api_key=self._api_key, request=request
        )

    def update_table(
        self, table_config: Union[TableRequest, Dict[str, Any]]
    ) -> UpdateTableResponse:
        """
        Update an existing table.

        Args:
            table_config: Updated table configuration (one of the TableConfig types) or dict.

        Returns:
            UpdateTableResponse.
        """
        self._logger.debug("Updating table")
        # Convert dict to Request if needed.
        if isinstance(table_config, dict):
            request = TableRequest.from_dict(table_config)
        elif not isinstance(table_config, TableRequest):
            try:
                request = TableRequest(table_config)
            except Exception:
                request = table_config
        else:
            request = table_config
        return self._table_api.patch_update_table_tables_patch(
            x_api_key=self._api_key, request=request
        )

    def list_tables(self) -> ListTablesResponse:
        """
        List all tables.

        Returns:
            ListTablesResponse with list of tables.
        """
        self._logger.debug("Listing tables")
        return self._table_api.get_tables_tables_get(x_api_key=self._api_key)

    def insert_table_rows(
        self, table_name: str, rows: List[Dict[str, Any]]
    ) -> TableInsertResponse:
        """
        Insert rows into a table.

        Args:
            table_name: Name of the table.
            rows: List of row dictionaries to insert.

        Returns:
            TableInsertResponse.
        """
        self._logger.debug("Inserting rows into table %s", table_name)
        insert_args = TableInsertArguments(data=rows)
        return self._table_api.post_table_insert_tables_table_name_insert_post(
            table_name=table_name,
            x_api_key=self._api_key,
            table_insert_arguments=insert_args,
        )

    def delete_table(self, table_name: str) -> DeleteTableResponse:
        """
        Delete a table.

        Args:
            table_name: Name of the table to delete.

        Returns:
            DeleteTableResponse.
        """
        self._logger.debug("Deleting table %s", table_name)
        return self._table_api.delete_table_route_tables_table_name_delete(
            table_name=table_name, x_api_key=self._api_key
        )

    # View API Methods

    def create_view(
        self, view_config: Union[ViewConfig, Dict[str, Any]]
    ) -> CreateViewResponse:
        """
        Create a new view.

        Args:
            view_config: View configuration (ViewConfig or dict).

        Returns:
            CreateViewResponse.
        """
        self._logger.debug("Creating view")
        # Convert dict to Request1 if needed.
        if isinstance(view_config, dict):
            request = ViewRequest.from_dict(view_config)
        elif not isinstance(view_config, ViewRequest):
            # Try to wrap specific view config (SQLViewConfig etc)
            try:
                request = ViewRequest(view_config)
            except Exception:
                request = view_config
        else:
            request = view_config
        return self._view_api.post_create_view_views_post(
            x_api_key=self._api_key, request1=request
        )

    def update_view(
        self, view_config: Union[ViewConfig, Dict[str, Any]]
    ) -> UpdateViewResponse:
        """
        Update an existing view.

        Args:
            view_config: Updated view configuration (ViewConfig or dict).

        Returns:
            UpdateViewResponse.
        """
        self._logger.debug("Updating view")
        # Convert dict to Request1 if needed.
        if isinstance(view_config, dict):
            request = ViewRequest.from_dict(view_config)
        elif not isinstance(view_config, ViewRequest):
            try:
                request = ViewRequest(view_config)
            except Exception:
                request = view_config
        else:
            request = view_config
        return self._view_api.patch_update_view_views_patch(
            x_api_key=self._api_key, request1=request
        )

    def list_views(self) -> ListViewsResponse:
        """
        List all views.

        Returns:
            ListViewsResponse with list of views.
        """
        self._logger.debug("Listing views")
        return self._view_api.get_views_views_get(x_api_key=self._api_key)

    def get_view(self, view_name: str) -> ResponseGetViewDetailsViewsViewNameGet:
        """
        Get details for a specific view.

        Args:
            view_name: Name of the view.

        Returns:
            ResponseGetViewDetailsViewsViewNameGet with view details.
        """
        self._logger.debug("Getting view details for %s", view_name)
        return self._view_api.get_view_details_views_view_name_get(
            view_name=view_name, x_api_key=self._api_key
        )

    def delete_view(self, view_name: str) -> DeleteViewResponse:
        """
        Delete a view.

        Args:
            view_name: Name of the view to delete.

        Returns:
            DeleteViewResponse.
        """
        self._logger.debug("Deleting view %s", view_name)
        return self._view_api.delete_view_views_view_name_delete(
            view_name=view_name, x_api_key=self._api_key
        )

    # Query API Methods

    def execute_query(
        self,
        engine_name: str,
        query: Union[RankQueryConfig, RankQueryBuilder, Dict[str, Any], str],
        parameters: Optional[Dict[str, Any]] = None,
        return_metadata: bool = False,
        return_explanation: bool = False,
        return_journey_explanations: bool = False,
        pagination_key: Optional[str] = None,
        ignore_pagination: bool = False,
    ) -> QueryResult:
        """
        Execute a query against a V2 engine.

        Args:
            engine_name: Name of the engine to query.
            query: Query configuration. Can be:
                - RankQueryConfig instance
                - RankQueryBuilder instance (will be built)
                - Dict representing a query config
                - String SQL query
            parameters: Query parameters dictionary for parameterized queries.
            return_metadata: Whether to return metadata in results.
            return_explanation: Whether to include detailed query execution
                explanation.
            return_journey_explanations: Whether to include per-entity journey
                tracking in results.
            pagination_key: Pagination key for continuing from a previous query.
            ignore_pagination: Whether to ignore pagination and return results
                from the beginning.

        Returns:
            QueryResult from the API.
        """
        self._logger.debug("Executing query")

        # Convert query to proper format.
        if isinstance(query, RankQueryBuilder):
            query = query.build()
        elif isinstance(query, dict):
            # Assume it's already in the right format.
            pass
        elif isinstance(query, str):
            # SQL query string - Query1 accepts strings directly.
            pass
        # If it's already a RankQueryConfig, convert to dict for QueryRequest.
        elif isinstance(query, RankQueryConfig):
            if hasattr(query, "model_dump"):
                query = query.model_dump(by_alias=True)
            else:
                query = dict(query)

        # Convert parameters to ParametersValue instances if needed.
        converted_parameters = None
        if parameters:
            converted_parameters = {
                k: ParametersValue(v) if not isinstance(v, ParametersValue) else v
                for k, v in parameters.items()
            }

        # Query1 accepts both dict/QueryConfig and string.
        # Convert string queries to Query1 instances.
        if isinstance(query, str):
            # String queries need to be wrapped in Query1
            query_obj = Query1(query)
        elif isinstance(query, dict):
            # Convert sets to lists for JSON serialization.
            def convert_sets_to_lists(obj):
                """Recursively convert sets to lists for JSON serialization."""
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_sets_to_lists(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets_to_lists(item) for item in obj]
                return obj

            query_cleaned = convert_sets_to_lists(query)
            # Dict queries need to be converted to Query1 via from_dict
            query_obj = Query1.from_dict(query_cleaned)
        elif isinstance(query, RankQueryConfig):
            if hasattr(query, "model_dump"):
                query_dict = query.model_dump(by_alias=True)
            else:
                query_dict = dict(query)

            # Convert sets to lists for JSON serialization.
            def convert_sets_to_lists(obj):
                """Recursively convert sets to lists for JSON serialization."""
                if isinstance(obj, set):
                    return list(obj)
                elif isinstance(obj, dict):
                    return {k: convert_sets_to_lists(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets_to_lists(item) for item in obj]
                return obj

            query_dict_cleaned = convert_sets_to_lists(query_dict)
            query_obj = Query1.from_dict(query_dict_cleaned)
        else:
            raise TypeError(
                f"Invalid query type: {type(query)}. Expected RankQueryConfig, dict, or str."
            )

        query_request = QueryRequest(
            query=query_obj,
            parameters=converted_parameters,
            return_metadata=return_metadata,
            return_explanation=return_explanation,
            return_journey_explanations=return_journey_explanations,
            pagination_key=pagination_key,
            ignore_pagination=ignore_pagination,
        )

        return self._query_api_call(
            self._query_api.execute_ad_hoc_query_query_post,
            engine_name=engine_name,
            query_request=query_request,
        )

    def execute_saved_query(
        self,
        engine_name: str,
        query_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        return_metadata: bool = True,
        return_explanation: bool = False,
        return_journey_explanations: bool = False,
        pagination_key: Optional[str] = None,
        ignore_pagination: bool = False,
    ) -> QueryResult:
        """
        Execute a saved query by name.

        Args:
            engine_name: Name of the engine containing the saved query.
            query_name: Name of the saved query to execute.
            parameters: Query parameters dictionary.
            return_metadata: Whether to return metadata in results (defaults
                to True for saved queries).
            return_explanation: Whether to include detailed query execution
                explanation.
            return_journey_explanations: Whether to include per-entity journey
                tracking in results.
            pagination_key: Pagination key for continuing from a previous query.
            ignore_pagination: Whether to ignore pagination and return results
                from the beginning.

        Returns:
            QueryResult from the API.
        """
        self._logger.debug("Executing saved query %s", query_name)

        # Convert parameters to ParametersValue instances if needed.
        converted_parameters = None
        if parameters:
            converted_parameters = {
                k: ParametersValue(v) if not isinstance(v, ParametersValue) else v
                for k, v in parameters.items()
            }

        saved_query_request = SavedQueryRequest(
            parameters=converted_parameters,
            return_metadata=return_metadata,
            return_explanation=return_explanation,
            return_journey_explanations=return_journey_explanations,
            pagination_key=pagination_key,
            ignore_pagination=ignore_pagination,
        )

        return self._query_api_call(
            self._query_api.execute_saved_query_queries_query_name_post,
            engine_name=engine_name,
            query_name=query_name,
            saved_query_request=saved_query_request,
        )

    def get_saved_query_info(
        self, engine_name: str, query_name: str
    ) -> SavedQueryInfoResponse:
        """
        Get information about a saved query.

        Args:
            engine_name: Name of the engine containing the saved query.
            query_name: Name of the saved query.

        Returns:
            SavedQueryInfoResponse with query information.
        """
        self._logger.debug(
            "Getting saved query info for %s in engine %s", query_name, engine_name
        )
        return self._query_api_call(
            self._query_api.get_saved_query_info_queries_query_name_get,
            engine_name=engine_name,
            query_name=query_name,
        )

    def list_saved_queries(self, engine_name: str) -> SavedQueryListResponse:
        """
        List all saved queries for an engine.

        Args:
            engine_name: Name of the engine to list saved queries for.

        Returns:
            SavedQueryListResponse with list of saved queries.
        """
        self._logger.debug("Listing saved queries for engine %s", engine_name)
        return self._query_api_call(
            self._query_api.list_saved_queries_queries_get,
            engine_name=engine_name,
        )
