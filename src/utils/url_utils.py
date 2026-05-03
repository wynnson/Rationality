from urllib.parse import urlparse


def is_reddit_post_url(url: str) -> bool:
    """Checks if the url is a real reddit url, handing:
        - reddit.com 
        - redd.it (shortener)
        - other domains ending in .reddit.com
    
    Args:
        url: user pasted link
    
    Returns:
        bool: is it a reddit post?
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        path = parsed_url.path
        
        is_reddit = (
            hostname == "reddit.com" or
            hostname == "redd.it" or 
            hostname.endswith(".reddit.com")
        )

        return is_reddit and ("/comments/" in path or hostname == "redd.it")

    except:
        return False


def to_reddit_json_url(url: str) -> str:
    """Convert user's url to json url.
    
    Args:
        url: user's reddit url
    
    Returns:
        str: url with json add-on
    """
    return url + ".json"