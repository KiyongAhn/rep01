"""Assembles the LangGraph skills workflow."""

from __future__ import annotations

import functools
from typing import Optional

from langgraph.graph import END, StateGraph

from .nodes import (
    GraphState,
    analyze_query,
    execute_skills,
    load_skill_context,
    respond,
    route_next,
    select_skills,
)
from .skill_executor import SkillExecutor
from .skill_registry import SkillRegistry


def create_skills_graph(
    skills_base_path: Optional[str] = None,
) -> StateGraph:
    """Build and compile the skills agent graph.

    Parameters
    ----------
    skills_base_path:
        Root directory containing skill sub-directories.
        Forwarded to :class:`SkillRegistry`.

    Returns
    -------
    A compiled LangGraph :class:`StateGraph` ready for ``.invoke()``.
    """
    registry = SkillRegistry(base_path=skills_base_path)
    executor = SkillExecutor(registry)

    # Bind dependencies via functools.partial so nodes stay pure functions
    _analyze = functools.partial(analyze_query, registry=registry)
    _load_ctx = functools.partial(load_skill_context, executor=executor)
    _execute = functools.partial(execute_skills, executor=executor)

    workflow = StateGraph(GraphState)

    # -- Add nodes --
    workflow.add_node("analyze", _analyze)
    workflow.add_node("select_skills", select_skills)
    workflow.add_node("load_skill_context", _load_ctx)
    workflow.add_node("execute_skills", _execute)
    workflow.add_node("respond", respond)

    # -- Entry point --
    workflow.set_entry_point("analyze")

    # -- Edges --
    workflow.add_conditional_edges(
        "analyze",
        route_next,
        {
            "select_skills": "select_skills",
            "respond": "respond",
        },
    )

    workflow.add_conditional_edges(
        "select_skills",
        route_next,
        {
            "load_skill_context": "load_skill_context",
            "respond": "respond",
        },
    )

    workflow.add_edge("load_skill_context", "execute_skills")
    workflow.add_edge("execute_skills", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()
