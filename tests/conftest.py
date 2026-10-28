# -*- coding: utf-8 -*-
"""pytest 根定位：把仓库根加入 sys.path，保证 `import backend.*` 在任何启动目录下都可用。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
