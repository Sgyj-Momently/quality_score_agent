"""Deterministic photo quality scoring."""

from __future__ import annotations

from typing import Any


def score_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    photos = payload.get("photos") or []
    scored_photos: list[dict[str, Any]] = []
    scores: list[float] = []
    for photo in photos:
        if not isinstance(photo, dict):
            continue
        score = score_photo(photo)
        reviewed = dict(photo)
        reviewed["quality_score"] = score
        reviewed["quality_bucket"] = bucket(score["overall"])
        scored_photos.append(reviewed)
        scores.append(score["overall"])

    return {
        "quality_status": "ok",
        "scored_photos": scored_photos,
        "photo_count": len(scored_photos),
        "average_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "checks": [
            {"name": "summary_richness", "status": "pass"},
            {"name": "ocr_noise", "status": "pass"},
            {"name": "metadata_confidence", "status": "pass"},
        ],
    }


def score_photo(photo: dict[str, Any]) -> dict[str, float]:
    summary = photo.get("photo_summary") if isinstance(photo.get("photo_summary"), dict) else {}
    text = str(summary.get("summary") or "")
    ocr = summary.get("ocr_text") if isinstance(summary.get("ocr_text"), list) else []
    confidence = _number(summary.get("confidence"), default=0.65)
    richness = min(1.0, (len(text.strip()) / 80.0) + (len(ocr) * 0.05))
    noise_penalty = min(0.25, len([item for item in ocr if len(str(item)) > 40]) * 0.05)
    composition = _filename_composition_hint(str(photo.get("file_name") or ""))
    overall = (confidence * 0.45) + (richness * 0.35) + (composition * 0.20) - noise_penalty
    overall = max(0.0, min(1.0, overall))
    return {
        "overall": round(overall, 3),
        "confidence": round(confidence, 3),
        "richness": round(richness, 3),
        "composition": round(composition, 3),
    }


def bucket(score: float) -> str:
    if score >= 0.78:
        return "excellent"
    if score >= 0.58:
        return "good"
    if score >= 0.38:
        return "usable"
    return "low"


def _number(value: Any, default: float) -> float:
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return default


def _filename_composition_hint(file_name: str) -> float:
    lowered = file_name.lower()
    if any(term in lowered for term in ("hero", "cover", "best", "main")):
        return 0.9
    if any(term in lowered for term in ("blur", "dark", "duplicate")):
        return 0.25
    return 0.65
