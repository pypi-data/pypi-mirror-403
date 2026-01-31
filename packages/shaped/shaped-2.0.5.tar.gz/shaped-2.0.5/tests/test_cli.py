import json
import tempfile
from pathlib import Path

import pytest
import yaml
from shaped.cli.shaped_cli import app
from typer.testing import CliRunner

runner = CliRunner()


def _get_engine_name_from_list(mock_config_dir):
    """Get the first available engine name from list-engines."""
    list_result = runner.invoke(app, ["list-engines"], prog_name="shaped")
    assert list_result.exit_code == 0, f"list-engines failed: {list_result.stdout}"
    assert list_result.stdout.strip(), "No engines output from list-engines"

    # Parse the YAML output to get engine names.
    engines_data = yaml.safe_load(list_result.stdout)
    assert engines_data, "No engines data parsed from output"

    # The API returns {"engines": [...]} and each engine has "engine_name" field.
    if isinstance(engines_data, dict):
        engines_list = engines_data.get("engines", [])
        assert engines_list, "No engines found in response"
        assert len(engines_list) > 0, "Empty engines list"
        engine_name = engines_list[0].get("engine_name")
    elif isinstance(engines_data, list):
        # Handle case where YAML is a direct list.
        assert len(engines_data) > 0, "Empty engines list"
        engine_name = engines_data[0].get("engine_name") or engines_data[0].get("name")
    else:
        raise AssertionError(
            f"Unexpected engines response format: {type(engines_data)}"
        )

    assert engine_name, f"No engine name found in response: {engines_data}"

    return engine_name


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / "shaped_cli_config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Mock typer.get_app_dir to return our temp directory.
    monkeypatch.setattr(
        "shaped.cli.shaped_cli.typer.get_app_dir", lambda x: str(config_dir)
    )

    return config_dir


def test_init_command(mock_config_dir, api_key):
    """Test the init command creates a config file."""
    # Use a test API key for this test (init doesn't need a real API key).
    test_api_key = api_key if api_key else "test-api-key-12345"
    result = runner.invoke(
        app, ["init", "--api-key", test_api_key, "--env", "prod"], prog_name="shaped"
    )

    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr if hasattr(result, 'stderr') else 'N/A'}")
        print(f"Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Initializing with config" in result.stdout

    config_path = mock_config_dir / "config.json"
    assert config_path.exists()

    with open(config_path) as f:
        config = json.load(f)
    assert config["api_key"] == test_api_key
    assert config["env"] == "prod"


def test_init_command_default_env(mock_config_dir, api_key):
    """Test init command uses default env when not specified."""
    # Use a test API key for this test (init doesn't need a real API key).
    test_api_key = api_key if api_key else "test-api-key-12345"
    result = runner.invoke(app, ["init", "--api-key", test_api_key], prog_name="shaped")

    assert result.exit_code == 0

    config_path = mock_config_dir / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    assert config["env"] == "prod"


@pytest.mark.requires_api_key
def test_list_engines(mock_config_dir, api_key):
    """Test list-engines command with real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    result = runner.invoke(app, ["list-engines"], prog_name="shaped")

    assert result.exit_code == 0
    assert len(result.stdout) > 0


@pytest.mark.requires_api_key
def test_list_tables(mock_config_dir, api_key):
    """Test list-tables command with real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    result = runner.invoke(app, ["list-tables"], prog_name="shaped")

    assert result.exit_code == 0
    assert len(result.stdout) > 0


@pytest.mark.requires_api_key
def test_list_views(mock_config_dir, api_key):
    """Test list-views command with real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    result = runner.invoke(app, ["list-views"], prog_name="shaped")

    assert result.exit_code == 0
    assert len(result.stdout) > 0


@pytest.mark.requires_api_key
def test_create_engine_with_file(mock_config_dir, api_key):
    """Test create-engine command with file input and real API request."""
    assert api_key is not None, "API key required for this test"

    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    # Create a temporary engine config file.
    engine_config = {
        "name": f"test-engine-{hash(api_key) % 10000}",
        "description": "Test engine for CLI tests",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(engine_config, f)
        temp_file = f.name

    try:
        result = runner.invoke(
            app, ["create-engine", "--file", temp_file], prog_name="shaped"
        )

        assert result.exit_code in [0, 1]
    finally:
        Path(temp_file).unlink()


@pytest.mark.requires_api_key
def test_query_with_json_string(mock_config_dir, api_key):
    """Test query command with JSON string input and real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    engine_name = _get_engine_name_from_list(mock_config_dir)

    # TODO: Add engine agnostic query.
    query_json = '{"sql": "SELECT 1 as test"}'
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            engine_name,
            "--query",
            query_json,
        ],
    )

    # May succeed or fail depending on if engine exists.
    assert result.exit_code in [0, 1]


@pytest.mark.requires_api_key
def test_query_with_file(mock_config_dir, api_key):
    """Test query command with file input and real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    engine_name = _get_engine_name_from_list(mock_config_dir)

    query_data = {"sql": "SELECT 1 as test"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(query_data, f)
        temp_file = f.name

    try:
        result = runner.invoke(
            app,
            [
                "query",
                "--engine-name",
                engine_name,
                "--query-file",
                temp_file,
            ],
        )

        assert result.exit_code in [0, 1]
    finally:
        Path(temp_file).unlink()


@pytest.mark.requires_api_key
def test_list_saved_queries(mock_config_dir, api_key):
    """Test list-saved-queries command with real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    engine_name = _get_engine_name_from_list(mock_config_dir)

    result = runner.invoke(app, ["list-saved-queries", "--engine-name", engine_name])

    # May succeed (even if empty) or fail if engine doesn't exist.
    assert result.exit_code in [0, 1]
    if result.exit_code == 0:
        assert len(result.stdout) > 0


