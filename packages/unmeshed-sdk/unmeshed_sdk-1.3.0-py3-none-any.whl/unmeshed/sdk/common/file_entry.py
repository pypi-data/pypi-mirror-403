from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class FileEntry(JSONSerializable):
    name: Optional[str] = None
    path: Optional[str] = None
    folder: Optional[bool] = None
    size: Optional[int] = None
    lastModified: Optional[str] = None
    fileExtension: Optional[str] = None
