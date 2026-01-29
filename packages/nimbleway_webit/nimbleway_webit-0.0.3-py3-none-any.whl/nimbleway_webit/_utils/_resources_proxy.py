from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `nimbleway_webit.resources` module.

    This is used so that we can lazily import `nimbleway_webit.resources` only when
    needed *and* so that users can just import `nimbleway_webit` and reference `nimbleway_webit.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("nimbleway_webit.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
