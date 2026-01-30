from pydantic import BaseModel
from typing import List

class ViolatedGuidelines(BaseModel):
    authority:str
    heading:str
    reason:str

class Validation(BaseModel):
    status:str
    explanation:str
    violated_guidelines: list[ViolatedGuidelines]
