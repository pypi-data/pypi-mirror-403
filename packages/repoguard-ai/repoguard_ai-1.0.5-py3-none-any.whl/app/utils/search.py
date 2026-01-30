from pydantic import BaseModel
from app.utils.cosine import sim_check
from app.services.embedding import embed
from collections import deque
from app.models.chunk import Chunk

def sim_search(query: str, chunks:list[Chunk], k=5):
    #basically call sim_check between query and all chunks one 1 by 1
    checker=[]
    search=[]
    comp=embed([query])[0]
    for chunk in chunks:
        check=sim_check(comp,chunk.embedding)
        checker.append((check,chunk))
    checker.sort(key=lambda x:x[0], reverse=True)

    for i in range(min(k,len(checker))):
        search.append(checker[i][1])
    return search

