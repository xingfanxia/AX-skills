from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "download_video.py"
SPEC = importlib.util.spec_from_file_location("download_video", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_swap_preserves_signed_path_and_query():
    source = (
        "https://bad.mcdn.bilivideo.cn:8082/upgcxcode/a/b/video.m4s"
        "?sig=fixture"
    )
    result = MODULE.swap_url_host(source, MODULE.BILI_CDN_CANDIDATES[0])
    assert result.startswith(f"https://{MODULE.BILI_CDN_CANDIDATES[0]}/upgcxcode/")
    assert result.endswith("?sig=fixture")
    assert ":8082" not in result


def test_cdn_choice_requires_material_improvement_for_healthy_original():
    source = "https://upos-good.bilivideo.com/upgcxcode/a/video.m4s?sig=fixture"
    results = [
        MODULE.ProbeResult("upos-good.bilivideo.com", True, 206, 1024, 20, 80, 10.0),
        MODULE.ProbeResult(MODULE.BILI_CDN_CANDIDATES[0], True, 206, 1024, 20, 70, 11.0),
    ]
    assert MODULE.choose_cdn_host(source, results, "auto") is None
    faster = [
        results[0],
        MODULE.ProbeResult(MODULE.BILI_CDN_CANDIDATES[0], True, 206, 1024, 10, 40, 14.0),
    ]
    assert MODULE.choose_cdn_host(source, faster, "auto") == MODULE.BILI_CDN_CANDIDATES[0]


def test_fast_measured_original_beats_bad_host_prior():
    source = (
        "https://upos-sz-mirrorcosov.bilivideo.com/"
        "upgcxcode/a/video.m4s?sig=fixture"
    )
    results = [
        MODULE.ProbeResult(
            "upos-sz-mirrorcosov.bilivideo.com", True, 206, 1024, 20, 30, 8.0,
        ),
        MODULE.ProbeResult(
            MODULE.BILI_CDN_CANDIDATES[0], True, 206, 1024, 30, 90, 1.0,
        ),
    ]
    assert MODULE.choose_cdn_host(source, results, "auto") is None


def test_dry_run_redacts_cookie_file(tmp_path, capsys):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    result = MODULE.main([
        "https://youtu.be/example",
        "--output-dir",
        str(tmp_path / "out"),
        "--cookies",
        str(cookie_file),
        "--dry-run",
    ])
    assert result == 0
    output = capsys.readouterr().out
    assert str(cookie_file) not in output
    assert "<COOKIE_FILE>" in output
    payload = json.loads(output)
    assert payload["authentication"]["mode"] == "file"
