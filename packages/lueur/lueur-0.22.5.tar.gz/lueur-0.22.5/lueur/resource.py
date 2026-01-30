from typing import Any, Iterable

import jsonpath

__all__ = ["iter_resource", "match_path", "filter_out_keys"]


def iter_resource(
    discovery: dict[str, Any], path: str
) -> Iterable[jsonpath.JSONPathMatch]:
    yield from jsonpath.finditer(path, discovery)


def match_path(
    discovery: dict[str, Any], path: str
) -> jsonpath.JSONPathMatch | None:
    return jsonpath.match(path, discovery)


def filter_out_keys(
    struct: dict[str, Any], keys: list[str | list[str]]
) -> dict[str, Any]:
    for k in keys:
        if isinstance(k, dict):
            struct.pop(k, None)
        elif isinstance(k, list):
            current = struct
            for i in k[:-1]:
                current = struct.get(i)  # type: ignore
                if current is None:
                    break

            if current:
                current.pop(k[-1], None)

    return struct
