from pydantic import BaseModel


class RedditRequest(BaseModel):
    url: str
    debate_question: str