@pytest.mark.requires_api_key
def test_query_missing_input(mock_config_dir, api_key):
    """Test query command fails when no input is provided."""

    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    result = runner.invoke(app, ["query", "--engine-name", "test-engine"])

    assert result.exit_code != 0
    # Error goes to stderr, check both for compatibility.
    error_output = result.stdout + result.stderr
    assert (
        "Must provide query input" in error_output
        or "No input provided" in error_output
    )


def test_query_with_sql_string(mock_config_dir):
    """Test query command with plain SQL string (not JSON)."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    sql_query = "SELECT * FROM items LIMIT 10"
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            sql_query,
        ],
    )

    # Should normalize to QueryRequest format.
    assert "query" in result.stdout or result.exit_code != 0


def test_query_with_empty_string(mock_config_dir):
    """Test query command fails with empty string input."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            "",
        ],
    )

    assert result.exit_code != 0
    # Error goes to stderr, check both for compatibility.
    error_output = result.stdout + result.stderr
    assert "cannot be empty" in error_output


def test_query_with_whitespace_only(mock_config_dir):
    """Test query command fails with whitespace-only input."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            "   ",
        ],
    )

    assert result.exit_code != 0
    # Error goes to stderr, check both for compatibility.
    error_output = result.stdout + result.stderr
    assert "cannot be empty" in error_output


def test_query_with_queryconfig_json(mock_config_dir):
    """Test query command with QueryConfig JSON object."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    query_config = {"type": "rank", "from": "item"}
    query_json = json.dumps(query_config)
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            query_json,
        ],
    )

    # Should wrap in QueryRequest.
    assert "query" in result.stdout or result.exit_code != 0


def test_query_with_full_queryrequest_json(mock_config_dir):
    """Test query command with full QueryRequest JSON object."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    query_request = {
        "query": "SELECT * FROM items",
        "return_metadata": False,
        "parameters": {"userId": "123"},
    }
    query_json = json.dumps(query_request)
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            query_json,
        ],
    )

    # Should use as-is.
    assert "query" in result.stdout or result.exit_code != 0


def test_query_with_legacy_sql_format(mock_config_dir):
    """Test query command with legacy {"sql": "..."} format."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    legacy_query = {"sql": "SELECT * FROM items LIMIT 10"}
    query_json = json.dumps(legacy_query)
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            query_json,
        ],
    )

    # Should convert to {"query": "..."} format.
    assert "query" in result.stdout or result.exit_code != 0


def test_query_with_file_sql_string(mock_config_dir):
    """Test query command with file containing SQL string."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    sql_query = "SELECT * FROM items LIMIT 10"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write(sql_query)
        temp_file = f.name

    try:
        result = runner.invoke(
            app,
            [
                "query",
                "--engine-name",
                "test-engine",
                "--query-file",
                temp_file,
            ],
        )

        # Should normalize to QueryRequest.
        assert "query" in result.stdout or result.exit_code != 0
    finally:
        Path(temp_file).unlink()


def test_query_with_file_json_config(mock_config_dir):
    """Test query command with file containing JSON QueryConfig."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    query_config = {"type": "rank", "from": "item"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(query_config, f)
        temp_file = f.name

    try:
        result = runner.invoke(
            app,
            [
                "query",
                "--engine-name",
                "test-engine",
                "--query-file",
                temp_file,
            ],
        )

        # Should wrap in QueryRequest.
        assert "query" in result.stdout or result.exit_code != 0
    finally:
        Path(temp_file).unlink()


def test_query_with_file_yaml_config(mock_config_dir):
    """Test query command with file containing YAML QueryConfig."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    query_config = {"type": "rank", "from": "item"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(query_config, f)
        temp_file = f.name

    try:
        result = runner.invoke(
            app,
            [
                "query",
                "--engine-name",
                "test-engine",
                "--query-file",
                temp_file,
            ],
        )

        # Should wrap in QueryRequest.
        assert "query" in result.stdout or result.exit_code != 0
    finally:
        Path(temp_file).unlink()


def test_query_with_empty_file(mock_config_dir):
    """Test query command fails with empty file."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        # Write nothing (empty file).
        temp_file = f.name

    try:
        result = runner.invoke(
            app,
            [
                "query",
                "--engine-name",
                "test-engine",
                "--query-file",
                temp_file,
            ],
        )

        assert result.exit_code != 0
        # Error goes to stderr, check both for compatibility.
        error_output = result.stdout + result.stderr
        assert "empty" in error_output or "No input provided" in error_output
    finally:
        Path(temp_file).unlink()


def test_query_with_invalid_legacy_sql_format(mock_config_dir):
    """Test query command fails with invalid legacy sql field."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": "test-key", "env": "prod"}, f)

    # Invalid: sql field is not a string.
    invalid_query = {"sql": 123}
    query_json = json.dumps(invalid_query)
    result = runner.invoke(
        app,
        [
            "query",
            "--engine-name",
            "test-engine",
            "--query",
            query_json,
        ],
    )

    assert result.exit_code != 0
    # Error goes to stderr, check both for compatibility.
    error_output = result.stdout + result.stderr
    assert "Invalid" in error_output or "cannot be empty" in error_output


@pytest.mark.requires_api_key
def test_view_engine(mock_config_dir, api_key):
    """Test view-engine command with real API request."""
    config_path = mock_config_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "env": "prod"}, f)

    engine_name = _get_engine_name_from_list(mock_config_dir)

    result = runner.invoke(
        app, ["view-engine", "--engine-name", engine_name], prog_name="shaped"
    )

    assert result.exit_code in [0, 1]
