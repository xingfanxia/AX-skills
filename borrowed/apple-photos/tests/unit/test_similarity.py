from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest
from PIL import Image

from apple_photos_cli.canonical import sha256_digest
from apple_photos_cli.cli import main
from apple_photos_cli.errors import ApplePhotosError
from apple_photos_cli.similarity import (
    SimilarityPolicy,
    compare_image_manifest,
    compare_images,
    load_pair_manifest,
    load_similarity_report,
    revalidate_similarity_report,
)


def _image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (8, 8)) -> None:
    Image.new("RGB", size, color).save(path)


def _rgb16_png(path: Path, value: int) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload))
        )

    ihdr = struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0)
    pixel = b"\x00" + struct.pack(">HHH", value, value, value)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(pixel))
        + chunk(b"IEND", b"")
    )


def test_identical_images_pass_with_zero_error(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 120, 140))
    _image(right, (100, 120, 140))

    result = compare_images(left, right, SimilarityPolicy())

    assert result["passed"] is True
    assert set(result["metrics"].values()) == {0.0}


def test_small_pixel_error_passes_default_policy(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 100, 100))
    _image(right, (102, 102, 102))

    result = compare_images(left, right, SimilarityPolicy())

    assert result["passed"] is True
    assert result["metrics"]["rgb_mean_absolute_error"] == pytest.approx(2 / 255)


def test_equal_global_brightness_does_not_bypass_pixel_gate(tmp_path: Path) -> None:
    left = Image.new("RGB", (2, 1))
    right = Image.new("RGB", (2, 1))
    left.putdata([(0, 0, 0), (255, 255, 255)])
    right.putdata([(255, 255, 255), (0, 0, 0)])
    left_path = tmp_path / "left.png"
    right_path = tmp_path / "right.png"
    left.save(left_path)
    right.save(right_path)

    result = compare_images(left_path, right_path, SimilarityPolicy())

    assert result["passed"] is False
    assert result["metrics"]["luma_mean_absolute_error"] == 1.0


def test_p99_uses_per_pixel_max_channel_error(tmp_path: Path) -> None:
    left = Image.new("RGB", (100, 1), (0, 0, 0))
    right = Image.new("RGB", (100, 1), (0, 0, 0))
    for x in range(3):
        right.putpixel((x, 0), (255, 0, 0))
    left_path = tmp_path / "left.png"
    right_path = tmp_path / "right.png"
    left.save(left_path)
    right.save(right_path)

    result = compare_images(left_path, right_path, SimilarityPolicy())

    assert result["passed"] is False
    assert result["metrics"]["rgb_p99_absolute_error"] == 1.0


