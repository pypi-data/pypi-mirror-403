import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import requests
import typer
import yaml
from pydantic import BaseModel
from tqdm import tqdm

APP_NAME = "SHAPED_CLI"

app = typer.Typer(name="shaped")


class Config(BaseModel):
    api_key: str
    env: str


def _write_config(config: Config):
    app_dir_path = Path(typer.get_app_dir(APP_NAME))
    app_dir_path.mkdir(parents=True, exist_ok=True)
    config_path = app_dir_path / "config.json"
    with open(config_path, "w") as f:
        f.write(config.model_dump_json())


def _read_config() -> Config:
    app_dir_path = Path(typer.get_app_dir(APP_NAME))
    config_path = app_dir_path / "config.json"
    with open(config_path, "r") as f:
        config = Config.model_validate_json(f.read())

    return config


def _get_shaped_url(config: Config) -> str:
    return f"https://api.{config.env}.shaped.ai/v2"


def _parse_file_as_json(file: typer.FileText) -> str:
    """
    Parse file contents as JSON string, converting from YAML if necessary.
    """
    if file.name.endswith(".json"):
        return json.dumps(json.load(file), indent=2)
    elif file.name.endswith(".yml") or file.name.endswith(".yaml"):
        return json.dumps(yaml.load(file, Loader=yaml.FullLoader), indent=2)
    else:
        raise ValueError(
            "Unsupported file type. Must be one of '.json', '.yml', or '.yaml'. "
            f"file_name={file.name}"
        )


def _parse_response_as_yaml(content: str) -> str:
    # Parse JSON response as YAML for pretty printing.
    return yaml.dump(json.loads(content), sort_keys=False)


def _normalize_query_to_request(query_input: str) -> str:
    """
    Normalize query input to a QueryRequest JSON string.

    The input can be:
    - A SQL string (e.g., "SELECT * FROM table")
    - A QueryConfig JSON object (e.g., {"type": "rank", ...})
    - A full QueryRequest JSON object (e.g., {"query": "...", "return_metadata": true})
    - Legacy format (e.g., {"sql": "SELECT * FROM table"})

    Returns a JSON string representing a QueryRequest.

    Raises:
        ValueError: If the input is invalid or cannot be normalized.
    """
    if not query_input or not query_input.strip():
        raise ValueError(
            "Query input cannot be empty. Provide a SQL query string or "
            "JSON query configuration."
        )

    # Try to parse as JSON first.
    try:
        parsed = json.loads(query_input)

        # If it's already a QueryRequest (has 'query' field), use as-is.
        if isinstance(parsed, dict) and "query" in parsed:
            return json.dumps(parsed)

        # Handle legacy {"sql": "..."} format.
        if isinstance(parsed, dict) and "sql" in parsed:
            sql_string = parsed["sql"]
            if not isinstance(sql_string, str) or not sql_string.strip():
                raise ValueError(
                    "Invalid 'sql' field in query. Expected a non-empty SQL string."
                )
            # Merge any other fields (like return_metadata) if present.
            request = {"query": sql_string, "return_metadata": True}
            if "return_metadata" in parsed:
                request["return_metadata"] = parsed["return_metadata"]
            if "parameters" in parsed:
                request["parameters"] = parsed["parameters"]
            return json.dumps(request)

        # If it's a dict but not a QueryRequest, wrap it as the query field.
        if isinstance(parsed, dict):
            return json.dumps({"query": parsed, "return_metadata": True})

        # If it's a string in JSON (unlikely but possible), treat as SQL.
        if isinstance(parsed, str):
            return json.dumps({"query": parsed, "return_metadata": True})

        # Other types, wrap as query.
        return json.dumps({"query": parsed, "return_metadata": True})
    except json.JSONDecodeError:
        # Not valid JSON, treat as SQL string.
        # This is expected for plain SQL queries, so we don't raise an error.
        return json.dumps({"query": query_input, "return_metadata": True})
    except ValueError as e:
        # Re-raise ValueError with context.
        raise ValueError(f"Invalid query input: {e}") from e


@app.command()
def init(
    api_key: str = typer.Option(..., "--api-key", help="Your Shaped API key."),
    env: str = typer.Option(
        "prod", "--env", help="Environment to use (e.g., prod, dev, staging)."
    ),
):
    """
    Initialize the Shaped CLI with your API key and environment.

    This command saves your configuration locally so you don't need to
    provide your API key for every command.
    """
    config = Config(api_key=api_key, env=env)
    _write_config(config)
    typer.echo(f"Initializing with config: {config.model_dump()}")


##############
# ENGINE API #
##############


