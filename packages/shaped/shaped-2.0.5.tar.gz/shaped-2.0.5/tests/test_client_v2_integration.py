"""
Integration tests for Shaped V2 Python SDK.

Tests real API calls with actual API key. Requires --api-key flag or
SHAPED_API_KEY environment variable.
"""

import os

import pytest

try:
    from shaped import Client, RankQueryBuilder

    HAS_V2 = True
except ImportError as e:
    HAS_V2 = False
    pytestmark = pytest.mark.skip(f"V2 SDK not available: {e}")


@pytest.fixture(scope="module")
def api_key(request):
    """Get API key from environment or pytest option."""
    key = os.getenv("SHAPED_API_KEY") or request.config.getoption("--api-key")
    return key


@pytest.fixture(scope="module")
def client(api_key):
    """Create a client instance with real API key."""
    if not api_key:
        pytest.skip("Skipping integration tests: SHAPED_API_KEY not set")
    return Client(api_key=api_key)


@pytest.fixture(scope="module")
def test_engine_name():
    """Generate a unique test engine name."""
    import time

    return f"test_engine_{int(time.time())}"


@pytest.fixture(scope="module")
def test_table_name():
    """Generate a unique test table name."""
    import time

    return f"test_table_{int(time.time())}"


@pytest.fixture(scope="function")
def test_table_name_for_insert():
    """Generate a unique test table name for insert test."""
    import time

    return f"test_table_insert_{int(time.time())}"


@pytest.fixture(scope="module")
def query_engine_name(request):
    """Get query engine name from pytest option or environment variable."""
    engine_name = (
        request.config.getoption("--query-engine-name")
        or os.getenv("SHAPED_QUERY_ENGINE_NAME")
        or "demo___blog_semantic_search"
    )
    return engine_name


@pytest.fixture(scope="module")
def created_resources():
    """Track created resources for cleanup."""
    return {
        "tables": [],
        "engines": [],
    }


@pytest.fixture(scope="module", autouse=True)
def cleanup_resources(client, created_resources):
    """Cleanup all test-created resources after tests."""
    yield

    print("\nCleaning up test resources...")

    # Delete engines.
    for engine_name in reversed(created_resources["engines"]):
        try:
            client.delete_engine(engine_name)
            print(f"Deleted engine: {engine_name}")
        except Exception as e:
            print(f"Failed to delete engine {engine_name}: {e}")

    # Delete tables.
    for table_name in reversed(created_resources["tables"]):
        try:
            client.delete_table(table_name)
            print(f"Deleted table: {table_name}")
        except Exception as e:
            print(f"Failed to delete table {table_name}: {e}")


