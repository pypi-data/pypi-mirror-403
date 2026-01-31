from dataclasses import dataclass, field
from typing import List, Optional

from .file_entry import FileEntry
from .json_decorator import JSONSerializable


@dataclass
class ListFilesResponse(JSONSerializable):
    currentPath: Optional[str] = None
    entries: List[FileEntry] = field(default_factory=list)
    errorMessage: Optional[str] = None
    error: Optional[bool] = None
