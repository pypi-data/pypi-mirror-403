# type: ignore

import pathlib

import pytest
from pymongo import MongoClient

from xt_st_common.config import StreamlitBaseSettings

dotenv_path = pathlib.Path(__file__).parent.resolve() / ".env-test"
config = StreamlitBaseSettings(_env_file=dotenv_path)

from xt_st_common import database
from xt_st_common.project_models import Project
from xt_st_common.storage import FileRef, StorageClient
from xt_st_common.utils import sizeof_fmt

client = MongoClient(config.MONGO_CONNECTION_STRING)
collection = client.get_database(name=config.DATABASE_NAME)["project"]


class MockStorage(StorageClient):
    def write_file(self, file_path: str, file_data: str, content_type="text/plain") -> FileRef:
        return FileRef(
            url=file_path,
            size=sizeof_fmt(1000),
            size_bytes=1000,
            path=file_path,
            name=pathlib.Path(file_path).name,
            content_type=content_type,
        )

    def get_file(self, file_name):
        pass

    def delete_file(self, file_name):
        pass

    def list_files(self, path_prefix=""):
        pass

    def file_exists(self, file_path: str):
        pass

    def copy_file(
        self,
        file_path: str,
        new_file_path: str,
        file_data: str,
        content_type,
        delete_original: bool,
    ):
        return FileRef(
            url=new_file_path,
            size=sizeof_fmt(1000),
            size_bytes=1000,
            path=new_file_path,
            name=pathlib.Path(new_file_path).name,
            content_type=None,
        )


_mock_storage = MockStorage()


@pytest.fixture
def mock_collection(mocker):
    mocker.patch("xt_st_common.database.get_collection", return_value=collection)
    return mocker


@pytest.fixture
def mock_storage(mocker):
    mocker.patch("xt_st_common.project_models.storage_client", return_value=_mock_storage)
    return mocker


@pytest.fixture
def project1(mock_collection):
    OWNER = "test_user"
    NAME = "Test Project"

    project = Project(name=NAME, owner=OWNER)
    yield project
    if database.project_duplicate_exists(name=NAME, owner=OWNER):
        collection.delete_one({"name": NAME, "owner": OWNER})


@pytest.fixture
def project2(mock_collection):
    OWNER = "test_user2"
    NAME = "Test Project2"

    project = Project(name=NAME, owner=OWNER)
    yield project
    if database.project_duplicate_exists(name=NAME, owner=OWNER):
        collection.delete_one({"name": NAME, "owner": OWNER})


@pytest.fixture
def proj_with_files(mock_storage):
    OWNER = "test_user3"
    NAME = "Test Project3"
    folder = ["foo", "foo/bar"]
    project = Project(name=NAME, owner=OWNER, folders=folder)
    project.add_replace_file(data_file="I am text", folder="foo", filename="file.txt")
    project.add_replace_file(data_file="I am text", folder="foo/bar", filename="file2.json")

    return project


@pytest.fixture
def proj_with_many_folders(mock_storage):
    # a project with many folders with the same names but in different tree positions
    OWNER = "test_user4"
    NAME = "Test Project4"
    folder = [
        "foo",
        "foo/bar",
        "foo/baz",
        "foo/bar/baz",
        "foo/baz/bar",
        "foo/bar/baz/qux",
        "baz",
        "baz/foo",
        "baz/foo/bar",
    ]
    project = Project(name=NAME, owner=OWNER, folders=folder)
    project.add_replace_file(data_file="I am text", folder="/", filename="file4.txt")
    project.add_replace_file(data_file="I am text", folder="foo", filename="file1.txt")
    project.add_replace_file(data_file="I am text", folder="foo/bar", filename="file2.json")
    project.add_replace_file(data_file="I am text", folder="baz/foo/bar", filename="file3.json")

    return project


def test_project_save(project1, mock_collection):
    mock_collection.patch("xt_st_common.session.get_user_email", return_value="test_user")
    database.save_project(project1)

    assert database.project_exists(str(project1.id))


def test_get_public_success(project2: Project, mock_collection):
    project2.public = True
    mock_collection.patch("xt_st_common.session.get_user_email", return_value="test_user")
    database.save_project(project2)

    results = database.get_projects(include_public=True)

    assert results is not None, "No projects were returned, expected project2"
    assert results[0].name == project2.name, "Public project was not returned"


