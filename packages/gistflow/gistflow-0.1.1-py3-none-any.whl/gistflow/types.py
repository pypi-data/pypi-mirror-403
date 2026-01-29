from dataclasses import dataclass
from typing import Optional, Any, Dict

JsonDict = Dict[str, Any]

@dataclass(frozen=True)
class GistSpec:
    gist_id: str
    filename: str = "state.json"

@dataclass(frozen=True)
class PullResult:
    changed: bool
    etag: Optional[str]
    data: Optional[JsonDict]
