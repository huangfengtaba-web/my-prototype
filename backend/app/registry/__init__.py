# -*- coding: utf-8 -*-
"""技能注册表包。

导入本包即完成全部技能注册（skills/__init__.py 里 import 各技能模块）。
"""
from backend.app.registry.core import (  # noqa: F401
    CATEGORY_ORDER,
    CATEGORY_TITLES,
    REGISTRY,
    get,
    legacy_view,
    names,
    register,
    system_prompt_fragment,
    to_mcp_tools,
    to_openai_tools,
    to_panel,
)
from backend.app.registry.types import Goal, Skill  # noqa: F401
from backend.app.registry.validate import validate, validate_args  # noqa: F401
from backend.app.registry import skills  # noqa: F401  （触发注册，必须放在最后）

__all__ = [
    "REGISTRY", "Skill", "Goal",
    "register", "get", "names", "legacy_view",
    "to_openai_tools", "to_mcp_tools", "to_panel", "system_prompt_fragment",
    "validate", "validate_args",
    "CATEGORY_ORDER", "CATEGORY_TITLES",
]