def test_get_public_exclude_when_false(project2: Project, mock_collection):
    project2.public = True
    mock_collection.patch("xt_st_common.session.get_user_email", return_value="test_user")
    database.save_project(project2)

    results = database.get_projects(include_public=False)

    assert not results, "A project was returned when excluding public"


def test_dont_return_private(project2: Project, mock_collection):
    project2.public = False
    mock_collection.patch("xt_st_common.session.get_user_email", return_value="test_user")
    mock_collection.patch("xt_st_common.database.get_user_email", return_value="test_user")
    database.save_project(project2)

    results = database.get_projects(include_public=True)

    assert not results, "A project was returned when project is private {}"


def test_authorised_user_can_access_project(project2: Project, mock_collection):
    project2.public = False
    project2.users = ["test_user"]
    mock_collection.patch("xt_st_common.session.get_user_email", return_value="test_user")
    mock_collection.patch("xt_st_common.database.get_user_email", return_value="test_user")
    database.save_project(project2)

    results = database.get_projects(include_public=True)

    assert results, "No project was returned"
    assert results[0].name == project2.name, "Project does not match"


def test_add_file(proj_with_files: Project):
    proj_with_files.add_replace_file(data_file="I am new text", folder="foo", filename="file3.txt")

    assert len(proj_with_files.files) == 3


def test_replace_file(proj_with_files: Project):
    proj_with_files.add_replace_file(data_file="I am new text", folder="foo", filename="file.txt")

    assert len(proj_with_files.files) == 2


def test_delete_file(proj_with_files: Project):
    proj_with_files.delete_file(proj_with_files.files[0])

    assert len(proj_with_files.files) == 1


def test_delete_deleted_file(proj_with_files: Project):
    file_ref = proj_with_files.files[0]
    proj_with_files.delete_file(file_ref)

    proj_with_files.delete_file(file_ref)

    assert len(proj_with_files.files) == 1


def test_get_folders_map(proj_with_files: Project):
    file_map = proj_with_files.get_folders_map()

    assert file_map[""] == "Project Root"
    assert file_map["foo/bar"] == "foo - bar"


def test_get_file_tree(proj_with_files: Project):
    file_tree = proj_with_files.get_file_tree()

    assert len(file_tree) == 1
    # assert len(file_tree[0]) == 3
    assert len(file_tree[0]["children"]) == 2


def test_get_files_by_extension(proj_with_files: Project):
    files = proj_with_files.get_files_in_folder(folder="", include_subfolders=True, extensions=["json"])

    assert len(files) == 1
    assert list(files.values())[0].name == "file2.json"


def test_get_files_in_folder(proj_with_many_folders: Project):
    files = proj_with_many_folders.get_files_in_folder(folder="foo/bar", include_subfolders=False, extensions=None)

    assert len(files) == 1
    assert list(files.values())[0].name == "file2.json"


def test_get_file_asc_sorted_files_in_folder(proj_with_many_folders: Project):
    files = proj_with_many_folders.get_files_in_folder(
        folder="/", include_subfolders=True, extensions=None, sort="file-asc"
    )

    assert len(files) == 4
    assert files == ["foo/file1.txt", "foo/bar/file2.json", "baz/foo/bar/file3.json", "file4.txt"]


def test_get_file_desc_sorted_files_in_folder(proj_with_many_folders: Project):
    files = proj_with_many_folders.get_files_in_folder(
        folder="/", include_subfolders=True, extensions=None, sort="file-desc"
    )

    assert len(files) == 4
    assert files == [
        "file4.txt",
        "baz/foo/bar/file3.json",
        "foo/bar/file2.json",
        "foo/file1.txt",
    ]


def test_get_folder_asc_sorted_files_in_folder(proj_with_many_folders: Project):
    files = proj_with_many_folders.get_files_in_folder(
        folder="/", include_subfolders=True, extensions=None, sort="folder-asc"
    )

    assert len(files) == 4
    assert files == [
        "file4.txt",
        "baz/foo/bar/file3.json",
        "foo/file1.txt",
        "foo/bar/file2.json",
    ]


