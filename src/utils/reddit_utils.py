import asyncio
import httpx
import random
import re


URL_RE = re.compile(r"https?://\S+")
MAX_USERS = 20
MAX_COMMENTS = 20
MAX_RETRY = 2
MAX_CONCURRENCY = 3
HEADERS = {"User-Agent": "RationalityBot/1.0 (by u/your_reddit_username)"}


def dfs_comments(comments):
    """Traverse the Reddit comment tree.

    Args:
        comments: json object of comments
    """
    stack = list(comments)

    while stack:
        item = stack.pop()

        kind = item.get("kind")
        data = item.get("data", {})

        if kind == "more":
            continue

        if data.get("stickied"):
            continue

        author = data.get("author")
        if author and author != "[deleted]":
            yield author

        replies = data.get("replies")

        if isinstance(replies, dict):
            reply_children = replies["data"]["children"]
            stack.extend(reply_children)


def get_authors(reddit_json) -> list:
    """Gets the authors from a post.

    Args:
        reddit_json: json object returned by reddit post

    Returns:
        list: list of authors
    """
    if (
        not reddit_json
        or len(reddit_json) < 2
        or not reddit_json[1]["data"]["children"]
    ):
        return []

    comments = reddit_json[1]["data"]["children"]
    authors = set(dfs_comments(comments))
    return list(authors)


async def get_random_user_comments(authors: list) -> dict[str, list[str]]:
    """Gets random users and their comments from authors list.

    Args:
        authors: author list

    Returns:
        dict[list[str]]: {"user": [history] pairs}
    """
    if not authors:
        return {}

    random.shuffle(authors)
    selected_users = authors[:MAX_USERS]
    users_comment_histories = {}

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = [_fetch_user_history(client, semaphore, user) for user in selected_users]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception) or result is None:
            continue

        user, history = result
        users_comment_histories[user] = history

    return users_comment_histories


async def _fetch_user_history(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    user: str,
) -> tuple[str, list[str]] | None:
    """Fetch and filter one user's recent comment history

    Args:
        client: shared async HTTP client for Reddit requests
        semaphore: concurrency limiter for outbound user profile calls
        user: reddit username

    Returns:
        tuple[str, list[str]] | None: 
        - (user, history) when comments are available after filtering links/media
        - otherwise None
    """
    async with semaphore:
        res = await get_user_comments(client, user)
        if res is None:
            return None

        res.raise_for_status()
        profile = res.json()
        comments = profile["data"]["children"]

        if not comments:
            return None

        history = []
        for comment in comments:
            if len(history) >= MAX_COMMENTS:
                break

            body = comment["data"].get("body", "")
            contains_media = check_body_media(body)

            if contains_media:
                continue

            history.append(body.strip())

        return user, history


async def get_user_comments(client: httpx.AsyncClient, user: str):
    """Grabs user comments.

    Args:
        user: reddit username

    Returns:
        Returns payload
    """
    for attempt in range(MAX_RETRY):
        query_url = f"https://www.reddit.com/user/{user}.json"
        res = await client.get(query_url, headers=HEADERS)

        if res.status_code != 429:
            return res

        await asyncio.sleep(2 ** (attempt + 1))

    return None


def check_body_media(body: str) -> bool:
    """Checks for any media / links.

    Args:
        body: user comment body

    Returns:
        bool: contains media?
    """
    if URL_RE.search(body):
        return True

    return False