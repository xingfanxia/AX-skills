"""Routing contract: real SDK serialization, mocked HTTP, no external calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import httpx
from openai import OpenAI, BadRequestError, RateLimitError

spec = importlib.util.spec_from_file_location("generate", Path(__file__).with_name("generate.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RoutingTests(unittest.TestCase):
    def run_route(self, first, edit=False, status=429, both=False):
        calls = []
        def respond(request):
            body = request.read()
            calls.append(body)
            code = status if len(calls) == 1 or both else 200
            data = {"error": {"message": "test", "type": "test"}} if code != 200 else {"created": 1, "data": [{"b64_json": "aW1hZ2U="}]}
            return httpx.Response(code, json=data)
        client = OpenAI(api_key="test", base_url="https://test.invalid/v1", max_retries=0,
                        http_client=httpx.Client(transport=httpx.MockTransport(respond)))
        second = "flare" if first == "sunburst" else "sunburst"
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp)/"input.png"
            image.write_bytes(b"test-reference-bytes")
            result = m.generate_with_fallback((client, "gpt-image-2.5-"+first),
                    (client, "gpt-image-2.5-"+second), "prompt", "1024x1024",
                    edit_images=[image] if edit else None)
        self.assertEqual(len(calls), 2)
        self.assertIn(first.encode(), calls[0])
        self.assertIn(second.encode(), calls[1])
        if edit:
            self.assertTrue(all(b"test-reference-bytes" in body for body in calls))
        self.assertEqual(result.data[0].b64_json, "aW1hZ2U=")

    def test_both_directions_and_operations(self):
        for variant in m.VARIANTS:
            for edit in (False, True):
                with self.subTest(variant=variant, edit=edit):
                    self.run_route(variant, edit)

    def test_no_fallback_on_bad_request(self):
        with self.assertRaises(BadRequestError):
            self.run_route("sunburst", status=400)

    def test_both_limited_surfaces(self):
        with self.assertRaises(RateLimitError):
            self.run_route("flare", both=True)

    def test_quota_error_is_not_retryable(self):
        error = RateLimitError("quota", response=httpx.Response(429, request=httpx.Request("POST", "https://test.invalid")), body={"code": "insufficient_quota"})
        self.assertFalse(m.is_retryable_rate_limit(error))

    def test_legacy_model_settings_cannot_override_25(self):
        client, model = m.build_azure_client({"AZURE_OPENAI_ENDPOINT":"https://test.invalid/openai/v1",
            "AZURE_OPENAI_API_KEY":"test", "AZURE_OPENAI_DEPLOYMENT":"legacy",
            "AZURE_OPENAI_MODEL":"legacy", "AZURE_OPENAI_API_VERSION":"v1"}, "flare")
        self.assertEqual(model, "gpt-image-2.5-flare")
        self.assertIn("gpt-image-2.5-flare", str(client.base_url))
        self.assertEqual(client._api_version, m.DEFAULT_AZURE_API_VERSION)

if __name__ == "__main__":
    unittest.main()
