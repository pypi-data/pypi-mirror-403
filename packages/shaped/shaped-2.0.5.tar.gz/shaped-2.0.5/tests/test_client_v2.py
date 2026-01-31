"""
Comprehensive tests for Shaped V2 Python SDK.

Tests all client methods to ensure they work correctly with the API spec.
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

try:
    from shaped import Client, RankQueryBuilder, ViewConfig
    from shaped.autogen.models.ai_enrichment_view_config import (
        AIEnrichmentViewConfig,
    )
    from shaped.autogen.models.query_result import QueryResult
    from shaped.autogen.models.setup_engine_response import SetupEngineResponse
    from shaped.autogen.models.sql_view_config import SQLViewConfig

    HAS_V2 = True
except ImportError:
    HAS_V2 = False
    pytestmark = pytest.mark.skip("V2 SDK not available")


@pytest.fixture
def mock_client():
    """Create a client instance with mocked API dependencies."""
    with patch("shaped.client.EngineApi"), patch("shaped.client.TableApi"), patch(
        "shaped.client.ViewApi"
    ), patch("shaped.client.QueryApi"):
        client = Client(api_key="test_api_key_123456789012345678901234567890")
        return client


@pytest.fixture
def sample_engine_config() -> Dict[str, Any]:
    """Sample engine configuration matching API spec."""
    return {
        "name": "test_engine",
        "version": "v2",
        "data": {
            "tables": [
                {
                    "name": "items",
                    "type": "table",
                    "table": {"table_name": "items"},
                }
            ],
        },
    }


@pytest.fixture
def sample_table_config() -> Dict[str, Any]:
    """Sample table configuration."""
    from shaped.autogen.models.postgres_table_config import PostgresTableConfig

    return PostgresTableConfig(
        name="test_table",
        description="Test Postgres table.",
        host="localhost",
        port=5432,
        user="test_user",
        password="test_password",
        table="items",
        database="test_db",
        replication_key="id",
    )


@pytest.fixture
def sample_sql_view_config() -> Dict[str, Any]:
    """Sample SQL view configuration."""
    return {
        "name": "test_view",
        "transform_type": "SQL",
        "description": "Test SQL view.",
        "sql_query": "SELECT * FROM items",
        "sql_transform_type": "VIEW",
    }


@pytest.fixture
def sample_ai_view_config() -> Dict[str, Any]:
    """Sample AI enrichment view configuration."""
    return {
        "name": "test_ai_view",
        "transform_type": "AI_ENRICHMENT",
        "description": "Test AI enrichment view.",
        "source_dataset": "items",
        "source_columns": ["description"],
        "source_columns_in_output": ["description"],
        "enriched_output_columns": ["category"],
        "prompt": "Extract category from description.",
    }


class TestClientInitialization:
    """Test client initialization and configuration."""

    def test_client_initialization_with_api_key(self):
        """Test client can be initialized with API key."""
        client = Client(api_key="test_api_key_123456789012345678901234567890")
        assert client._api_key == "test_api_key_123456789012345678901234567890"
        assert client._base_url == "https://api.shaped.ai/v2"

    def test_client_initialization_with_custom_base_url(self):
        """Test client can be initialized with custom base URL."""
        client = Client(
            api_key="test_api_key_123456789012345678901234567890",
            base_url="https://custom.api.shaped.ai/v2",
        )
        assert client._base_url == "https://custom.api.shaped.ai/v2"

    def test_client_has_all_api_instances(self, mock_client):
        """Test that client initializes all API instances."""
        assert mock_client._engine_api is not None
        assert mock_client._table_api is not None
        assert mock_client._view_api is not None
        assert mock_client._query_api is not None
        # TransformApi and DatasetApi removed (V1 API)


class TestEngineAPI:
    """Test Engine API methods."""

    def test_create_engine(self, mock_client, sample_engine_config):
        """Test creating an engine."""
        mock_response = SetupEngineResponse(
            engine_url="https://example.com/engines/test_engine",
        )
        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            return_value=mock_response
        )

        result = mock_client.create_engine(sample_engine_config)

        assert result.engine_url.endswith("test_engine")
        mock_client._engine_api.post_setup_engine_engines_post.assert_called_once()

    def test_update_engine(self, mock_client, sample_engine_config):
        """Test updating an engine."""
        mock_response = SetupEngineResponse(
            engine_url="https://example.com/engines/test_engine",
        )
        mock_client._engine_api.patch_update_engine_engines_patch = Mock(
            return_value=mock_response
        )

        result = mock_client.update_engine(sample_engine_config)

        assert result.engine_url.endswith("test_engine")
        mock_client._engine_api.patch_update_engine_engines_patch.assert_called_once()

    def test_list_engines(self, mock_client):
        """Test listing engines."""
        from shaped.autogen.models.engine import Engine
        from shaped.autogen.models.list_engines_response import (
            ListEnginesResponse,
        )

        mock_response = ListEnginesResponse(
            engines=[
                Engine(
                    engine_name="engine1",
                    description=None,
                    engine_uri="engine://engine1",
                    created_at="2024-01-01T00:00:00Z",
                    trained_at=None,
                    status="ready",
                    version="v2",
                )
            ]
        )
        mock_client._engine_api.get_engines_engines_get = Mock(
            return_value=mock_response
        )

        result = mock_client.list_engines()

        assert len(result.engines) == 1
        assert result.engines[0].engine_name == "engine1"
        mock_client._engine_api.get_engines_engines_get.assert_called_once()

    def test_get_engine(self, mock_client):
        """Test getting engine details."""
        from shaped.autogen.models.engine_details_response import (
            EngineDetailsResponse,
        )
        from shaped.autogen.models.engine_schema import EngineSchema

        mock_response = EngineDetailsResponse(
            engine_uri="engine://test_engine",
            created_at="2024-01-01T00:00:00Z",
            status="ready",
            config={"name": "test_engine"},
            engine_schema=EngineSchema(
                user=[],
                item=[],
                interaction=[],
            ),
        )
        mock_client._engine_api.get_engine_details_engines_engine_name_get = Mock(
            return_value=mock_response
        )

        result = mock_client.get_engine("test_engine")

        assert result.config["name"] == "test_engine"
        mock_client._engine_api.get_engine_details_engines_engine_name_get.assert_called_once()

    def test_delete_engine(self, mock_client):
        """Test deleting an engine."""
        from shaped.autogen.models.delete_engine_response import (
            DeleteEngineResponse,
        )

        mock_response = DeleteEngineResponse(message="Engine deleted")
        mock_client._engine_api.delete_engine_engines_engine_name_delete = Mock(
            return_value=mock_response
        )

        result = mock_client.delete_engine("test_engine")

        assert result.message == "Engine deleted"
        mock_client._engine_api.delete_engine_engines_engine_name_delete.assert_called_once()


class TestTableAPI:
    """Test Table API methods."""

    def test_create_table(self, mock_client, sample_table_config):
        """Test creating a table."""
        from shaped.autogen.models.create_table_response import (
            CreateTableResponse,
        )

        mock_response = CreateTableResponse(
            message="Table created.",
        )
        mock_client._table_api.post_create_table_tables_post = Mock(
            return_value=mock_response
        )

        result = mock_client.create_table(sample_table_config)

        assert result.message == "Table created."
        mock_client._table_api.post_create_table_tables_post.assert_called_once()

    def test_update_table(self, mock_client, sample_table_config):
        """Test updating a table."""
        from shaped.autogen.models.update_table_response import (
            UpdateTableResponse,
        )

        mock_response = UpdateTableResponse(
            message="Table updated.",
        )
        mock_client._table_api.patch_update_table_tables_patch = Mock(
            return_value=mock_response
        )

        result = mock_client.update_table(sample_table_config)

        assert result.message == "Table updated."
        mock_client._table_api.patch_update_table_tables_patch.assert_called_once()

    def test_list_tables(self, mock_client):
        """Test listing tables."""
        from shaped.autogen.models.list_tables_response import (
            ListTablesResponse,
        )

        mock_response = ListTablesResponse(tables=[])
        mock_client._table_api.get_tables_tables_get = Mock(return_value=mock_response)

        result = mock_client.list_tables()

        assert isinstance(result.tables, list)
        mock_client._table_api.get_tables_tables_get.assert_called_once()

    def test_insert_table_rows(self, mock_client):
        """Test inserting rows into a table."""
        from shaped.autogen.models.table_insert_response import (
            TableInsertResponse,
        )

        mock_response = TableInsertResponse(message="Inserted 5 rows.")
        mock_client._table_api.post_table_insert_tables_table_name_insert_post = Mock(
            return_value=mock_response
        )

        rows = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        result = mock_client.insert_table_rows("test_table", rows)

        assert result.message == "Inserted 5 rows."
        mock_client._table_api.post_table_insert_tables_table_name_insert_post.assert_called_once()

    def test_delete_table(self, mock_client):
        """Test deleting a table."""
        from shaped.autogen.models.delete_table_response import (
            DeleteTableResponse,
        )

        mock_response = DeleteTableResponse(message="Table deleted.")
        mock_client._table_api.delete_table_route_tables_table_name_delete = Mock(
            return_value=mock_response,
        )

        result = mock_client.delete_table("test_table")

        assert result.message == "Table deleted."
        mock_client._table_api.delete_table_route_tables_table_name_delete.assert_called_once()


class TestViewAPI:
    """Test View API methods."""

    def test_create_view_sql(self, mock_client, sample_sql_view_config):
        """Test creating a SQL view."""
        from shaped.autogen.models.create_view_response import (
            CreateViewResponse,
        )

        mock_response = CreateViewResponse(message="View created.")
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=mock_response
        )

        view_config = SQLViewConfig(**sample_sql_view_config)
        result = mock_client.create_view(view_config)

        assert result.message == "View created."
        mock_client._view_api.post_create_view_views_post.assert_called_once()

    def test_create_view_ai(self, mock_client, sample_ai_view_config):
        """Test creating an AI enrichment view."""
        from shaped.autogen.models.create_view_response import (
            CreateViewResponse,
        )

        mock_response = CreateViewResponse(message="View created.")
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=mock_response
        )

        view_config = AIEnrichmentViewConfig(**sample_ai_view_config)
        result = mock_client.create_view(view_config)

        assert result.message == "View created."
        mock_client._view_api.post_create_view_views_post.assert_called_once()

    def test_update_view(self, mock_client, sample_sql_view_config):
        """Test updating a view."""
        from shaped.autogen.models.update_view_response import (
            UpdateViewResponse,
        )

        mock_response = UpdateViewResponse(message="View updated.")
        mock_client._view_api.patch_update_view_views_patch = Mock(
            return_value=mock_response,
        )

        view_config = SQLViewConfig(**sample_sql_view_config)
        result = mock_client.update_view(view_config)

        assert result.message == "View updated."
        mock_client._view_api.patch_update_view_views_patch.assert_called_once()

    def test_list_views(self, mock_client):
        """Test listing views."""
        from shaped.autogen.models.list_views_response import (
            ListViewsResponse,
        )

        mock_response = ListViewsResponse(views=[])
        mock_client._view_api.get_views_views_get = Mock(return_value=mock_response)

        result = mock_client.list_views()

        assert isinstance(result.views, list)
        mock_client._view_api.get_views_views_get.assert_called_once()

    def test_get_view(self, mock_client):
        """Test getting view details."""
        from datetime import datetime

        from shaped.autogen.models.response_get_view_details_views_view_name_get import (
            ResponseGetViewDetailsViewsViewNameGet,
        )
        from shaped.autogen.models.transform_status import TransformStatus
        from shaped.autogen.models.view_details_sql import ViewDetailsSQL

        view_details = ViewDetailsSQL(
            name="test_view",
            uri="view://test_view",
            status=TransformStatus.ACTIVE,
            created_at=datetime.utcnow(),
            source_table_names=["items"],
            type="SQL",
        )
        mock_response = ResponseGetViewDetailsViewsViewNameGet(
            actual_instance=view_details,
        )
        mock_client._view_api.get_view_details_views_view_name_get = Mock(
            return_value=mock_response
        )

        result = mock_client.get_view("test_view")

        assert result.actual_instance.name == "test_view"
        mock_client._view_api.get_view_details_views_view_name_get.assert_called_once()

    def test_delete_view(self, mock_client):
        """Test deleting a view."""
        from shaped.autogen.models.delete_view_response import (
            DeleteViewResponse,
        )

        mock_response = DeleteViewResponse(message="View deleted")
        mock_client._view_api.delete_view_views_view_name_delete = Mock(
            return_value=mock_response
        )

        result = mock_client.delete_view("test_view")

        assert result.message == "View deleted"
        mock_client._view_api.delete_view_views_view_name_delete.assert_called_once()


class TestQueryAPI:
    """Test Query API methods."""

    def test_execute_query_with_dict(self, mock_client):
        """Test executing a query with a dict."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {
            "type": "rank",
            "from": "item",
            "retrieve": [
                {
                    "type": "similarity",
                    "embedding_ref": "test_embedding",
                    "query_encoder": {"user_id": "123"},
                }
            ],
        }
        result = mock_client.execute_query("test_engine", query)

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_ad_hoc_query_query_post.assert_called_once()

    def test_execute_query_with_builder(self, mock_client):
        """Test executing a query with RankQueryBuilder."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        from shaped import Similarity

        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "test_user"},
                )
            )
            .build()
        )
        result = mock_client.execute_query("test_engine", query)

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_ad_hoc_query_query_post.assert_called_once()

    def test_execute_query_with_all_parameters(self, mock_client):
        """Test executing a query with all optional parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {
            "type": "rank",
            "from": "item",
            "retrieve": [
                {
                    "type": "similarity",
                    "embedding_ref": "test_embedding",
                    "query_encoder": {"user_id": "123"},
                }
            ],
        }
        result = mock_client.execute_query(
            "test_engine",
            query,
            parameters={"user_id": "123"},
            return_metadata=True,
            return_explanation=True,
            return_journey_explanations=True,
            pagination_key="key123",
            ignore_pagination=False,
        )

        assert isinstance(result, QueryResult)
        call_args = mock_client._query_api.execute_ad_hoc_query_query_post.call_args
        assert call_args is not None

    def test_execute_saved_query(self, mock_client):
        """Test executing a saved query."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine", "my_query", parameters={"user_id": "123"}
        )

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_saved_query_queries_query_name_post.assert_called_once()

    def test_execute_saved_query_with_all_parameters(self, mock_client):
        """Test executing a saved query with all optional parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine",
            "my_query",
            parameters={"user_id": "123"},
            return_metadata=True,
            return_explanation=True,
            return_journey_explanations=True,
            pagination_key="key123",
            ignore_pagination=False,
        )

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_saved_query_queries_query_name_post.assert_called_once()

    def test_get_saved_query_info(self, mock_client):
        """Test getting saved query info."""
        from shaped.autogen.models.saved_query_info_response import (
            SavedQueryInfoResponse,
        )

        mock_response = SavedQueryInfoResponse(
            name="my_query", params=["userId", "limit"]
        )
        mock_client._query_api.get_saved_query_info_queries_query_name_get = Mock(
            return_value=mock_response
        )

        result = mock_client.get_saved_query_info("test_engine", "my_query")

        assert result.name == "my_query"
        assert result.params == ["userId", "limit"]
        mock_client._query_api.get_saved_query_info_queries_query_name_get.assert_called_once()

    def test_list_saved_queries(self, mock_client):
        """Test listing saved queries."""
        from shaped.autogen.models.saved_query_list_response import (
            SavedQueryListResponse,
        )

        mock_response = SavedQueryListResponse(queries=["query1", "query2"])
        # Use _query_api_call which wraps the API call
        mock_client._query_api.list_saved_queries_queries_get = Mock(
            return_value=mock_response
        )

        result = mock_client.list_saved_queries("test_engine")

        # The result should be the response from _query_api_call
        assert result == mock_response
        assert isinstance(result.queries, list)
        assert len(result.queries) == 2
        assert result.queries == ["query1", "query2"]
        mock_client._query_api.list_saved_queries_queries_get.assert_called_once()


