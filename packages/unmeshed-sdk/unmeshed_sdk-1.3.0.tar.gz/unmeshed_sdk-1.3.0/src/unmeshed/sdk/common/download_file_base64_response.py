from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class DownloadFileBase64Response(JSONSerializable):
    fileName: Optional[str] = None
    fileSize: Optional[int] = None
    contentBase64: Optional[str] = None
    errorMessage: Optional[str] = None
    error: Optional[bool] = None
