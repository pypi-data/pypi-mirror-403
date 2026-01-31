"""
Error handling tests for Shaped V2 Python SDK.

Tests error scenarios and exception handling.
"""

from unittest.mock import Mock, patch

import pytest
from shaped import Client
from shaped.autogen.exceptions import ApiException


@pytest.fixture
def mock_client():
    """Create a client instance with mocked API dependencies."""
    with patch("shaped.client.EngineApi"), patch("shaped.client.TableApi"), patch(
        "shaped.client.ViewApi"
    ), patch("shaped.client.QueryApi"):
        client = Client(api_key="test_api_key_123456789012345678901234567890")
        return client


class TestAPIExceptions:
    """Test API exception handling."""

    def test_bad_request_exception(self, mock_client):
        """Test 400 Bad Request exception handling."""
        from shaped.autogen.exceptions import BadRequestException

        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            side_effect=BadRequestException(status=400, reason="Bad Request")
        )

        with pytest.raises(BadRequestException) as exc_info:
            mock_client.create_engine({"name": "test", "version": "v2", "data": {}})
        assert exc_info.value.status == 400

    def test_unauthorized_exception(self, mock_client):
        """Test 401 Unauthorized exception handling."""
        from shaped.autogen.exceptions import UnauthorizedException

        mock_client._engine_api.get_engines_engines_get = Mock(
            side_effect=UnauthorizedException(status=401, reason="Unauthorized")
        )

        with pytest.raises(UnauthorizedException) as exc_info:
            mock_client.list_engines()
        assert exc_info.value.status == 401

    def test_not_found_exception(self, mock_client):
        """Test 404 Not Found exception handling."""
        from shaped.autogen.exceptions import NotFoundException

        mock_client._engine_api.get_engine_details_engines_engine_name_get = Mock(
            side_effect=NotFoundException(status=404, reason="Not Found")
        )

        with pytest.raises(NotFoundException) as exc_info:
            mock_client.get_engine("nonexistent_engine")
        assert exc_info.value.status == 404

    def test_conflict_exception(self, mock_client):
        """Test 409 Conflict exception handling."""
        from shaped.autogen.exceptions import ConflictException

        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            side_effect=ConflictException(status=409, reason="Conflict")
        )

        with pytest.raises(ConflictException) as exc_info:
            mock_client.create_engine(
                {"name": "existing_engine", "version": "v2", "data": {}}
            )
        assert exc_info.value.status == 409

    def test_unprocessable_entity_exception(self, mock_client):
        """Test 422 Unprocessable Entity exception handling."""
        from shaped.autogen.exceptions import UnprocessableEntityException

        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            side_effect=UnprocessableEntityException(
                status=422, reason="Unprocessable Entity"
            )
        )

        with pytest.raises(UnprocessableEntityException) as exc_info:
            mock_client.create_engine({"invalid": "config"})
        assert exc_info.value.status == 422

    def test_service_exception(self, mock_client):
        """Test 500+ Service Exception handling."""
        from shaped.autogen.exceptions import ServiceException

        mock_client._engine_api.get_engines_engines_get = Mock(
            side_effect=ServiceException(status=500, reason="Internal Server Error")
        )

        with pytest.raises(ServiceException) as exc_info:
            mock_client.list_engines()
        assert exc_info.value.status == 500

    def test_generic_api_exception(self, mock_client):
        """Test generic ApiException handling."""
        mock_client._engine_api.get_engines_engines_get = Mock(
            side_effect=ApiException(status=418, reason="I'm a teapot")
        )

        with pytest.raises(ApiException) as exc_info:
            mock_client.list_engines()
        assert exc_info.value.status == 418


class TestQueryAPIErrorHandling:
    """Test Query API specific error handling."""

    def test_query_api_call_injects_headers(self, mock_client):
        """Test _query_api_call properly injects API key in headers."""
        mock_method = Mock(return_value="result")
        result = mock_client._query_api_call(mock_method, arg1="value1")

        assert result == "result"
        mock_method.assert_called_once()
        call_kwargs = mock_method.call_args[1]
        assert "_headers" in call_kwargs
        assert call_kwargs["_headers"]["x-api-key"] == mock_client._api_key

    def test_execute_query_propagates_exceptions(self, mock_client):
        """Test execute_query propagates API exceptions."""
        from shaped.autogen.exceptions import BadRequestException

        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            side_effect=BadRequestException(status=400, reason="Invalid query")
        )

        with pytest.raises(BadRequestException):
            mock_client.execute_query("test_engine", {"invalid": "query"})

    def test_execute_saved_query_propagates_exceptions(self, mock_client):
        """Test execute_saved_query propagates API exceptions."""
        from shaped.autogen.exceptions import NotFoundException

        mock_client._query_api.execute_saved_query_queries_query_name_post = Mock(
            side_effect=NotFoundException(status=404, reason="Query not found")
        )

        with pytest.raises(NotFoundException):
            mock_client.execute_saved_query("test_engine", "nonexistent_query")


class TestEdgeCaseErrorHandling:
    """Test edge case error scenarios."""

    def test_create_engine_with_missing_required_fields(self, mock_client):
        """Test create_engine with missing required fields."""
        from shaped.autogen.exceptions import UnprocessableEntityException

        mock_client._engine_api.post_setup_engine_engines_post = Mock(
            side_effect=UnprocessableEntityException(
                status=422, reason="Missing required field: name"
            )
        )

        with pytest.raises(UnprocessableEntityException):
            mock_client.create_engine({"version": "v2"})  # Missing name

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

    def test_execute_query_with_empty_query(self, mock_client):
        """Test execute_query with empty query dict."""
        from shaped.autogen.exceptions import BadRequestException

        mock_client._query_api.execute_ad_hoc_query_query_post = Mock(
            side_effect=BadRequestException(status=400, reason="Empty query")
        )

        with pytest.raises(BadRequestException):
            mock_client.execute_query("test_engine", {})

    def test_execute_query_with_invalid_query_type(self, mock_client):
        """Test execute_query with invalid query type."""
        # Should raise a validation error for invalid query type.

        with pytest.raises(TypeError):
            mock_client.execute_query("test_engine", 12345)  # Invalid type.