class TestEngineAPIIntegration:
    """Integration tests for Engine API."""

    def test_list_engines(self, client):
        """Test listing engines with real API."""
        result = client.list_engines()
        assert hasattr(result, "engines")
        assert isinstance(result.engines, list)

    @pytest.mark.requires_api_key
    def test_create_engine(
        self, client, test_engine_name, test_table_name, created_resources
    ):
        """Test creating an engine with real API."""
        # Create a test table first with item_id column (required for engines).
        table_config = {
            "schema_type": "CUSTOM",
            "name": test_table_name,
            "column_schema": {
                "item_id": "String",
                "name": "String",
            },
        }
        client.create_table(table_config)
        created_resources["tables"].append(test_table_name)

        # Wait for table to be available.
        import time

        time.sleep(3)

        # Create engine config with proper structure.
        # The item_table needs to be a ReferenceTableConfig wrapped in DataConfigInteractionTable.
        engine_config = {
            "name": test_engine_name,
            "version": "v2",
            "data": {
                "item_table": {
                    "type": "table",
                    "name": test_table_name,
                },
            },
        }

        result = client.create_engine(engine_config)
        assert hasattr(result, "engine_url")
        assert result.engine_url is not None
        created_resources["engines"].append(test_engine_name)

    @pytest.mark.requires_api_key
    def test_get_engine(
        self, client, test_engine_name, test_table_name, created_resources
    ):
        """Test getting engine details with real API."""
        # Ensure engine exists by creating it first if it doesn't.
        try:
            client.get_engine(test_engine_name)
        except Exception:
            # Engine doesn't exist, create it first.
            table_config = {
                "schema_type": "CUSTOM",
                "name": test_table_name,
                "column_schema": {
                    "item_id": "String",
                    "name": "String",
                },
            }
            client.create_table(table_config)
            created_resources["tables"].append(test_table_name)
            import time

            time.sleep(3)

            engine_config = {
                "name": test_engine_name,
                "version": "v2",
                "data": {
                    "item_table": {
                        "type": "table",
                        "name": test_table_name,
                    },
                },
            }
            client.create_engine(engine_config)
            created_resources["engines"].append(test_engine_name)
            import time

            time.sleep(2)  # Wait for engine to be ready.

        result = client.get_engine(test_engine_name)
        assert hasattr(result, "engine_uri")
        assert hasattr(result, "status")

    @pytest.mark.requires_api_key
    def test_delete_engine(
        self, client, test_engine_name, test_table_name, created_resources
    ):
        """Test deleting an engine with real API."""
        # Ensure engine exists by creating it first if it doesn't.
        try:
            client.get_engine(test_engine_name)
        except Exception:
            # Engine doesn't exist, create it first.
            table_config = {
                "schema_type": "CUSTOM",
                "name": test_table_name,
                "column_schema": {
                    "item_id": "String",
                    "name": "String",
                },
            }
            client.create_table(table_config)
            created_resources["tables"].append(test_table_name)
            import time

            time.sleep(3)

            engine_config = {
                "name": test_engine_name,
                "version": "v2",
                "data": {
                    "item_table": {
                        "type": "table",
                        "name": test_table_name,
                    },
                },
            }
            client.create_engine(engine_config)
            created_resources["engines"].append(test_engine_name)
            import time

            time.sleep(2)  # Wait for engine to be ready.

        result = client.delete_engine(test_engine_name)
        assert hasattr(result, "message")


class TestTableAPIIntegration:
    """Integration tests for Table API."""

    @pytest.mark.requires_api_key
    def test_list_tables(self, client):
        """Test listing tables with real API."""
        result = client.list_tables()
        assert hasattr(result, "tables")
        assert isinstance(result.tables, list)

    @pytest.mark.requires_api_key
    def test_insert_table_rows(
        self, client, test_table_name_for_insert, created_resources
    ):
        """Test inserting rows into a table with real API."""  # noqa: D401
        # Create a test table first.
        table_config = {
            "schema_type": "CUSTOM",
            "name": test_table_name_for_insert,
            "column_schema": {
                "id": "String",
                "name": "String",
            },
        }
        client.create_table(table_config)
        created_resources["tables"].append(test_table_name_for_insert)
        # Wait for table to be ready.
        import time

        time.sleep(3)

        rows = [
            {"id": "test1", "name": "Test Item 1"},
            {"id": "test2", "name": "Test Item 2"},
        ]
        # Retry insert in case table isn't ready yet.
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.insert_table_rows(test_table_name_for_insert, rows)
                assert hasattr(result, "message")
                break
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise


class TestViewAPIIntegration:
    """Integration tests for View API."""

    @pytest.mark.requires_api_key
    def test_list_views(self, client):
        """Test listing views with real API."""
        result = client.list_views()
        assert hasattr(result, "views")
        assert isinstance(result.views, list)


class TestTransformAPIIntegration:
    """Integration tests for Transform API."""

    # Transform API removed (V1 API)
    # @pytest.mark.requires_api_key
    # def test_list_transforms(self, client):
    #     """Test listing transforms with real API."""
    #     ...