def test_get_folder_desc_sorted_files_in_folder(proj_with_many_folders: Project):
    files = proj_with_many_folders.get_files_in_folder(
        folder="/", include_subfolders=True, extensions=None, sort="folder-desc"
    )

    assert len(files) == 4
    assert files == [
        "foo/bar/file2.json",
        "foo/file1.txt",
        "baz/foo/bar/file3.json",
        "file4.txt",
    ]


def test_add_folders(proj_with_files: Project):
    added_count = proj_with_files.add_folders("test1/test2,test3")

    assert added_count == 3
    assert len(proj_with_files.folders) == 5


def test_add_existing_folders(proj_with_files: Project):
    added_count = proj_with_files.add_folders("foo/bar")

    assert added_count == 0
    assert len(proj_with_files.folders) == 2


def test_move_file_to_path(proj_with_files: Project):
    file = proj_with_files.files[0]

    proj_with_files.move_file_to_path(file, str(file.path.replace(file.name, "renamed.txt")))

    assert proj_with_files.files[0].name == "renamed.txt"


def test_copy_file_to_path(proj_with_files: Project):
    orig_file = proj_with_files.files[0]

    proj_with_files.copy_file_to_path(orig_file, str(orig_file.path.replace(orig_file.name, "copied.txt")))

    assert len(proj_with_files.files) == 3
    assert proj_with_files.files[0].name == orig_file.name
    assert proj_with_files.files[2].name == "copied.txt"


def test_copy_existing_file_to_path(proj_with_files: Project):
    orig_file = proj_with_files.files[0]

    proj_with_files.copy_file_to_path(orig_file, str(orig_file.path.replace(orig_file.name, "copied.txt")))

    proj_with_files.copy_file_to_path(orig_file, str(orig_file.path.replace(orig_file.name, "copied.txt")))

    assert len(proj_with_files.files) == 3
    assert proj_with_files.files[0].name == orig_file.name
    assert proj_with_files.files[2].name == "copied.txt"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "foo",
            2,
        ),
        (
            "foo/bar",
            1,
        ),
        (
            "foo/baz",
            1,
        ),
        (
            "baz",
            1,
        ),
        (
            "blah",
            0,
        ),
        (
            "/",
            0,
        ),
        (
            "",
            0,
        ),
    ],
)
def test_get_subfolders(test_input: str, expected: int, proj_with_many_folders: Project):
    subfolders = proj_with_many_folders.get_subfolders(test_input, include_all=False)

    assert len(subfolders) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "foo",
            5,
        ),
        (
            "foo/bar",
            2,
        ),
        (
            "foo/baz",
            1,
        ),
        (
            "baz",
            2,
        ),
        (
            "blah",
            0,
        ),
        (
            "/",
            0,
        ),
        (
            "",
            0,
        ),
    ],
)
def test_get_all_subfolders(test_input: str, expected: int, proj_with_many_folders: Project):
    subfolders = proj_with_many_folders.get_subfolders(test_input, include_all=True)

    assert len(subfolders) == expected


def test_delete_folders(proj_with_many_folders: Project):
    proj_with_many_folders.delete_folder("foo")

    assert len(proj_with_many_folders.folders) == 3
    assert len(proj_with_many_folders.files) == 2


@pytest.mark.parametrize(
    "from_name, to_name",
    [("foo", "foo2"), ("foo/bar", "foo/bar2"), ("baz", "baz2"), ("foo/bar/baz/qux", "foo/bar/baz/qux2")],
)
def test_rename_folder(from_name: str, to_name: str, proj_with_many_folders: Project):
    # get a count of the sub folders before the rename
    original_count = len(proj_with_many_folders.get_subfolders(from_name, include_all=True))

    proj_with_many_folders.rename_folder(from_name, to_name)

    assert original_count == len(proj_with_many_folders.get_subfolders(to_name, include_all=True))


def test_rename_project(proj_with_many_folders: Project):
    new_name = "renamed_project"

    proj_with_many_folders.rename_project(proj_with_many_folders.name, new_name)

    assert proj_with_many_folders.name == new_name
    for file_ref in proj_with_many_folders.files:
        assert new_name in file_ref.path
