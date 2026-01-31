from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `ost_builder.resources` module.

    This is used so that we can lazily import `ost_builder.resources` only when
    needed *and* so that users can just import `ost_builder` and reference `ost_builder.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("ost_builder.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
