from functools import cache

import yaml


@cache
def get_config(filepath="config.yml"):
    with open(filepath, "r", encoding="utf-8") as f:
        data_loaded = yaml.safe_load(f)
    return data_loaded


def get_db_name():
    return get_config()["mongo"]["db"]


def get_collection_name():
    return get_config()["mongo"]["collection"]


def get_sources():
    return get_config()["sources"]


def get_sources_names_list():
    return [source["name"] for source in get_sources()]


def get_creds_keys_list(source_type="all"):
    return [
        source["creds_key"] for source in get_sources() if source_type in (source["type"], "all")
    ]
