from fastapi import APIRouter, HTTPException

from schemas.reddit import RedditRequest
from services.reddit_service import fetch_reddit_json


router = APIRouter()


@router.post("/reddit")
def get_reddit_post(body: RedditRequest):
    try:
        return fetch_reddit_json(body.url)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch Reddit data")
    
