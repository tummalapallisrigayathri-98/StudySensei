# src/backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from recommend import recommend_items

# ------------------------------------------------------------
# Create FastAPI App
# ------------------------------------------------------------

app = FastAPI(
    title="StudySensi Backend API",
    description="API for recommending next learning items",
    version="1.0.0"
)

# ------------------------------------------------------------
# CORS (required for Streamlit or any web UI)
# ------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # you can lock this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Request Model
# ------------------------------------------------------------

class RequestBody(BaseModel):
    user_id: str
    query: str
    k: int = 5

# ------------------------------------------------------------
# API Endpoint: /api/recommend
# ------------------------------------------------------------

@app.post("/api/recommend")
def recommend_api(body: RequestBody):
    """
    Returns top-k recommended items for a user and query.
    """
    try:
        recs = recommend_items(body.user_id, body.query, body.k)
        return {"recommendations": recs}
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# Health Check (optional)
# ------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "StudySensi backend running!"}
