"""Offline budget checks. No real Groq request or API key is needed."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["GROQ_API_KEY"] = "test-placeholder"

import agent


def completion(content, usage=1500, reason="stop"):
    choice = SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=reason)
    return SimpleNamespace(choices=[choice], usage=SimpleNamespace(total_tokens=usage))


class TokenBudgetTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db = patch.object(agent, "BUDGET_DB", Path(temp.name) / "budget.sqlite")
        db.start()
        self.addCleanup(db.stop)

    def test_each_length_fits_with_multibyte_evidence_and_one_request(self):
        for length in ("brief", "detailed"):
            with self.subTest(length=length), patch.object(
                agent.client.chat.completions, "create", return_value=completion("Report")
            ) as model, patch.object(agent, "time") as clock:
                clock.time.return_value = 100 if length == "brief" else 200
                self.assertEqual(agent.make_request("é" * 300, ["海" * 6000, "📖" * 6000], length), "Report")
                model.assert_called_once()
                args = model.call_args.kwargs
                payload = sum(len(m["content"].encode()) for m in args["messages"])
                self.assertLessEqual(payload + agent.CHAT_OVERHEAD + args["max_completion_tokens"], 8000)

    def test_concurrent_reservations_share_capacity(self):
        def try_reserve(_):
            try:
                agent.reserve_tokens(4000)
                return True
            except agent.BudgetError:
                return False
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(try_reserve, range(4))), 2)

    def test_window_releases_and_actual_usage_is_charged(self):
        with patch.object(agent.time, "time", return_value=100), patch.object(
            agent.client.chat.completions, "create", return_value=completion("Report", 1200)
        ):
            agent.make_request("topic", ["Evidence"], "brief")
            with self.assertRaises(agent.BudgetError) as error:
                agent.reserve_tokens(6801)
            self.assertEqual(error.exception.retry_after, 60)
            agent.reserve_tokens(6800)
        with patch.object(agent.time, "time", return_value=300):
            agent.reserve_tokens(8000)

    def test_truncated_or_empty_content_is_not_published(self):
        for response in (completion("partial", reason="length"), completion("")):
            with patch.object(agent.client.chat.completions, "create", return_value=response):
                with self.assertRaises(agent.ResearchError):
                    agent.make_request("topic", ["Evidence"], "brief")

    def test_oversized_topic_never_reaches_model(self):
        with patch.object(agent.client.chat.completions, "create") as model:
            with self.assertRaises(agent.ResearchError):
                agent.make_request("x" * 9000, ["Evidence"], "detailed")
            model.assert_not_called()
