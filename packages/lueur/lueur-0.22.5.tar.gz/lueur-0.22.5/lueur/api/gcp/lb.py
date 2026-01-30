import re
from typing import Any, Pattern, cast
from urllib.parse import urlparse

from pydantic import BaseModel

from lueur.resource import iter_resource

__all__ = ["lb_config_from_url", "LoadBalancerConfig"]


class LoadBalancerConfig(BaseModel):
    project: str
    url: str
    service: str
    urlmap: str
    path_matcher: str
    path: str
    is_global: bool = False
    is_regional: bool = False


def lb_config_from_url(
    snapshot: dict[str, Any], url: str
) -> LoadBalancerConfig | None:
    """
    Extract the load balancer config for a given URL.
    """
    defaults = {
        "project": "",
        "url": url,
        "service": "",
        "urlmap": "",
        "path_matcher": "",
        "path": "",
        "is_global": False,
        "is_regional": False,
    }

    p = urlparse(url)
    host = p.hostname
    path = p.path

    for m in iter_resource(
        snapshot,
        f"$.resources[?@.struct.hostRules.*.hosts contains '{host}']",
    ):
        urlmap = cast(dict, m.value)
        defaults["is_global"] = (
            True if urlmap["meta"]["kind"].startswith("global-") else False
        )
        defaults["is_regional"] = not defaults["is_global"]
        defaults["project"] = urlmap["meta"]["project"]
        matches = extract_path_prefixes(urlmap)
        defaults.update(get_first_match(matches, path or "/"))

        return LoadBalancerConfig.model_validate(defaults)

    return None


###############################################################################
# Private functions
###############################################################################
def extract_path_prefixes(
    urlmap: dict[str, Any],
) -> dict[Pattern, dict[str, str]]:
    matches = {}

    for pm in urlmap["struct"]["pathMatchers"]:
        for rr in pm["routeRules"]:
            for mr in rr.get("matchRules", []):
                if "prefixMatch" in mr:
                    matches[re.compile(f"^{mr['prefixMatch']}")] = {
                        "urlmap": urlmap["meta"]["name"],
                        "service": get_higest_priority_service(
                            rr["routeAction"]["weightedBackendServices"]
                        ),
                        "path_matcher": pm["name"],
                        "path": mr["prefixMatch"],
                    }
                elif "fullPathMatch" in mr:
                    matches[re.compile(f"^{mr['fullPathMatch']}$")] = {
                        "urlmap": urlmap["meta"]["name"],
                        "service": get_higest_priority_service(
                            rr["routeAction"]["weightedBackendServices"]
                        ),
                        "path_matcher": pm["name"],
                        "path": mr["fullPathMatch"],
                    }
                elif "regexMatch" in mr:
                    matches[re.compile(mr["regexMatch"])] = {
                        "urlmap": urlmap["meta"]["name"],
                        "service": get_higest_priority_service(
                            rr["routeAction"]["weightedBackendServices"]
                        ),
                        "path_matcher": pm["name"],
                        "path": mr["regexMatch"],
                    }

    return matches


def get_higest_priority_service(services: list[dict[str, Any]]) -> str:
    return max(services, key=lambda x: x["weight"])["backendService"].rsplit(
        "/", 1
    )[-1]


def get_first_match(
    matches: dict[Pattern, dict[str, str]], path: str
) -> dict[str, str]:
    for k, v in matches.items():
        if k.match(path):
            return v

    return {}
