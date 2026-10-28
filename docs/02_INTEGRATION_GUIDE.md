# 02 · 三资产融合指南（文件级映射）

> 这份文档回答「**怎么结合**」。每一条都有：来源路径 → 目标路径 → 命令 → 校验方法。

---

## 0. 融合总览

```
┌─────────────────────┐
│ A 本地交付物          │  9 页原型 + 六步 MILP 算法 + 8 份设计文档
│ D:\工作\嘉定GTX\...   │  → 提供「内容主体」
└──────────┬──────────┘
           │ cp 复制
┌─────────────────────┐
│ B my-prototype      │  Vite 8 + 原生 JS，2 页，已部署 Vercel
│ github.com/...       │  → 提供「工程骨架」
└──────────┬──────────┘
           │ git merge
┌─────────────────────┐
│ C SemiconFab        │  Fab 数字孪生静态站（SimPy + 设备编目）
│ github.com/...       │  → 提供「仿真叙事」
└──────────┬──────────┘
           │ git subtree
           ▼
    gtx-fso-litho（monorepo）
```

**分工逻辑**：
- B 是**骨架**（构建配置、依赖管理）→ 前端工程以它为底
- A 是**血肉**（9 页原型 + 真算法）→ 内容全部来自它
- C 是**叙事**（仿真视角）→ 代码拉进 `vendor/` 供参考与移植，不直接托管

---

## 1. 文件级映射表

### 1.1 资产 A → 工程目录

| # | 来源（资产 A） | 目标 | 方式 | 说明 |
|---|---|---|---|---|
| 1 | `02_原型/index.html` | `frontend/index.html` | cp | 总览 Dashboard，作为前端首页 |
| 2 | `02_原型/config_zone.html` | `frontend/prototypes/config_zone.html` | cp | 数据配置区（9 页签） |
| 3 | `02_原型/data_zone.html` | `frontend/prototypes/data_zone.html` | cp | 数据接入区（4 页签） |
| 4 | `02_原型/equip_temp_layer_config.html` | `frontend/prototypes/equip_temp_layer_config.html` | cp | 温层配置（复用基准页） |
| 5 | `02_原型/log_zone.html` | `frontend/prototypes/log_zone.html` | cp | 日志区（2 页签） |
| 6 | `02_原型/model_zone.html` | `frontend/prototypes/model_zone.html` | cp | 模型管理区（4 页签） |
| 7 | `02_原型/result_litho.html` | `frontend/prototypes/result_litho.html` | cp | Litho 排程结果（7 二级页） |
| 8 | `02_原型/result_reticle.html` | `frontend/prototypes/result_reticle.html` | cp | Reticle 排程结果（2 二级页） |
| 9 | `02_原型/stacking_bond_ui_v6.html` | `frontend/prototypes/stacking_bond_ui_v6.html` | cp | EQP Loading（复用基准页） |
| 10 | `02_原型/_DESIGN_SPEC.md` | `docs/_DESIGN_SPEC.md` | cp | **Design Token + 字段清单，前端配色依据** |
| 11 | `04_算法demo/litho_solver.py` | `backend/solver/litho_solver.py` | cp + 改 1 行 | 六步 MILP 主程序 |
| 12 | `04_算法demo/mock_data.py` | `backend/solver/mock_data.py` | cp | 机台/Lot/光罩/配置 |
| 13 | `03_文档/*.md`（8 份） | `docs/specs/*.md` | cp | **设计基线，只读** |

### 1.2 资产 B → 工程目录

| 来源（资产 B） | 目标 | 处理 |
|---|---|---|
| `package.json` | `frontend/package.json` | 保留，作为前端依赖基线 |
| `vite.config.js` | `frontend/vite.config.js` | 保留，**需改造为多页入口** |
| `temp-layer-config.html` | ❌ 删除 | 与资产 A 第 4 项同源，保留 A 版本 |
| `stacking-bond.html` | ❌ 删除 | 与资产 A 第 9 项同源，保留 A 版本 |

