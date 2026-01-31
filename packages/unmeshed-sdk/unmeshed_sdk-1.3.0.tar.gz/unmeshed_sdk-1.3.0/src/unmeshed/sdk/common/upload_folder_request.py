from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class UploadFolderRequest(JSONSerializable):
    folderPath: Optional[str] = None
