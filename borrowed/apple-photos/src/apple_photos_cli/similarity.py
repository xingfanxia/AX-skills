from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import os
import stat
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageCms, ImageOps

from apple_photos_cli.canonical import sha256_digest
from apple_photos_cli.errors import stale, usage_error
from apple_photos_cli.manifests import validate_schema
from apple_photos_cli.models import SCHEMA_VERSION

MAX_INPUT_BYTES = 1024 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000
SUPPORTED_8_BIT_MODES = {"1", "L", "LA", "P", "RGB", "RGBA"}


@dataclass(frozen=True, slots=True)
class SimilarityPolicy:
    max_rgb_mae: float = 0.01
    max_luma_mae: float = 0.01
    max_rgb_p99: float = 0.05

    def validate(self) -> None:
        for name, value in (
            ("max_rgb_mae", self.max_rgb_mae),
            ("max_luma_mae", self.max_luma_mae),
            ("max_rgb_p99", self.max_rgb_p99),
        ):
            if not 0 <= value <= 1:
                raise usage_error(f"{name} must be between 0 and 1.")

    def to_dict(self) -> dict[str, float]:
        return {
            "max_rgb_mae": self.max_rgb_mae,
            "max_luma_mae": self.max_luma_mae,
            "max_rgb_p99": self.max_rgb_p99,
        }

    def delete_eligible(self) -> bool:
        return (
            self.max_rgb_mae <= 0.01
            and self.max_luma_mae <= 0.01
            and self.max_rgb_p99 <= 0.05
        )


def _read_frozen_bytes(path: Path, *, label: str) -> bytes:
    try:
        with path.open("rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise usage_error(f"{label} must be a regular file.")
            chunks = []
            byte_count = 0
            while chunk := stream.read(1024 * 1024):
                byte_count += len(chunk)
                if byte_count > MAX_INPUT_BYTES:
                    raise usage_error(
                        f"{label} exceeds the {MAX_INPUT_BYTES}-byte input limit.",
                        code="E_SIMILARITY_INPUT_TOO_LARGE",
                    )
                chunks.append(chunk)
            return b"".join(chunks)
    except OSError as exc:
        raise usage_error(
            f"Cannot read {label}.", code="E_SIMILARITY_READ_FAILED"
        ) from exc


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _source_bit_depth(data: bytes, source: Image.Image) -> int | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 25:
        return data[24]
    tags = getattr(source, "tag_v2", None)
    if tags is not None and 258 in tags:
        values = tags[258]
        if isinstance(values, int):
            return values
        return max(int(value) for value in values)
    bits = getattr(source, "bits", None)
    return int(bits) if bits is not None else None


def _normalized_rgb(
    data: bytes, *, media_type: str | None, label: str
) -> tuple[Image.Image, dict[str, Any]]:
    if media_type and not media_type.startswith("image/"):
        raise usage_error(
            f"{label} is not a still image.",
            code="E_SIMILARITY_MEDIA_UNSUPPORTED",
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise usage_error(
                        f"{label} exceeds the {MAX_IMAGE_PIXELS}-pixel decode limit.",
                        code="E_SIMILARITY_IMAGE_TOO_LARGE",
                    )
                if getattr(source, "n_frames", 1) != 1:
                    raise usage_error(
                        f"{label} is animated or multi-frame.",
                        code="E_SIMILARITY_MEDIA_UNSUPPORTED",
                    )
                source_bit_depth = _source_bit_depth(data, source)
                if source_bit_depth is None:
                    raise usage_error(
                        f"{label} source bit depth cannot be verified.",
                        code="E_SIMILARITY_BIT_DEPTH_UNVERIFIED",
                    )
                if source_bit_depth is not None and source_bit_depth > 8:
                    raise usage_error(
                        f"{label} uses unsupported {source_bit_depth}-bit samples.",
                        code="E_SIMILARITY_BIT_DEPTH_UNSUPPORTED",
                    )
                if source.mode not in SUPPORTED_8_BIT_MODES:
                    raise usage_error(
                        f"{label} uses unsupported pixel mode {source.mode}.",
                        code="E_SIMILARITY_BIT_DEPTH_UNSUPPORTED",
                    )
                transposed = ImageOps.exif_transpose(source)
                if transposed.mode in {"LA", "RGBA"} or "transparency" in transposed.info:
                    alpha = transposed.convert("RGBA").getchannel("A")
                    if alpha.getextrema() != (255, 255):
                        raise usage_error(
                            f"{label} has non-opaque alpha.",
                            code="E_SIMILARITY_ALPHA_UNSUPPORTED",
                        )
                icc_profile = transposed.info.get("icc_profile")
                color_normalization = "assumed_srgb"
                if icc_profile:
                    try:
                        source_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile))
                        target_profile = ImageCms.createProfile("sRGB")
                        normalized = ImageCms.profileToProfile(
                            transposed, source_profile, target_profile, outputMode="RGB"
                        )
                        color_normalization = "embedded_icc_to_srgb"
                    except (ImageCms.PyCMSError, OSError, TypeError, ValueError) as exc:
                        raise usage_error(
                            f"Cannot normalize {label} ICC profile.",
                            code="E_SIMILARITY_COLOR_PROFILE",
                        ) from exc
                else:
                    normalized = transposed.convert("RGB")
                image = normalized.copy()
                return image, {
                    "width": image.width,
                    "height": image.height,
                    "orientation_normalization": "exif_transpose",
                    "color_normalization": color_normalization,
                    "source_mode": source.mode,
                    "source_bit_depth": source_bit_depth,
                }
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise usage_error(
            f"{label} exceeds Pillow's safe decode limit.",
            code="E_SIMILARITY_IMAGE_TOO_LARGE",
        ) from exc
    except (OSError, ValueError, SyntaxError) as exc:
        raise usage_error(
            f"Cannot decode {label}.", code="E_SIMILARITY_DECODE_FAILED"
        ) from exc