### 1.3 资产 C → 工程目录

| 来源（资产 C） | 目标 | 处理 |
|---|---|---|
| 整个仓库 | `vendor/semiconfab-fork/` | subtree 拉入，**保留 LICENSE** |
| SimPy 仿真模块 | 参考 | 移植到 `frontend/src/pages/simulation/`（算法精化档） |

---

## 2. 第 11 项必改：`litho_solver.py` 的 import

原文件是「同目录脚本模式」：

```python
from mock_data import (CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN, fmt)
```

迁入 `backend/solver/` 后要支持 **`python -m backend.solver`** 包模式调用，必须改成兼容写法：

```python
try:                                    # 包模式：python -m backend.solver
    from .mock_data import (CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN, fmt)
except ImportError:                     # 脚本模式：python litho_solver.py
    from mock_data import (CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN, fmt)
```

> 不改的话：直接跑脚本没问题，但 FastAPI 里 `import backend.solver.litho_solver` 会 `ModuleNotFoundError`。

**另一处必改**：`main()` 开头加一行重置，否则被 API 反复调用时步骤会累积：

```python
def main():
    SUMMARY["steps"] = []               # 支持被 API 反复调用，先清空历史步骤
```

**第三处（可选但推荐）**：`main()` 末尾 `return SUMMARY`，并把结果结构化为
`SUMMARY["schedule"]`（排程列表）与 `SUMMARY["reticles"]`（光罩状态），供前端直接消费。

---

## 3. 前端多页配置（Vite）

`frontend/vite.config.js` 要把 9 页都声明为入口：

```js
import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  root: __dirname,
  build: {
    rollupOptions: {
      input: {
        index:      resolve(__dirname, 'index.html'),
        dataZone:   resolve(__dirname, 'prototypes/data_zone.html'),
        configZone: resolve(__dirname, 'prototypes/config_zone.html'),
        modelZone:  resolve(__dirname, 'prototypes/model_zone.html'),
        resultLitho:   resolve(__dirname, 'prototypes/result_litho.html'),
        resultReticle: resolve(__dirname, 'prototypes/result_reticle.html'),
        logZone:    resolve(__dirname, 'prototypes/log_zone.html'),
        stacking:   resolve(__dirname, 'prototypes/stacking_bond_ui_v6.html'),
        equipTemp:  resolve(__dirname, 'prototypes/equip_temp_layer_config.html'),
        schedTest:  resolve(__dirname, 'src/pages/scheduling-test/index.html'),
      }
    }
  },
  server: { port: 5173 }
})
```

### 关键约束

1. **9 个迁入 HTML 的内联 `<style>` / `<script>` 保持不动**
   - 原因：它们已跑通，拆开有回归风险
   - Design Token 只抽一份给**新页面**（`scheduling-test`）用
2. **跨页链接必须仍为相对路径**
   - 迁入的 9 页之间用 `href="xxx.html"`，放在 `prototypes/` 子目录后仍然互相可达
   - 但 `index.html` 在 `frontend/` 根，指向 prototypes 的链接要改成 `prototypes/xxx.html`
3. **PM 评论气泡机制保留**：`.q[data-cm]` 属性与「💬评论模式」开关不要删

---

## 4. 路径校验（迁移后必做）

迁移完成后跑一遍，确认没有断链：

```bash
cd /d/codex/2026-10-28-23-35-39/frontend

# 列出所有 HTML 里的 href/src 引用
grep -ohE '(href|src)="[^"]*"' index.html prototypes/*.html \
  | sed -E 's/.*="//; s/"$//' \
  | grep -vE '^(http|https|#|data:|//)' \
  | sort -u
```

逐个人工核对：每个列出的相对路径，对应文件必须存在。

**重点检查**：`index.html` 里指向 `prototypes/` 下页面的链接（这是唯一可能发生断链的地方）。

