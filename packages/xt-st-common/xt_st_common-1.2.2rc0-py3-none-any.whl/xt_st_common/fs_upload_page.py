"""An upload page which uses the server filesystem for storage."""

import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from typing import Iterable, List, Union
from zipfile import ZIP_DEFLATED, ZipFile
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_tree_select import tree_select

from xt_st_common.config import StreamlitBaseSettings

settings = StreamlitBaseSettings()


def list_directory(path: str, include_empty=True) -> list[str]:
    """Return a list of all the files in a directory."""
    files = []
    for root, directories, filenames in os.walk(path):
        relative_root = root.replace(path, "")

        # Collect empty directories separately otherwise they never appear in the list
        if include_empty:
            for d in directories:
                full_dir = Path(root) / d
                if len(os.listdir(full_dir)) == 0:
                    files.append(str(Path(relative_root) / d) + os.sep)

        # Collect files
        for filename in filenames:
            files.append(Path(relative_root) / filename)
    return files


def create_file_tree(files: Iterable[str]) -> list[dict[str, str]]:
    """Using a list of file paths return a tree structure compatible with `streamlit_tree_select`."""
    file_tree = []
    files = sorted(files, key=str)
    for file in files:
        parts = str(file).split(os.sep)
        current_level = file_tree
        for i, part in enumerate(parts):
            existing = [node for node in current_level if node["label"] == part]
            if existing:
                current_level = existing[0].setdefault("children", [])
            else:
                new_node = {
                    "label": part,
                    "value": os.sep.join(parts[: i + 1]),
                }
                current_level.append(new_node)
                if i != len(parts) - 1:
                    current_level = new_node.setdefault("children", [])
    return file_tree


def _is_child_path(child_path, parent_path):
    """Returns `True` if the `child_path` is inside the `parent_path`."""
    # make both absolute
    parent_path = os.path.realpath(parent_path) + os.sep
    child_path = os.path.realpath(child_path)

    # return true, if the common prefix of both is equal to parent_path
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([child_path, parent_path]) == parent_path


def _prepare_download(files: List[str], root_dir: str = "") -> BytesIO:
    """Prepare zip file for download."""
    mem_zip = BytesIO()
    with ZipFile(mem_zip, "w") as zf:
        for file in files:
            fpath = Path(root_dir + os.sep + file)
            if fpath.is_dir():
                continue
            zf.write(str(fpath), arcname=file, compress_type=ZIP_DEFLATED)
    return mem_zip


def _delete_files(files: List[str], root_dir: str = "") -> None:
    """
    Delete the list of files.

    The root directory of a list of
    relative paths can be passed using `root_dir`.
    """
    dir_list = []
    for path in files:
        fpath = Path(root_dir + os.sep + path)

        # If you're deleting the root directory just recreate it rather than
        # manually recursing through the structure
        if path == "/" and len(root_dir) > 0:
            rmtree(root_dir)
            Path.mkdir(root_dir)
            return

        # Check path is a child of the expected root directory
        if not _is_child_path(fpath, root_dir):
            raise PermissionError(f"Attempting to remove file outside root directory: ['{path}']")

        # If path is a directory defer until later once all the files are removed
        # (can't remove a non-empty directory)
        if fpath.is_dir():
            dir_list.append(str(fpath))
        else:
            Path.unlink(fpath)

    # Remove the collected directories
    # - Sort longest->shortest so that we remove deepest directories first
    # - Create a set to make sure they're unique (empty directories appear twice otherwise)
    dir_list = sorted(set(dir_list), key=len, reverse=True)
    if "dir_list" not in st.session_state:
        st.session_state["dir_list"] = dir_list
    for path in dir_list:
        Path.rmdir(path)


def upload_page(data_dir: str, accepted_ft: Union[None, str, List[str]] = None, dl_prefix: str = "data"):
    """
    Render the upload page which uses the servers local filesystem for storage.

    ### Parameters
        data_dir: str
            directory to store data in on the server

        accepted_ft: str or list of str or None
            Accepted filetypes for upload (passed to `st.file_uploader()`)

        dl_prefix: str
            Name of the zip when downloading will be `{dl_prefix}-Y-m-d_H.M.S.zip`
    """
    c1, c2 = st.columns(2)

    # Show file structure
    with c1:
        file_list = list_directory(data_dir + os.sep)
        file_tree = [{"label": "/", "value": "/", "children": create_file_tree(file_list)}]
        ts = tree_select(file_tree, expanded=["/"], check_model="all")

    # Show upload widget and other controls
    with c2:
        # File Upload
        uploaded_files = st.file_uploader("Upload input file(s)", accept_multiple_files=True, type=accepted_ft)
        for uploaded_file in uploaded_files:
            save_path = Path(data_dir, uploaded_file.name)
            with Path.open(save_path, "wb") as w:
                w.write(uploaded_file.getvalue())

        # File Download
        files_selected, dl_data = (False, "")
        if ts["checked"]:
            files_selected = True
            dl_data = _prepare_download(ts["checked"], root_dir=data_dir)

        l_btn, r_btn, _ = st.columns([1, 1, 2])
        with l_btn:
            st.download_button(
                "Zip & Download",
                data=dl_data,
                file_name=f"{dl_prefix}-{datetime.now(tz=ZoneInfo(settings.TIMEZONE)).strftime('%Y-%m-%d_%H.%M.%S')}.zip",
                disabled=not files_selected,
            )
        with r_btn:
            if st.button("Delete Selected", disabled=not files_selected, type="primary"):
                _delete_files(ts["checked"], root_dir=data_dir)
                st.rerun()
