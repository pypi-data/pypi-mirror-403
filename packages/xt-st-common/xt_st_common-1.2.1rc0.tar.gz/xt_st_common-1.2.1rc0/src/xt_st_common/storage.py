import logging
import mimetypes
import os
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional, Union

import streamlit as st
from minio import Minio
from minio.commonconfig import CopySource
from minio.credentials import IamAwsProvider
from minio.credentials.providers import StaticProvider
from minio.error import MinioException
from minio.helpers import ObjectWriteResult
from pydantic import BaseModel

from xt_st_common.config import StorageType, StreamlitBaseSettings

from .utils import sizeof_fmt

settings = StreamlitBaseSettings()


class FileRef(BaseModel):
    size: Optional[str]  # e.g. '3 KB'
    size_bytes: Optional[int]
    url: Optional[str] = None  # download url
    gs_uri: Optional[str] = None  # GSC Uri
    path: str  # path to current item (e.g. /folder1/someFile.txt)

    name: str
    content_type: Optional[str]

    def set_size(self, _bytes: int):
        self.size = sizeof_fmt(_bytes)
        self.size_bytes = _bytes

    def get_root(self):
        return "/".join(self.path.split("/")[:2])

    def get_prefix(self):
        return self.path.rsplit("/", 1)[0]

    def get_folder(self):
        return self.path.rsplit("/", 2)[1]

    def get_user_folders(self):
        """Get all the folders between the project root and the filename.

        Returns:
            str: User folders separated by "/"
        """
        folders = self.path.split("/")

        if len(folders) < 3:
            return ""

        return "/".join(folders[2:-1])

    def get_suffix(self):
        return self.path.split(self.get_prefix())[1]

    def get_ext(self):
        parts = self.name.rsplit(".", 1)
        return None if len(parts) <= 1 else f"{parts[-1]}"


class StorageClient(ABC):
    @abstractmethod
    def write_file(self, file_path: str, file_data: str, content_type="text/plain") -> FileRef:
        pass

    @abstractmethod
    def get_file(self, file_name):
        pass

    @abstractmethod
    def delete_file(self, file_name):
        pass

    @abstractmethod
    def list_files(self, path_prefix=""):
        pass

    @abstractmethod
    def file_exists(self, file_path: str):
        pass

    @abstractmethod
    def copy_file(
        self,
        file_path: str,
        new_file_path: str,
        delete_original: bool = False,
    ):
        pass


class MinioStorageClient(StorageClient):
    def __init__(
        self,
        bucket: str,
        endpoint="s3.amazonaws.com",
        credentials=IamAwsProvider(),
        secure=True,
    ):
        if not bucket:
            raise ValueError("bucket name must be set")

        self.__bucket = bucket
        # Check environment variables have been set
        if isinstance(credentials, IamAwsProvider):
            for var in ["AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_REGION", "AWS_ROLE_ARN"]:
                if os.environ.get(var) is None or len(str(os.environ.get(var))) <= 0:
                    raise ValueError("Environment Variable {var} missing")

        # Create the Minio Client
        __client = Minio(endpoint, credentials=credentials, secure=secure)
        exists = __client.bucket_exists(bucket)
        if not exists:
            __client.make_bucket(bucket)
            logging.info(f"Minio Bucket created: {bucket}")

        self.__client = __client

    @classmethod
    def object_to_file(
        cls,
        obj: ObjectWriteResult,
        file_length: int = 0,
        content_type: str = "text/plain",
    ) -> FileRef:
        path = obj.object_name
        path_segments = path.split("/")
        name = path_segments[-1]

        return FileRef(
            url=obj.bucket_name + obj.object_name,
            size=sizeof_fmt(file_length),
            size_bytes=file_length,
            path=path,
            name=name,
            content_type=content_type,
        )

    def write_file(self, file_path: str, file_data: Union[str, bytes], content_type=None) -> Optional[FileRef]:
        if isinstance(file_data, str):
            file_bytes = BytesIO(file_data.encode("utf-8"))
            file_len = len(file_data)
            # print(f"STR: {file_len}; {file_data}")
        elif isinstance(file_data, BytesIO):
            file_bytes: BytesIO = file_data
            file_len = file_bytes.getbuffer().nbytes
            # print(f"BytesIO: {file_len}")
        else:
            file_bytes = BytesIO(file_data)
            file_len = len(file_data)

        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0]

        # set MIME_TYPE for MSCL/GeoTek files
        if content_type is None and file_path.lower().endswith((".cal", ".out", ".raw", ".sbd", ".xrf")):
            content_type = "text/plain"

        obj = self.__client.put_object(self.__bucket, file_path, file_bytes, file_len, content_type=content_type)
        return self.object_to_file(obj, file_len, content_type)

    def copy_file(
        self,
        file_path: str,
        new_file_path: str,
        content_type,
        size_bytes: int,
        delete_original: bool = False,
    ) -> Optional[FileRef]:
        obj = self.__client.copy_object(self.__bucket, new_file_path, CopySource(self.__bucket, file_path))

        new_file_ref = self.object_to_file(obj, file_length=size_bytes, content_type=content_type)

        if delete_original:
            self.delete_file(file_path)

        return new_file_ref

    def get_file(self, file_path: str):
        response_data = None
        try:
            response = self.__client.get_object(self.__bucket, file_path)
            # Read data from response.
            response_data = BytesIO(response.read())
            response_data.name = file_path
        finally:
            response.close()
            response.release_conn()

        return response_data

    def delete_file(self, file_path: str):
        self.__client.remove_object(self.__bucket, file_path)

    def list_files(self, path_prefix="", recursive=True):
        return self.__client.list_objects(self.__bucket, prefix=path_prefix, recursive=recursive)

    def file_exists(self, file_path: str):
        try:
            stats = self.__client.stat_object(self.__bucket, file_path)
            return stats is not None
        except MinioException as err:
            if hasattr(err, "code") and err.code == "NoSuchKey":
                return False
            logging.error(str(err))
            raise err


@st.cache_resource()
def storage_client():
    if settings.STORAGE_TYPE not in [StorageType.MINIO, StorageType.MINIO_AWS]:
        raise ValueError("STORAGE_TYPE may not be blank when using the storage_client")
    if settings.BUCKET_NAME is None:
        raise ValueError("BUCKET_NAME may not be blank!")
    if settings.STORAGE_TYPE == StorageType.MINIO_AWS:
        return MinioStorageClient(settings.BUCKET_NAME)  # type: ignore
    if settings.STORAGE_TYPE == StorageType.MINIO:
        if settings.MINIO_ENDPOINT is None:
            raise ValueError("MINIO_ENDPOINT may not be blank!")
        if settings.MINIO_SECRET_KEY is None:
            raise ValueError("MINIO_SECRET_KEY may not be blank!")
        if settings.MINIO_ACCESS_KEY is None:
            raise ValueError("MINIO_ACCESS_KEY may not be blank!")
        return MinioStorageClient(
            settings.BUCKET_NAME,
            endpoint=settings.MINIO_ENDPOINT,
            credentials=StaticProvider(settings.MINIO_ACCESS_KEY, settings.MINIO_SECRET_KEY.get_secret_value()),
            secure=settings.MINIO_HTTPS,
        )
    raise NotImplementedError(f"Storage Type {settings.STORAGE_TYPE} not supported")