def _mean_from_histogram(histogram: list[int], sample_count: int) -> float:
    weighted = sum((index % 256) * count for index, count in enumerate(histogram))
    return weighted / (sample_count * 255)


def _quantile_from_histogram(histogram: list[int], quantile: float) -> float:
    target = sum(histogram) * quantile
    cumulative = 0
    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= target:
            return value / 255
    return 1.0


def compare_images(left: Path, right: Path, policy: SimilarityPolicy) -> dict[str, Any]:
    policy.validate()
    left_bytes = _read_frozen_bytes(left, label="left input")
    right_bytes = _read_frozen_bytes(right, label="right input")
    byte_identical = left_bytes == right_bytes
    left_image, left_decode = _normalized_rgb(
        left_bytes, media_type=mimetypes.guess_type(left.name)[0], label="left input"
    )
    try:
        right_image, right_decode = _normalized_rgb(
            right_bytes, media_type=mimetypes.guess_type(right.name)[0], label="right input"
        )
        try:
            dimensions_equal = left_image.size == right_image.size
            if not dimensions_equal:
                return {
                    "passed": False,
                    "byte_identical": byte_identical,
                    "dimensions_equal": False,
                    "left": {"sha256": _sha256_bytes(left_bytes), "decode": left_decode},
                    "right": {"sha256": _sha256_bytes(right_bytes), "decode": right_decode},
                    "metrics": None,
                    "failed_checks": ["dimensions_equal"],
                }

            pixel_count = left_image.width * left_image.height
            rgb_difference = ImageChops.difference(left_image, right_image)
            try:
                rgb_histogram = rgb_difference.histogram()
                channel_differences = rgb_difference.split()
                try:
                    first_two_max = ImageChops.lighter(
                        channel_differences[0], channel_differences[1]
                    )
                    try:
                        pixel_max_difference = ImageChops.lighter(
                            first_two_max, channel_differences[2]
                        )
                        try:
                            pixel_max_histogram = pixel_max_difference.histogram()
                        finally:
                            pixel_max_difference.close()
                    finally:
                        first_two_max.close()
                finally:
                    for channel in channel_differences:
                        channel.close()
                left_luma = left_image.convert("L")
                right_luma = right_image.convert("L")
                try:
                    luma_difference = ImageChops.difference(left_luma, right_luma)
                    try:
                        luma_histogram = luma_difference.histogram()
                    finally:
                        luma_difference.close()
                finally:
                    left_luma.close()
                    right_luma.close()
            finally:
                rgb_difference.close()
            metrics = {
                "rgb_mean_absolute_error": _mean_from_histogram(
                    rgb_histogram, pixel_count * 3
                ),
                "luma_mean_absolute_error": _mean_from_histogram(luma_histogram, pixel_count),
                "rgb_p99_absolute_error": _quantile_from_histogram(
                    pixel_max_histogram, 0.99
                ),
                "rgb_max_absolute_error": max(
                    (value for value, count in enumerate(pixel_max_histogram) if count),
                    default=0,
                )
                / 255,
            }
        finally:
            right_image.close()
    finally:
        left_image.close()
    failed_checks = [
        name
        for name, passed in (
            ("rgb_mean_absolute_error", metrics["rgb_mean_absolute_error"] <= policy.max_rgb_mae),
            (
                "luma_mean_absolute_error",
                metrics["luma_mean_absolute_error"] <= policy.max_luma_mae,
            ),
            ("rgb_p99_absolute_error", metrics["rgb_p99_absolute_error"] <= policy.max_rgb_p99),
        )
        if not passed
    ]
    return {
        "passed": not failed_checks,
        "byte_identical": byte_identical,
        "dimensions_equal": True,
        "left": {"sha256": _sha256_bytes(left_bytes), "decode": left_decode},
        "right": {"sha256": _sha256_bytes(right_bytes), "decode": right_decode},
        "metrics": metrics,
        "failed_checks": failed_checks,
    }


