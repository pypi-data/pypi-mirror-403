from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class UploadFileResponse(JSONSerializable):
    status: Optional[str] = None
    filePath: Optional[str] = None
    fileName: Optional[str] = None
    errorMessage: Optional[str] = None
    error: Optional[bool] = None
