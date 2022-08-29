from datetime import datetime
from functools import cache

import yaml


@cache
def get_config(filepath: str = "config.yml") -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data_loaded = yaml.safe_load(f)
    return data_loaded


def get_db_name() -> str:
    return get_config()["mongo"]["db"]


def get_collection_name() -> str:
    return get_config()["mongo"]["collection"]


def get_sources() -> list[dict[str, str | datetime]]:
    return get_config()["sources"]


def get_source(name: str) -> dict[str, str | datetime]:
    for source in get_sources():
        if source["name"] == name:
            return source
    raise ValueError(f"No config is found for source {name}")


def get_sources_names_list() -> list[str]:
    return [source["name"] for source in get_sources()]


def get_creds_keys_list(source_type: str = "all") -> list[str]:
    return [
        source["creds_key"] for source in get_sources() if source_type in (source["type"], "all")
    ]
