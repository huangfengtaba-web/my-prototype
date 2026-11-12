# -*- coding: utf-8 -*-
"""技能定义集合。

导入本模块即完成全部技能注册。新增技能时在此追加 import。
"""
from backend.app.registry.skills import cases  # noqa: F401
from backend.app.registry.skills import sim  # noqa: F401
from backend.app.registry.skills import solving  # noqa: F401
from backend.app.registry.skills import workflow  # noqa: F401

__all__ = ["cases", "solving", "sim", "workflow"]
