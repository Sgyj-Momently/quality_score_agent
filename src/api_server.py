"""FastAPI entrypoint for the quality score agent."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

from .error_envelope import install_envelope_handlers
from .scorer import score_bundle

app = FastAPI(title="Quality Score Agent API", version="0.1.0")

# ADR 005 표준 에러 envelope 등록.
install_envelope_handlers(app)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


class QualityScoreRequest(BaseModel):
    project_id: str = Field(min_length=1)
    photos: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quality_score_agent"}


@app.post("/api/v1/quality-scores")
def create_quality_scores(request: QualityScoreRequest) -> dict[str, Any]:
    return {"project_id": request.project_id, **score_bundle(request.model_dump())}

