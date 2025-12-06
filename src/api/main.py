# src/api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import json
from recommender.baselines import MostPopular
from recommender.persistence import Persistence


app = FastAPI(title="StudySensi Recommender API")


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
SAMPLE_INTERACTIONS = os.path.join(DATA_PATH, 'sample_interactions.csv')


# Initialize simple persistence & recommender
p = Persistence(interactions_path=SAMPLE_INTERACTIONS)
recommender = MostPopular(p)


# Simple in-memory items metadata (toy). In real project, move to DB
ITEMS = {
"i1": {"title": "Intro to Python", "type": "course", "tags": ["python","basics"]},
"i2": {"title": "Data Structures - Exercises", "type": "exercise", "tags": ["algorithms","ds"]},
"i3": {"title": "Machine Learning Foundations", "type": "course", "tags": ["ml","basics"]},
"i4": {"title": "Reinforcement Learning - Overview", "type": "course", "tags": ["rl"]}
}


class RecoRequest(BaseModel):
user_id: str
query: Optional[str] = None
context: Optional[Dict[str, Any]] = None
k: Optional[int] = 5


class LogEvent(BaseModel):
user_id: str
item_id: str
event_type: str
timestamp: str


@app.post('/api/recommend')
def recommend(req: RecoRequest):
# For MVP: use simple MostPopular recommender with optional topic filtering
candidates = recommender.get_top_k(k=req.k)


# If query contains a tag (simple matching), boost items with matching tags
if req.query:
q = req.query.lower()
boosted = []
for it in candidates:
tags = ITEMS.get(it, {}).get('tags', [])
if any(q in t for t in tags) or q in ITEMS.get(it, {}).get('title','').lower():
boosted.append(it)
# put boosted first, preserve order
final = boosted + [x for x in candidates if x not in boosted]
else:
final = candidates


results = []
for item_id in final[:req.k]:
uvicorn.run('src.api.main:app', host='0.0.0.0', port=8000, reload=True)