def load_pair_manifest(path: Path, *, frozen_bytes: bytes | None = None) -> list[dict[str, Any]]:
    pairs = []
    seen_ids: set[str] = set()
    try:
        content = frozen_bytes if frozen_bytes is not None else _read_frozen_bytes(
            path, label="pair manifest"
        )
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise usage_error(f"Cannot read pair manifest: {path}") from exc
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            pair_id = value["pair_id"]
            left = value["left"]
            right = value["right"]
            candidate = value["candidate_local_identifier"]
            keeper = value["keeper_local_identifier"]
            if not all(
                isinstance(item, str) and item
                for item in (pair_id, left, right, candidate, keeper)
            ):
                raise TypeError
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise usage_error(
                f"Invalid pair manifest record on line {number}.", code="E_SCHEMA_INVALID"
            ) from exc
        if pair_id in seen_ids:
            raise usage_error(f"Duplicate pair_id on line {number}.", code="E_SCHEMA_INVALID")
        seen_ids.add(pair_id)
        if candidate == keeper:
            raise usage_error(
                f"Pair candidate and keeper must differ on line {number}.",
                code="E_SCHEMA_INVALID",
            )
        pairs.append(
            {
                "pair_id": pair_id,
                "left": Path(left),
                "right": Path(right),
                "candidate_local_identifier": candidate,
                "keeper_local_identifier": keeper,
            }
        )
        if len(pairs) > 50:
            raise usage_error(
                "Pixel evidence is limited to 50 pairs per report.",
                code="E_DELETE_BATCH_TOO_LARGE",
            )
    if not pairs:
        raise usage_error("Pair manifest must contain at least one record.")
    return pairs


