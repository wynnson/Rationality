import json
import random
import re

from litellm import acompletion
from pathlib import Path
from jinja2 import Template

from enums import Models


SRC_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = SRC_DIR / "agents" / "prompts"


# ================ TEMPLATES ================ #


def load_agent_template(name: str) -> Template:
    return Template((PROMPTS_DIR / f"{name}.md").read_text())


VOTER_TEMPLATE = load_agent_template("vote")
BINARIZER_TEMPLATE = load_agent_template("question_binarizer")
DEBATE_TEMPLATE = load_agent_template("debate")


async def run_voter(
    user: str,
    comment_history: list[str],
    options: dict,
    debate_history: str = "",
):
    """Async runner for each agent.

    Args:
        user: reddit username
        comment_history: user's comment history
        debate_question: user's question
    """
    voter_prompt = VOTER_TEMPLATE.render(
        username=user,
        user_comments="\n".join(comment_history),
    )

    user_prompt = f"""
        Question:
        {options["neutral_question"]}

        Options:
        {json.dumps([options["option_a"], options["option_b"]])}

        Debate history:
        {debate_history or "None"}

        Vote by returning confidence scores and a short reason.
    """

    res = await acompletion(
        model=random.choice(list(Models)),
        messages=[
            {"role": "system", "content": voter_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return user, res


async def run_debater_turn(
    user: str,
    comment_history: list[str],
    neutral_question: str,
    side: str,
    opponent_side: str,
    round_number: int,
    debate_history: str,
) -> tuple[str, str]:
    """Generate one debate turn for a single debater.

    Args:
        user: reddit username
        comment_history: user's comment history
        neutral_question: normalized debate question
        side: side the debater must defend this round
        opponent_side: side defended by the opposing debater
        round_number: current debate round number
        debate_history: prior debate transcript context

    Returns:
        tuple[str, str]: (user, argument text)
    """
    debate_prompt = DEBATE_TEMPLATE.render(
        username=user,
        user_comments="\n".join(comment_history),
    )

    user_prompt = f"""
        Question:
        {neutral_question}

        Your side to defend:
        {side}

        Opponent side:
        {opponent_side}

        Current round:
        {round_number}

        Debate history so far:
        {debate_history or "None"}

        Return JSON with exactly one key: {{"argument": "..."}}
    """

    res = await acompletion(
        model=random.choice(list(Models)),
        messages=[
            {"role": "system", "content": debate_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = res.choices[0].message.content or ""
    payload = parse_model_json(content)

    if isinstance(payload, dict) and isinstance(payload.get("argument"), str):
        return user, payload["argument"].strip()

    return user, content.strip()


async def question_binarizer(debate_question: str) -> dict:
    """Transforms user's debate question into 2 binary options.

    Args:
        debate_question: user query

    Returns:
        dict: {
            neutral_question: ...
            option 1: ...
            option 2: ...
        }
    """
    binarizer_prompt = BINARIZER_TEMPLATE.render()
    res = await acompletion(
        model=random.choice(list(Models)),
        messages=[
            {"role": "system", "content": binarizer_prompt},
            {"role": "user", "content": debate_question},
        ],
    )

    content = res.choices[0].message.content or ""
    return parse_model_json(content)


def parse_model_json(content: str):
    """Removes JSON fences.

    Args:
        content: return from LLM

    Returns:
        object: parsed json content
    """
    content = content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)
