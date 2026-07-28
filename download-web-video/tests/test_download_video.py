from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "download_video.py"
SPEC = importlib.util.spec_from_file_location("download_video", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DownloadVideoTests(unittest.TestCase):
    def test_swap_preserves_signed_path_and_query(self):
        source = (
            "https://bad.mcdn.bilivideo.cn:8082/upgcxcode/a/b/video.m4s"
            "?sig=fixture"
        )
        result = MODULE.swap_url_host(source, MODULE.BILI_CDN_CANDIDATES[0])
        self.assertTrue(
            result.startswith(
                f"https://{MODULE.BILI_CDN_CANDIDATES[0]}/upgcxcode/"
            )
        )
        self.assertTrue(result.endswith("?sig=fixture"))
        self.assertNotIn(":8082", result)

    def test_cdn_choice_requires_material_improvement_for_healthy_original(self):
        source = "https://upos-good.bilivideo.com/upgcxcode/a/video.m4s?sig=fixture"
        results = [
            MODULE.ProbeResult(
                "upos-good.bilivideo.com", True, 206, 1024, 20, 80, 10.0
            ),
            MODULE.ProbeResult(
                MODULE.BILI_CDN_CANDIDATES[0], True, 206, 1024, 20, 70, 11.0
            ),
        ]
        self.assertIsNone(MODULE.choose_cdn_host(source, results, "auto"))
        faster = [
            results[0],
            MODULE.ProbeResult(
                MODULE.BILI_CDN_CANDIDATES[0], True, 206, 1024, 10, 40, 14.0
            ),
        ]
        self.assertEqual(
            MODULE.choose_cdn_host(source, faster, "auto"),
            MODULE.BILI_CDN_CANDIDATES[0],
        )

    def test_fast_measured_original_beats_bad_host_prior(self):
        source = (
            "https://upos-sz-mirrorcosov.bilivideo.com/"
            "upgcxcode/a/video.m4s?sig=fixture"
        )
        results = [
            MODULE.ProbeResult(
                "upos-sz-mirrorcosov.bilivideo.com",
                True,
                206,
                1024,
                20,
                30,
                8.0,
            ),
            MODULE.ProbeResult(
                MODULE.BILI_CDN_CANDIDATES[0],
                True,
                206,
                1024,
                30,
                90,
                1.0,
            ),
        ]
        self.assertIsNone(MODULE.choose_cdn_host(source, results, "auto"))

    def test_dry_run_redacts_cookie_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cookie_file = root / "cookies.txt"
            cookie_file.write_text(
                "# Netscape HTTP Cookie File\n",
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = MODULE.main([
                    "https://youtu.be/example",
                    "--output-dir",
                    str(root / "out"),
                    "--cookies",
                    str(cookie_file),
                    "--dry-run",
                ])
            self.assertEqual(result, 0)
            rendered = output.getvalue()
            self.assertNotIn(str(cookie_file), rendered)
            self.assertIn("<COOKIE_FILE>", rendered)
            payload = json.loads(rendered)
            self.assertEqual(payload["authentication"]["mode"], "file")

    def test_bilibili_auto_uses_native_downloader_even_when_aria2_exists(self):
        self.assertFalse(MODULE.should_use_aria2("bilibili", "auto", True))
        self.assertTrue(MODULE.should_use_aria2("bilibili", "force", True))
        self.assertTrue(MODULE.should_use_aria2("youtube", "auto", True))

    def test_media_validation_checks_tracks_not_only_container_duration(self):
        probe = {
            "streams": [
                {"codec_type": "video", "duration": "1230.0"},
                {"codec_type": "audio", "duration": "3074.0"},
            ],
            "format": {"duration": "3074.0"},
        }
        with self.assertRaisesRegex(MODULE.DownloadError, "video=1230.0s"):
            MODULE.evaluate_media_probe(
                probe,
                expected_duration=3074.0,
                expect_video=True,
                expect_audio=True,
            )

    def test_media_validation_accepts_complete_required_streams(self):
        probe = {
            "streams": [
                {"codec_type": "video", "duration": "3033.71"},
                {"codec_type": "audio", "duration": "3033.69"},
            ],
            "format": {"duration": "3033.71"},
        }
        result = MODULE.evaluate_media_probe(
            probe,
            expected_duration=3033.71,
            expect_video=True,
            expect_audio=True,
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["actual_duration_seconds"], 3033.69)


if __name__ == "__main__":
    unittest.main()
