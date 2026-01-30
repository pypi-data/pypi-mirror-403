"""Decorators for django-boosted."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class AdminBoostViewConfig:
    """Configuration for admin boost view decorator."""

    template_name: str | None = None
    path_fragment: str | None = None
    requires_object: bool | None = None
    permission: str = "view"


def admin_boost_view(
    view_type: str,
    label: str,
    *,
    config: AdminBoostViewConfig | None = None,
    **kwargs,
):
    if config is None:
        config = AdminBoostViewConfig(
            template_name=kwargs.get("template_name"),
            path_fragment=kwargs.get("path_fragment"),
            requires_object=kwargs.get("requires_object"),
            permission=kwargs.get("permission", "view"),
        )

    def decorator(func: Callable) -> Callable:
        func._admin_boost_view_config = {  # type: ignore[attr-defined]
            "name": func.__name__,
            "view_type": view_type,
            "label": label,
            "template_name": config.template_name,
            "path_fragment": config.path_fragment,
            "requires_object": config.requires_object,
            "permission": config.permission,
        }
        return func

    return decorator
