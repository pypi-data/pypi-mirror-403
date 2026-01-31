from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class DeleteFileResponse(JSONSerializable):
    message: Optional[str] = None
    errorMessage: Optional[str] = None
    error: Optional[bool] = None
