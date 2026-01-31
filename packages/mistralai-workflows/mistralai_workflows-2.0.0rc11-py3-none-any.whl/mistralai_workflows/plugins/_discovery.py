import importlib
import pkgutil
from importlib.metadata import packages_distributions, version
from typing import NamedTuple, cast

PLUGIN_NAMESPACE = cast(str, __package__)  # cast so it's not typed as optional str
SELF = __name__.split(".")[-1]


class ContributionInfo(NamedTuple):
    name: str
    ispkg: bool
    dist_name: str | None
    dist_version: str | None


def list_plugins() -> list[ContributionInfo]:
    """List names and versions of all installed plugins."""
    pkg_to_dist = packages_distributions()
    results: list[ContributionInfo] = []
    for module_info in pkgutil.iter_modules(importlib.import_module(PLUGIN_NAMESPACE).__path__):
        if module_info.name != SELF:
            import_name = f"{PLUGIN_NAMESPACE}.{module_info.name}"
            dist_names = pkg_to_dist.get(import_name, [])
            (dist_name, dist_version) = (dist_names[0], version(dist_names[0])) if dist_names else (None, None)
            results.append(ContributionInfo(module_info.name, module_info.ispkg, dist_name, dist_version))
    return results