class TestTypeAliases:
    """Test that type aliases work correctly."""

    def test_view_config_type_alias(self, mock_client, sample_sql_view_config):
        """Test ViewConfig type alias accepts both SQL and AI configs."""
        from shaped.autogen.models.create_view_response import (
            CreateViewResponse,
        )

        mock_response = CreateViewResponse(message="View created.")
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=mock_response
        )

        # Should accept SQLViewConfig
        sql_config: ViewConfig = SQLViewConfig(**sample_sql_view_config)
        result = mock_client.create_view(sql_config)
        assert result.message == "View created."

        # Should accept AIEnrichmentViewConfig
        ai_config: ViewConfig = AIEnrichmentViewConfig(
            name="test_ai",
            transform_type="AI_ENRICHMENT",
            description="Test AI view.",
            source_dataset="items",
            source_columns=["description"],
            source_columns_in_output=["description"],
            enriched_output_columns=["category"],
            prompt="test",
        )
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=CreateViewResponse(message="View created."),
        )
        result = mock_client.create_view(ai_config)
        assert result.message == "View created."

    # TransformConfig removed (V1 API)
    # def test_transform_config_type_alias(self, mock_client, sample_sql_view_config):
    #     """Test TransformConfig type alias accepts both SQL and AI configs."""
    #     ...
