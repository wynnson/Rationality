import asyncio
import json

from services.reddit_service import fetch_users_comment_histories
from utils.agent_utils import question_binarizer, run_voter


async def spawn_debate_agents(url: str, debate_question: str) -> dict:
    """Spawn agents to debate on a question in parallel.

    Args:
        url: reddit post url
        debate_question: question agents are debating on

    Returns:
        dict:
        {
            "option": winning option
            "score": confidence score
        }
    """
    user_comment_histories = await fetch_users_comment_histories(url)
    options = await question_binarizer(debate_question)

    tasks = [
        run_voter(user, comment_history, debate_question, options)
        for user, comment_history in user_comment_histories.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    votes = {}
    for result in results:
        if isinstance(result, Exception):
            continue

        user, res = result
        scores = json.loads(res.choices[0].message.content)
        winning_idx = scores.index(max(scores))

        votes[user] = {
            "option": options[winning_idx],
            "score": scores[winning_idx],
        }

    return votes
