"""This module contains utilities for reading config properties"""
from datetime import datetime
from functools import cache

import yaml


@cache
def get_config(filepath: str = "config.yml") -> dict:
    """Loads yaml config file and caches it's content in memory.

    Parameters
    ----------
    filepath : str, optional
        File path, by default "config.yml"

    Returns
    -------
    dict
        Loaded contents of the file as a dict
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data_loaded = yaml.safe_load(f)
    return data_loaded


def get_db_name() -> str:
    """
    Returns
    -------
    str
        MongoDB database name specified in the config
    """
    return get_config()["mongo"]["db"]


def get_collection_name() -> str:
    """
    Returns
    -------
    str
        Collection that is used to store the donations
    """
    return get_config()["mongo"]["collection"]


def get_sources() -> list[dict[str, str | datetime]]:
    """
    Returns
    -------
    list[dict[str, str | datetime]]
        List of donation source configs
    """
    return get_config()["sources"]


def get_source(name: str) -> dict[str, str | datetime]:
    """Retrieve a config for specific donation source.

    Parameters
    ----------
    name : str
        Donation source name.

    Returns
    -------
    dict[str, str | datetime]
        Config for specific donation source

    Raises
    ------
    ValueError
        If specified name is not found in the config file.
    """
    for source in get_sources():
        if source["name"] == name:
            return source
    raise ValueError(f"No config is found for source {name}")


def get_sources_names_list() -> list[str]:
    """
    Returns
    -------
    list[str]
       List of available source names in the config file.
    """
    return [source["name"] for source in get_sources()]


def get_creds_keys_list(source_type: str = "all") -> list[str]:
    """Get credentials keys for donation sources.

    Parameters
    ----------
    source_type : str, optional
        Type of the source, by default "all"

    Returns
    -------
    list[str]
       Credentials keys for donation sources.
    """
    return [
        source["creds_key"] for source in get_sources() if source_type in (source["type"], "all")
    ]
