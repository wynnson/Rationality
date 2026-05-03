import asyncio

import httpx

from utils.url_utils import is_reddit_post_url, to_reddit_json_url
from utils.reddit_utils import get_authors, get_random_user_comments


HEADERS = {"User-Agent": "Rationality/1.0"}
BACKOFF_SECONDS = (1, 2, 4, 8)


async def fetch_users_comment_histories(url: str) -> dict:
    """
    Get users comment histories.

    Args:
        url: reddit post url

    Returns:
        dict of random users and comment histories: {"user": [history]}
    """
    if not is_reddit_post_url(url):
        raise ValueError("Invalid Reddit URL")

    json_url = to_reddit_json_url(url)

    res = None

    async with httpx.AsyncClient(timeout=60) as client:
        for delay in BACKOFF_SECONDS:
            res = await client.get(json_url, headers=HEADERS)

            if res.status_code != 429:
                res.raise_for_status()
                break

            await asyncio.sleep(delay)

        else:
            raise httpx.HTTPStatusError(
                f"429 Client Error: Too Many Requests for url: {json_url}",
                request=res.request,
                response=res,
            )

    authors = get_authors(res.json())
    user_comment_histories = await get_random_user_comments(authors)
    return user_comment_histories