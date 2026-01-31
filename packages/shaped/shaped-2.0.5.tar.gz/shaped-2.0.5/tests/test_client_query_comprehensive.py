"""
Comprehensive tests for Client query methods covering edge cases and parameter handling.
"""

from unittest.mock import Mock, patch

import pytest

try:
    from shaped import Client, RankQueryBuilder, Similarity
    from shaped.autogen.models.query_result import QueryResult
    from shaped.autogen.models.saved_query_info_response import SavedQueryInfoResponse
    from shaped.autogen.models.saved_query_list_response import SavedQueryListResponse

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


class TestClientQueryComprehensive:
    """Comprehensive tests for Client query methods."""

    def test_execute_query_with_dict_query(self, mock_client):
        """Test executing a query with dict query."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query("test_engine", query)

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_ad_hoc_query_query_post.assert_called_once()

    def test_execute_query_with_rank_query_builder(self, mock_client):
        """Test executing a query with RankQueryBuilder."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .build()
        )
        result = mock_client.execute_query("test_engine", query)

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_ad_hoc_query_query_post.assert_called_once()

    def test_execute_query_with_string_query(self, mock_client):
        """Test executing a query with SQL string."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = "SELECT * FROM items LIMIT 10"
        result = mock_client.execute_query("test_engine", query)

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_ad_hoc_query_query_post.assert_called_once()

    def test_execute_query_with_parameters_int(self, mock_client):
        """Test executing a query with integer parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine", query, parameters={"limit": 50, "offset": 10}
        )

        assert isinstance(result, QueryResult)
        call_args = mock_client._query_api.execute_ad_hoc_query_query_post.call_args
        assert call_args is not None

    def test_execute_query_with_parameters_float(self, mock_client):
        """Test executing a query with float parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine", query, parameters={"threshold": 0.75, "weight": 0.5}
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_parameters_bool(self, mock_client):
        """Test executing a query with boolean parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine",
            query,
            parameters={"include_metadata": True, "filter_active": False},
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_parameters_list_str(self, mock_client):
        """Test executing a query with list of strings parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine",
            query,
            parameters={"categories": ["electronics", "books", "clothing"]},
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_parameters_list_int(self, mock_client):
        """Test executing a query with list of integers parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine", query, parameters={"ids": [1, 2, 3, 4, 5]}
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_parameters_mixed(self, mock_client):
        """Test executing a query with mixed parameter types."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine",
            query,
            parameters={
                "userId": "user123",
                "limit": 50,
                "threshold": 0.75,
                "active": True,
                "categories": ["electronics", "books"],
                "ids": [1, 2, 3],
            },
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_all_flags(self, mock_client):
        """Test executing a query with all optional flags."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine",
            query,
            parameters={"userId": "123"},
            return_metadata=True,
            return_explanation=True,
            return_journey_explanations=True,
            pagination_key="page2",
            ignore_pagination=False,
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_pagination(self, mock_client):
        """Test executing a query with pagination."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query(
            "test_engine", query, pagination_key="next_page_key_123"
        )

        assert isinstance(result, QueryResult)

    def test_execute_query_with_ignore_pagination(self, mock_client):
        """Test executing a query with ignore_pagination flag."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query("test_engine", query, ignore_pagination=True)

        assert isinstance(result, QueryResult)

    def test_execute_saved_query_with_parameters(self, mock_client):
        """Test executing a saved query with parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine", "my_query", parameters={"userId": "123", "limit": 50}
        )

        assert isinstance(result, QueryResult)
        mock_client._query_api.execute_saved_query_queries_query_name_post.assert_called_once()

    def test_execute_saved_query_with_all_flags(self, mock_client):
        """Test executing a saved query with all optional flags."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine",
            "my_query",
            parameters={"userId": "123"},
            return_metadata=True,
            return_explanation=True,
            return_journey_explanations=True,
            pagination_key="page2",
            ignore_pagination=False,
        )

        assert isinstance(result, QueryResult)

    def test_get_saved_query_info(self, mock_client):
        """Test getting saved query info."""
        mock_response = SavedQueryInfoResponse(
            name="my_query", params=["userId", "limit", "category"]
        )
        mock_client._query_api.get_saved_query_info_queries_query_name_get = Mock(
            return_value=mock_response
        )

        result = mock_client.get_saved_query_info("test_engine", "my_query")

        assert isinstance(result, SavedQueryInfoResponse)
        assert result.name == "my_query"
        assert result.params == ["userId", "limit", "category"]
        mock_client._query_api.get_saved_query_info_queries_query_name_get.assert_called_once()

    def test_get_saved_query_info_empty_params(self, mock_client):
        """Test getting saved query info with no parameters."""
        mock_response = SavedQueryInfoResponse(name="my_query", params=[])
        mock_client._query_api.get_saved_query_info_queries_query_name_get = Mock(
            return_value=mock_response
        )

        result = mock_client.get_saved_query_info("test_engine", "my_query")

        assert isinstance(result, SavedQueryInfoResponse)
        assert result.name == "my_query"
        assert result.params == []

    def test_list_saved_queries_empty(self, mock_client):
        """Test listing saved queries when none exist."""
        mock_response = SavedQueryListResponse(queries=[])
        mock_client._query_api.list_saved_queries_queries_get = Mock(
            return_value=mock_response
        )

        result = mock_client.list_saved_queries("test_engine")

        assert isinstance(result, SavedQueryListResponse)
        assert isinstance(result.queries, list)
        assert len(result.queries) == 0

    def test_list_saved_queries_multiple(self, mock_client):
        """Test listing multiple saved queries."""
        mock_response = SavedQueryListResponse(
            queries=["query1", "query2", "query3", "query4"]
        )
        mock_client._query_api.list_saved_queries_queries_get = Mock(
            return_value=mock_response
        )

        result = mock_client.list_saved_queries("test_engine")

        assert isinstance(result, SavedQueryListResponse)
        assert len(result.queries) == 4
        assert result.queries == ["query1", "query2", "query3", "query4"]

    def test_execute_query_with_none_parameters(self, mock_client):
        """Test executing a query with None parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query("test_engine", query, parameters=None)

        assert isinstance(result, QueryResult)

    def test_execute_query_with_empty_parameters(self, mock_client):
        """Test executing a query with empty parameters dict."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            return_value=mock_response
        )

        query = {"type": "rank", "from": "item", "retrieve": []}
        result = mock_client.execute_query("test_engine", query, parameters={})

        assert isinstance(result, QueryResult)

    def test_execute_saved_query_with_none_parameters(self, mock_client):
        """Test executing a saved query with None parameters."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine", "my_query", parameters=None
        )

        assert isinstance(result, QueryResult)

    def test_execute_saved_query_with_empty_parameters(self, mock_client):
        """Test executing a saved query with empty parameters dict."""
        mock_response = QueryResult(results=[], metadata={})
        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            return_value=mock_response
        )

        result = mock_client.execute_saved_query(
            "test_engine", "my_query", parameters={}
        )

        assert isinstance(result, QueryResult)
