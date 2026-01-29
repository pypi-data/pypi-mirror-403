from datetime import datetime  # noqa: F401
from typing import List  # noqa: UP035

from pydantic import BaseModel


class MemoryCreate(BaseModel):
    content: str
    tags: List[str] = []  # noqa: UP006

class Memory(BaseModel):
    id: str
    content: str
    tags: List[str] = []# noqa: UP006
    created_at: str

class SearchResult(BaseModel):
    id: str
    content: str
    tags: List[str] # noqa: UP006
    created_at: str
    distance: float
