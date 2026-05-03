from fastapi import APIRouter, HTTPException

from agents.generator import spawn_debate_agents
from schemas.reddit import RedditRequest


router = APIRouter()


@router.post("/debate")
async def get_reddit_post(body: RedditRequest):
    try:
        res = await spawn_debate_agents(body.url, body.debate_question)
        return res
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))