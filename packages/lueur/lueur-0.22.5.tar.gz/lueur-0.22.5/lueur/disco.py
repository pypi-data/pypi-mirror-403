import secrets
from datetime import datetime, timezone
from pathlib import Path

from .make_id import make_id
from .models import Discovery, Meta, Resource

__all__ = ["merge_discoveries", "load_discovery"]


def merge_discoveries(
    *discoveries: Discovery,
) -> Discovery:
    name = secrets.token_hex(8)

    resources: list[Resource] = []
    for d in discoveries:
        resources.extend(d.resources)

    return Discovery(
        id=make_id(name),
        resources=resources,
        meta=Meta(
            name=name,
            display=f"Snaphot {datetime.now(timezone.utc)}",
            kind="mixed",
            category=None,
        ),
    )


def load_discovery(snapshot_file: Path) -> Discovery:
    return Discovery.model_validate_json(snapshot_file.read_bytes())