@app.command()
def create_engine(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the engine configuration."
    ),
):
    """
    Create a new engine.

    The engine configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    typer.echo(payload)
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code not in [200, 201]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def update_engine(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the engine configuration."
    ),
):
    """
    Update an existing engine.

    The engine configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    typer.echo(payload)
    response = requests.patch(url, headers=headers, data=payload)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def list_engines():
    """
    List all engines.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def view_engine(
    engine_name: str = typer.Option(..., help="Name of the engine to view."),
):
    """
    View the configuration of a specific engine.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def delete_engine(
    engine_name: str = typer.Option(..., help="Name of the engine to delete."),
):
    """
    Delete an engine.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.delete(url, headers=headers)
    if response.status_code not in [200, 204]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    if response.text:
        typer.echo(_parse_response_as_yaml(response.text))


##############
# TABLE API   #
##############


@app.command()
def create_table_from_uri(
    name: str = typer.Option(..., help="Name of the table to create."),
    path: str = typer.Option(..., help="Path to the data file."),
    type: str = typer.Option(
        ..., help="File type. One of: parquet, csv, tsv, json, jsonl."
    ),
):
    """
    Create a table from a data file and automatically insert the data.

    The table schema is inferred from the first chunk of data.
    """
    chunks = _read_chunks(path, type, chunk_size=1)
    chunk = next(iter(chunks))
    if chunk is None:
        raise ValueError("No data found in file.")

    chunk_columns = list(chunk.columns)
    if chunk_columns == 0:
        raise ValueError("No columns found.")

    chunk_column_definitions = {col: "String" for col in chunk_columns}
    table_definition = {
        "name": name,
        "schema_type": "CUSTOM",
        "column_schema": chunk_column_definitions,
    }
    table_created = _create_table_from_payload(json.dumps(table_definition))
    if table_created:
        table_insert(name, path, type)


@app.command()
def create_table(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the table configuration."
    ),
):
    """
    Create a new table.

    The table configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    _create_table_from_payload(payload)


def _create_table_from_payload(payload: str) -> bool:
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }
    typer.echo(payload)
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code not in [200, 201]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))
    return response.status_code in [200, 201]


@app.command()
def list_tables():
    """
    List all tables.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def view_table(
    table_name: str = typer.Option(..., help="Name of the table to view."),
):
    """
    View the configuration of a specific table.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables/{table_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def update_table(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the table configuration."
    ),
):
    """
    Update an existing table.

    The table configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    typer.echo(payload)
    response = requests.patch(url, headers=headers, data=payload)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def table_insert(
    table_name: str = typer.Option(..., help="Name of the table to insert data into."),
    file: str = typer.Option(..., help="Path to the data file to insert."),
    type: str = typer.Option(
        ..., help="File type. One of: parquet, csv, tsv, json, jsonl."
    ),
):
    """
    Insert data into a table from a file.

    Data is read in chunks and uploaded progressively with a progress bar.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables/{table_name}/insert"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }
    bar = tqdm(unit=" Records")

    def _write_chunk(chunk: pd.DataFrame):
        bar.update(len(chunk))
        payload = json.dumps({"data": json.loads(chunk.to_json(orient="records"))})
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            typer.echo(f"Error: {response.status_code}\n{response.text}")
            bar.close()
            raise typer.Exit(1)

    # Chunk read and upload.
    for chunk in _read_chunks(file, type, chunk_size=1000):
        _write_chunk(chunk)

    bar.close()


def _read_chunks(file: str, type: str, chunk_size: int) -> pd.DataFrame:
    if type == "parquet":

        # Note this only works for parquet partitions (i.e. single binary files).
        parquet = pq.ParquetFile(file)
        for chunk in parquet.iter_batches(batch_size=chunk_size):
            yield chunk.to_pandas()

    elif type == "csv":
        with pd.read_csv(file, chunksize=chunk_size) as reader:
            for chunk in reader:
                yield chunk

    elif type == "tsv":
        with pd.read_csv(file, chunksize=chunk_size, sep="\t") as reader:
            for chunk in reader:
                yield chunk

    elif type in ["json", "jsonl"]:
        with pd.read_json(file, chunksize=chunk_size, lines=True) as reader:
            for chunk in reader:
                yield chunk

    else:
        raise NotImplementedError(f"Type '{type}' not implemented.")


@app.command()
def delete_table(
    table_name: str = typer.Option(..., help="Name of the table to delete."),
):
    """
    Delete a table.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/tables/{table_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.delete(url, headers=headers)
    if response.status_code not in [200, 204]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    if response.text:
        typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def create_view(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the view configuration."
    ),
):
    """
    Create a new view.

    The view configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/views"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    typer.echo(payload)
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code not in [200, 201]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


#################
# VIEW API       #
#################


