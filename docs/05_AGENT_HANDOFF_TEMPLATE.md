# 05 · Agent 交接模板

> **用法**：复制本文件内容 → 覆盖 `STATUS.md` → 填表 → 交给下一个 Agent。
> 目的：让任意 Agent（Zcode / WorkBuddy / Claude / Cursor / 任意 LLM）30 秒接上手。

---

## 模板（复制以下内容到 STATUS.md）

```markdown
# STATUS · 项目接力状态机

> 任何 Agent 接手本项目，第一件事就是读这个文件。
> 读完再读 CHECKLIST.md。两份加起来 30 秒恢复完整上下文。

---

## 当前阶段

阶段：<MVP 档 / 部署档 / 算法精化档> · <一句话描述当前在做什么>
进度：████░░░░░░░░  XX%
阻塞：<无 / 具体阻塞项>
下一步：<下一个具体动作>

| 项 | 值 |
|---|---|
| 当前阶段 | |
| 上一阶段产物 | |
| 本阶段负责人 | |
| 最近更新 | YYYY-MM-DD HH:MM |
| 阻塞项 | |

---

## 已完成 ✅

| # | 事项 | 产物路径 |
|---|---|---|
| 1 | | |

---

## 未完成 ❌（按优先级排序）

| 优先级 | 事项 | 应产出 | 依赖 |
|---|---|---|---|
| P0 | | | |
| P1 | | | |
| P2 | | | |

---

## 关键文件路径

| 用途 | 绝对路径 |
|---|---|
| 工程根 | D:\codex\2026-10-28-23-35-39 |
| 算法主程序 | backend\solver\litho_solver.py |
| mock 数据 | backend\solver\mock_data.py |
| 求解器 CLI | backend\solver\cli.py |
| 设计规范 | docs\_DESIGN_SPEC.md |
| 原始交付物（只读） | D:\工作\嘉定GTX\GTX_FSO_交付物 |
|  | |

---

## 环境事实

- Python：3.11（.venv 或 miniconda）
- 求解器：CBC，已 Optimal 验证
- 网络：需代理 http://127.0.0.1:10808
- 原型：CSS/JS 全内联、相对路径、含 PM 评论气泡
- 其他：

---

## 下一步动作（按序执行）

1.
2.
3.

---

## 接力规则

1. 开工前：读 STATUS.md + CHECKLIST.md
2. 每完成一项：更新 CHECKLIST.md 勾选
3. 做不动的：标 ❌ 写阻塞原因，禁止静默跳过
4. 收工前：更新本文件的「当前阶段 / 已完成 / 未完成 / 下一步动作」
5. 禁止：改动 docs/specs/ 与 docs/_DESIGN_SPEC.md
```

---

## 给 Agent 的启动提示词（复制粘贴）

```
你在接手一个已进行中的项目。请先做三件事，再开始干活：

1. 读 D:\codex\2026-10-28-23-35-39\STATUS.md
2. 读 D:\codex\2026-10-28-23-35-39\CHECKLIST.md
3. 读 D:\codex\2026-10-28-23-35-39\docs\HANDOFF_TO_AGENT.md

项目目标：把 SemiconFab 仿真站 + 嘉定 GTX 六步光刻排程算法（PuLP MILP）
融合成一个可运行、可演示、可部署的系统。

验收标准（四项全绿）：
- python -m backend.solver run  →  step2/step3 = Optimal
- curl localhost:8000/api/health  →  200
- cd frontend && npm run build  →  无错误
- 9 页 HTML 跨页跳转无 404

你的任务：<在这里写具体任务>

约束：
- 前端 Vite + 原生 JS，禁止引入 React/Vue
- 9 个迁入 HTML 的内联样式不许拆
- docs/specs/ 与 _DESIGN_SPEC.md 只读
- 做不动的项在 CHECKLIST.md 标 ❌ 写原因，禁止静默跳过
- 收工前必须更新 STATUS.md 的四项状态
```

---

## 交接清单（交给下一个 Agent 前自查）

- [ ] `STATUS.md` 四项已更新（当前阶段 / 已完成 / 未完成 / 下一步）
- [ ] `CHECKLIST.md` 已勾选，阻塞项标了 ❌ 和原因
- [ ] 验收四项跑过，结果写进 `STATUS.md`
- [ ] 新增的关键文件路径已登记到「关键文件路径」表
- [ ] 如果引入了新的非直觉设计，写进 `HANDOFF_TO_AGENT.md` 的「三个已知的非直觉设计」
- [ ] 代码已 commit，避免下一个 Agent 拿到脏工作区

---

## 版本记录

| 日期 | 交接方 | 阶段 | 备注 |
|---|---|---|---|
| 2026-10-29 | WorkBuddy | MVP 档 40% | 骨架 + 资产迁移 + 文档体系完成，后端/前端待写 |
