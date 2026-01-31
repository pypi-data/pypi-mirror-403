from typing import List, Optional

import pandas as pd
import streamlit as st

# from mpl_toolbox_ui.common.config import Settings
from xt_st_common.database import (
    Project,
    delete_project,
    get_project,
    get_project_cache,
    get_projects,
    project_duplicate_exists,
    save_project,
)
from xt_st_common.project_models import ProjectState
from xt_st_common.session import get_user_email
from xt_st_common.storage import FileRef, storage_client
from xt_st_common.utils import (
    get_encoding_and_dialect,
    get_state,
    seperate_users,
    set_state,
)


def has_project_write_access(project: Project):
    return project.owner.lower() == get_user_email().lower() or get_user_email().lower() in (
        user.lower() for user in project.users
    )


def state_reset():
    for s in ProjectState:
        if s in [ProjectState.PROJECT_TO_DELETE, ProjectState.FILE_TO_DELETE]:
            set_state(s, None)
        else:
            set_state(s, "")


def get_selected_project() -> Optional[Project]:
    project = get_state("selected_project", None)
    if project is None:
        return None
    if not isinstance(project, Project):
        raise ValueError("Selected project is not the correct type")
    return project


def get_selected_folder() -> str:
    return get_state("project_folder_select", "")


def get_selected_project_or_error() -> Project:
    project = get_selected_project()
    if project is None:
        raise ValueError("No project was selected")
    return project


def set_selected_project(project: Optional[Project]):
    if project is not None and not isinstance(project, Project):
        raise ValueError("Setting selected project to a type other than project")
    st.session_state.selected_project = project


def submit_delete_project(project: Project):
    """Callback function to set state in order to enable a delete on the next run."""
    # display a warning if the user entered an existing name

    if project is None:
        st.toast("No project is selected", icon="⚠️")
    elif project.owner.lower() != get_user_email().lower():
        st.toast(f"Delete of project **{project.name}** failed: You are not the owner.", icon="⚠️")
    else:
        set_state(
            ProjectState.PROJECT_DELETE_CONFIRM,
            (
                "Deleting will remove all files that are part of project: "
                + f"**'{project.name}'**. Are you sure you want to continue?"
            ),
        )
        set_state(ProjectState.PROJECT_TO_DELETE, project)


def action_delete(project: Project):
    if project.id is not None and project.owner.lower() == get_user_email().lower():
        delete_project(project.id)
    st.toast(f"Project **'{project.name}'** deleted successfully", icon="🎉")


def action_delete_folder(folder):
    project = get_selected_project_or_error()
    project.delete_folder(folder)
    save_project(project)
    st.toast(f"Folders **'{folder}'** was deleted successfully", icon="🎉")


# def submit_delete_file(file: FileRef):
#     """Callback function to set state in order to enable a delete on the next run."""
#     # display a warning if the user entered an existing name
#     project = st.session_state.selected_project
#     if project is None:
#         set_state(ProjectState.FILE_WARNING_MESSAGE, "No project is selected")
#     elif file is None:
#         set_state(ProjectState.FILE_WARNING_MESSAGE, "No file is selected")
#     elif not has_project_write_access(project):
#         set_state(
#             ProjectState.FILE_WARNING_MESSAGE,
#             f"You don't have write access to project: {project.name}",
#         )
#         return
#     else:
#         set_state(
#             ProjectState.FILE_DELETE_CONFIRM,
#             f"Are you sure you want to delete file **'{file.name}'**?",
#         )
#         set_state(ProjectState.FILE_TO_DELETE, file)


def action_delete_file(_file: FileRef):
    project = get_selected_project_or_error()
    if not has_project_write_access(project):
        st.toast(f"You don't have write access to project: {project.name}", icon="⚠️")
        return
    project.delete_file(_file)
    save_project(project)
    st.toast(f"File {_file.name} was deleted successfully", icon="🎉")


