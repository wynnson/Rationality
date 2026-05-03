import asyncio

from services.reddit_service import fetch_users_comment_histories
from utils.agent_utils import (
    parse_model_json,
    question_binarizer,
    run_debater_turn,
    run_voter,
)


DEBATE_ROUNDS = 5


def _build_debate_history(rounds: list[dict]) -> str:
    """Build transcript text from completed debate rounds.

    Args:
        rounds: completed rounds with arguments from both debaters

    Returns:
        str: serialized transcript for model context
    """
    lines = []
    for prior_round in rounds:
        lines.append(
            f"Round {prior_round['round']} | {prior_round['most_confident']['user']} ({prior_round['most_confident']['side']}): {prior_round['most_confident']['argument']}"
        )
        lines.append(
            f"Round {prior_round['round']} | {prior_round['least_confident']['user']} ({prior_round['least_confident']['side']}): {prior_round['least_confident']['argument']}"
        )
    return "\n".join(lines)


def _parse_vote_payload(raw_content: str) -> tuple[list[float], str]:
    """Parse voter json payload into scores and reason.

    Args:
        raw_content: raw model response content

    Returns:
        tuple[list[float], str]: two confidence scores and rationale text
    """
    payload = parse_model_json(raw_content)
    scores = payload.get("scores")
    reason = payload.get("reason", "")
    return scores, reason.strip()


def _vote_from_scores(options: dict, scores: list[float]) -> dict:
    """Build normalized vote object from score list.

    Args:
        options: binary option mapping
        scores: confidence scores aligned to option order

    Returns:
        dict: normalized vote fields with winner metadata
    """
    winning_idx = scores.index(max(scores))
    winning_option = options["option_a"] if winning_idx == 0 else options["option_b"]
    return {
        "option": winning_option,
        "score": scores[winning_idx],
        "winning_idx": winning_idx,
        "scores": scores,
    }


async def _collect_votes(
    options: dict,
    user_comment_histories: dict[str, list[str]],
    debate_history: str = "",
) -> dict[str, dict]:
    """Run all voter agents and collect valid votes.

    Args:
        options: binary option mapping for the question
        user_comment_histories: user histories keyed by username
        debate_history: optional transcript context used for revote

    Returns:
        dict[str, dict]: normalized votes keyed by username
    """
    tasks = [
        run_voter(user, comment_history, options, debate_history)
        for user, comment_history in user_comment_histories.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    votes = {}
    for result in results:
        if isinstance(result, Exception):
            continue

        user, res = result

        try:
            completion = res
            content = completion.choices[0].message.content or ""
            scores, reason = _parse_vote_payload(content)
            vote = _vote_from_scores(options, scores)
            vote["reason"] = reason
            votes[user] = vote
        
        except Exception:
            continue

    return votes


def _pick_debaters(votes: dict[str, dict]) -> tuple[str, str]:
    """pick most and least confident voters.

    Args:
        votes: normalized vote objects keyed by username.

    Returns:
        tuple[str, str]: (most_confident_user, least_confident_user).
    """
    ranked_users = sorted(votes.items(), key=lambda item: item[1]["score"])
    least_confident_user = ranked_users[0][0]
    most_confident_user = ranked_users[-1][0]
    return most_confident_user, least_confident_user


async def _run_debate_rounds(
    options: dict,
    user_comment_histories: dict[str, list[str]],
    most_confident_user: str,
    least_confident_user: str,
    most_side: str,
    least_side: str,
) -> list[dict]:
    """run multi-round debate between selected users.

    Args:
        options: binary option mapping with neutral question.
        user_comment_histories: user histories keyed by username.
        most_confident_user: user arguing their original winning side.
        least_confident_user: user arguing the opposite side.
        most_side: side text assigned to most confident user.
        least_side: side text assigned to least confident user.

    Returns:
        list[dict]: round-by-round debate transcript entries.
    """
    rounds = []

    for round_number in range(1, DEBATE_ROUNDS + 1):
        debate_history = _build_debate_history(rounds)
        debate_tasks = [
            run_debater_turn(
                most_confident_user,
                user_comment_histories.get(most_confident_user, []),
                options["neutral_question"],
                most_side,
                least_side,
                round_number,
                debate_history,
            ),
            run_debater_turn(
                least_confident_user,
                user_comment_histories.get(least_confident_user, []),
                options["neutral_question"],
                least_side,
                most_side,
                round_number,
                debate_history,
            ),
        ]

        turn_results = await asyncio.gather(*debate_tasks, return_exceptions=True)

        most_argument = ""
        least_argument = ""

        for turn in turn_results:
            if isinstance(turn, Exception):
                continue
            if not isinstance(turn, tuple) or len(turn) != 2:
                continue

            speaker, argument = turn
            if speaker == most_confident_user:
                most_argument = argument
            elif speaker == least_confident_user:
                least_argument = argument

        rounds.append(
            {
                "round": round_number,
                "most_confident": {
                    "user": most_confident_user,
                    "side": most_side,
                    "argument": most_argument,
                },
                "least_confident": {
                    "user": least_confident_user,
                    "side": least_side,
                    "argument": least_argument,
                },
            }
        )

    return rounds


async def spawn_debate_agents(url: str, debate_question: str) -> dict:
    """spawn, debate, and revote across reddit-derived agents.

    Args:
        url: reddit post url
        debate_question: question agents are debating on

    Returns:
        dict: options, before/after votes, and debate rounds.
    """
    user_comment_histories = await fetch_users_comment_histories(url)
    options = await question_binarizer(debate_question)

    before_votes = await _collect_votes(options, user_comment_histories)

    if len(before_votes) < 2:
        return {
            "options": options,
            "votes": {
                "before": before_votes,
                "after": {},
            },
            "debate": {
                "rounds": [],
                "error": "Need at least two valid voters to run debate rounds.",
            },
        }

    most_confident_user, least_confident_user = _pick_debaters(before_votes)

    most_side_idx = before_votes[most_confident_user]["winning_idx"]
    least_side_idx = 1 - most_side_idx

    most_side = options["option_a"] if most_side_idx == 0 else options["option_b"]
    least_side = options["option_a"] if least_side_idx == 0 else options["option_b"]

    rounds = await _run_debate_rounds(
        options,
        user_comment_histories,
        most_confident_user,
        least_confident_user,
        most_side,
        least_side,
    )

    full_debate_history = _build_debate_history(rounds)
    after_votes = await _collect_votes(
        options, user_comment_histories, full_debate_history
    )

    return {
        "options": options,
        "votes": {
            "before": before_votes,
            "after": after_votes,
        },
        "debate": {
            "round_count": DEBATE_ROUNDS,
            "most_confident_user": most_confident_user,
            "least_confident_user": least_confident_user,
            "rounds": rounds,
        },
    }