def test_16_bit_images_are_rejected_instead_of_clamped(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    Image.new("I;16", (2, 2), 256).save(left)
    Image.new("I;16", (2, 2), 65535).save(right)

    with pytest.raises(ApplePhotosError) as captured:
        compare_images(left, right, SimilarityPolicy())

    assert captured.value.code == "E_SIMILARITY_BIT_DEPTH_UNSUPPORTED"


def test_16_bit_truecolor_png_is_rejected_before_pillow_downconversion(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _rgb16_png(left, 0xFF00)
    _rgb16_png(right, 0xFFFF)

    with pytest.raises(ApplePhotosError) as captured:
        compare_images(left, right, SimilarityPolicy())

    assert captured.value.code == "E_SIMILARITY_BIT_DEPTH_UNSUPPORTED"


def test_unknown_source_bit_depth_is_not_assumed_to_be_8_bit(tmp_path: Path) -> None:
    left = tmp_path / "left.ppm"
    right = tmp_path / "right.ppm"
    left.write_bytes(b"P6\n1 1\n65535\n" + struct.pack(">HHH", 0xFF00, 0xFF00, 0xFF00))
    right.write_bytes(b"P6\n1 1\n65535\n" + struct.pack(">HHH", 0xFFFF, 0xFFFF, 0xFFFF))

    with pytest.raises(ApplePhotosError) as captured:
        compare_images(left, right, SimilarityPolicy())

    assert captured.value.code == "E_SIMILARITY_BIT_DEPTH_UNVERIFIED"


def test_non_opaque_alpha_is_rejected(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    Image.new("RGBA", (2, 2), (10, 20, 30, 0)).save(left)
    Image.new("RGBA", (2, 2), (10, 20, 30, 0)).save(right)

    with pytest.raises(ApplePhotosError) as captured:
        compare_images(left, right, SimilarityPolicy())

    assert captured.value.code == "E_SIMILARITY_ALPHA_UNSUPPORTED"


def test_dimension_mismatch_fails_closed(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (0, 0, 0), (8, 8))
    _image(right, (0, 0, 0), (9, 8))

    result = compare_images(left, right, SimilarityPolicy())

    assert result["passed"] is False
    assert result["metrics"] is None
    assert result["failed_checks"] == ["dimensions_equal"]


def test_policy_rejects_out_of_range_threshold() -> None:
    with pytest.raises(ApplePhotosError, match="between 0 and 1"):
        SimilarityPolicy(max_rgb_mae=1.1).validate()


def test_manifest_requires_unique_pair_ids(tmp_path: Path) -> None:
    manifest = tmp_path / "pairs.jsonl"
    record = {
        "pair_id": "pair-1",
        "left": "a",
        "right": "b",
        "candidate_local_identifier": "candidate-id",
        "keeper_local_identifier": "keeper-id",
    }
    manifest.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n")

    with pytest.raises(ApplePhotosError, match="Duplicate pair_id"):
        load_pair_manifest(manifest)


def test_batch_report_is_non_authorizing_and_digest_bound(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    invalid = tmp_path / "not-image.txt"
    _image(left, (10, 20, 30))
    _image(right, (10, 20, 30))
    invalid.write_text("not an image")
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(
        "\n".join(
            json.dumps(record)
            for record in (
                    {
                        "pair_id": "pass",
                        "left": str(left),
                        "right": str(right),
                        "candidate_local_identifier": "candidate-pass",
                        "keeper_local_identifier": "keeper-pass",
                    },
                    {
                        "pair_id": "reject",
                        "left": str(left),
                        "right": str(invalid),
                        "candidate_local_identifier": "candidate-reject",
                        "keeper_local_identifier": "keeper-reject",
                    },
            )
        )
        + "\n"
    )

    report = compare_image_manifest(manifest, tmp_path / "report.json", SimilarityPolicy())

    assert report["delete_authorizing"] is False
    assert report["gate_passed"] is False
    assert report["counts"] == {
        "total": 2,
        "compared": 1,
        "passed": 1,
        "failed": 0,
        "rejected": 1,
        "byte_identical": 1,
    }
    assert report["items"][1]["error"]["code"] == "E_SIMILARITY_MEDIA_UNSUPPORTED"
    assert str(invalid) not in report["items"][1]["error"]["message"]
    digest = report.pop("report_sha256")
    assert digest == sha256_digest(report)


def test_pixel_report_authorizes_byte_different_images_within_policy(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 100, 100))
    _image(right, (102, 102, 102))
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "pair_id": "pair-1",
                "left": str(left),
                "right": str(right),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )

    report_path = tmp_path / "report.json"
    report = compare_image_manifest(manifest, report_path, SimilarityPolicy())

    assert report["gate_passed"] is True
    assert report["delete_authorizing"] is True
    assert report["counts"]["byte_identical"] == 0
    revalidate_similarity_report(load_similarity_report(report_path), manifest)


def test_byte_identical_pair_is_not_delete_authorizing(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 100, 100))
    right.write_bytes(left.read_bytes())
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "pair_id": "pair-1",
                "left": str(left),
                "right": str(right),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )

    report = compare_image_manifest(manifest, tmp_path / "report.json", SimilarityPolicy())

    assert report["gate_passed"] is True
    assert report["delete_authorizing"] is False
    assert report["counts"]["byte_identical"] == 1


def test_lax_pixel_policy_is_never_delete_authorizing(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 100, 100))
    _image(right, (110, 110, 110))
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "pair_id": "pair-1",
                "left": str(left),
                "right": str(right),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )

    report = compare_image_manifest(
        manifest,
        tmp_path / "report.json",
        SimilarityPolicy(max_rgb_mae=0.5, max_luma_mae=0.5, max_rgb_p99=0.5),
    )

    assert report["gate_passed"] is True
    assert report["delete_authorizing"] is False


def test_pair_source_drift_invalidates_authorizing_report(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    _image(left, (100, 100, 100))
    _image(right, (102, 102, 102))
    manifest = tmp_path / "pairs.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "pair_id": "pair-1",
                "left": str(left),
                "right": str(right),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )
    report_path = tmp_path / "report.json"
    compare_image_manifest(manifest, report_path, SimilarityPolicy())
    _image(left, (120, 120, 120))

    with pytest.raises(ApplePhotosError) as captured:
        revalidate_similarity_report(load_similarity_report(report_path), manifest)

    assert captured.value.code == "E_PIXEL_EVIDENCE_STALE"


def test_cli_returns_partial_when_any_pair_is_rejected(tmp_path: Path, capsys) -> None:
    left = tmp_path / "left.png"
    invalid = tmp_path / "not-image.txt"
    _image(left, (10, 20, 30))
    invalid.write_text("not an image")
    manifest = tmp_path / "pairs.jsonl"
    report_path = tmp_path / "report.json"
    manifest.write_text(
        json.dumps(
            {
                "pair_id": "reject",
                "left": str(left),
                "right": str(invalid),
                "candidate_local_identifier": "candidate-id",
                "keeper_local_identifier": "keeper-id",
            }
        )
        + "\n"
    )

    exit_code = main(
        [
            "evidence",
            "compare-images",
            "--input-manifest",
            str(manifest),
            "--output",
            str(report_path),
        ]
    )
    envelope = json.loads(capsys.readouterr().out)

    assert exit_code == 8
    assert envelope["ok"] is False
    assert envelope["status"] == "partial"
