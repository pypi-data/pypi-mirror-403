from datetime import datetime
from typing import Any, Literal, cast

import msgspec
from pydantic import BaseModel, Field, RootModel

from lueur.date_time import now

__all__ = [
    "Resource",
    "Meta",
    "Discovery",
    "Recommendation",
    "Rule",
    "Rules",
    "GCPProject",
    "K8SMeta",
    "AWSMeta",
    "GrafanaMeta",
]


class Link(BaseModel):
    direction: Literal["in", "out"]
    kind: str
    path: str
    pointer: str
    id: str


class Meta(BaseModel):
    name: str
    display: str
    dt: datetime = Field(default_factory=now)
    kind: str
    platform: str | None = None
    category: (
        Literal[
            "network",
            "observability",
            "storage",
            "compute",
            "security",
            "loadbalancer",
            "integration",
            "memorystore",
            "sql",
            "gke",
            "dns",
        ]
        | None
    )


class GCPMeta(Meta):
    project: str
    region: str | None = None
    zone: str | None = None
    self_link: str | None = None
    regional: bool = False


class K8SMeta(Meta):
    ns: str | None = None


class AWSMeta(Meta):
    region: str | None = None


class GrafanaMeta(Meta):
    pass


class Resource(BaseModel):
    id: str
    meta: Meta | GCPMeta | AWSMeta | K8SMeta
    links: list[Link] = Field(default_factory=list)
    struct: dict


class Discovery(BaseModel):
    id: str
    meta: Meta
    resources: list[Resource]


class Recommendation(BaseModel):
    id: str
    meta: Meta


class JSonPathRuleMatcher(BaseModel):
    type: Literal["jsonpath"]
    path: str


class Rule(BaseModel):
    key: str
    target_kinds: list[str]
    reason: str
    explanation: str
    severity: Literal["critical", "warning", "info"]
    matcher: JSonPathRuleMatcher


Rules = RootModel[list[Rule]]


class FaultScenarioVar(BaseModel):
    type: Literal["env"] = "env"
    key: str
    default: bytes | dict | list | int | float | str | bool | None = None
    env_var_type: (
        Literal["bytes", "int", "float", "bool", "str", "json"] | None
    ) = "str"


Activity = RootModel[dict[str, Any]]


class FaultScenario(BaseModel):
    title: str
    purpose: str
    tags: list[str]
    vars: dict[str, FaultScenarioVar]
    faults: list[Activity]
    verification: dict[str, str | list[Activity]] | None = None
    rollbacks: list[Activity] | None = None

    def as_experiment(self) -> dict[str, Any]:
        x = {
            "title": self.title,
            "description": self.purpose,
            "tags": self.tags,
            "runtime": {
                "hypothesis": {"strategy": "default"},
                "rollbacks": {"strategy": "always"},
            },
            "configuration": {k: v.model_dump() for k, v in self.vars.items()},
            "method": [],
        }

        if self.verification:
            probes = cast(list[Activity], self.verification["probes"])
            x["steady-state-hypothesis"] = {
                "title": self.verification["title"],
                "probes": [f.model_dump() for f in probes],
            }

        if self.faults:
            x["method"] = [f.model_dump() for f in self.faults]

        if self.rollbacks:
            x["rollbacks"] = [f.model_dump() for f in self.rollbacks]

        return x


class GCPProject(BaseModel):
    id: str
    name: str
    organization: str


class SnapshotMeta(msgspec.Struct):
    name: str
    display: str
    kind: str
    region: str | None = None
    zone: str | None = None


class SnapshotLink(msgspec.Struct):
    pointer: str


class SnapshotResource(msgspec.Struct):
    meta: SnapshotMeta
    links: list[SnapshotLink]


class Snapshot(msgspec.Struct):
    resources: list[SnapshotResource]


class AbortFaultPolicy(BaseModel):
    http_status: int
    percentage: float


class DelayFaultPolicy(BaseModel):
    fixed_delay_seconds: str
    fixed_delay_nanos: int
    percentage: float


class HostRedirect(BaseModel):
    host: str
    path: str


class HostPath(BaseModel):
    paths: list[str]
    faults: list[AbortFaultPolicy | DelayFaultPolicy] | None = None


class HostRouteRule(BaseModel):
    priority: int
    kind: str
    path: str


class HostRoute(BaseModel):
    rules: list[HostRouteRule]


class HostRouteAction(BaseModel):
    default: bool = False


class Host(BaseModel):
    domains: list[str]
    paths: HostPath | HostRoute | HostRedirect | HostRouteAction


class LoadBalancer(BaseModel):
    name: str
    display: str
    region: str | None = None
    zone: str | None = None
    hosts: list[Host]
    snapshot_pointer: str


class SiteEntities(BaseModel):
    lb: list[LoadBalancer]


class Site(BaseModel):
    entities: SiteEntities


class ChatMessage(msgspec.Struct):
    role: Literal["system", "user"]
    content: str


class LatencyChat(msgspec.Struct):
    prelude: list[ChatMessage]
    ready: list[ChatMessage]
    postface: list[ChatMessage]


class HTTPErrorChat(msgspec.Struct):
    prelude: list[ChatMessage]
    ready: list[ChatMessage]
    postface: list[ChatMessage]


class CTKChat(msgspec.Struct):
    postface: list[ChatMessage]
