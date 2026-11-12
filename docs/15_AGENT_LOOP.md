# Loop Engineering · 自主规划循环

> 从「LLM 选一个工具 → 执行 → 回答」升级为 **Plan → Act → Observe → Reflect → Replan**，
> 能对一个业务目标反复尝试，直到达成或确认不可达。

---

## 1. 它和原来的 Agent 差在哪

| | `POST /api/agent/chat`（原有） | `POST /api/agent/loop`（新增） |
|---|---|---|
| 范式 | 单层 ReAct | 五阶段显式循环 |
| 有无目标 | 无（用户问什么答什么） | **有目标**，且可机器判定是否达成 |
| 失败处理 | 回答「跑失败了」 | 换方案重试（最多 N 次） |
| 可审计 | 仅响应里的 tool_calls 数组 | **轨迹逐行落盘**，可回放 |
| 成本控制 | MAX_ITER=6 | 轮次/重规划/token/墙钟 四道硬闸 |

**真实例子**（规则模式，实测）：

```
用户：让急货 9 点前上机
→ R1 run_solve(urgent-A01)     上机 10:00，未达成（差 60 分钟）
→ R2 run_solve(default)        仍 10:00，未达成
→ R3 run_solve(urgent-A01,fix) 仍 10:00，未达成
→ 停止：「已达最大重规划次数 3」，并给出证据 slack_min=-60
```

不是「跑一次失败就认输」，而是**真的试了三种方案**，最后如实告知差距。

---

## 2. 五阶段

```
        ┌──────────────────────────────────────────┐
        ↓                                          │
     PLAN ──→ ACT ──→ OBSERVE ──→ REFLECT ──┬── met ──→ DONE
   （规划） （执行）  （提炼）   （判定）    │
                                            ├── not met & 有预算 → REPLAN ─┘
                                            └── 预算/轮次耗尽 → STOPPED
```

| 阶段 | 做什么 | 代码 |
|---|---|---|
| **PLAN** | 产出步骤序列（LLM 优先，失败回落规则计划） | `loop.plan_llm` / `loop.plan_rule` |
| **ACT** | 调技能注册表执行一步；同参数在一次循环内缓存 | `loop.act` |
| **OBSERVE** | 把结果压成关键数字（run_id / 上机时间 / MakeSpan / 准时率） | `loop.observe` |
| **REFLECT** | **确定性判定**目标是否达成 +（可选）LLM 解释差距 | `goals.evaluate` + `loop.reflect` |
| **REPLAN** | 未达成则换方案再来一轮 | `loop.plan_rule`（按 replans 次数换策略） |

### 关键设计：判定权不在 LLM 手里

```python
met, evidence = goals.evaluate(goal, ctx)   # 纯函数，可单测
```

LLM 只在 `reflect` 里生成一句**解释**，无法改变 `met`。
避免「模型自评自夸」这种在演示和评审中最致命的不可信行为。

---

## 3. 目标语法（自然语言 → 结构化）

| 用户说法 | 解析结果 | 判定逻辑 |
|---|---|---|
| 让急货 10 点前上机 | `urgent_deadline{lot:LOT-A01, deadline:600}` | `LOT-A01.start ≤ 10:00` |
| LOT-A01 必须 09:30 开工 | `urgent_deadline{deadline:570}` | 同上 |
| MakeSpan 不晚于 12:35 | `makespan_le{limit:755}` | `max(end) ≤ 12:35` |
| 准时率要达到 95% 以上 | `on_time_ge{rate:0.95}` | `sim.kpis.on_time_rate ≥ 0.95` |
| 其它 | `freeform` | 交 LLM 判定，结果标 `llm_judged: true` |

---

## 4. 怎么开

默认**关闭**（防止误触发烧 token）。

```bash
# 方式一：环境变量（长期）
AGENT_LOOP_ENABLED=1

# 方式二：单次调用传参（推荐调试用）
curl -X POST localhost:8000/api/agent/loop \
  -H "Content-Type: application/json" \
  -d '{"goal": "让急货 10 点前上机", "enabled": true, "max_rounds": 5}'
```

其他可调项（`.env`）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `AGENT_LOOP_MAX_ROUNDS` | 8 | 总轮次上限 |
| `AGENT_LOOP_MAX_REPLANS` | 3 | 重规划次数上限 |
| `AGENT_LOOP_BUDGET_TOKENS` | 20000 | token 预算（超过即停） |
| `AGENT_LOOP_MAX_WALL_S` | 180 | 墙钟上限（秒） |
| `AGENT_LOOP_EXPLAIN` | 1 | 是否让 LLM 解释差距（关掉可省 token） |

---

## 5. API

```
POST /api/agent/loop
  body: {goal, max_rounds?, budget_tokens?, enabled?}
  resp: {trace_id, status, goal, goal_met, evidence, explanation,
         stopped_reason, rounds, replans, plan, observations, reflections, usage, elapsed_s}

GET  /api/agent/loop/{trace_id}    → 从轨迹文件重建状态（跨进程可查）
GET  /api/agent/trace/{trace_id}   → 原始事件流 + 汇总
```

