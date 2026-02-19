"""Streamlit chat UI for the LangGraph Skills system."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `src` and `skills` are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.skill_registry import SkillRegistry
from src.skills_graph import create_skills_graph

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SKILLS_DIR = str(PROJECT_ROOT / "skills")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LangGraph Skills Chat",
    page_icon="🛠️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stMain > div { max-width: 900px; margin: 0 auto; }
    .skill-badge {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        margin: 2px;
    }
    .status-box {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 0.85em;
    }
    .status-success { background: #e6f4ea; border-left: 4px solid #34a853; }
    .status-error   { background: #fce8e6; border-left: 4px solid #ea4335; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    st.session_state.graph = None
if "registry" not in st.session_state:
    st.session_state.registry = SkillRegistry(base_path=SKILLS_DIR)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("LangGraph Skills")

    # API key input
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="ANTHROPIC_API_KEY for LLM calls",
    )
    if api_key:
        import os
        os.environ["ANTHROPIC_API_KEY"] = api_key

    st.divider()

    # Available skills
    st.subheader("Available Skills")
    skills = st.session_state.registry.list_skills()
    for skill in skills:
        with st.expander(f"**{skill['name']}** v{skill['version']}"):
            st.write(skill["description"])
            st.caption("Triggers: " + ", ".join(f"`{t}`" for t in skill["triggers"]))

    st.divider()

    # Graph init button
    if st.button("Initialize Graph", use_container_width=True):
        try:
            st.session_state.graph = create_skills_graph(skills_base_path=SKILLS_DIR)
            st.success("Graph initialized!")
        except Exception as e:
            st.error(f"Failed: {e}")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Skills loaded: {len(skills)}")

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("LangGraph Skills Chat")
st.caption("Type a message to trigger skills automatically. Examples: "
           '"Create a Q4 sales report", "Analyze data summary", '
           '"Extract text from a pdf", "Test webapp on localhost"')

# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        # Show skill metadata if present
        if msg.get("skills_used"):
            badges = " ".join(
                f'<span class="skill-badge">{s}</span>' for s in msg["skills_used"]
            )
            st.markdown(f"**Skills used:** {badges}", unsafe_allow_html=True)
        if msg.get("execution_results"):
            with st.expander("Execution details"):
                st.json(msg["execution_results"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
if user_input := st.chat_input("Ask anything..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process with graph or fall back
    with st.chat_message("assistant"):
        if st.session_state.graph is None:
            # Try to auto-initialise
            try:
                st.session_state.graph = create_skills_graph(
                    skills_base_path=SKILLS_DIR,
                )
            except Exception:
                st.session_state.graph = None

        if st.session_state.graph is not None:
            with st.spinner("Processing..."):
                try:
                    result = st.session_state.graph.invoke({
                        "messages": [HumanMessage(content=user_input)],
                        "available_skills": [],
                        "selected_skills": [],
                        "skill_contexts": {},
                        "execution_results": {},
                        "next_action": None,
                    })

                    ai_content = result["messages"][-1].content
                    selected = result.get("selected_skills", [])
                    exec_results = result.get("execution_results", {})

                    st.markdown(ai_content)

                    if selected:
                        badges = " ".join(
                            f'<span class="skill-badge">{s}</span>' for s in selected
                        )
                        st.markdown(
                            f"**Skills used:** {badges}", unsafe_allow_html=True
                        )

                    if exec_results:
                        with st.expander("Execution details"):
                            st.json(exec_results)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ai_content,
                        "skills_used": selected,
                        "execution_results": exec_results if exec_results else None,
                    })

                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                    })
        else:
            fallback = ("Please set your **ANTHROPIC_API_KEY** in the sidebar "
                        "to enable the LangGraph skills pipeline.")
            st.warning(fallback)
            st.session_state.messages.append({
                "role": "assistant",
                "content": fallback,
            })
