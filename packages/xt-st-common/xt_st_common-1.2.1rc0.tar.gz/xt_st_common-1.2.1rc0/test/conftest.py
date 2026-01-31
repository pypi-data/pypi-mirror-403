import pathlib

import pytest
import streamlit as st
from pymongo import MongoClient

from xt_st_common.config import StreamlitBaseSettings

# Ensure tests use the test .env
dotenv_path = pathlib.Path(__file__).parent.resolve() / ".env-test"
config = StreamlitBaseSettings(_env_file=dotenv_path)

client = MongoClient(config.MONGO_CONNECTION_STRING)
collection = client.get_database(name=config.DATABASE_NAME)["project"]


@pytest.fixture(autouse=True)
def clear_project_collection():
    """Clear the `project` collection before and after each test to avoid cross-test data leakage."""
    # ensure streamlit caches don't return stale results between tests
    try:
        st.cache_data.clear()
    except Exception:
        pass
    try:
        st.cache_resource.clear()
    except Exception:
        pass

    collection.delete_many({})
    yield
    collection.delete_many({})
