"""LangGraph node functions for the skills workflow."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from typing_extensions import TypedDict

from .skill_executor import SkillExecutor
from .skill_registry import SkillRegistry

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# State definition
# ------------------------------------------------------------------

class GraphState(TypedDict):
    messages: list[BaseMessage]
    available_skills: list[dict]
    selected_skills: list[str]
    skill_contexts: dict
    execution_results: dict
    next_action: Optional[str]


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def _get_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(temperature=0)


def _last_human_query(messages: list[BaseMessage]) -> str:
    """Extract the text of the most recent human message."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


# ------------------------------------------------------------------
# Node: analyze_query
# ------------------------------------------------------------------

def analyze_query(state: GraphState, *, registry: SkillRegistry) -> dict[str, Any]:
    """Inspect the latest user message and search for matching skills."""
    query = _last_human_query(state["messages"])
    available = registry.search_skills(query)
    next_action = "select_skills" if available else "respond"
    return {
        "available_skills": available,
        "next_action": next_action,
    }


# ------------------------------------------------------------------
# Node: select_skills
# ------------------------------------------------------------------

_SELECT_SYSTEM = """\
You are a skill router.  Given the user's query and a list of available skills,
choose which skills should be used.  Return ONLY a JSON array of skill name
strings, e.g. ["report_generator"].  If none are appropriate, return [].
Do NOT include any other text, only the JSON array."""


def select_skills(state: GraphState) -> dict[str, Any]:
    """Ask the LLM to pick the most relevant skill(s)."""
    query = _last_human_query(state["messages"])
    skills_desc = json.dumps(state["available_skills"], indent=2)

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=_SELECT_SYSTEM),
        HumanMessage(
            content=f"User query: {query}\n\nAvailable skills:\n{skills_desc}"
        ),
    ])

    try:
        selected = json.loads(response.content)
        if not isinstance(selected, list):
            selected = []
    except (json.JSONDecodeError, TypeError):
        logger.warning("LLM returned non-JSON for skill selection: %s", response.content)
        selected = []

    next_action = "load_skill_context" if selected else "respond"
    return {
        "selected_skills": selected,
        "next_action": next_action,
    }


# ------------------------------------------------------------------
# Node: load_skill_context
# ------------------------------------------------------------------

def load_skill_context(state: GraphState, *, executor: SkillExecutor) -> dict[str, Any]:
    """Read SKILL.md and schema.json for each selected skill."""
    contexts: dict[str, Any] = {}
    for skill_name in state["selected_skills"]:
        contexts[skill_name] = executor.load_skill_context(skill_name)
    return {
        "skill_contexts": contexts,
        "next_action": "execute_skills",
    }


# ------------------------------------------------------------------
# Node: execute_skills
# ------------------------------------------------------------------

_PARAMS_SYSTEM = """\
You are a skill parameter extractor.  Given the skill documentation, its JSON
schema (if any), and the user's request, produce ONLY a JSON object with the
parameters needed to call the skill.  Do NOT include any other text."""


def execute_skills(
    state: GraphState,
    *,
    executor: SkillExecutor,
) -> dict[str, Any]:
    """For each selected skill, let the LLM produce params then execute."""
    query = _last_human_query(state["messages"])
    results: dict[str, Any] = {}
    llm = _get_llm()

    for skill_name in state["selected_skills"]:
        ctx = state["skill_contexts"].get(skill_name, {})
        skill_doc = ctx.get("skill_doc") or "(no documentation)"
        schema = json.dumps(ctx.get("schema")) if ctx.get("schema") else "(no schema)"

        # Ask LLM to produce execution parameters
        response = llm.invoke([
            SystemMessage(content=_PARAMS_SYSTEM),
            HumanMessage(
                content=(
                    f"User request: {query}\n\n"
                    f"Skill documentation:\n{skill_doc}\n\n"
                    f"Parameter schema:\n{schema}"
                )
            ),
        ])

        try:
            params = json.loads(response.content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse params for %s: %s", skill_name, response.content)
            params = {}

        result = executor.execute_skill(skill_name, params)
        results[skill_name] = result

    return {
        "execution_results": results,
        "next_action": "respond",
    }


# ------------------------------------------------------------------
# Node: respond
# ------------------------------------------------------------------

_RESPOND_SYSTEM = """\
You are a helpful assistant.  Use the skill execution results (if any) to
craft a clear, informative response to the user's request.  If no skills were
executed, answer the query directly using your own knowledge."""


def respond(state: GraphState) -> dict[str, Any]:
    """Generate a final natural-language response."""
    query = _last_human_query(state["messages"])
    exec_results = state.get("execution_results") or {}

    context_parts: list[str] = []
    if exec_results:
        for skill_name, result in exec_results.items():
            context_parts.append(
                f"--- {skill_name} result ---\n{json.dumps(result, indent=2)}"
            )

    context_block = "\n\n".join(context_parts) if context_parts else "(no skill results)"

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=_RESPOND_SYSTEM),
        HumanMessage(
            content=(
                f"User request: {query}\n\n"
                f"Skill execution results:\n{context_block}"
            )
        ),
    ])

    new_messages = list(state["messages"]) + [AIMessage(content=response.content)]
    return {
        "messages": new_messages,
        "next_action": None,
    }


# ------------------------------------------------------------------
# Router
# ------------------------------------------------------------------

def route_next(state: GraphState) -> str:
    """Return the next node name based on ``state['next_action']``."""
    return state.get("next_action") or "respond"
