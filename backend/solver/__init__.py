# -*- coding: utf-8 -*-
"""GTX FSO Litho 求解器包。

两种运行方式都支持：
    python backend/solver/litho_solver.py      脚本模式
    python -m backend.solver run               包模式（推荐，见 cli.py）
"""
from . import litho_solver

__all__ = ["litho_solver"]
