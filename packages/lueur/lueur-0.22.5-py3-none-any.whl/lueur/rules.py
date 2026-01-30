from pathlib import Path
from typing import Any, Iterable

import jsonpath

from lueur.models import Resource, Rule, Rules

__all__ = [
    "load_all_rules",
    "match_by_rule",
    "iter_resource",
    "get_at",
    "get_resource",
]


def load_all_rules(definitions: str | Path) -> Rules:
    return Rules.model_validate_json(Path(definitions).read_bytes())


def match_by_rule(resource: Resource, rule: Rule) -> Any | None:
    return jsonpath.findall(rule.matcher.path, resource.struct)


def iter_resource(
    discovery: dict[str, Any], path: str
) -> Iterable[jsonpath.JSONPathMatch]:
    yield from jsonpath.finditer(path, discovery)


def get_at(discovery: dict[str, Any], pointer: str) -> Any:
    return jsonpath.JSONPointer(pointer).resolve(discovery)


def get_resource(
    discovery: dict[str, Any], path: str
) -> jsonpath.JSONPathMatch | None:
    return jsonpath.match(path, discovery)
