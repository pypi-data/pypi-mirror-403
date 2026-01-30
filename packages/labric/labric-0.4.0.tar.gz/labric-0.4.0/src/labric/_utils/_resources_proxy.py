from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `labric.resources` module.

    This is used so that we can lazily import `labric.resources` only when
    needed *and* so that users can just import `labric` and reference `labric.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("labric.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
