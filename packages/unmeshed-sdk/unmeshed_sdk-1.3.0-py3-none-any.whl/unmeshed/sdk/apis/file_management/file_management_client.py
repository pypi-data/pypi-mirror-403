import json
import os
from dataclasses import asdict, fields
from typing import TypeVar, Type

import requests

from ..http.http_client_factory import HttpClientFactory
from ..http.http_request_factory import HttpRequestFactory
from ...common.file_entry import FileEntry
from ...common.list_files_request import ListFilesRequest
from ...common.list_files_response import ListFilesResponse
from ...common.download_file_base64_response import DownloadFileBase64Response
from ...common.download_file_request import DownloadFileRequest
from ...common.delete_file_request import DeleteFileRequest
from ...common.delete_file_response import DeleteFileResponse
from ...common.upload_file_response import UploadFileResponse
from ...common.upload_folder_request import UploadFolderRequest
from ...configs.client_config import ClientConfig
from ...logger_config import get_logger

logger = get_logger(__name__)


class FileManagementClient:
    def __init__(self, http_client_factory: HttpClientFactory, http_request_factory: HttpRequestFactory,
                 client_config: ClientConfig):
        self.client_config = client_config
        self.__http_client = http_client_factory.create()
        self.http_request_factory = http_request_factory
        self.__files_url = "api/files/"

    T = TypeVar('T')

    @staticmethod
    def dict_to_dataclass(data: dict, dataclass_type: Type[T]) -> T:
        valid_fields = {f.name for f in fields(dataclass_type)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return dataclass_type(**filtered_data)

    def __populate_file_entry(self, entry_json) -> FileEntry:
        return self.dict_to_dataclass(entry_json or {}, FileEntry)

    def __populate_list_files_response(self, response_json) -> ListFilesResponse:
        entries_json = response_json.get("entries") or []
        entries = [self.__populate_file_entry(entry_json) for entry_json in entries_json]
        list_files_response_json = dict(response_json)
        list_files_response_json["entries"] = entries
        return self.dict_to_dataclass(list_files_response_json, ListFilesResponse)

    def __populate_upload_file_response(self, response_json) -> UploadFileResponse:
        return self.dict_to_dataclass(response_json or {}, UploadFileResponse)

    def __populate_download_file_base64_response(self, response_json) -> DownloadFileBase64Response:
        return self.dict_to_dataclass(response_json or {}, DownloadFileBase64Response)

    def __populate_delete_file_response(self, response_json) -> DeleteFileResponse:
        return self.dict_to_dataclass(response_json or {}, DeleteFileResponse)

    def view_files(self, list_files_request: ListFilesRequest) -> ListFilesResponse:
        if list_files_request is None:
            raise ValueError("ListFilesRequest cannot be None")

        params = {}
        json_body = asdict(list_files_request)  # type: ignore

        try:
            response = self.http_request_factory.create_post_request(
                self.__files_url + "view",
                params=params,
                body=json_body
            )
            if response.status_code != 200:
                raise RuntimeError("Failed to view files " + response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred while fetching files: %s", http_err)
            raise RuntimeError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error("Request error occurred while fetching files: %s", req_err)
            raise RuntimeError(f"Request error: {req_err}") from req_err
        except Exception as e:
            logger.error("An unexpected error occurred while fetching files: %s", e)
            raise RuntimeError(f"Unexpected error: {e}") from e

        try:
            response_json = json.loads(response.text)
            return self.__populate_list_files_response(response_json)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def delete_file(self, delete_file_request: DeleteFileRequest, http_read_timeout: int = 120) -> DeleteFileResponse:
        if delete_file_request is None:
            raise ValueError("DeleteFileRequest cannot be None")
        if not delete_file_request.path or not delete_file_request.path.strip():
            raise ValueError("DeleteFileRequest.path cannot be empty")

        body = asdict(delete_file_request)  # type: ignore
        response = self.http_request_factory.create_delete_request(
            self.__files_url + "delete",
            params={},
            body=body,
            http_read_timeout=http_read_timeout,
        )
        try:
            response_json = json.loads(response.text)
            delete_response = self.__populate_delete_file_response(response_json)
            if delete_response.error:
                raise RuntimeError(delete_response.errorMessage or "File delete failed.")
            return delete_response
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def upload_file(self, file_path: str, folder_path: str = "/", custom_file_name: str = None,
                    http_read_timeout: int = 120) -> UploadFileResponse:
        if not file_path:
            raise ValueError("file_path cannot be empty")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")

        resolved_folder_path = folder_path.strip() if folder_path else "/"
        resolved_folder_path = resolved_folder_path or "/"
        file_name = custom_file_name.strip() if custom_file_name else os.path.basename(file_path)
        if not file_name:
            raise ValueError("File name must not be empty.")

        with open(file_path, "rb") as file_obj:
            files = {"file": (file_name, file_obj)}

            params = {"folderPath": resolved_folder_path}
            if custom_file_name:
                params["customFileName"] = file_name

            response = self.http_request_factory.create_multipart_post_request(
                self.__files_url + "upload",
                params=params,
                data=None,
                files=files,
                headers={},
                http_read_timeout=http_read_timeout
            )

        try:
            response_json = json.loads(response.text)
            upload_response = self.__populate_upload_file_response(response_json)
            if upload_response.error:
                raise RuntimeError(upload_response.errorMessage or "File upload failed.")
            return upload_response
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err

    def download_file(self, download_file_request: DownloadFileRequest, http_read_timeout: int = 120) -> bytes:
        if download_file_request is None:
            raise ValueError("DownloadFileRequest cannot be None")
        if not download_file_request.path or not download_file_request.path.strip():
            raise ValueError("DownloadFileRequest.path cannot be empty")

        body = asdict(download_file_request)  # type: ignore
        response = self.http_request_factory.create_post_request(
            self.__files_url + "download",
            params={},
            body=body,
            http_read_timeout=http_read_timeout,
        )
        return response.content

    def upload_folder(self, upload_folder_request: UploadFolderRequest, http_read_timeout: int = 120) -> dict:
        if upload_folder_request is None:
            raise ValueError("UploadFolderRequest cannot be None")
        if not upload_folder_request.folderPath or not upload_folder_request.folderPath.strip():
            raise ValueError("UploadFolderRequest.folderPath cannot be empty")

        body = asdict(upload_folder_request)  # type: ignore
        response = self.http_request_factory.create_post_request(
            self.__files_url + "uploadFolder",
            params={},
            body=body,
            http_read_timeout=http_read_timeout,
        )
        try:
            response_json = json.loads(response.text)
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err
        return response_json

    def download_file_base64(self, download_file_request: DownloadFileRequest, http_read_timeout: int = 120) -> DownloadFileBase64Response:
        if download_file_request is None:
            raise ValueError("DownloadFileRequest cannot be None")
        if not download_file_request.path or not download_file_request.path.strip():
            raise ValueError("DownloadFileRequest.path cannot be empty")

        body = asdict(download_file_request)  # type: ignore
        response = self.http_request_factory.create_post_request(
            self.__files_url + "downloadBase64",
            params={},
            body=body,
            http_read_timeout=http_read_timeout,
        )
        try:
            response_json = json.loads(response.text)
            download_response = self.__populate_download_file_base64_response(response_json)
            if download_response.error:
                raise RuntimeError(download_response.errorMessage or "Download (base64) failed.")
            return download_response
        except json.JSONDecodeError as json_err:
            logger.error("Failed to parse the response JSON: %s", json_err)
            raise RuntimeError(f"Failed to parse response JSON: {json_err}") from json_err
