from pydantic import BaseModel
from typing import Optional

class Chunk(BaseModel):
    authority: str
    heading: str
    content: str
    embedding: Optional[list[float]]=None