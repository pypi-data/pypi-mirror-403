from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

from ...configs.client_config import ClientConfig
from ...logger_config import get_logger
from ...utils.unmeshed_common_utils import UnmeshedCommonUtils

logger = get_logger(__name__)

class HttpRequestFactory:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config
        self.base_url = client_config.get_base_url()
        self.port = client_config.get_port()
        self.bearer_value = f"Bearer client.sdk.{self.client_config.get_client_id()}.{UnmeshedCommonUtils.create_secure_hash(self.client_config.get_auth_token())}"

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.bearer_value,
            "Connection": "keep-alive"
        })
        # noinspection HttpUrlsUsage
        self.session.mount('http://', HTTPAdapter(pool_connections=2, pool_maxsize=10, max_retries=3))
        self.session.mount('https://', HTTPAdapter(pool_connections=2, pool_maxsize=10, max_retries=3))

    def __build_uri(self, path: str) -> str:
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        parsed_url = urlparse(self.base_url)
        has_port = parsed_url.port is not None
        url = f"{self.base_url}/{path}" if has_port or self.base_url.startswith(
            "https:") else f"{self.base_url}:{self.port}/{path}"

        return url

    @staticmethod
    def _augment_exception_with_server_error(exc):
        response = getattr(exc, "response", None)
        if response is None:
            return exc

        server_message = None
        try:
            if response.text:
                payload = response.json()
                server_message = payload.get("errorMessage") or payload.get("message") or payload.get("error")
        except Exception:
            # Fall back to raw text if JSON parsing fails
            server_message = response.text if response is not None else None

        if server_message:
            base_message = str(exc) if exc.args else ""
            detailed_message = f"{base_message} | server_message: {server_message}" if base_message else server_message
            exc.args = (detailed_message,)
        return exc

    def _make_request(self, method, path, params=None, body=None, headers=None, timeout=10):
        uri = self.__build_uri(path)

        request_headers = headers or {}
        if "Content-Type" not in request_headers and (body is not None or method in ("POST", "PUT", "PATCH")):
            request_headers = dict(request_headers)
            request_headers["Content-Type"] = "application/json"

        try:
            response = self.session.request(method, uri, json=body, params=params, headers=request_headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            augmented_exc = self._augment_exception_with_server_error(e)
            response = getattr(e, "response", None)
            if response is not None:
                logger.error(
                    "Request failed [%s %s] status=%s url=%s server_message=%s",
                    method,
                    path,
                    getattr(response, "status_code", None),
                    getattr(response, "url", None),
                    getattr(getattr(augmented_exc, "args", []), "__iter__", lambda: [])().__iter__().__next__() if augmented_exc.args else None,
                )
            else:
                logger.error("Request failed : %s", augmented_exc)
            raise augmented_exc

    def _make_multipart_request(self, method, path, params=None, data=None, files=None, headers=None, timeout=30):
        uri = self.__build_uri(path)
        request_headers = self.session.headers.copy()
        request_headers.pop("Content-Type", None)
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method,
                uri,
                params=params,
                data=data,
                files=files,
                headers=request_headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            augmented_exc = self._augment_exception_with_server_error(e)
            response = getattr(e, "response", None)
            if response is not None:
                logger.error(
                    "Request failed [%s %s] status=%s url=%s server_message=%s",
                    method,
                    path,
                    getattr(response, "status_code", None),
                    getattr(response, "url", None),
                    getattr(getattr(augmented_exc, "args", []), "__iter__", lambda: [])().__iter__().__next__() if augmented_exc.args else None,
                )
            else:
                logger.error("Request failed : %s", augmented_exc)
            raise augmented_exc

    def create_get_request(self, path, params=None):
        return self._make_request("GET", path, params)

    def create_post_request(self, path, params=None, body=None, http_read_timeout=10):
        return self._make_request("POST", path, params, body, timeout=http_read_timeout)

    def create_post_request_with_headers(self, path, params=None, headers=None, body=None, http_read_timeout=10):
        return self._make_request("POST", path, params, body, headers, timeout=http_read_timeout)

    def create_put_request(self, path, params=None, body=None):
        return self._make_request("PUT", path, params, body)

    def create_post_request_with_body(self, path, body=None):
        return self.create_post_request(path, body=body)

    def create_delete_request(self, path, params=None, body=None, http_read_timeout=10):
        return self._make_request("DELETE", path, params, body, timeout=http_read_timeout)

    def create_multipart_post_request(self, path, params=None, data=None, files=None, headers=None, http_read_timeout=30):
        return self._make_multipart_request("POST", path, params=params, data=data, files=files, headers=headers, timeout=http_read_timeout)
