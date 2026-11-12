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



class WorkflowTests(unittest.TestCase):
    def test_report_wording_does_not_determine_http_status(self):
        text = "The agent could not find agreement between the sources."
        with patch.object(agent, "make_request", return_value=text), patch.object(
            agent, "web_search", return_value=["source"]
        ), patch.object(agent, "read_page", return_value="Evidence"):
            result = api.research(api.ResearchRequest(topic="  example  "))
        self.assertEqual(result, {"topic": "example", "report": text, "sources": ["source"]})

    def test_no_evidence_skips_model_and_cli_save(self):
        with patch.object(agent, "web_search", return_value=[]), patch.object(agent, "make_request") as model:
            with self.assertRaises(HTTPException) as failure:
                api.research(api.ResearchRequest(topic="example"))
            self.assertEqual(failure.exception.status_code, 502)
            self.assertEqual(agent.run_agent("example"), (failure.exception.detail, []))
            with patch("builtins.input", return_value="example"), patch("builtins.print"), patch.object(main, "save_report") as save:
                main.main()
                save.assert_not_called()
            model.assert_not_called()

    def test_budget_error_reaches_browser_with_wait_time(self):
        with patch.object(api, "research_topic", side_effect=agent.BudgetError(23)):
            with self.assertRaises(HTTPException) as failure:
                api.research(api.ResearchRequest(topic="example"))
            self.assertEqual(failure.exception.status_code, 429)
            self.assertEqual(failure.exception.headers["Retry-After"], "23")

    def test_pdf_export_accepts_a_completed_report(self):
        result = api.pdf(api.ReportRequest(topic="example", content="A finding."))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["content-type"], "application/pdf")
        self.assertTrue(result.body.startswith(b"%PDF-"))

    def test_http_error_page_is_excluded_from_evidence(self):
        with patch.object(tools.requests, "get") as get, patch.object(agent, "web_search", return_value=["source"]):
            get.return_value.raise_for_status.side_effect = HTTPError("page missing")
            with self.assertRaises(agent.ResearchError):
                agent.research_topic("example")
