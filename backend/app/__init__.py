# -*- coding: utf-8 -*-
"""GTX FSO Litho · 后端 API 包。

.env 加载位置说明（重要）：
    下面几个模块都在【模块级】读环境变量：
        store.py               → SUPABASE_DB_URL
        ai/dify_client.py      → DIFY_BASE / DIFY_KEY_*
        docgen/renderers.py    → PPT_ENGINE_PATH / DOCGEN_TEMPLATE
    因此 load_dotenv() 必须放在包初始化里（本文件），
    保证任何 backend.app.* 子模块被 import 时 .env 已生效。
    若放到 api.py 里会太晚——那些子模块在 api.py 的 import 阶段就已执行。
"""
import os

# 尽早加载 .env。未安装 python-dotenv 时静默跳过（Render 用进程级环境变量）。
try:
    from dotenv import load_dotenv

    # __file__ = <仓库根>/backend/app/__init__.py，向上三级得到仓库根
    _ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _ENV_PATH = os.path.join(_ROOT, ".env")
    load_dotenv(_ENV_PATH if os.path.exists(_ENV_PATH) else None)
except ImportError:
    pass
