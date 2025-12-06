# src/backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from recommend import recommend_items

# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------
app = FastAPI(
    title="StudySensi Backend API",
    description="Recommendation Engine for adaptive learning",
    version="1.0.0"
)

# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Request Schema
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
    start = time.time()
    
    try:
        recs = recommend_items(body.user_id, body.query, body.k)
        latency = round((time.time() - start) * 1000, 2)

        logging.info(
            f"/api/recommend OK | {latency} ms | user={body.user_id} | query='{body.query}'"
        )

        return {
            "recommendations": recs,
            "latency_ms": latency
        }

    except Exception as e:
        latency = round((time.time() - start) * 1000, 2)

        logging.error(
            f"/api/recommend ERROR | {latency} ms | user={body.user_id} | error={str(e)}"
        )

        return {
            "error": str(e),
            "latency_ms": latency
        }

# ------------------------------------------------------------
# Health Check
# ------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "StudySensi backend running!"}
