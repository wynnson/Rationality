from pydantic import BaseModel


class RedditRequest(BaseModel):
    url: str