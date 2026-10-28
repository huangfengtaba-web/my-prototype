# 06 · AI 能力：工作流引擎 + 排程 Agent

> 本文档回答：AI 能力的架构是什么、接口怎么调、LLM 怎么接入、怎么扩展。
> 实现代码：`backend/app/workflow.py`（工作流）+ `backend/app/agent/`（Agent）。

---

## 1. 总览：三层 AI 能力

```
┌────────────────────────────────────────────────────────┐
│ L3  Agent（backend/app/agent/）                         │
│     对话入口，LLM 自主决策（function calling）           │
│     无 LLM Key 时规则模式兜底（演示永不冷场）             │
├────────────────────────────────────────────────────────┤
│ L2  工作流引擎（backend/app/workflow.py）                │
│     模板化步骤编排：校验→求解→仿真→对比→报告             │
│     后台线程异步执行，每步独立状态/耗时/输出              │
├────────────────────────────────────────────────────────┤
│ L1  原子能力                                             │
│     求解（solver_runner，子进程隔离）                    │
│     仿真（backend/sim，执行态 DES）                      │
│     数据（mock_data / cases）                            │
└────────────────────────────────────────────────────────┘
```

分工：**L1 干活、L2 编排、L3 决策**。Agent 的工具就是 L1/L2 的封装，
工作流的步骤函数也直接调 L1 —— 任何一层都可单独使用。

---

## 2. 工作流引擎

### 2.1 预置模板

| 模板 ID | 步骤 | 用途 |
|---|---|---|
| `daily-scheduling` | 数据校验 → 六步 MILP → 执行态仿真 → 生成报告 | 生产日计划主链路，验证计划抗扰动性 |
| `scenario-compare` | 多场景求解（基线/急货/光罩延迟）→ 结果对比 → 生成报告 | What-if 分析，对比 MakeSpan 与急货开工 |

### 2.2 接口

```bash
# 模板清单
curl http://127.0.0.1:8000/api/workflow/templates

# 异步启动（线程执行，返回后轮询）
curl -X POST http://127.0.0.1:8000/api/workflow/run \
     -H "Content-Type: application/json" \
     -d '{"template": "daily-scheduling", "params": {"case": "urgent-A01", "seed": 42}}'
# → {"wf_id": "ab12cd34", "status": "pending", ...}

# 轮询状态（前端每 1.2s 一次）
curl http://127.0.0.1:8000/api/workflow/status/ab12cd34
# → steps: [{name, status(running/done/failed), seconds, output, error}, ...]
# → status: done 后，report 步骤的 output.markdown 即完整报告
```

### 2.3 扩展新工作流（两步）

1. 写一个步骤函数（签名统一 `step(ctx, params) -> dict`，抛异常即该步失败）；
2. 在 `TEMPLATES` 加条目：`steps: [(id, 名称, fn), ...]` + `params` 默认值。

`ctx` 是步骤间的共享黑板（如 `ctx["solve"]` 求解结果、`ctx["sim"]` 仿真结果）。

---

## 3. 排程 Agent

### 3.1 双模式

| 模式 | 触发条件 | 行为 |
|---|---|---|
| **LLM 模式** | 配置了 `LLM_API_BASE` + `LLM_API_KEY` | OpenAI 兼容 function calling，模型自主决定调哪些工具（最多 6 轮） |
| **规则模式**（默认） | 无 LLM 配置，或 LLM 调用失败 | 关键词路由：带用例名的执行意图 > 仿真/对比/工作流 > 清单查询 > 数据概况 |

两种模式共用同一套工具（7 个），响应结构一致：`{session_id, mode, reply, tool_calls[]}`，
前端把 `tool_calls` 渲染成 🔧 chip（工具名 + 结果摘要）。

### 3.2 工具清单（backend/app/agent/tools.py）

| 工具 | 功能 |
|---|---|
| `list_cases` | 列出 scenario 用例 |
| `run_solve` | 跑六步 MILP（子进程隔离） |
| `get_result` | 按 run_id 查历史结果 |
| `get_mock_data` | 机台/Lot/光罩数据概览 |
| `run_sim` | 求解 + 执行态仿真 |
| `run_workflow` | 执行工作流模板 |
| `list_workflows` | 模板与最近运行记录 |

### 3.3 接入 LLM（可选，三行环境变量）

```bash
# .env 或系统环境变量
LLM_API_BASE=https://api.openai.com/v1     # 或任意 OpenAI 兼容网关（one-api/智谱/通义）
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o-mini                      # glm-4-flash / qwen-plus 等均可
```

配置后 `/api/agent/status` 返回 `{"mode": "llm", "model": "..."}`，AI 助手页右上角徽章变绿。
**不配置也完全不影响其他功能**——规则模式覆盖了所有演示话术。

### 3.4 接口

```bash
curl -X POST http://127.0.0.1:8000/api/agent/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "跑一下 urgent-A01 看看急货排得怎么样"}'
# → {"session_id":"...", "mode":"rule",
#    "tool_calls":[{"name":"run_solve","args":{"case":"urgent-A01"},...}],
#    "reply":"求解完成（run_id `xx`），MILP Optimal，急货 LOT-A01 开工 10:00。"}
```

会话记忆：同 `session_id` 保留最近 20 条（内存，重启清空）。

### 3.5 扩展新工具（两步）

1. 在 `tools.py` 写函数 + 在 `TOOLS` 注册（name → desc/args/fn）；
2. 完成。LLM 的 tools spec（`tool_specs_for_llm`）与规则路由都会自动看到新工具
   （规则路由需加一条关键词，见 `agent.py::_rule_route` 的优先级注释）。

---

## 4. 执行态仿真（L1 的仿真腿，SemiconFab 叙事移植）

- 代码：`backend/sim/fab_sim.py`（轻量自研 DES，零第三方依赖，事件按计划开工时间全局推进）
- 三类扰动：机台故障（MTBF 900min/MTTR 30min，指数分布）、光罩接力搬送（跨机台 10+5min）、良率返工（5% 概率时长×2）
- **同种子完全可复现**（`random.Random(seed)` 锚定），演示与测试都依赖这一点
- KPI：准时率（±15min 容差）、MakeSpan 偏差、平均/最大延误、QTime 违约、故障/返工次数
- 接口：`POST /api/sim/run {"case": "...", "seed": 42, "breakdown": true}`

---

## 5. 测试口径

- `tests/test_workflow.py`：两个模板端到端 done、报告非空、对比表场景齐全且急货开工随光罩延迟变化
- `tests/test_agent.py`：规则路由 7 类意图全对、会话记忆、未知意图给帮助
- `tests/test_sim.py`：同种子确定性、KPI 合理性、无扰动时基本贴合计划、4 场景可跑

跑法：仓库根 `pytest tests/ -q`，当前 **23 passed**。