@app.command()
def list_views():
    """
    List all views.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/views"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def view_view(
    view_name: str = typer.Option(..., help="Name of the view to view."),
):
    """
    View the configuration of a specific view.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/views/{view_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def update_view(
    file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the view configuration."
    ),
):
    """
    Update an existing view.

    The view configuration can be provided via:
    - --file: Path to a JSON/YAML file
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/views"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    if not sys.stdin.isatty():
        payload = sys.stdin.read()
    elif file is not None:
        payload = _parse_file_as_json(file)
    else:
        raise ValueError("Must provide either a '--file' or stdin input.")

    typer.echo(payload)
    response = requests.patch(url, headers=headers, data=payload)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def delete_view(
    view_name: str = typer.Option(..., help="Name of the view to delete."),
):
    """
    Delete a view.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/views/{view_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.delete(url, headers=headers)
    if response.status_code not in [200, 204]:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    if response.text:
        typer.echo(_parse_response_as_yaml(response.text))


#################
# QUERY API     #
#################


@app.command()
def query(
    engine_name: str = typer.Option(
        ..., help="Name of the engine to execute the query against."
    ),
    query_file: typer.FileText = typer.Option(
        None, help="Path to a JSON or YAML file containing the query."
    ),
    query: str = typer.Option(
        None, help="Query string (SQL or JSON). Can be used instead of --query-file."
    ),
):
    """
    Execute an ad-hoc query against an engine.

    The query can be provided via:
    - --query-file: Path to a JSON/YAML file
    - --query: SQL query string or JSON string containing the query
    - stdin: Pipe JSON/YAML content
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}/query"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }

    try:
        # Check stdin only if no other input options are provided.
        # If stdin is not a TTY, peek to see if there's content.
        stdin_has_content = False
        stdin_content = ""
        if not sys.stdin.isatty() and query_file is None and query is None:
            # Only read from stdin if no other options provided.
            stdin_content = sys.stdin.read()
            stdin_has_content = bool(stdin_content.strip())
            if not stdin_has_content:
                raise ValueError(
                    "No input provided via stdin. Provide a SQL query string or "
                    "JSON query configuration."
                )

        if stdin_has_content:
            # Read from stdin and normalize to QueryRequest.
            payload = _normalize_query_to_request(stdin_content)
        elif query_file is not None:
            # Read file content and normalize to QueryRequest.
            # Files can contain SQL strings or JSON/YAML.
            try:
                # Try to parse as JSON/YAML first.
                query_file.seek(0)
                file_content = _parse_file_as_json(query_file)
            except (ValueError, json.JSONDecodeError, yaml.YAMLError) as e:
                # If parsing fails, read as raw content (e.g., SQL string).
                query_file.seek(0)
                file_content = query_file.read()
                if not file_content.strip():
                    raise ValueError(
                        f"File '{query_file.name}' is empty or could not be parsed. "
                        "Provide a SQL query string or valid JSON/YAML configuration."
                    ) from e
            payload = _normalize_query_to_request(file_content)
        elif query is not None:
            # Normalize CLI string input to QueryRequest.
            payload = _normalize_query_to_request(query)
        else:
            raise ValueError(
                "Must provide query input via one of:\n"
                "  - --query-file: Path to a file containing SQL or JSON/YAML\n"
                "  - --query: SQL query string or JSON string\n"
                "  - stdin: Pipe SQL or JSON/YAML content"
            )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: Unexpected error processing query input: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(payload)
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code != 200:
        # Try to parse error response for better error message.
        try:
            error_data = response.json()
            error_msg = error_data.get(
                "message", error_data.get("detail", response.text)
            )
            typer.echo(f"Error {response.status_code}: {error_msg}", err=True)
        except (json.JSONDecodeError, ValueError):
            typer.echo(f"Error {response.status_code}: {response.text}", err=True)
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def execute_saved_query(
    engine_name: str = typer.Option(
        ..., help="Name of the engine containing the saved query."
    ),
    query_name: str = typer.Option(..., help="Name of the saved query to execute."),
):
    """
    Execute a previously saved query by name.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}/queries/{query_name}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": config.api_key,
    }
    response = requests.post(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def view_saved_query(
    engine_name: str = typer.Option(
        ..., help="Name of the engine containing the saved query."
    ),
    query_name: str = typer.Option(..., help="Name of the saved query to view."),
):
    """
    View the definition of a saved query.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}/queries/{query_name}"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


@app.command()
def list_saved_queries(
    engine_name: str = typer.Option(
        ..., help="Name of the engine to list saved queries for."
    ),
):
    """
    List all saved queries for an engine.
    """
    config = _read_config()
    url = f"{_get_shaped_url(config)}/engines/{engine_name}/queries"
    headers = {"accept": "application/json", "x-api-key": config.api_key}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        typer.echo(f"Error: {response.status_code}\n{response.text}")
        raise typer.Exit(1)
    typer.echo(_parse_response_as_yaml(response.text))


def main():
    """Entry point for the shaped CLI command."""
    app(prog_name="shaped")


if __name__ == "__main__":
    main()