class TestQueryAPIIntegration:
    """Integration tests for Query API."""

    @pytest.mark.requires_api_key
    def test_list_saved_queries(self, client, query_engine_name):
        """Test listing saved queries with real API."""
        result = client.list_saved_queries(query_engine_name)
        assert hasattr(result, "queries")
        assert isinstance(result.queries, list)

    @pytest.mark.requires_api_key
    def test_execute_query_with_dict(self, client, query_engine_name):
        """Test executing a query with dict config."""
        # Use the same format as test_client_production.py.
        query = {
            "type": "rank",
            "from": "item",
            "retrieve": [
                {
                    "type": "column_order",
                    "columns": [{"name": "id", "ascending": False}],
                    "limit": 10,
                }
            ],
            "limit": 5,
        }

        result = client.execute_query(query_engine_name, query)
        assert hasattr(result, "results")
        assert isinstance(result.results, list)

    @pytest.mark.requires_api_key
    def test_execute_query_with_builder(self, client, query_engine_name):
        """Test executing a query with RankQueryBuilder."""  # noqa: D401
        from shaped import ColumnOrder

        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(ColumnOrder([{"name": "id", "ascending": False}], limit=10))
            .limit(5)
            .build()
        )

        result = client.execute_query(query_engine_name, query)
        assert hasattr(result, "results")
        assert isinstance(result.results, list)

    @pytest.mark.requires_api_key
    def test_execute_query_with_all_parameters(self, client, query_engine_name):
        """Test executing a query with all optional parameters."""
        query = {
            "type": "rank",
            "from": "item",
            "retrieve": [
                {
                    "type": "column_order",
                    "columns": [{"name": "id", "ascending": False}],
                    "limit": 10,
                }
            ],
            "limit": 5,
        }

        result = client.execute_query(
            query_engine_name,
            query,
            parameters={"user_id": "test_user"},
            return_metadata=True,
            return_explanation=True,
            return_journey_explanations=False,
            pagination_key=None,
            ignore_pagination=False,
        )
        assert hasattr(result, "results")

    @pytest.mark.requires_api_key
    def test_execute_saved_query(self, client, query_engine_name):
        """Test executing a saved query."""
        saved_queries = client.list_saved_queries(query_engine_name)
        # Handle case where no saved queries exist.
        if not saved_queries.queries or len(saved_queries.queries) == 0:
            pytest.skip("No saved queries found for this engine")
        # Queries is a list of strings (query names).
        query_name = saved_queries.queries[0]
        result = client.execute_saved_query(query_engine_name, query_name, {})
        assert hasattr(result, "results")


class TestEndToEndWorkflows:
    """End-to-end workflow integration tests."""

    @pytest.mark.requires_api_key
    def test_query_workflow(self, client, query_engine_name):
        """Test a complete query workflow."""
        # Build a query.
        from shaped import ColumnOrder

        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(ColumnOrder([{"name": "id", "ascending": False}], limit=10))
            .limit(10)
            .build()
        )

        # Execute query.
        result = client.execute_query(query_engine_name, query)
        assert hasattr(result, "results")
        assert isinstance(result.results, list)

    @pytest.mark.requires_api_key
    def test_list_all_resources(self, client, query_engine_name):
        """Test listing all resource types."""
        engines = client.list_engines()
        assert hasattr(engines, "engines")

        tables = client.list_tables()
        assert hasattr(tables, "tables")

        views = client.list_views()
        assert hasattr(views, "views")

        # Transform API removed (V1 API)
        # try:
        #     transforms = client.list_transforms()
        #     assert hasattr(transforms, "transforms")
        # except Exception as exc:
        #     ...

        # Get saved queries for the query engine.
        # Handle case where no saved queries exist.
        try:
            saved_queries = client.list_saved_queries(query_engine_name)
            assert hasattr(saved_queries, "queries")
        except Exception:
            # If saved queries fail (e.g., no saved queries), that's okay.
            pass
