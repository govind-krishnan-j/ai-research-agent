import os
import unittest
from unittest.mock import patch

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["GROQ_API_KEY"] = "test-placeholder"

import httpx
import api


class BetaAccessTests(unittest.IsolatedAsyncioTestCase):
    async def test_invite_is_required_for_site_and_api(self):
        with patch.object(api, "require_invite", True), patch.object(api, "invite_code", "demo-invite"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app),
                                         base_url="http://test") as client:
                self.assertEqual((await client.get("/healthz")).status_code, 200)
                self.assertEqual((await client.get("/")).status_code, 401)
                for endpoint in ("/api/research", "/api/pdf"):
                    response = await client.post(endpoint, json={}, auth=("beta", "incorrect"))
                    self.assertEqual(response.status_code, 401)
                    self.assertIn("Basic", response.headers["www-authenticate"])
                with patch.object(api, "research_topic", return_value=("Test report", [])):
                    response = await client.post("/api/research", json={"topic": "test"},
                                                 auth=("beta", "demo-invite"))
                    self.assertEqual(response.json()["report"], "Test report")

    async def test_public_access_ignores_saved_invite_code(self):
        with patch.object(api, "require_invite", False), patch.object(api, "invite_code", "old-invite"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app),
                                         base_url="http://test") as client:
                self.assertEqual((await client.get("/")).status_code, 200)
                with patch.object(api, "research_topic", return_value=("Public report", [])):
                    response = await client.post("/api/research", json={"topic": "test"})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["report"], "Public report")
                with patch.object(api, "generate_pdf_bytes", return_value=b"%PDF-test"):
                    response = await client.post("/api/pdf", json={"topic": "test", "content": "Report"})
                    self.assertEqual(response.status_code, 200)
