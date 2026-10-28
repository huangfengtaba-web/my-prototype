# 接力手册 · 给任意接手 Agent

> **开工前 30 秒**：读 [`../STATUS.md`](../STATUS.md) → 读 [`../CHECKLIST.md`](../CHECKLIST.md) → 读本文件。
> 三份读完即可完整恢复上下文，不需要重新探索代码库。

---

## 1. 这个项目是什么

把「Fab 数字孪生仿真」（SemiconFab 开源站）与「嘉定 GTX 光刻区六步排程算法」（自研 PuLP MILP）
合成为一个**可运行、可演示、可部署**的系统。

**判断你做对了没有的唯一标准**：
浏览器点「运行求解」→ 后端真跑 CBC 求解器 → 页面回填排程结果。
做不到这一步，就是没做完。

---

## 2. 最小上下文（5 项，缺一不可）

| # | 上下文 | 在哪看 |
|---|---|---|
| 1 | 当前处于哪个阶段 | `STATUS.md` → 「当前阶段」 |
| 2 | 已完成什么 | `STATUS.md` → 「已完成 ✅」 |
| 3 | 未完成什么 + 为什么卡住 | `CHECKLIST.md` → 「阻塞登记」 |
| 4 | 关键文件在哪 | `STATUS.md` → 「关键文件路径」 |
| 5 | 下一步做什么 | `STATUS.md` → 「下一步动作」 |

---

## 3. 三条铁律

### 铁律 1：不要静默跳过

做不动的项，在 `CHECKLIST.md` 标 `❌` 并写阻塞原因。**禁止**假装完成或删掉条目。

### 铁律 2：不要改设计基线

以下目录**只读**：

- `docs/specs/`（8 份设计文档）
- `docs/_DESIGN_SPEC.md`（Design Token + 字段清单）

有疑问去 `D:\工作\嘉定GTX\GTX_FSO_交付物` 查原版，不要在工程里改。

### 铁律 3：收工必更新

收工前必须更新 `STATUS.md` 的**四项**：当前阶段 / 已完成 / 未完成 / 下一步动作。
**这是下一个人能不能接上手的关键。**

---

## 4. 技术事实（已验证，不要重复探索）

| 项 | 事实 |
|---|---|
| 工程根 | `D:\codex\2026-10-28-23-35-39` |
| 后端栈 | Python 3.11 + FastAPI + PuLP（CBC 求解器） |
| 前端栈 | Vite 8 + **原生 JS**（禁止引入 React/Vue） |
| 求解器状态 | CBC 已跑出 **Optimal**，零配置可用 |
| 网络 | pip / git 需代理 `http://127.0.0.1:10808`（直连失败） |
| 原型 HTML | CSS/JS **全内联**，跨页**全相对路径**，含 **PM 评论气泡**（勿删） |
| 交付物目录 | `D:\工作\嘉定GTX\GTX_FSO_交付物`，**不是** git 仓库 |

### 三个已知的非直觉设计

1. **算法调用必须进程隔离**
   `mock_data.py` 的 `LOTS`/`CONFIG`/`RETICLES` 是模块级可变对象，scenario 覆盖会改它们。
   同进程反复调用会污染 → `solver_runner.py` 每次新起子进程。

2. **9 个迁入 HTML 的内联样式不许拆**
   它们已跑通，拆开有回归风险。Design Token 只抽一份给新页面用。

3. **不用 SemiconFab 的 Cloudflare Pages**
   它是纯静态站，无后端，跑不了 CBC。拉进 `vendor/` 由 Vite 接管路由。

---

## 5. 验收自检（做完跑一遍）

```bash
cd /d/codex/2026-10-28-23-35-39

# ① 算法跑通
python -m backend.solver run
# 预期：step2/step3 = Optimal，LOT-A01 上机 10:00，RT-0101 就绪 09:45

# ② 后端探活
uvicorn backend.app.api:app --reload --port 8000 &
curl http://127.0.0.1:8000/api/health
# 预期：{"ok":true,"solver":"CBC"}

# ③ 前端构建
cd frontend && npm run build
# 预期：无错误，dist/ 生成

# ④ 路径无断链
cd frontend
grep -ohE '(href|src)="[^"]*"' index.html prototypes/*.html \
  | sed -E 's/.*="//; s/"$//' | grep -vE '^(http|https|#|data:|//)' | sort -u
# 预期：逐个核对，每个相对路径文件都存在
```

**四项全绿才算做完。** 任一不绿，标 ❌ 写原因。

---

## 6. 分档范围（先问清楚做哪一档）

| 档位 | 范围 |
|---|---|
| **MVP** | 骨架 + 9 页接入 + 算法迁后端 + `/api/solve` 打通 + VSCode 配置 + 文档 + 本地跑通 |
| **部署** | + Vercel 前端 + Railway 后端 + 环境变量 + 生产联调 |
| **算法精化** | + 4 个 scenario + pytest + 甘特图渲染 + solver 适配器 |

**不要越档。** 用户没说做下一档就停在当前档。

---

## 7. 常见误判（别踩）

| 误判 | 事实 |
|---|---|
| 「只有两个页面，很简单」 | 那是已部署的 my-prototype。本地交付物有 **9 页 / 32 页签** |
| 「SemiconFab 有调度算法，直接用」 | 它只有 SimPy 仿真，**没有** reticle/MILP 排程算法 |
| 「可以随便用 SemiconFab」 | **PolyForm 非商用**。商用必须删 `vendor/` |
| 「算法是 mock 的」 | 不，是**真跑 CBC 求解器**，已 Optimal 验证 |
| 「原型要改成 React」 | 禁止。Vite + 原生 JS，沿用 my-prototype 栈 |

---

## 8. 交回给用户的格式

收工时在回复里给：

1. **改了哪些文件**（路径清单）
2. **验收自检四项结果**（✅/❌）
3. **未完成项 + 阻塞原因**
4. **下一步建议**

然后调用文件展示，让用户能直接打开 `STATUS.md` 和 `README.md`。

---

## 9. 需要用户才能做的事（别自己硬扛）

| 事项 | 为什么需要用户 |
|---|---|
| GitHub 建空仓库 | 需账号权限 |
| Personal Access Token | 需用户生成 |
| Vercel / Railway 授权 | 需账号登录 |
| 确认商用性质 | 决定 `vendor/` 去留 |
| 客户源表确认 | OverLap / Wafer 页签的字段来源 |
