from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, parse_qsl, urlparse

SQLITE_FILE_NAME = "db.sqlite3"


def _parser_sqlite_uri(
    data: ParseResult, base_dir: Path | None = None
) -> dict[str, Any]:
    if data.hostname:
        sqlite_file_name = data.hostname

    elif data.path:
        sqlite_file_name = data.path

    else:
        sqlite_file_name = SQLITE_FILE_NAME

    if base_dir:
        sqlite_file_name = base_dir.joinpath(sqlite_file_name).as_posix()

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": sqlite_file_name,
    }


def _parser_service_sql_uri(data: ParseResult, engine: str) -> dict[str, Any]:
    """postgresql/mysql..."""
    return {
        "ENGINE": engine,
        "HOST": data.hostname,
        "PORT": data.port,
        "NAME": data.path.lstrip("/"),
        "USER": data.username,
        "PASSWORD": data.password,
    }


def _parser_options(query: str) -> dict[str, Any]:
    if not query:
        return {}

    data = parse_qsl(query)
    if not data:
        return {}

    result = dict()
    for item in data:
        key, value = item

        # parser value
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        elif value.isdecimal():
            if "." in value:
                value = float(value)
            else:
                value = int(value)

        # parser key
        keys_chain = key.split(".")
        current_dict = result
        for key in keys_chain[:-1]:
            if key not in current_dict or not isinstance(current_dict[key], dict):
                current_dict[key] = {}

            current_dict = current_dict[key]

        final_key = keys_chain[-1]
        current_dict[final_key] = value

    return result


def parser_database_uri(uri: str, base_dir: Path | None = None) -> dict[str, Any]:
    """返回 Django settings DATABASES 字典"""
    data = urlparse(uri)
    match data.scheme:
        case "sqlite":
            result = _parser_sqlite_uri(data, base_dir)

        case "postgresql" | "postgres":
            result = _parser_service_sql_uri(data, "django.db.backends.postgresql")

        case _:
            raise ValueError(f"[{data.scheme}] is an unsupported database type")

    options = _parser_options(data.query)
    if options:
        result["OPTIONS"] = options

    return result
