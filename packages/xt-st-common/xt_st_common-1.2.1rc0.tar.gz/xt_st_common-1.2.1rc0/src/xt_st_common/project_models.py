import logging
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

import natsort
from bson import ObjectId
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, WithJsonSchema

from xt_st_common.config import StreamlitBaseSettings
from xt_st_common.storage import FileRef, storage_client

settings = StreamlitBaseSettings()


def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[
    Union[str, ObjectId],
    AfterValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


class ProjectState(str, Enum):
    PROJECT_DELETE_CONFIRM = "proj_delete_confirm"
    PROJECT_TO_DELETE = "proj_delete"
    PROJECT_SUCCESS_MESSAGE = "proj_success_message"
    PROJECT_WARNING_MESSAGE = "proj_warning_message"

    FOLDER_TO_DELETE = "upload_delete_folder"
    FOLDER_ADDED = "upload_folder_added"

    UPLOAD_SUCCESS_MESSAGE = "upload_success_message"
    UPLOAD_WARNING_MESSAGE = "upload_warning_message"
    UPLOAD_DELETE_CONFIRM = "upload_delete_confirm"

    FILE_DELETE_CONFIRM = "file_delete_confirm"
    FILE_TO_DELETE = "file_to_delete"
    FILE_SUCCESS_MESSAGE = "file_success_message"
    FILE_WARNING_MESSAGE = "file_warning_message"
    FILE_MESSAGE = "file_message"

    # FILE_MANAGER_UPLOAD = "file_manager_upload_file"
    FILE_MANAGER_REPLACE_FILE = "file_manager_replace_file"

    def __str__(self):
        return str(self.value)


class Project(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    description: str = ""
    public: bool = False
    application: str = settings.APP_NAME
    files: List[FileRef] = []
    folders: List[str] = []
    owner: str = ""
    users: List[str] = []  # Users with access to this project

    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    def get_users_string(self):
        return ",".join(self.users)

    def get_folders_map(self):
        fol_dict = {"": "Project Root"}
        for folder in self.folders:
            parts = folder.strip("/").split("/")
            fol_dict[folder] = " - ".join(parts)
        return fol_dict

    def get_folder_path(self, folder):
        return f"{self.id!s}/{self.name}/{folder}".strip("/")

    def get_files_in_folder(
        self,
        folder: str,
        include_subfolders: bool = True,
        extensions: Optional[List[str]] = None,
        null_option: Optional[str] = None,
        sort: Literal["none", "file-asc", "file-desc", "folder-asc", "folder-desc"] = "none",
    ):
        """
        _summary_.

        Parameters
        ----------
        folder : str
            The folder to search, set to '' to search the root folder.
        include_subfolders : bool, optional
            If true will find all files in subfolders, if false will only search the specified folder, by default True
        extensions : List[str], optional
            Extensions to match on, MUST BE LOWERCASE without a '.' use None to not filter on extensions,
            by default None
        null_option : _type_, optional
            Will add a default 'None' item to the list if None no default item will be added, by default None
        sort : str, optional
            Will enable sorting the file list by only filename or by parent folder in ascending or descending order
        Returns
        -------
        _type_
            _description_
        """

        _files: Dict[str, Union[None, FileRef]] = {} if null_option is None else {null_option: None}

        path = self.get_folder_path(folder)
        for file in self.files:
            if path in file.path:
                file_path = file.path.removeprefix(path).strip("/")
                if (include_subfolders or file_path.find("/") <= 0) and (
                    extensions is None or str(Path(file.name).suffix).strip(".").lower() in extensions
                ):
                    _files[file_path] = file

        if sort == "file-asc":
            _files = natsort.natsorted(_files, reverse=False, key=lambda x: _files[x].name)
        elif sort == "file-desc":
            _files = natsort.natsorted(_files, reverse=True, key=lambda x: _files[x].name)
        elif sort == "folder-asc":
            _files = natsort.natsorted(_files, reverse=False, key=lambda x: _files[x].get_user_folders())
        elif sort == "folder-desc":
            _files = natsort.natsorted(_files, reverse=True, key=lambda x: _files[x].get_user_folders())

        return _files

    def get_subfolders(self, folder: str, include_all: bool = False) -> list:
        """
        Get subfolders of the provided search folder.

        Args:
            folder (str): The name of the folder to search for subfolders
            include_all(bool): If False, return only the immediate children of the search folder.
                If True, return *all* sub folders ie. the children of children. Default False.

        Returns:
            list[str]: A list of sub folder strings
        """

        if include_all:
            # when split on the folder name, a subfolder will have "" as the first split entry.
            return [sub for sub in self.folders if sub.split(f"{folder}/")[0] == ""]

        return [
            # do as above, but don't accept subfolders that contain "/" (and are therefore children)
            sub
            for sub in self.folders
            if (sub.split(f"{folder}/")[0] == "") and "/" not in sub.split(f"{folder}/")[1]
        ]

    def populate_node(self, _dict, part, parts):
        if part not in _dict:
            _dict[part] = {}

        if parts:
            self.populate_node(_dict[part], parts[0], parts[1:])

    def populate_children(self, _dict, key, children, path, show_checkbox=True):
        if child_dict := _dict[key]:
            for child_key in child_dict:
                new_children = None
                new_path = f"{path}/{child_key}"
                if child_dict[child_key]:
                    new_children = []
                    self.populate_children(child_dict, child_key, new_children, new_path, show_checkbox)
                children.append(
                    {
                        "label": child_key,
                        "value": f"{path}/{child_key}",
                        "children": new_children,
                        "showCheckbox": show_checkbox,
                    }
                )

    def get_file_tree(self, show_checkbox=True):
        main_dict = {}
        full_list = (
            [file.path.removeprefix(self.get_folder_path("")).strip("/") for file in self.files] if self.files else []
        )
        if self.folders:
            full_list.extend(self.folders)
        if not full_list:
            return []
        for folder in full_list:
            parts = folder.split("/")
            self.populate_node(main_dict, parts[0], parts[1:])

        nodes = []
        for key in main_dict:
            children = None
            if main_dict[key]:
                children = []
                self.populate_children(main_dict, key, children, key, show_checkbox)
            nodes.append({"label": key, "value": key, "children": children, "showCheckbox": show_checkbox})

        return nodes

    def add_replace_file(self, data_file, folder: str, filename: str, content_type=None) -> FileRef:
        path = f"{self.get_folder_path(folder)}/{filename}".strip("/")
        return self.add_replace_file_by_path(data_file, path, content_type=content_type)

    def add_replace_file_by_path(self, data_file, path: str, content_type=None) -> FileRef:
        try:
            file_ref = storage_client().write_file(path, data_file, content_type)
            replaced = False
            for idx, file in enumerate(self.files):
                if file.path == path:
                    self.files[idx] = file_ref
                    replaced = True
                    break
            if not replaced:
                self.files.append(file_ref)
            return file_ref
        except Exception as err:
            logging.error(err)
            raise err

    def move_file_to_path(self, file: FileRef, new_path: str) -> FileRef:
        """
        Move the file referenced by file_ref to the new_path.

        Args:
            file_ref (FileRef): A file reference object for the existing file
            new_path (str): The new path where the file to be moved to

        Returns:
            FileRef: The file reference for the newly moved file.
        """
        new_file_ref = storage_client().copy_file(
            file.path,
            new_path,
            file.content_type,
            file.size_bytes,
            delete_original=True,
        )
        index = self.files.index(file)
        self.files[index] = new_file_ref
        return new_file_ref

    def copy_file_to_path(self, file_ref: FileRef, new_path: str) -> FileRef:
        """
        Copy the file referenced by file_ref to the new_path.

        Args:
            file_ref (FileRef): A file reference object for the existing file
            new_path (str): The new path where the file to be copied to

        Returns:
            FileRef: The file reference for the newly copied file.
        """
        new_file_ref = storage_client().copy_file(
            file_ref.path,
            new_path,
            file_ref.content_type,
            file_ref.size_bytes,
            delete_original=False,
        )
        replaced = False
        for idx, file in enumerate(self.files):
            if file.path == new_path:
                self.files[idx] = new_file_ref
                replaced = True
                break
        if not replaced:
            self.files.append(new_file_ref)
        return new_file_ref

    def delete_file(self, file: FileRef):
        storage_client().delete_file(file.path)
        try:
            self.files.remove(file)
        except ValueError:
            logging.warning(f"File {file.path} didn't exist and couldn't be deleted.")

    def add_folders(self, folders_string: str):
        folders = set(self.folders)
        new_folders = folders_string.split(",")
        count = 0
        for folder in new_folders:
            folder = folder.strip().replace(" ", "_").strip("/")
            folder_parts = folder.split("/")
            # add each part
            for idx, part in enumerate(folder_parts):
                part_string = part if idx == 0 else f"{'/'.join(folder_parts[:idx + 1])}"

                # only increment count if the part_string doesn't already exist in the folder list
                if part_string not in folders:
                    folders.add(part_string)
                    count += 1

        try:
            self.folders = list(folders)
        except AttributeError:
            logging.warning("Weird odmatic error, attempting to ignore")

        return count

    def delete_folder(self, folder: str):
        """
        Recursively delete the files and sub folders of the provided folder name.

        Args:
            folder (str): The name of the folder to be recursively deleted
        """
        try:
            sub_folders = self.get_subfolders(folder)

            # recursively delete any sub folders first
            for sub_folder in sub_folders:
                # this "if" appears to be redundant but the sub-folder may already have been
                # deleted in another recursion branch
                if sub_folder in self.folders:
                    self.delete_folder(sub_folder)

            folder_path = self.get_folder_path(folder)
            self.folders.remove(folder)
            for file in [x for x in self.files if folder_path in x.path]:
                self.delete_file(file)
        except ValueError:
            logging.warning(f"Folder {folder} didn't exist and couldn't be deleted.")

    def rename_folder(self, existing_name: str, new_name: str):
        """
        Rename the folder with existing name with new_name and move all of its files.

        Args:
            existing_name (str): The name of the existing folder
            new_name (str): The new path where the file to be moved to

        Returns:
            FileRef: The file reference for the newly moved file.
        """

        sub_folders = self.get_subfolders(existing_name)

        # recursively move any sub folders first
        for sub_folder in sub_folders:
            # this "if" appears to be redundant but the sub-folder may already have been
            # moved in another recursion branch
            if sub_folder in self.folders:
                self.rename_folder(sub_folder, sub_folder.replace(existing_name, new_name))

        files = self.get_files_in_folder(existing_name, include_subfolders=False)
        for file_ref in files.values():
            self.move_file_to_path(file_ref, "/".join([file_ref.get_root(), new_name, file_ref.name]))
        self.folders[self.folders.index(existing_name)] = new_name

    def rename_project(self, existing_name: str, new_name: str):
        """
        Rename the current project and update all of its file paths.

        Args:
            existing_name (str): The existing name of the project
            new_name (str): The name to rename the project as
        """
        for file_ref in self.files:
            (
                self.move_file_to_path(
                    file_ref,
                    "/".join(
                        [
                            file_ref.get_root().replace(existing_name, new_name),
                            file_ref.get_user_folders(),
                            file_ref.name,
                        ]
                    ).replace("//", "/"),
                ),
            )

        self.name = new_name
