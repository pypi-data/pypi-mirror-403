# repoguard/run.py
import requests
from app.models.validation import Validation
import os
from repoguard.repo import get_repo_id
from repoguard.docs import load_repo_docs

REPOGUARD_API =  "https://repoguard-lp49.onrender.com"

def analyze_remote():
    repo_id = get_repo_id()
    readme, docs, coc = load_repo_docs()

    resp = requests.post(
        f"{REPOGUARD_API}/analyze",
        json={
            "repo_id": repo_id,
            "readme": readme,
            "docs": docs,
            "code_of_conduct": coc,
        },
        timeout=60,
    )
    resp.raise_for_status()

def validate_remote(diff: str) -> Validation:
    repo_id = get_repo_id()

    payload = {
        "repo_id": repo_id,
        "diff": diff,
    }

    resp = requests.post(
        f"{REPOGUARD_API}/validate",
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return Validation.model_validate(resp.json())

