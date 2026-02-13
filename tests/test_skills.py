"""Tests for the LangGraph skills system.

These tests exercise the SkillRegistry, SkillExecutor, individual skills,
and the graph node functions (with LLM calls mocked out).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

# ---------------------------------------------------------------------------
# Resolve the skills directory relative to this test file
# ---------------------------------------------------------------------------

SKILLS_DIR = str(Path(__file__).resolve().parent.parent / "skills")


# ===================================================================
# SkillRegistry tests
# ===================================================================

from src.skill_registry import SkillRegistry


class TestSkillRegistry:
    def test_loads_all_skills(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        names = {s["name"] for s in registry.list_skills()}
        assert "report_generator" in names
        assert "data_analyzer" in names
        assert "email_composer" in names
        assert "webapp_testing" in names
        assert "pdf_processor" in names

    def test_search_finds_report(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("I want to create a sales report")
        names = [r["name"] for r in results]
        assert "report_generator" in names

    def test_search_finds_email(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("I need to compose email for the team")
        names = [r["name"] for r in results]
        assert "email_composer" in names

    def test_search_finds_data_analyzer(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("analyze data from the CSV")
        names = [r["name"] for r in results]
        assert "data_analyzer" in names

    def test_search_finds_webapp_testing(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("I need to test webapp on localhost")
        names = [r["name"] for r in results]
        assert "webapp_testing" in names

    def test_search_finds_webapp_testing_by_playwright(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("run a playwright test on my site")
        names = [r["name"] for r in results]
        assert "webapp_testing" in names

    def test_search_finds_pdf_processor(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("extract text from a pdf file")
        names = [r["name"] for r in results]
        assert "pdf_processor" in names

    def test_search_finds_pdf_by_merge(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("merge pdf documents together")
        names = [r["name"] for r in results]
        assert "pdf_processor" in names

    def test_search_no_match(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        results = registry.search_skills("tell me a joke")
        assert results == []

    def test_get_skill_by_name(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        meta = registry.get_skill_by_name("report_generator")
        assert meta is not None
        assert meta.name == "report_generator"
        assert meta.entry_point == "main.py"

    def test_get_skill_not_found(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        assert registry.get_skill_by_name("nonexistent") is None

    def test_nonexistent_base_path(self):
        registry = SkillRegistry(base_path="/tmp/no_such_dir_xyz")
        assert registry.list_skills() == []


# ===================================================================
# SkillExecutor tests
# ===================================================================

from src.skill_executor import SkillExecutor


class TestSkillExecutor:
    @pytest.fixture()
    def executor(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        return SkillExecutor(registry)

    def test_load_context_report_generator(self, executor):
        ctx = executor.load_skill_context("report_generator")
        assert "error" not in ctx
        assert ctx["skill_doc"] is not None
        assert "Report Generator" in ctx["skill_doc"]
        assert ctx["schema"] is not None
        assert "report_type" in ctx["schema"]["properties"]

    def test_load_context_missing_skill(self, executor):
        ctx = executor.load_skill_context("does_not_exist")
        assert "error" in ctx

    def test_execute_report_generator(self, executor):
        result = executor.execute_skill(
            "report_generator", {"report_type": "sales", "period": "Q4"}
        )
        assert result["status"] == "success"
        assert "report_path" in result
        assert "summary" in result

    def test_execute_data_analyzer(self, executor):
        result = executor.execute_skill(
            "data_analyzer",
            {"dataset": "test", "analysis_type": "summary"},
        )
        assert result["status"] == "success"
        assert result["analysis_type"] == "summary"

    def test_execute_email_composer(self, executor):
        result = executor.execute_skill(
            "email_composer",
            {"email_type": "meeting_request", "recipient": "Alice"},
        )
        assert result["status"] == "success"
        assert "subject" in result
        assert "body" in result
        assert "Alice" in result["body"]

    def test_load_context_webapp_testing(self, executor):
        ctx = executor.load_skill_context("webapp_testing")
        assert "error" not in ctx
        assert "Web Application Testing" in ctx["skill_doc"]
        assert ctx["schema"] is not None
        assert "url" in ctx["schema"]["properties"]
        assert "actions" in ctx["schema"]["properties"]

    def test_execute_webapp_testing(self, executor):
        result = executor.execute_skill(
            "webapp_testing",
            {
                "url": "http://localhost:3000",
                "actions": [
                    {"type": "screenshot", "path": "/tmp/test.png"},
                    {"type": "click", "selector": "button#submit"},
                ],
            },
        )
        assert result["status"] == "success"
        assert len(result["results"]) == 2
        assert result["results"][0]["action"] == "screenshot"
        assert result["results"][1]["action"] == "click"

    def test_load_context_pdf_processor(self, executor):
        ctx = executor.load_skill_context("pdf_processor")
        assert "error" not in ctx
        assert "PDF Processor" in ctx["skill_doc"]
        assert ctx["schema"] is not None
        assert "operation" in ctx["schema"]["properties"]

    def test_execute_pdf_processor(self, executor):
        result = executor.execute_skill(
            "pdf_processor",
            {"operation": "extract_text", "input_path": "report.pdf"},
        )
        assert result["status"] == "success"
        assert result["operation"] == "extract_text"
        assert result["pages_processed"] == 10

    def test_execute_missing_skill(self, executor):
        result = executor.execute_skill("nonexistent", {})
        assert "error" in result


# ===================================================================
# Individual skill tests
# ===================================================================


class TestReportGeneratorSkill:
    def test_defaults(self):
        from skills.report_generator.main import execute

        result = execute({})
        assert result["status"] == "success"
        assert result["report_path"] == "/tmp/sales_Q4.pdf"

    def test_analytics(self):
        from skills.report_generator.main import execute

        result = execute({"report_type": "analytics", "period": "2024"})
        assert result["report_path"] == "/tmp/analytics_2024.pdf"
        assert "total_visits" in result["summary"]


class TestDataAnalyzerSkill:
    def test_anomaly_detection(self):
        from skills.data_analyzer.main import execute

        result = execute({"dataset": "ds", "analysis_type": "anomaly_detection"})
        assert result["status"] == "success"
        assert result["results"]["anomalies_found"] == 7

    def test_with_columns(self):
        from skills.data_analyzer.main import execute

        result = execute(
            {"dataset": "ds", "analysis_type": "summary", "columns": ["a", "b"]}
        )
        assert result["results"]["filtered_columns"] == ["a", "b"]


class TestEmailComposerSkill:
    def test_casual_tone(self):
        from skills.email_composer.main import execute

        result = execute(
            {"email_type": "follow_up", "recipient": "Bob", "tone": "casual"}
        )
        assert "Hey Bob" in result["body"]

    def test_key_points(self):
        from skills.email_composer.main import execute

        result = execute(
            {
                "email_type": "status_update",
                "recipient": "Team",
                "key_points": ["Milestone 1 done", "On track"],
            }
        )
        assert "Milestone 1 done" in result["body"]


class TestWebappTestingSkill:
    def test_screenshot_action(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:8080",
            "actions": [{"type": "screenshot", "path": "/tmp/shot.png"}],
        })
        assert result["status"] == "success"
        assert result["url"] == "http://localhost:8080"
        assert result["results"][0]["status"] == "success"
        assert result["results"][0]["path"] == "/tmp/shot.png"

    def test_click_and_fill_actions(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:3000",
            "actions": [
                {"type": "click", "selector": "#login-btn"},
                {"type": "fill", "selector": "#username", "value": "admin"},
                {"type": "fill", "selector": "#password", "value": "secret"},
                {"type": "click", "selector": "#submit"},
            ],
        })
        assert result["status"] == "success"
        assert len(result["results"]) == 4
        assert all(r["status"] == "success" for r in result["results"])
        assert result["results"][1]["value"] == "admin"

    def test_check_text_action(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:3000",
            "actions": [{"type": "check_text", "text": "Welcome"}],
        })
        assert result["results"][0]["found"] is True

    def test_console_logs_action(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:3000",
            "actions": [{"type": "get_console_logs"}],
        })
        assert result["status"] == "success"
        assert len(result["console_logs"]) > 0
        assert result["console_logs"][0]["level"] == "info"

    def test_unknown_action_type(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:3000",
            "actions": [{"type": "hover", "selector": "#btn"}],
        })
        assert result["status"] == "success"
        assert result["results"][0]["status"] == "error"
        assert "Unknown action type" in result["results"][0]["message"]

    def test_no_actions_error(self):
        from skills.webapp_testing.main import execute

        result = execute({"url": "http://localhost:3000", "actions": []})
        assert result["status"] == "error"

    def test_browser_config(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:3000",
            "actions": [{"type": "screenshot"}],
            "headless": False,
            "wait_for_idle": False,
        })
        assert result["browser_config"]["headless"] is False
        assert result["browser_config"]["wait_for_idle"] is False

    def test_full_e2e_flow(self):
        from skills.webapp_testing.main import execute

        result = execute({
            "url": "http://localhost:5173",
            "actions": [
                {"type": "screenshot", "path": "/tmp/before.png"},
                {"type": "fill", "selector": "#search", "value": "test query"},
                {"type": "click", "selector": "button[type=submit]"},
                {"type": "check_text", "text": "Results"},
                {"type": "screenshot", "path": "/tmp/after.png"},
                {"type": "get_console_logs"},
            ],
        })
        assert result["status"] == "success"
        assert len(result["results"]) == 6
        assert all(r["status"] == "success" for r in result["results"])
        assert len(result["console_logs"]) > 0


class TestPdfProcessorSkill:
    def test_extract_text(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "extract_text", "input_path": "doc.pdf"})
        assert result["status"] == "success"
        assert result["page_count"] == 10
        assert "Extracted text" in result["text"]

    def test_extract_text_specific_pages(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "extract_text",
            "input_path": "doc.pdf",
            "pages": [0, 2, 4],
        })
        assert result["status"] == "success"
        assert result["pages_processed"] == 3

    def test_extract_tables(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "extract_tables", "input_path": "data.pdf"})
        assert result["status"] == "success"
        assert result["tables_found"] == 2
        assert result["tables"][0]["headers"] == ["Name", "Value", "Change"]

    def test_extract_metadata(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "extract_metadata", "input_path": "doc.pdf"})
        assert result["status"] == "success"
        assert result["metadata"]["title"] == "Quarterly Report"
        assert result["metadata"]["author"] == "Finance Team"

    def test_merge(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "merge",
            "input_paths": ["a.pdf", "b.pdf", "c.pdf"],
            "output_path": "/tmp/merged.pdf",
        })
        assert result["status"] == "success"
        assert result["files_merged"] == 3
        assert result["output_path"] == "/tmp/merged.pdf"

    def test_merge_no_inputs(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "merge", "input_paths": []})
        assert result["status"] == "error"

    def test_split(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "split",
            "input_path": "big.pdf",
            "output_path": "/tmp",
        })
        assert result["status"] == "success"
        assert result["pages_split"] == 10
        assert len(result["output_files"]) == 10

    def test_rotate(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "rotate",
            "input_path": "doc.pdf",
            "rotation_degrees": 180,
            "pages": [0, 1],
        })
        assert result["status"] == "success"
        assert result["rotation_degrees"] == 180
        assert result["pages_rotated"] == [0, 1]

    def test_create(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "create",
            "output_path": "/tmp/new.pdf",
            "content": {
                "title": "My Document",
                "body": ["Paragraph 1", "Paragraph 2", "Paragraph 3"],
            },
        })
        assert result["status"] == "success"
        assert result["title"] == "My Document"
        assert result["paragraphs"] == 3

    def test_encrypt(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "encrypt",
            "input_path": "doc.pdf",
            "password": "s3cret",
        })
        assert result["status"] == "success"
        assert result["encrypted"] is True

    def test_encrypt_no_password(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "encrypt", "input_path": "doc.pdf"})
        assert result["status"] == "error"

    def test_add_watermark(self):
        from skills.pdf_processor.main import execute

        result = execute({
            "operation": "add_watermark",
            "input_path": "doc.pdf",
            "watermark_text": "DRAFT",
        })
        assert result["status"] == "success"
        assert result["watermark_text"] == "DRAFT"
        assert result["pages_watermarked"] == 10

    def test_unknown_operation(self):
        from skills.pdf_processor.main import execute

        result = execute({"operation": "compress"})
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]


# ===================================================================
# Node function tests (LLM mocked)
# ===================================================================

from src.nodes import (
    GraphState,
    analyze_query,
    execute_skills,
    load_skill_context,
    respond,
    route_next,
    select_skills,
)


def _make_state(**overrides) -> GraphState:
    defaults: GraphState = {
        "messages": [HumanMessage(content="Create a Q4 sales report")],
        "available_skills": [],
        "selected_skills": [],
        "skill_contexts": {},
        "execution_results": {},
        "next_action": None,
    }
    defaults.update(overrides)
    return defaults


class TestAnalyzeQueryNode:
    def test_finds_skills(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        state = _make_state()
        result = analyze_query(state, registry=registry)
        assert len(result["available_skills"]) > 0
        assert result["next_action"] == "select_skills"

    def test_no_skills(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        state = _make_state(messages=[HumanMessage(content="hello")])
        result = analyze_query(state, registry=registry)
        assert result["available_skills"] == []
        assert result["next_action"] == "respond"


class TestSelectSkillsNode:
    @patch("src.nodes._get_llm")
    def test_selects_skill(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='["report_generator"]'
        )
        mock_get_llm.return_value = mock_llm

        state = _make_state(
            available_skills=[
                {"name": "report_generator", "description": "Generate reports"}
            ],
        )
        result = select_skills(state)
        assert result["selected_skills"] == ["report_generator"]
        assert result["next_action"] == "load_skill_context"

    @patch("src.nodes._get_llm")
    def test_no_selection(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="[]")
        mock_get_llm.return_value = mock_llm

        state = _make_state(available_skills=[])
        result = select_skills(state)
        assert result["selected_skills"] == []
        assert result["next_action"] == "respond"

    @patch("src.nodes._get_llm")
    def test_invalid_json_fallback(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="not json")
        mock_get_llm.return_value = mock_llm

        state = _make_state(available_skills=[])
        result = select_skills(state)
        assert result["selected_skills"] == []
        assert result["next_action"] == "respond"


class TestLoadSkillContextNode:
    def test_loads_context(self):
        registry = SkillRegistry(base_path=SKILLS_DIR)
        executor = SkillExecutor(registry)
        state = _make_state(selected_skills=["report_generator"])
        result = load_skill_context(state, executor=executor)
        assert "report_generator" in result["skill_contexts"]
        assert result["skill_contexts"]["report_generator"]["skill_doc"] is not None


class TestExecuteSkillsNode:
    @patch("src.nodes._get_llm")
    def test_executes_skill(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content='{"report_type": "sales", "period": "Q4"}'
        )
        mock_get_llm.return_value = mock_llm

        registry = SkillRegistry(base_path=SKILLS_DIR)
        executor = SkillExecutor(registry)

        state = _make_state(
            selected_skills=["report_generator"],
            skill_contexts={
                "report_generator": {
                    "skill_doc": "...",
                    "schema": None,
                }
            },
        )
        result = execute_skills(state, executor=executor)
        assert "report_generator" in result["execution_results"]
        assert result["execution_results"]["report_generator"]["status"] == "success"


class TestRespondNode:
    @patch("src.nodes._get_llm")
    def test_respond_with_results(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(
            content="Your Q4 sales report is ready."
        )
        mock_get_llm.return_value = mock_llm

        state = _make_state(
            execution_results={
                "report_generator": {"status": "success", "report_path": "/tmp/sales_Q4.pdf"}
            }
        )
        result = respond(state)
        last_msg = result["messages"][-1]
        assert isinstance(last_msg, AIMessage)
        assert "Q4" in last_msg.content

    @patch("src.nodes._get_llm")
    def test_respond_without_results(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Hello! How can I help?")
        mock_get_llm.return_value = mock_llm

        state = _make_state(
            messages=[HumanMessage(content="hello")],
            execution_results={},
        )
        result = respond(state)
        assert len(result["messages"]) == 2


class TestRouter:
    def test_routes_to_select(self):
        assert route_next({"next_action": "select_skills"}) == "select_skills"

    def test_routes_to_respond_default(self):
        assert route_next({"next_action": None}) == "respond"

    def test_routes_to_respond_explicit(self):
        assert route_next({"next_action": "respond"}) == "respond"
