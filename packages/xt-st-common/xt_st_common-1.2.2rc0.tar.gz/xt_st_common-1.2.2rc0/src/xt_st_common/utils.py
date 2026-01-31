import csv
import time
from collections import defaultdict
from enum import Enum
from io import BytesIO
from typing import Any, Optional, Union

import chardet
import streamlit as st

# from pydantic import BaseModel

# from dask.distributed import Client

# @st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
# def get_dask_client():
#     client = Client("tcp://127.0.0.1:8786")
#     # client = Client()

#     return client


def get_encoding_and_dialect(input_file: BytesIO):
    sample_bytes = 1048576  # 1 Megabyte
    _bytes = input_file.read(sample_bytes)

    result = chardet.detect(_bytes)
    charenc = result["encoding"]

    if charenc == "ascii":
        charenc = "utf8"

    dialect = csv.Sniffer().sniff(str(_bytes))
    input_file.seek(0)

    return charenc, dialect


def sizeof_fmt(num: Optional[Union[float, int]], suffix="B") -> str:
    if num is None:
        return ""
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Y", suffix)


def seperate_users(users_string):
    users_array = users_string.strip().lower().split(",")
    return [user.strip() for user in users_array]


FILE_MARKER = "<files>"


def attach(branch, trunk):
    """Insert a branch of directories on its trunk."""
    parts = branch.split("/", 1)
    if len(parts) == 1:  # branch is a file
        trunk[FILE_MARKER].append(parts[0])
    else:
        node, others = parts
        if node not in trunk:
            trunk[node] = defaultdict(dict, ((FILE_MARKER, []),))
        attach(others, trunk[node])


def get_state(state_name: Union[str, Enum], default: Optional[Any] = ""):
    if str(state_name) not in st.session_state or st.session_state[str(state_name)] is None:
        st.session_state[str(state_name)] = default
    return st.session_state[str(state_name)]


def set_state(state_name: Union[str, Enum], value: Any):
    st.session_state[str(state_name)] = value


def wait():
    """Used in Poe scripts."""
    time.sleep(3)