def submit_add_project(project: Optional[Project] = None):
    """Callback function during adding a new project."""

    message_verb = "updated"
    container = st.session_state.message_box if "message_box" in st.session_state else st

    name = get_state("create_project_name")
    description = str(get_state("create_project_description"))
    users = get_state("create_project_users")
    is_public = bool(get_state("create_project_public", False))

    if not name:
        container.warning("No project name was provided")
        return

    users_list = seperate_users(users)
    if project is None:
        message_verb = "created"
        project = Project(
            name=name,
            owner=get_user_email(),
            description=description,
            users=users_list,
            public=is_public,
        )
        if project_duplicate_exists(project.name, project.owner, str(project.id)):
            st.toast(f"A Project with the name: **'{name}'** already exists", icon="⚠️")
            return
    else:
        # Get latest DB copy of the project
        project = get_project(str(project.id), st.session_state.project_cache)
        if project is None:
            st.toast(f"Cannot update project: **'{name}'** not found in database", icon="⚠️")
            return
        project.__dict__.update(
            {
                "name": name,
                "description": description,
                "users": users_list,
                "public": is_public,
            }
        )

    project = save_project(project)
    set_selected_project(project)

    st.toast(f":green[Project **'{name}'** has been {message_verb}.]", icon="🎉")
    return


def add_folders():
    project = st.session_state.selected_project
    folders_string = st.session_state.add_project_folder_name

    if not folders_string:
        st.toast(":red[Cannot add new folders:] Folder name was empty", icon="⚠️")
        return

    if not has_project_write_access(project):
        st.toast(f"You don't have write access to project: {project.name}", icon="⚠️")
        return

    count = project.add_folders(folders_string)
    save_project(project)
    st.toast(f"{count} folders were added to **'{project.name}'**", icon="🎉")


def move_file(selected_file: FileRef, new_path: str):
    project: Project = st.session_state["selected_project"]

    if not new_path:
        st.toast("Cannot move file. New path was empty", icon="⚠️")
        return

    if selected_file.path == new_path:
        st.toast("Cannot move file. New path is the same as the existing path", icon="⚠️")
        return

    if not has_project_write_access(project):
        st.toast(f"You don't have write access to project: {project.name}", icon="⚠️")
        return

    project.move_file_to_path(selected_file, new_path)

    save_project(project)

    st.toast(f"File **'{selected_file.name}'** was succesfully moved to **'{new_path.split('/', 1)[1]}'**", icon="🎉")


def move_folder(selected_folder: str, new_folder_name: str):
    project: Project = st.session_state["selected_project"]

    if "/" in selected_folder:
        leaf_folder = selected_folder.split("/")[-1]
        folder_root = selected_folder.split(f"/{leaf_folder}")[0]
        full_new_folder_name = "/".join([folder_root, new_folder_name])
    else:
        leaf_folder = selected_folder
        folder_root = ""
        full_new_folder_name = "/".join([new_folder_name])

    if "/" in new_folder_name:
        st.toast("Cannot rename folder. New name must not contain slash (/) characters", icon="⚠️")
        return

    if not new_folder_name:
        st.toast("Cannot rename folder. New name was empty", icon="⚠️")
        return

    if leaf_folder == new_folder_name:
        st.toast("Cannot rename folder. New name is the same as the existing name", icon="⚠️")
        return

    if not has_project_write_access(project):
        st.toast(f"You don't have write access to project: {project.name}", icon="⚠️")
        return

    project.rename_folder(selected_folder, full_new_folder_name)

    save_project(project)

    st.toast(f"Folder **'{leaf_folder}'** was succesfully renamed to **'{new_folder_name}'**", icon="🎉")


def copy_file_to_project(selected_file: FileRef, new_project: Project):
    current_project: Project = st.session_state["selected_project"]

    if not has_project_write_access(new_project):
        st.toast(f"You don't have write access to project: {new_project.name}", icon="⚠️")
        return

    if current_project.name in selected_file.get_prefix():
        new_path = f"{selected_file.get_prefix().replace(current_project.name, new_project.name).replace(str(current_project.id), str(new_project.id))}{selected_file.get_suffix()}"  # noqa: E501
    else:
        st.toast("Cannot copy file. File does not exist in current project", icon="⚠️")
        return

    if selected_file.path == new_path:
        st.toast("Cannot copy file. New path is the same as the current path.", icon="⚠️")
        return

    new_file_ref = new_project.copy_file_to_path(selected_file, new_path)

    # if there are user folders included with the new path, add them to the project as well
    new_folder_message = ""
    folders_string = new_file_ref.get_user_folders()
    if folders_string != "":
        new_folder_count = new_project.add_folders(folders_string)
        if new_folder_count > 0:
            new_folder_message = f"**{new_folder_count}** folders were added."

    save_project(new_project)

    st.toast(
        f"File **'{selected_file.name}'** was succesfully copied to **'{new_project.name}'**. " + new_folder_message,
        icon="🎉",
    )


