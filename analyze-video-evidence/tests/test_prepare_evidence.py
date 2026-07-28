from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "prepare_evidence.py"
SPEC = importlib.util.spec_from_file_location("prepare_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_timestamp_parser_accepts_srt_and_clock_values():
    assert MODULE.timestamp_seconds("00:01:02,500") == 62.5
    assert MODULE.timestamp_seconds("01:02.250") == 62.25
    assert MODULE.timestamp_seconds("9.5") == 9.5


def test_subtitle_parser_deduplicates_adjacent_auto_captions():
    text = """WEBVTT

00:00:01.000 --> 00:00:02.000
<c>hello</c>

00:00:02.100 --> 00:00:03.000
hello

00:00:04.000 --> 00:00:05.000
world
"""
    cues = MODULE.parse_subtitles(text)
    assert [(cue.start, cue.end, cue.text) for cue in cues] == [
        (1.0, 3.0, "hello"),
        (4.0, 5.0, "world"),
    ]


def test_uniform_schedule_covers_edges_without_sampling_exact_boundaries():
    assert MODULE.uniform_timestamps(100, 4) == [12.5, 37.5, 62.5, 87.5]


def test_human_chinese_subtitle_precedes_auto_caption(tmp_path):
    human = tmp_path / "video.zh.srt"
    automatic = tmp_path / "video.ai-zh.srt"
    human.write_text("", encoding="utf-8")
    automatic.write_text("", encoding="utf-8")
    media = tmp_path / "video.mp4"
    media.write_bytes(b"not-used")
    assert MODULE.find_subtitles(media, None) == human