`status` 取值：`done`（达成）｜`stopped`（未达成/被硬闸停）｜`disabled`（未开启）

---

## 6. 轨迹（可审计）

`.runtime/traces/YYYY-MM-DD/{trace_id}.jsonl`，每行一个事件：

```json
{"ts":"2026-11-12T22:31:05","phase":"start","payload":{"goal":"LOT-A01 需在 10:00 前上机","kind":"urgent_deadline"}}
{"ts":"...","phase":"plan","payload":{"round":1,"steps":[{"skill":"run_solve","args":{"case":"urgent-A01"}}]}}
{"ts":"...","phase":"act","payload":{"round":1,"step":"run_solve","ok":true,"cached":false,"ms":851}}
{"ts":"...","phase":"observe","payload":{"digest":{"urgent_start":"10:00","makespan":"12:35","lots":9}}}
{"ts":"...","phase":"reflect","payload":{"met":true,"evidence":{"slack_min":0}}}
{"ts":"...","phase":"end","payload":{"status":"done","usage":{"solve_calls":1}}}
```

回答得了这三个问题：
- 这次为什么判定达成 / 未达成？（`reflect.evidence`）
- 卡在哪一轮、试了几种方案？（`plan` + `replan` 事件）
- 花了多少求解 / token？（`end.usage`）

---

## 7. 评测 harness

```bash
python -m harness.run_eval          # 7 个 golden 用例
python -m harness.run_eval -v       # 带每轮观测
python -m harness.run_eval -k on_time   # 只跑匹配的
```

| 用例 | 验证点 |
|---|---|
| `urgent_first` | 可达目标 1~2 轮达成 |
| `makespan_ok` | 另一类目标也能达成 |
| `on_time_sim` | 必须先调 `run_sim` 才能判定 |
| `on_time_unreachable` | 收紧指标后靠**重规划换参数**达成（证明不是原地打转） |
| `replan_unreachable` | 真不可达时如实停止，且尝试过 ≥2 种方案 |
| `wall_clock_stop` | 墙钟硬闸生效 |
| `bad_args_handled` | 非法参数转成 error，循环不崩 |

**全部在规则模式下跑，零 LLM 调用、零 token 消耗。**

---

## 8. 加新目标类型的步骤

1. `goals.py` 的 `parse_goal` 加一条正则分支
2. `goals.evaluate` 加对应的确定性判定（返回 `evidence` 字典）
3. `loop.plan_rule` 加该目标的首轮策略与重规划策略
4. `harness/cases/loop-golden.yaml` 加一个用例
5. `pytest tests/test_loop.py -q` + `python -m harness.run_eval`

判定必须是纯函数（不依赖网络/LLM），否则无法进 CI。

---

## 9. 云端（Render）配置

**先看有没有 `SUPABASE_DB_URL`**，两种情况的配置完全不同：

| 你的环境 | `AGENT_SESSION_STORE` | 结果 |
|---|---|---|
| **有** `SUPABASE_DB_URL` | **删掉这个变量**（用 `auto`）或设 `pg` | 会话存 Postgres，重启/休眠不丢 |
| **没有** DSN | 设 `memory` | 纯内存，重启丢会话（与改造前行为一致） |

> ⚠️ 有 DSN 时**不要**设 `memory` —— 那会主动放弃阶段三刚做好的持久化能力。

用 `pg` 之前必须先建表（DDL 见 `docs/11_VSCODE_DEPLOY_SUPABASE.md` §5.2.1）：

```sql
create table if not exists agent_sessions (
  session_id text primary key,
  messages   jsonb not null default '[]'::jsonb,
  summary    text  not null default '',
  mode       text,
  updated_at timestamptz not null default now()
);
```

**表没建时不会报错**：`PgStore.load/save` 的异常被吞掉，等价于「无持久化」。
所以要么建表后用 `auto`/`pg`，要么明确设 `memory`，别指望它能自动降级成功。

### 自主规划开关

| 位置 | 建议 | 原因 |
|---|---|---|
| Render | `AGENT_LOOP_ENABLED=0` 或不加 | 防止误触发烧 token |
| 本地 `.env` | `AGENT_LOOP_ENABLED=1` | 演示/调试用 |
| 前端「🎯 自主规划」面板 | 无需配置 | 请求体里已写死 `enabled: true` |

---

## 10. 已知限制

- **求解是确定性的**：同 `(case, fix)` 结果完全一样，所以重规划只能「换场景 / 换参数 / 关扰动」，不能指望微调运气。这是物理约束，不是缺陷。
- **同步执行**：`POST /api/agent/loop` 阻塞到循环结束（最长 `max_wall_s`）。若前端需要进度条，应改为异步 + 轮询 `GET /api/agent/loop/{trace_id}`。
- **PLAN 的步骤上限 4 步**：复杂任务（跨工段、多目标）需要更长的计划，V3 再放开。
