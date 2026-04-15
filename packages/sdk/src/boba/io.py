"""File IO helpers for CLI and benchmark workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


def load_yaml_model(path: Path, model_type: type[ModelT]) -> ModelT:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return model_type.model_validate(payload)


def load_plan(path: Path, model_type: type[ModelT]) -> ModelT:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return model_type.model_validate_json(text)
    payload = yaml.safe_load(text)
    return model_type.model_validate(payload)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

