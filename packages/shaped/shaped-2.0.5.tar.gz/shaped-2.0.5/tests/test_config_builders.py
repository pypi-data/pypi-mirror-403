"""
Tests for Shaped config builders (Engine, Table, View).
"""

from unittest.mock import Mock, patch

import pytest
from shaped import Client, Engine, Table, View
from shaped.autogen.models.engine_config_v2 import EngineConfigV2
from shaped.autogen.models.postgres_table_config import PostgresTableConfig
from shaped.autogen.models.sql_view_config import SQLViewConfig


@pytest.fixture
def mock_client():
    """Create a client instance with mocked API dependencies."""
    with patch("shaped.client.EngineApi"), patch("shaped.client.TableApi"), patch(
        "shaped.client.ViewApi"
    ), patch("shaped.client.QueryApi"):
        client = Client(api_key="test_api_key_123456789012345678901234567890")
        return client


class TestEngineBuilder:
    def test_build_engine_config(self):
        """Test building an Engine config."""
        engine = (
            Engine("test-engine")
            .description("My test engine")
            .interactions("events")
            .users("users")
            .items("items")
            .schedule("@daily")
        )

        config = engine.build()

        assert isinstance(config, EngineConfigV2)
        assert config.name == "test-engine"
        assert config.description == "My test engine"
        assert config.data.interaction_table.actual_instance.name == "events"
        assert config.data.user_table.actual_instance.name == "users"
        assert config.data.item_table.actual_instance.name == "items"
        assert config.data.schedule == "@daily"


class TestTableBuilder:
    def test_postgres_table(self):
        """Test building Postgres table config."""
        config = Table.Postgres(
            name="pg_users",
            host="localhost",
            port=5432,
            user="user",
            password="pwd",
            database="db",
            table="users",
            replication_key="id",
            description="Users table",
        )

        assert isinstance(config, PostgresTableConfig)
        assert config.name == "pg_users"
        assert config.host == "localhost"
        assert config.schema_type == "POSTGRES"


class TestViewBuilder:
    def test_sql_view(self):
        """Test building SQL view config."""
        config = View.SQL(
            name="active_users",
            query="SELECT * FROM users WHERE active = true",
            description="Active users only",
        )

        assert isinstance(config, SQLViewConfig)
        assert config.name == "active_users"
        assert config.sql_query == "SELECT * FROM users WHERE active = true"
        assert (
            config.sql_transform_type.value == "VIEW"
            if hasattr(config.sql_transform_type, "value")
            else "VIEW"
        )


class TestClientIntegration:
    def test_create_engine_with_builder(self, mock_client):
        """Test create_engine accepts Engine builder."""
        engine = Engine("test-engine").interactions("events")

        # Mock response
        mock_response = Mock()
        mock_response.engine_url = "https://api.shaped.ai/v2/engines/test-engine"
        mock_client._engine_api.post_setup_engine_engines_post.return_value = (
            mock_response
        )

        result = mock_client.create_engine(engine)

        assert result.engine_url == "https://api.shaped.ai/v2/engines/test-engine"
        mock_client._engine_api.post_setup_engine_engines_post.assert_called_once()
        call_args = mock_client._engine_api.post_setup_engine_engines_post.call_args
        assert call_args.kwargs["engine_config_v2"].name == "test-engine"

    def test_create_table_with_builder_object(self, mock_client):
        """Test create_table accepts Table config object from builder."""
        config = Table.Postgres(
            name="pg_users",
            host="localhost",
            port=5432,
            user="user",
            password="pwd",
            database="db",
            table="users",
            replication_key="id",
        )

        mock_response = Mock()
        mock_response.message = "Table created"
        mock_client._table_api.post_create_table_tables_post.return_value = (
            mock_response
        )

        result = mock_client.create_table(config)

        assert result.message == "Table created"
        mock_client._table_api.post_create_table_tables_post.assert_called_once()
        # Verify it was wrapped in Request (TableRequest)
        call_args = mock_client._table_api.post_create_table_tables_post.call_args
        request_arg = call_args.kwargs["request"]
        # It should be a TableRequest (Request) object
        # And actual_instance should be PostgresTableConfig
        assert request_arg.actual_instance.name == "pg_users"

    def test_create_view_with_builder_object(self, mock_client):
        """Test create_view accepts View config object from builder."""
        config = View.SQL(
            name="active_users",
            query="SELECT * FROM users",
        )

        mock_response = Mock()
        mock_response.message = "View created"
        mock_client._view_api.post_create_view_views_post.return_value = mock_response

        result = mock_client.create_view(config)

        assert result.message == "View created"
        mock_client._view_api.post_create_view_views_post.assert_called_once()
        call_args = mock_client._view_api.post_create_view_views_post.call_args
        request_arg = call_args.kwargs["request1"]
        assert request_arg.actual_instance.name == "active_users"
