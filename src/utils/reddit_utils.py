import random
import re
import requests
import time


URL_RE = re.compile(r"https?://\S+")
MAX_USERS = 10
MAX_COMMENTS = 20
MAX_RETRY = 2


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
        not reddit_json or 
        len(reddit_json) < 2 or
        not reddit_json[1]["data"]["children"]
    ):
        return []

    comments = reddit_json[1]["data"]["children"]
    authors = set(dfs_comments(comments))
    return list(authors)


def get_random_user_comments(authors: list) -> dict[list[str]]:
    """Gets random users and their comments from authors list.

    Args:
        authors: author list

    Returns:
        dict[list[str]]: {"user": [history] pairs}
    """
    if not authors:
        return {}

    random.shuffle(authors)
    users_comment_histories = {}
    
    for user in authors[:MAX_USERS]:
        try:
            res = get_user_comments(user)
            res.raise_for_status()
            profile = res.json()
            comments = profile["data"]["children"]
            
            if not comments:
                continue
            
            history = []
            for comment in comments:
                if len(history) > MAX_COMMENTS:
                    break
                
                body = comment["data"]["body"]
                contains_media = check_body_media(body)

                if contains_media:
                    continue

                history.append(body.strip())

            users_comment_histories[user] = history
        
        except Exception:
            time.sleep(5)
            continue
    
    return users_comment_histories


def get_user_comments(user: str):
    """Grabs user comments.

    Args:
        user: reddit username

    Returns:
        Returns payload
    """
    res = None

    for _ in range(MAX_RETRY):
        query_url = f"https://www.reddit.com/user/{user}.json"
        res = requests.get(query_url, timeout=60)

        if res.status_code != 429:
            return res
        
        time.sleep(2)  # backoff

    return res

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