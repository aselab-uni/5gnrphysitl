from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import numpy as np


def infer_shape(value: Any) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return [int(dim) for dim in value.shape]
    if hasattr(value, "shape") and not isinstance(value, (str, bytes)):
        try:
            return [int(dim) for dim in value.shape]
        except Exception:  # pragma: no cover
            return None
    if isinstance(value, (list, tuple)):
        return [int(dim) for dim in np.asarray(value, dtype=object).shape]
    return None


@dataclass(slots=True)
class StageArtifact:
    name: str
    artifact_type: str
    payload: Any
    description: str
    input_shape: list[int] | None = None
    output_shape: list[int] | None = None
    notes: str = ""
    excerpt: str | None = None
    symbol_sensitive: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.artifact_type,
            "artifact_type": self.artifact_type,
            "payload": self.payload,
            "description": self.description,
            "input_shape": self.input_shape,
            "output_shape": self.output_shape,
            "notes": self.notes,
            "excerpt": self.excerpt,
            "symbol_sensitive": self.symbol_sensitive,
        }


@dataclass(slots=True)
class PipelineStage:
    key: str
    section: str
    flow_label: str
    title: str
    description: str
    metrics: dict[str, Any]
    artifacts: list[StageArtifact]
    input_shape: list[int] | None = None
    output_shape: list[int] | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "section": self.section,
            "flow_label": self.flow_label,
            "title": self.title,
            "description": self.description,
            "metrics": self.metrics,
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
            "artifact_type": self.artifacts[0].artifact_type if self.artifacts else "text",
            "input_shape": self.input_shape,
            "output_shape": self.output_shape,
            "notes": self.notes,
        }


def normalize_stage_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(artifact)
    artifact_type = str(normalized.get("artifact_type", normalized.get("kind", "text")))
    payload = normalized.get("payload")
    normalized["kind"] = artifact_type
    normalized["artifact_type"] = artifact_type
    normalized.setdefault("input_shape", infer_shape(payload))
    normalized.setdefault("output_shape", infer_shape(payload))
    normalized.setdefault("notes", "")
    normalized.setdefault("excerpt", None)
    normalized.setdefault("symbol_sensitive", artifact_type in {"grid", "waveform", "constellation_compare"})
    return normalized


def normalize_pipeline_stage(stage: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(stage)
    artifacts = normalized.get("artifacts")
    if artifacts is None:
        artifacts = [
            {
                "name": normalized.get("artifact_name", "Primary view"),
                "kind": normalized.get("preview_kind", "text"),
                "payload": normalized.get("data"),
                "description": normalized.get("description", ""),
            }
        ]
    normalized_artifacts = [normalize_stage_artifact(artifact) for artifact in artifacts]
    normalized["artifacts"] = normalized_artifacts
    normalized["artifact_type"] = normalized.get(
        "artifact_type",
        normalized_artifacts[0]["artifact_type"] if normalized_artifacts else "text",
    )
    normalized.setdefault("input_shape", normalized_artifacts[0].get("input_shape") if normalized_artifacts else None)
    normalized.setdefault("output_shape", normalized_artifacts[0].get("output_shape") if normalized_artifacts else None)
    normalized.setdefault("notes", "")
    metrics = dict(normalized.get("metrics", {}))
    metrics.setdefault("Artifact type", normalized["artifact_type"])
    metrics.setdefault("Input shape", normalized.get("input_shape"))
    metrics.setdefault("Output shape", normalized.get("output_shape"))
    normalized["metrics"] = metrics
    return normalized


def stage_artifact(
    *,
    name: str,
    artifact_type: str,
    payload: Any,
    description: str,
    input_shape: list[int] | None = None,
    output_shape: list[int] | None = None,
    notes: str = "",
    excerpt: str | None = None,
    symbol_sensitive: bool = False,
) -> dict[str, Any]:
    return StageArtifact(
        name=name,
        artifact_type=artifact_type,
        payload=payload,
        description=description,
        input_shape=input_shape,
        output_shape=output_shape if output_shape is not None else infer_shape(payload),
        notes=notes,
        excerpt=excerpt,
        symbol_sensitive=symbol_sensitive,
    ).as_dict()


def pipeline_stage(
    *,
    key: str,
    section: str,
    flow_label: str,
    title: str,
    description: str,
    metrics: Mapping[str, Any],
    artifacts: Iterable[Mapping[str, Any]],
    input_shape: list[int] | None = None,
    output_shape: list[int] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    normalized_artifacts = [normalize_stage_artifact(artifact) for artifact in artifacts]
    return PipelineStage(
        key=key,
        section=section,
        flow_label=flow_label,
        title=title,
        description=description,
        metrics=dict(metrics),
        artifacts=[
            StageArtifact(
                name=str(artifact["name"]),
                artifact_type=str(artifact["artifact_type"]),
                payload=artifact.get("payload"),
                description=str(artifact.get("description", "")),
                input_shape=artifact.get("input_shape"),
                output_shape=artifact.get("output_shape"),
                notes=str(artifact.get("notes", "")),
                excerpt=artifact.get("excerpt"),
                symbol_sensitive=bool(artifact.get("symbol_sensitive", False)),
            )
            for artifact in normalized_artifacts
        ],
        input_shape=input_shape,
        output_shape=output_shape if output_shape is not None else (normalized_artifacts[0].get("output_shape") if normalized_artifacts else None),
        notes=notes,
    ).as_dict()
