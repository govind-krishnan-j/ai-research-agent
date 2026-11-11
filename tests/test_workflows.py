"""Offline checks at the agent, CLI and HTTP boundaries."""

import os
import unittest
from unittest.mock import patch

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["GROQ_API_KEY"] = "test-placeholder"

from fastapi import HTTPException
from requests import HTTPError

import agent
import api
import main
import tools
from test_agent_finish import response, sized_report, tool


class WorkflowTests(unittest.TestCase):
    def test_report_wording_does_not_determine_http_status(self):
        text = sized_report("The agent could not find agreement between the sources.")
        with patch.object(agent, "call_llm", return_value=response(content=text)):
            result = api.research(api.ResearchRequest(topic="  example  "))
        self.assertEqual(result, {"topic": "example", "report": text, "sources": []})

    def test_empty_completion_without_evidence_is_a_failure(self):
        with patch.object(agent, "call_llm", return_value=response(content=" ")):
            with self.assertRaises(HTTPException) as failure:
                api.research(api.ResearchRequest(topic="example"))
            legacy_message, sources = agent.run_agent("example")
        self.assertEqual(failure.exception.status_code, 502)
        self.assertIn("source material", failure.exception.detail)
        self.assertEqual(legacy_message, failure.exception.detail)
        self.assertEqual(sources, [])

    def test_cli_does_not_save_failure(self):
        with patch("builtins.input", return_value="example"), patch("builtins.print"), patch.object(
            agent, "call_llm", side_effect=RuntimeError("offline")
        ), patch.object(main, "save_report") as save:
            main.main()
        save.assert_not_called()

    def test_agent_can_correct_bad_arguments_within_the_same_run(self):
        scripted = [
            response(tool_calls=[tool("read_page", "{", "bad")]),
            response(tool_calls=[tool("read_page", '{"url":"https://example.org"}', "good")]),
            response(content=sized_report("Finished")),
        ]
        with patch.object(agent, "call_llm", side_effect=scripted) as model, patch.dict(
            agent.available_tools, {"read_page": lambda url: "example text"}
        ):
            report, sources = agent.research_topic("example")
        self.assertEqual((report, sources), (sized_report("Finished"), ["https://example.org"]))
        messages = model.call_args.args[0]
        self.assertTrue(any(m.get("tool_call_id") == "bad" and "Invalid arguments" in m["content"] for m in messages))

    def test_pdf_export_accepts_a_completed_report(self):
        result = api.pdf(api.ReportRequest(topic="example", content="A finding."))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["content-type"], "application/pdf")
        self.assertTrue(result.body.startswith(b"%PDF-"))

    def test_http_error_page_is_excluded_from_evidence(self):
        state = {"read_count": 0, "sources": [], "pages": []}
        with patch.object(tools.requests, "get") as get:
            get.return_value.raise_for_status.side_effect = HTTPError("page missing")
            result = agent.execute_tool(tool("read_page", '{"url":"https://example.org"}', "p"), state)
        self.assertIn("Could not read page", result["content"])
        self.assertEqual(state, {"read_count": 1, "sources": [], "pages": []})
