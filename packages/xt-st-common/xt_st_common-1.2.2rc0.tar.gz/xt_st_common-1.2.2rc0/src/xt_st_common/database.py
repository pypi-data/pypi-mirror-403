import random
from typing import List, Optional, Union

import streamlit as st
from bson.objectid import ObjectId
from pymongo import MongoClient

from xt_st_common.project_models import Project
from xt_st_common.session import get_user_email

from .config import StreamlitBaseSettings

settings = StreamlitBaseSettings()
PROJECT_COLLECTION_NAME = "project"


@st.cache_resource
def init_connection():
    settings = StreamlitBaseSettings()
    if None in [settings.DATABASE_NAME, settings.MONGO_CONNECTION_STRING]:
        raise ValueError("Can't get mongo engine when connection string is None.")
    client = MongoClient(settings.MONGO_CONNECTION_STRING)
    # engine = SyncEngine(client=client, database=settings.DATABASE_NAME)
    # engine.configure_database([Project], update_existing_indexes=True)
    return client.get_database(name=settings.DATABASE_NAME)


@st.cache_resource
def get_collection(name="project"):
    db_client = init_connection()
    return db_client[name]


@st.cache_data(ttl=30)
def get_project(project_id: str, cache_id=None) -> Optional[Project]:
    project_dict = get_collection().find_one({"_id": ObjectId(project_id)})
    return Project(**project_dict) if project_dict is not None else None


@st.cache_data(ttl=30)
def get_projects(include_public=False, other_apps=True, shared_project=True, cache_id=None) -> List[Project]:
    current_user = get_user_email()
    or_query = {
        "$or": [
            {"owner": {"$regex": f"^{current_user}$", "$options": "i"}},
        ]
    }
    if include_public:
        or_query["$or"].append({"public": True})
    if shared_project:
        or_query["$or"].append({"users": {"$elemMatch": {"$regex": f"^{current_user}$", "$options": "i"}}}),

    if len(or_query["$or"]) == 1:
        or_query = or_query["$or"][0]

    query = or_query if other_apps else {"$and": [{"application": f"{settings.APP_NAME}"}, or_query]}
    return [Project(**item) for item in get_collection().find(query)]


@st.cache_data(ttl=30)
def project_exists(project_id: str, cache_id=None) -> bool:
    return get_collection().count_documents({"_id": ObjectId(project_id)}) > 0


@st.cache_data(ttl=30)
def project_duplicate_exists(name: str, owner: str, project_id: Optional[str] = None, cache_id=None) -> bool:
    return (
        get_collection().count_documents(
            {"_id": {"$ne": ObjectId(project_id)}, "name": name, "owner": {"$regex": f"^{owner}$", "$options": "i"}}
        )
        > 0
    )


@st.cache_data(ttl=30)
def get_owned_projects(owner: str, cache_id=None) -> List[Project]:
    return [Project(**item) for item in get_collection().find({"owner": {"$regex": f"^{owner}$", "$options": "i"}})]


def reset_project_cache():
    st.session_state.project_cache = random.random()


def get_project_cache():
    if "project_cache" not in st.session_state:
        reset_project_cache()
    return st.session_state.project_cache


def save_project(project: Project):
    if project.id is None:
        result = get_collection().insert_one(project.dict(exclude={"id"}))
        project.id = result.inserted_id
    else:
        get_collection().update_one(
            {"_id": ObjectId(project.id) if project.id is not None else None},
            {"$set": project.dict(exclude={"id"})},
            upsert=True,
        )
    reset_project_cache()
    return project


def delete_project(project_id: Union[str, ObjectId]):
    get_collection().delete_one({"_id": ObjectId(project_id)})
    reset_project_cache()