---

## 5. 后端融合：把算法接进 API

### 5.1 为什么必须进程隔离

`mock_data.py` 的 `LOTS` / `CONFIG` / `RETICLES` 是**模块级可变对象**。
scenario 覆盖会直接改它们，同进程内反复调用 → 第二次调用拿到的已是第一次被改过的数据。

**解法**：`solver_runner.py` 每次求解新起子进程：

```python
cmd = [sys.executable, "-m", "backend.solver", "run", "--out", out_dir, "--json"]
if case:
    cmd += ["--case", case]
proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                      encoding="utf-8", timeout=120)
```

- `cwd=REPO_ROOT`（仓库根）保证 `backend.solver` 可导入
- `timeout=120` 防求解卡死
- 代价约 2s 冷启动（求解本身仅 0.2s），演示可接受

### 5.2 数据流

```
前端 scheduling-test 页
   │ POST /api/solve/run  {"case": "urgent-A01"}
   ▼
backend/app/api.py
   ▼
backend/app/solver_runner.py  → 子进程 python -m backend.solver run --case X --json
   ▼                              ├─ 加载 tests/cases/X.yaml
   │                              ├─ 覆盖 mock_data 内存对象
   │                              ├─ 跑六步 MILP（CBC）
   │                              └─ 输出 output/step1~6_*.csv + run_summary.json
   ▼
解析 JSON → 存 RUNS[run_id] → 返回 {run_id, status, summary}
   ▼
前端渲染排程列表 + 甘特
```

---

## 6. 融合顺序（建议严格按此执行）

| 步骤 | 动作 | 校验 |
|---|---|---|
| 1 | `git init` + 目录骨架 | `ls` 目录齐全 |
| 2 | 拉 B（my-prototype） | `frontend/package.json` 存在 |
| 3 | 拉 C（subtree） | `vendor/semiconfab-fork/LICENSE*` 存在 |
| 4 | 复制 A 的 9 页 HTML | `ls frontend/prototypes/` 有 8 个文件 |
| 5 | 复制 A 的算法 + 改 import | `python -m backend.solver run` 跑通 |
| 6 | 复制 A 的文档 | `ls docs/specs/` 有 8 个文件 |
| 7 | 写前端 vite.config.js | `npm run build` 通过 |
| 8 | 写后端 api.py + solver_runner.py | `curl /api/health` 返回 200 |
| 9 | 写 scheduling-test 页 | 点按钮能拿到求解结果 |
| 10 | 路径校验 | §4 脚本无断链 |
| 11 | 提交 + 推送 | GitHub 可见 |

---

## 7. 冲突处理原则

| 冲突 | 原则 |
|---|---|
| A 与 B 有同源页面（温层配置 / Stacking Bond） | **保留 A**（A 是含 PM 评论气泡的完整版） |
| B 的构建配置 vs A 的单文件形态 | **保留 B 的配置**，但 A 的 9 页**不拆**内联样式 |
| C 的静态站 vs 需要后端跑求解器 | **不托管 C**，拉进 `vendor/` 由 Vite 接管 |
| 设计文档被改动 | `docs/specs/` 与 `_DESIGN_SPEC.md` **只读**，有疑问回交付物目录查原版 |

---

## 8. 明确不做的（避免范围蔓延）

- ❌ 不把 `00_素材/` 的 docx / pptx 入版本库（大二进制，需要时到交付物目录取）
- ❌ 不迁移 `01_PPT/`（`build_ppt.py:8` 硬编码 `D:/工作/...` 绝对路径，换机器必挂）
- ❌ 不迁移 `tools/harness-anything/`（PPT 引擎，与本工程无关）
- ❌ 不拆 9 页 HTML 的内联样式（回归风险远大于收益）
- ❌ 不在 MVP 阶段移植 SemiconFab 的 SimPy 仿真（先跑通排程主线）