@st.cache_data(ttl=300)
def get_df_preview(path: str, ext: Optional[str], num_rows=25):
    # if filepath.suffix == ".zip":
    #     frame = get_gdf_from_file(filepath)
    #     return frame.iloc[:num_rows, :-1]
    _ext = ext.strip(".").lower() if ext else None
    if _ext == "csv":
        file = storage_client().get_file(path)
        encoding, dialect = get_encoding_and_dialect(file)
        return pd.read_csv(file, nrows=num_rows, sep=dialect.delimiter, encoding=encoding)
    if _ext == "feather":
        file = storage_client().get_file(path)
        return pd.read_feather(file)
    if _ext == "xlsx":
        file = storage_client().get_file(path)
        return pd.read_excel(file, sheet_name=0, nrows=num_rows)

    return None


def get_string_preview(fileref: FileRef):
    file = storage_client().get_file(fileref.path)
    return file.getvalue().decode("utf-8")


@st.cache_data(ttl=15)
def get_proj_options(
    include_public: bool = False,
    other_apps: bool = True,
    shared_project: bool = True,
    selected_in_options: bool = True,
    cache_id=None,
):
    selected_project = get_selected_project()
    projects = get_projects(include_public, other_apps, shared_project, get_project_cache())
    sel_idx = 0
    options = {}
    for idx, proj in enumerate(projects):
        if selected_project and proj.id == selected_project.id:
            if selected_in_options:
                sel_idx = idx
            else:
                # when selected_in_options is false, skip the rest of this iteration
                continue

        option_str = f"{proj.name} ({proj.application}){'- 📢Public' if proj.public else ''}"
        if not proj.public and proj.owner.lower() != get_user_email().lower():
            option_str += " - 🤝Shared"
        options[idx] = option_str
    return options, projects, sel_idx


def on_project_select():
    proj_idx = get_state("project_select")
    include_public = bool(get_state("include_public_projects", False))
    include_other_apps = bool(get_state("include_other_apps", False))
    options, projects, _ = get_proj_options(include_public, include_other_apps, cache_id=get_project_cache())

    if proj_idx is not None and proj_idx > -1:
        selected_project = projects[proj_idx] if proj_idx != -1 else None
        set_selected_project(selected_project)
    else:
        set_selected_project(None)


def parse_csv_data(raw_df: pd.DataFrame, header_row, units_row, skip_rows: Optional[List[int]] = None):
    units = {}
    if skip_rows is None:
        skip_rows = []

    raw_df.columns = raw_df.iloc[header_row]

    if units_row is not None and units_row != "None":
        units = raw_df.iloc[units_row].to_dict()
        if units_row != header_row and units_row not in skip_rows:
            raw_df = raw_df.drop(labels=units_row)

    if header_row not in skip_rows:
        raw_df = raw_df.drop(labels=header_row)

    raw_df = raw_df.drop(labels=skip_rows)
    raw_df = raw_df.reset_index(drop=True)

    return raw_df, units


def submit_edit_projects(edited_project_data):
    project_table_data = st.session_state.get("project_editor_key")
    for changed_id in project_table_data["edited_rows"]:
        # Get latest DB copy of the project
        db_project = get_project(
            str(edited_project_data["id"][changed_id]),
            st.session_state.project_cache,
        )
        if db_project is None:
            st.toast(
                f":orange[Cannot update project:] **'{edited_project_data['name'][changed_id]}'** "
                + " not found in database",
                icon="⚠️",
            )
        elif db_project.owner.lower() != get_user_email().lower():
            st.toast(
                f":orange[Save changes on project **{db_project.name}** failed:] You are not the owner.", icon="⚠️"
            )
        else:
            original_name = db_project.name
            db_project.__dict__.update(
                {
                    "name": edited_project_data["name"][changed_id],
                    "description": edited_project_data["description"][changed_id],
                    "users": seperate_users(edited_project_data["users"][changed_id]),
                    "public": bool(edited_project_data["public"][changed_id]),
                }
            )
            if project_duplicate_exists(db_project.name, db_project.owner, str(db_project.id)):
                st.toast(
                    f":orange[Cannot update project:] A Project with the name: **'{db_project.name}'** "
                    + "already exists",
                    icon="⚠️",
                )
            else:
                if original_name != edited_project_data["name"][changed_id]:
                    db_project.rename_project(original_name, edited_project_data["name"][changed_id])
                db_project = save_project(db_project)
                st.toast(f"Project **'{db_project.name}'** updated successfully", icon="🎉")
