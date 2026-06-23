"""
Prompt builder.

Renders structured LLM prompts from user preferences and candidate
restaurant data for the Groq API.
"""

from __future__ import annotations

import json
from typing import List

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.candidate_mapper import restaurants_to_dtos


_SYSTEM_PROMPT = """\
You are a concise restaurant recommendation assistant.
You will receive a JSON list of candidate restaurants and a set of user preferences.
Your task is to select the top {top_k} restaurants that best match the user's preferences,
rank them from best to worst, and provide a brief 1–2 sentence explanation for each choice.

Respond ONLY with valid JSON matching this schema:
{{
  "summary": "<one paragraph overall summary>",
  "recommendations": [
    {{
      "id": "<restaurant id from candidates>",
      "rank": <int>,
      "name": "<restaurant name>",
      "cuisine": "<cuisines>",
      "rating": <float|null>,
      "estimated_cost": <int|null>,
      "explanation": "<why this pick>"
    }}
  ]
}}
Do NOT include any text outside the JSON object.
"""

_USER_TEMPLATE = """\
<user_preferences>
  Location: {location}
  Budget: {budget}
  Minimum Rating: {min_rating}
  Cuisine: {cuisine}
  Additional: {additional}
</user_preferences>

<candidates>
{candidates_json}
</candidates>
"""


def build_system_prompt() -> str:
    """Return the system-level prompt instructing the LLM on output format."""
    return _SYSTEM_PROMPT.format(top_k=settings.top_k_recommendations)


def build_user_prompt(
    prefs: UserPreferences,
    candidates: List[Restaurant],
) -> str:
    """Render the user message containing preferences and candidate data.

    Args:
        prefs: Validated user preferences.
        candidates: Pre-filtered restaurant candidates.

    Returns:
        A formatted string for the user role in the chat completion.
    """
    dtos = restaurants_to_dtos(candidates)

    return _USER_TEMPLATE.format(
        location=prefs.location,
        budget=prefs.budget,
        min_rating=prefs.min_rating,
        cuisine=prefs.cuisine or "Any",
        additional=prefs.additional or "None",
        candidates_json=json.dumps(dtos, indent=2),
    )

