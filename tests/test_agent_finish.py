"""Regression checks for report generation after tool use."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["GROQ_API_KEY"] = "test-placeholder"

import agent  # noqa: E402


def response(content=None, tool_calls=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))]
    )


def tool(name, arguments, call_id):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class FinishReportTests(unittest.TestCase):
    def test_finishes_with_source_text_and_no_tool_history(self):
        calls = []
        scripted = iter([
            response(tool_calls=[tool("web_search", '{"query":"test"}', "s1")]),
            response(tool_calls=[
                tool("read_page", '{"url":"https://one.example"}', "p1"),
                tool("read_page", '{"url":"https://two.example"}', "p2"),
            ]),
            response(content="## Summary\nA sourced report."),
        ])

        def fake_llm(messages, allow_tools=True):
            calls.append((messages, allow_tools))
            return next(scripted)

        with patch.object(agent, "call_llm", side_effect=fake_llm), patch.dict(
            agent.available_tools,
            {
                "web_search": lambda query: ["https://one.example", "https://two.example"],
                "read_page": lambda url: f"Page content from {url}. " * 10,
            },
        ):
            report, sources = agent.run_agent("test")

        self.assertIn("sourced report", report)
        self.assertEqual(sources, ["https://one.example", "https://two.example"])
        final_messages, allow_tools = calls[-1]
        self.assertFalse(allow_tools)
        self.assertEqual([item["role"] for item in final_messages], ["system", "user"])
        self.assertIn("Page content from https://one.example", final_messages[1]["content"])

    def test_recovers_after_tool_choice_error_without_exposing_it(self):
        scripted = iter([
            response(tool_calls=[tool("read_page", '{"url":"https://one.example"}', "p1")]),
            RuntimeError("tool_use_failed: Tool choice is none, but model called a tool"),
            response(content="## Summary\nRecovered report."),
        ])

        def fake_llm(messages, allow_tools=True):
            item = next(scripted)
            if isinstance(item, Exception):
                raise item
            return item

        with patch.object(agent, "call_llm", side_effect=fake_llm), patch.dict(
            agent.available_tools, {"read_page": lambda url: "Readable source text. " * 10}
        ):
            report, sources = agent.run_agent("test")

        self.assertIn("Recovered report", report)
        self.assertEqual(sources, ["https://one.example"])


if __name__ == "__main__":
    unittest.main()
