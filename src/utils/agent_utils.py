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


async def run_voter(
    user: str, 
    comment_history: list[str], 
    debate_question: str, 
    options: list
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
        {debate_question}

        Options:
        {json.dumps(options)}

        Vote by returning confidence scores for the options.
    """

    res = await acompletion(
        model=random.choice(list(Models)),
        messages=[
            {"role": "system", "content": voter_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return user, res


async def question_binarizer(debate_question: str) -> list:
    """Transforms user's debate question into 2 binary options.

    Args:
        debate_question: user query

    Returns:
        list: [option 1, option 2]
    """
    binarizer_prompt = BINARIZER_TEMPLATE.render()
    res = await acompletion(
        model=random.choice(list(Models)),
        messages=[
            {"role": "system", "content": binarizer_prompt},
            {"role": "user", "content": debate_question},
        ],
    )

    content = res.choices[0].message.content
    options = parse_model_json(content)
    return [options["option_a"], options["option_b"]]


def parse_model_json(content: str) -> dict:
    """Remove JSON fences
    
    Args:
        content: return from LLM
    
    Returns:
        dict: json content
    """
    content = content.strip()

    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)