"""
Edge case tests for Shaped V2 Python SDK.

Tests edge cases, empty inputs, and boundary conditions.
"""

from unittest.mock import Mock, patch

import pytest

try:
    from shaped import Client, RankQueryBuilder, ViewConfig
    from shaped.autogen.models.ai_enrichment_view_config import (
        AIEnrichmentViewConfig,
    )
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


class TestEmptyInputs:
    """Test handling of empty and null inputs."""

    def test_list_methods_with_empty_results(self, mock_client):
        """Test list methods handle empty results."""
        from shaped.autogen.models.list_engines_response import (
            ListEnginesResponse,
        )
        from shaped.autogen.models.list_tables_response import (
            ListTablesResponse,
        )
        from shaped.autogen.models.list_views_response import (
            ListViewsResponse,
        )

        # Empty engines
        mock_client._engine_api.get_engines_engines_get = Mock(
            return_value=ListEnginesResponse(engines=[])
        )
        result = mock_client.list_engines()
        assert len(result.engines) == 0

        # Empty tables
        mock_client._table_api.get_tables_tables_get = Mock(
            return_value=ListTablesResponse(tables=[])
        )
        result = mock_client.list_tables()
        assert len(result.tables) == 0

        # Empty views
        mock_client._view_api.get_views_views_get = Mock(
            return_value=ListViewsResponse(views=[])
        )
        result = mock_client.list_views()
        assert len(result.views) == 0

    def test_insert_table_rows_with_empty_list(self, mock_client):
        """Test insert_table_rows with empty list."""
        from shaped.autogen.models.table_insert_response import (
            TableInsertResponse,
        )

        mock_response = TableInsertResponse(message="Inserted 0 rows.")
        mock_client._table_api.post_table_insert_tables_table_name_insert_post = Mock(
            return_value=mock_response
        )

        result = mock_client.insert_table_rows("test_table", [])
        assert result.message == "Inserted 0 rows."

    def test_execute_query_with_empty_parameters(self, mock_client):
        """Test execute_query with empty parameters dict."""
        from shaped.autogen.models.query_result import QueryResult

        mock_response = QueryResult(results=[])
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
        result = mock_client.execute_query("test_engine", query, parameters={})
        assert len(result.results) == 0

    def test_execute_saved_query_with_empty_parameters(self, mock_client):
        """Test execute_saved_query with empty parameters."""
        from shaped.autogen.models.query_result import QueryResult

        mock_response = QueryResult(results=[])
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine", "my_query", parameters={}
        )
        assert len(result.results) == 0


class TestNoneAndOptionalInputs:
    """Test handling of None and optional inputs."""

    def test_create_engine_with_optional_fields_none(self, mock_client):
        """Test create_engine with optional fields set to None."""
        from shaped.autogen.models.setup_engine_response import (
            SetupEngineResponse,
        )

        mock_response = SetupEngineResponse(
            engine_url="https://example.com/engines/test_engine",
        )
        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            return_value=mock_response
        )

        config = {
            "name": "test_engine",
            "version": "v2",
            "data": {"tables": []},
            "description": None,
            "tags": None,
        }
        result = mock_client.create_engine(config)
        assert result.engine_url.endswith("test_engine")

    def test_execute_query_with_none_optional_params(self, mock_client):
        """Test execute_query with None optional parameters."""
        from shaped.autogen.models.query_result import QueryResult

        mock_response = QueryResult(results=[])
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
            parameters=None,
            return_metadata=False,
            return_explanation=None,
            pagination_key=None,
        )
        assert isinstance(result, QueryResult)


class TestInvalidInputs:
    """Test handling of invalid inputs."""

    def test_create_engine_with_invalid_config_type(self, mock_client):
        """Test create_engine raises error with invalid config type."""
        from shaped.autogen.exceptions import UnprocessableEntityException

        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            side_effect=UnprocessableEntityException(
                status=422, reason="Invalid config type"
            )
        )

        with pytest.raises(UnprocessableEntityException):
            mock_client.create_engine("not a dict")

    def test_insert_table_rows_with_invalid_row_format(self, mock_client):
        """Test insert_table_rows with invalid row format."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            mock_client.insert_table_rows("test_table", ["not", "a", "dict"])

    def test_execute_query_with_invalid_query_type(self, mock_client):
        """Test execute_query with invalid query type."""

        with pytest.raises(TypeError):
            mock_client.execute_query("test_engine", 12345)  # Not a valid query type.


class TestTypeAliases:
    """Test ViewConfig type alias."""

    def test_view_config_accepts_sql_config(self, mock_client):
        """Test ViewConfig accepts SQLViewConfig."""
        from shaped.autogen.models.create_view_response import (
            CreateViewResponse,
        )
        from shaped.autogen.models.sql_transform_type import SQLTransformType

        mock_response = CreateViewResponse(message="View created")
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=mock_response
        )

        sql_config: ViewConfig = SQLViewConfig(
            name="test_view",
            transform_type="SQL",
            description=None,
            sql_query="SELECT id, name FROM items",
            sql_transform_type=SQLTransformType.VIEW,
        )
        result = mock_client.create_view(sql_config)
        assert result.message == "View created"

    def test_view_config_accepts_ai_config(self, mock_client):
        """Test ViewConfig accepts AIEnrichmentViewConfig."""
        from shaped.autogen.models.create_view_response import (
            CreateViewResponse,
        )

        mock_response = CreateViewResponse(message="View created")
        mock_client._view_api.post_create_view_views_post = Mock(
            return_value=mock_response
        )

        ai_config: ViewConfig = AIEnrichmentViewConfig(
            name="test_ai_view",
            transform_type="AI_ENRICHMENT",
            description=None,
            source_dataset="items",
            source_columns=["description"],
            source_columns_in_output=["description", "category"],
            enriched_output_columns=["category"],
            prompt="Extract category from description.",
        )
        result = mock_client.create_view(ai_config)
        assert result.message == "View created"

    # TransformConfig removed (V1 API)
    # def test_transform_config_accepts_both_types(self, mock_client):
    #     """Test TransformConfig accepts both SQL and AI configs."""
    #     ...


class TestQueryBuilderEdgeCases:
    """Test query builder edge cases."""

    def test_query_builder_without_steps(self):
        """Test building a query without any steps."""
        query = RankQueryBuilder().build()
        assert query is not None
        assert isinstance(query, dict) or hasattr(query, "type")

    def test_query_builder_with_only_from_entity(self):
        """Test query builder with only from entity set."""
        query = RankQueryBuilder().from_entity("item").build()
        assert query is not None
        assert (
            isinstance(query, dict)
            or hasattr(query, "from")
            or hasattr(query, "var_from")
        )

    def test_query_builder_invalid_entity_type(self):
        """Test query builder with invalid entity type."""
        with pytest.raises(ValueError):
            RankQueryBuilder().from_entity("invalid_entity")

    def test_query_builder_multiple_retrieve_steps(self):
        """Test query builder with multiple retrieve steps."""
        from shaped import ColumnOrder, Similarity

        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb",
                    query_encoder={"user_id": "user123"},
                ),
                ColumnOrder([{"name": "popularity", "ascending": False}]),
            )
            .build()
        )
        assert query is not None
        assert hasattr(query, "retrieve") or (
            isinstance(query, dict) and "retrieve" in query
        )
