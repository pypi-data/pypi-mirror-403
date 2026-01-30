from typing import Union,Optional
from pydantic import BaseModel
from fastapi import FastAPI
from app.services.chunking import chunker
from app.services.embedding import embed
from app.db import init_db
from app.utils.store import store_chunks
from app.services.embedding import embed
from app.models.chunk import Chunk
from app.db import get_conn
from app.services.validator import run_validate
import os
import psycopg2

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


class AnalyzeReq(BaseModel):
    repo_id:str
    readme:str
    docs:str
    code_of_conduct:Optional[str]= None
    
@app.post("/analyze")
def analyze(req:AnalyzeReq):
    connect=get_conn()
    all_chunks:list[Chunk]=[]

    readme_chunks=chunker(req.readme,authority="README")
    contributing_chunks=chunker(req.docs,authority="CONTRIBUTING")
    coc_chunks:list[Chunk]=[]

    if(req.code_of_conduct):
        coc_chunks=chunker(req.code_of_conduct,authority="CODE OF CONDUCT")
    
    all_chunks.extend(readme_chunks)
    all_chunks.extend(contributing_chunks)
    if(len(coc_chunks)):
        all_chunks.extend(coc_chunks)

    #initialise db
    init_db()

    #embed chunk
    embeddings = embed([c.content for c in all_chunks])
    for chunk, emb in zip(all_chunks, embeddings):
      chunk.embedding = emb

    #store chunks
    store_chunks(connect,req.repo_id,all_chunks)

class ValidateReq(BaseModel):
    repo_id:str
    diff:str

@app.post("/validate")
def validate(req:ValidateReq):
    connect=get_conn()
    return run_validate(
        repo_id=req.repo_id,
        diff=req.diff,
        connect=connect
    )