def compare_image_manifest(
    manifest_path: Path, output: Path, policy: SimilarityPolicy
) -> dict[str, Any]:
    policy.validate()
    manifest_bytes = _read_frozen_bytes(manifest_path, label="pair manifest")
    items = []
    for pair in load_pair_manifest(manifest_path, frozen_bytes=manifest_bytes):
        try:
            comparison = compare_images(pair["left"], pair["right"], policy)
            item = {
                "pair_id": pair["pair_id"],
                "candidate_local_identifier": pair["candidate_local_identifier"],
                "keeper_local_identifier": pair["keeper_local_identifier"],
                "status": "compared",
                **comparison,
            }
        except Exception as exc:
            from apple_photos_cli.errors import ApplePhotosError

            if not isinstance(exc, ApplePhotosError):
                raise
            item = {
                "pair_id": pair["pair_id"],
                "candidate_local_identifier": pair["candidate_local_identifier"],
                "keeper_local_identifier": pair["keeper_local_identifier"],
                "status": "rejected",
                "passed": False,
                "error": exc.to_dict(),
            }
        items.append(item)

    compared = sum(item["status"] == "compared" for item in items)
    passed = sum(item["status"] == "compared" and item["passed"] for item in items)
    rejected = sum(item["status"] == "rejected" for item in items)
    byte_identical = sum(
        item["status"] == "compared" and item["byte_identical"] for item in items
    )
    gate_passed = passed == len(items)
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "apple_photos_pixel_similarity",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "mode": "pixel_similarity_delete_evidence",
        "delete_authorizing": gate_passed and byte_identical == 0 and policy.delete_eligible(),
        "source_manifest_sha256": _sha256_bytes(manifest_bytes),
        "policy": policy.to_dict(),
        "counts": {
            "total": len(items),
            "compared": compared,
            "passed": passed,
            "failed": compared - passed,
            "rejected": rejected,
            "byte_identical": byte_identical,
        },
        "gate_passed": gate_passed,
        "items": items,
    }
    report["report_sha256"] = sha256_digest(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def load_similarity_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise usage_error(
            "Cannot read pixel similarity report.", code="E_SIMILARITY_READ_FAILED"
        ) from exc
    except json.JSONDecodeError as exc:
        raise usage_error(
            "Pixel similarity report is not valid JSON.", code="E_SCHEMA_INVALID"
        ) from exc
    if not isinstance(report, dict):
        raise usage_error(
            "Pixel similarity report root must be an object.", code="E_SCHEMA_INVALID"
        )
    validate_schema(report, "pixel-similarity-report-v1.schema.json")
    sealed = dict(report)
    observed_digest = sealed.pop("report_sha256")
    if sha256_digest(sealed) != observed_digest:
        raise stale(
            "Pixel similarity report digest does not match its contents.",
            code="E_MANIFEST_TAMPERED",
        )
    items = report["items"]
    pair_ids = [item["pair_id"] for item in items]
    candidates = [item["candidate_local_identifier"] for item in items]
    keepers = {item["keeper_local_identifier"] for item in items}
    if len(pair_ids) != len(set(pair_ids)) or len(candidates) != len(set(candidates)):
        raise usage_error(
            "Pixel report pair and candidate identifiers must be unique.",
            code="E_SCHEMA_INVALID",
        )
    if set(candidates) & keepers:
        raise usage_error("A delete candidate cannot also be a keeper.", code="E_SCHEMA_INVALID")
    compared = sum(item["status"] == "compared" for item in items)
    passed = sum(item["status"] == "compared" and item["passed"] for item in items)
    rejected = sum(item["status"] == "rejected" for item in items)
    byte_identical = sum(
        item["status"] == "compared" and item["byte_identical"] for item in items
    )
    expected_counts = {
        "total": len(items),
        "compared": compared,
        "passed": passed,
        "failed": compared - passed,
        "rejected": rejected,
        "byte_identical": byte_identical,
    }
    if report["counts"] != expected_counts:
        raise usage_error("Pixel report counts are inconsistent.", code="E_SCHEMA_INVALID")
    gate_passed = passed == len(items)
    policy = SimilarityPolicy(**report["policy"])
    policy.validate()
    delete_authorizing = gate_passed and byte_identical == 0 and policy.delete_eligible()
    if report["gate_passed"] != gate_passed or report["delete_authorizing"] != delete_authorizing:
        raise usage_error(
            "Pixel report authorization state is inconsistent.", code="E_SCHEMA_INVALID"
        )
    return report


def revalidate_similarity_report(report: dict[str, Any], pair_manifest: Path) -> None:
    manifest_bytes = _read_frozen_bytes(pair_manifest, label="pair manifest")
    if _sha256_bytes(manifest_bytes) != report["source_manifest_sha256"]:
        raise stale(
            "Pixel pair manifest digest does not match the report.",
            code="E_MANIFEST_TAMPERED",
        )
    pairs = load_pair_manifest(pair_manifest, frozen_bytes=manifest_bytes)
    if len(pairs) != len(report["items"]):
        raise stale("Pixel pair set changed after comparison.", code="E_PIXEL_EVIDENCE_STALE")
    policy = SimilarityPolicy(**report["policy"])
    for pair, item in zip(pairs, report["items"], strict=True):
        identity = {
            "pair_id": pair["pair_id"],
            "candidate_local_identifier": pair["candidate_local_identifier"],
            "keeper_local_identifier": pair["keeper_local_identifier"],
        }
        if any(item.get(key) != value for key, value in identity.items()):
            raise stale(
                "Pixel pair identity changed after comparison.",
                code="E_PIXEL_EVIDENCE_STALE",
            )
        try:
            comparison = compare_images(pair["left"], pair["right"], policy)
        except Exception as exc:
            from apple_photos_cli.errors import ApplePhotosError

            if not isinstance(exc, ApplePhotosError):
                raise
            raise stale(
                f"Pixel pair can no longer be verified: {pair['pair_id']}.",
                code="E_PIXEL_EVIDENCE_STALE",
            ) from exc
        expected = {**identity, "status": "compared", **comparison}
        if item != expected:
            raise stale(
                f"Pixel comparison changed for {pair['pair_id']}.",
                code="E_PIXEL_EVIDENCE_STALE",
            )
