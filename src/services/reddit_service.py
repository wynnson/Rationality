import requests

from utils.url_utils import is_reddit_post_url, to_reddit_json_url
from utils.reddit_utils import get_authors, get_random_user_comments


def fetch_reddit_json(url: str):
    """Get user histories.
    
    Args:
        url: reddit post url

    Returns:
        JSON object of random users and comment histories.
    """
    if not is_reddit_post_url(url):
        raise ValueError("Invalid Reddit URL")
    
    json_url = to_reddit_json_url(url)

    res = requests.get(json_url, timeout=60)
    res.raise_for_status()

    authors = get_authors(res.json())
    user_comment_histories = get_random_user_comments(authors)
    return user_comment_histories