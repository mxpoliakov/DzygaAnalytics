"""This module contains utilities for working with MongoDB"""
import os

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from common.config import get_collection_name
from common.config import get_db_name


def get_database() -> Database:
    """
    Get database connection. Requires MONGO_URI secret environment variable.

    Returns
    -------
    Database
        Connection to MongoDB Database
    """
    return MongoClient(os.environ["MONGO_URI"])[get_db_name()]


def get_collection(collection_name: None | str = None) -> Collection:
    """Get connection to donations collection.

    Parameters
    ----------
    collection_name : None | str, optional
        Collection name where donations are stored.
        If None the name from config file would be used

    Returns
    -------
    Collection
        Connection to MongoDB Collection
    """
    collection_name = collection_name if collection_name is not None else get_collection_name()
    return get_database().get_collection(collection_name)
