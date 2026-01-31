from dataclasses import dataclass
from typing import Optional

from .json_decorator import JSONSerializable


@dataclass
class ListFilesRequest(JSONSerializable):
    path: Optional[str] = None
