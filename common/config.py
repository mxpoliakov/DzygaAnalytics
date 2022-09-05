"""This module contains utilities for reading config properties"""
import os
import re
from datetime import datetime
from functools import cache

import yaml


@cache
def get_config(filepath: str = "config.yml") -> dict:
    """Loads yaml config file and caches it's content in memory.
    Modifies yaml.SafeLoader to expand strings like ${ENV_VAR} into
    environment variable value.

    Parameters
    ----------
    filepath : str, optional
        File path, by default "config.yml"

    Returns
    -------
    dict
        Loaded contents of the file as a dict
    """
    env_pattern = re.compile(r".*?\${(.*?)}.*?")

    def env_constructor(loader: yaml.loader.SafeLoader, node: yaml.nodes.ScalarNode) -> str:
        _ = loader
        value = node.value
        match = env_pattern.match(value)
        env_var = match.group()[2:-1]
        return os.environ[env_var] + value[match.end() :]

    yaml.add_implicit_resolver("!pathex", env_pattern, Loader=yaml.loader.SafeLoader)
    yaml.add_constructor("!pathex", env_constructor, Loader=yaml.loader.SafeLoader)

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


def get_mongo_uri() -> str:
    """
    Returns
    -------
    str
        MongoDB secret URI that allows access to database
    """
    return get_config()["mongo"]["mongo_uri"]


def get_collection_name() -> str:
    """
    Returns
    -------
    str
        Collection that is used to store the donations
    """
    return get_config()["mongo"]["collection"]


def get_sources(source_type=None) -> list[dict[str, str | datetime]]:
    """
    Returns
    -------
    list[dict[str, str | datetime]]
        List of donation source configs
    """
    sources = get_config()["sources"]

    if source_type is not None:
        return [source for source in sources if source_type in source["type"]]

    return sources


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
