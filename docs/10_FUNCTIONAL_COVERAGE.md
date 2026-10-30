# 10 · 功能点覆盖矩阵（对照需求 V0.5 / 设计 V0.1-0922 / RFP 响应 / 总体计划 / 培训手册）

> 生成：2026-10-31｜依据：`docs/refs/`（四份文档提取文本）+ 培训手册 PDF + 系统现状实测。
> 权威功能点清单来自《GTX PxFSO总体计划.xlsx → LithoScheduling-客户版本》39 项（排程 33 + UI 3 + 工程化 3）。
> 状态口径：✅ 真系统已实现（有页面/接口/测试证据）｜🟡 部分（演示级/简化实现）｜❌ 未实现｜🔗 需外部系统数据（MES/APC/QTMS/SDR 实接才能完整）。

---

## 1. 总览

| 维度 | 覆盖 |
|---|---|
| 结果页面六件套（培训手册 P11） | ✅ 全部真数据化：Scanner Schedule（/litho-schedule）、Reticle Schedule（/reticle-schedule）、**Barc Schedule（本次新增 Tab）**、**Reticle Transport（本次新增 Tab）**、**Scheduling Log + Error Management（本次新增 /logs）** |
| 排程功能点 33 项 | ✅ 9 项 ｜ 🟡 12 项 ｜ ❌ 8 项 ｜ 🔗 4 项需外部数据 |
| UI 功能点 3 项 | ✅ 2 项（结果界面/基本配置）｜ 🟡 1 项（模型参数 UI） |
| 工程化 3 项 | ✅ 3 项（中间结果 CSV/JSON、功能开关=CONFIG、集成=REST+时间轴） |
| 算法主链 | 六步全部可运行（PuLP+CBC，4 场景 Optimal，pytest 23/23） |

## 2. 排程功能点 33 项逐条对照（总体计划-客户版本编号）

### 阶段一（1~25）

| # | 功能点 | RFP | 状态 | 系统证据 / 差距 |
|---|---|---|---|---|
| 1 | 24h 来货（Coming WIP）+ 提前调 Reticle | 2.1.1 | 🟡 | 到站时间 ready 已入模（step1/3）；Coming WIP 批次流未建模；Reticle 提前搬送已入时间轴（start-300 出发） |
| 2 | BARC 组 Batch + 最早最晚派工 + Scanner Hungry | 2.1.2 | 🟡 | ER/LR 窗口已算（step5 反推 + Barc Schedule 视图）；**Batch 组批、Hungry 派工未实现** |
| 3 | 不 Over QTime、控货在 BARC | 2.1.3 | 🟡 | Remain QTime 作开工下界硬约束（step3）；「控在 BARC」的拉货逻辑未实现 |
| 4 | QTMS：上下游 WIP 平衡 + Next Loop Hungry | 2.1.4 | 🟡 | QTMS 超水位标记+卡控跳过（step4）✓；WIP 平衡未实现 🔗 需 QTMS 水位数据 |
| 5 | Key Lot 派工 | 2.1.6 | ✅ | 优先级权重 pri_flow_w + PRI1 急货最早上机有测试断言 |
| 6 | Bullet SHR/SSHR/Normal | 2.1.6 | 🟡 | tags 打标 SHR/NormalBullet 已入模；SSHR 等级未细分 |
| 7 | Ship Lot 优先派工 | 2.1.6 | 🟡 | Ship 打标在 mock；未单独加权 |
| 8 | 机台内 Reticle 储位 + 提前 Load in | 2.1.6+2.1.9 | 🟡 | 储位物理容量/管理水位参数（stocker_phys/water）+RT-0204 场景；提前 Load 在时间轴 ✓；逐机台储位水位推演未实现 |
| 9 | 温层：同温层>升降温>降温 | 2.1.7 | ✅ | 换温 20min 计入细排程约束（temp-conflict 场景覆盖） |
| 10 | Reticle Purge/IRIS/StarLight 计时计片卡控 | 2.1.8 | 🟡 | iris_at/StarLight 到期已作开工下界（光罩就绪耦合）✓；**剩余片数/动态余量未实现** |
| 11 | 连续同 Recipe 连批 | 2.1.7 | ❌ | 加工时长按 wph 统一假设，无 Recipe 维度 |
| 12 | 连续同 Reticle 连批 | 2.1.7 | 🟡 | 同光罩换罩代价 w_changeover 进目标函数（等效连批激励）✓；窗口内连续 M 批片数阈值未实现 |
| 13 | Monitor Lot 与时效 | 基本需求 | ❌ | 未建模 |
| 14 | BARC 同 Stage 放货间隔 2h（可配置） | 2.1.1 | ✅ | release_gap_min=120 后处理卡控（SHR 豁免），有场景覆盖 |
| 15 | MoveTarget 优先派工 | 2.1.6 | ❌ | 无该属性 |
| 16 | MES Queue 插队 Flag | 2.1.6 | ❌ | |
| 17 | Module 插队 Quota | 2.1.6 | ❌ | |
| 18 | Key Stage 优先 | 2.1.6 | ❌ | |
| 19 | Reticle 状态推演 + 输出搬送指令 | 2.1.9 | ✅ | step6 五态推演 + /api/twin/timeline 搬送事件 + 3D OHT 回放 + Reticle Transport 视图（指令下发 SDR 属 🔗 外部接口） |
| 20 | QTMS 水位管控结合 | 2.1.3 | 🟡 | 超水位标记/跳过 ✓；按 Loop 的水位计算联动 🔗 需 QTMS 数据 |
| 21 | 机台宕机不可用 | 基本需求 | 🟡 | 排程模型无停机窗（ready 静态）；执行态仿真有 MTBF/MTTR 故障 |
| 22 | Schedule PM | 基本需求 | ❌ | |
| 23 | Stacking Bond 长期 Loading Balance + 派工结合 | 2.1.5 | ❌ | 原型 UI（stacking_bond_ui_v6）已演示；真算法未实现 🔗 需绑定关系数据 |
| 24 | 同步字段确认 | — | 🟡 | mock_data 按宽表口径；正式对接见 docs/specs/06 宽表清单 |
| 25 | 阶段一回归测试 | — | 🟡 | pytest 23 条覆盖已实现子集；需随功能扩充 |

### 阶段二（26~33）

| # | 功能点 | RFP | 状态 | 差距 |
|---|---|---|---|---|
| 26 | Chuck 大小片/奇偶片 Unit 满 Run | 2.2.2 | ❌ | 🔗 需 Chuck 绑定数据 |
| 27 | PiRun Lot 加速上机 | 2.2.4 | ❌ | 🔗 需 MES 标识 |
| 28 | Fix Lot（个数/时间冻结） | 基本需求 | ❌ | 可纯算法实现（相邻版本冻结），排期 |
| 29 | Purge/IRIS/StarLight 特殊动作控制搬送 | 2.1.8 | 🟡 | IRIS 动作已在时间轴推演；动作类型细分到搬送指令未做 |
| 30 | APC 校验卡控并调整派工 | 2.2.1+2.2.3 | ❌ | 🔗 需 ELR/APC 数据（24 项检查） |
| 31 | Doma Etch RunPath | 2.2.5 | ❌ | 🔗 需 Doma Recipe/Chamber 数据 |
| 32 | 下游 Doma Loading Balance | 2.2.5 | ❌ | 同上 |
| 33 | 阶段二回归 | — | — | |

### UI（34~36）与工程化（37~39）

| # | 功能点 | 状态 | 证据 |
|---|---|---|---|
| 34 | 基本配置项 UI（Bullet/转温/搬送时间） | 🟡 | 原型 config_zone 全套 UI（mock）；真系统 CONFIG 参数已入模、经 Scenario 覆盖生效，**配置管理 API/UI 未接** |
| 35 | 结果界面：EQP-Lot 甘特 + Reticle 甘特 | ✅ | /litho-schedule、/reticle-schedule 真数据 |
| 36 | 模型参数/迭代步数/求解时间配置 | 🟡 | CONFIG.time_limit_s/权重可经 Scenario 覆盖；无 UI |
| 37 | 每步中间结果输出 | ✅ | step1~6 CSV（utf-8-sig）+ run_summary.json + result_litho 中间结果页签（原型） |
| 38 | 算法功能点开关配置 | ✅ | CONFIG 权重/时限/温层/间隔可调；LITHO_SOLVER 适配器 |
| 39 | 算法输出集成方案 | ✅ | REST（14+ 接口）+ JSON/CSV + 3D 时间轴契约 + docs/specs/05 |

## 3. 结果页面六件套（培训手册 P11）→ 真数据对照

| 页面 | 字段要求 | 真数据实现 | 位置 |
|---|---|---|---|
| Scheduling Log | 模型/Version/状态/起止 | ✅ 本次新增 | /logs |
| Scanner Schedule | 甘特+List（Lot/EQP/Reticle/起止） | ✅ 已有 | /litho-schedule |
| Reticle Schedule | 五态时间轴 | ✅ 已有 | /reticle-schedule |
| Reticle Transport | 搬送路径/原因/引发排程信息 | ✅ 本次新增 Tab | /reticle-schedule |
| Barc Schedule | Is Release/窗口/BatchId/Litho Start/Reason | ✅ 本次新增 Tab | /litho-schedule |
| Error Management | Error Type/Info/Detail/版本时间 | ✅ 本次新增 | /logs |

## 4. 配置页面（培训手册 P12）→ 现状

Lot Control / Priority Config / Data Parameter / Transport Config / Temperature Config / Bullet Lot / Fix Lot / Reticle Config / Process Config / Eqp Group / Schedule Model —— **原型 UI 全覆盖（mock）**；
真系统侧：温层耗时/放货间隔/IRIS 链路/换罩代价/储位水位/求解时限等**已参数化并入模**（mock_data.CONFIG + Scenario 覆盖 + /api/mock/data 只读导出）；**配置管理 API + 生效 UI 未接**（路线图 R1）。

## 5. 明确的系统边界（诚实声明）

1. **外部系统数据**：MES/APC(ELR)/QTMS/SDR/Chuck/Doma/Stacking 绑定的真覆盖需要宽表数据接入（docs/specs/06 已列清单）。演示系统以 mock 数据 + 事件流模拟语义，标注 🔗 的功能点在数据接入后才能"真"。
2. **算法深度**：当前 MILP 覆盖 分配/时序/温层/QTime 下界/光罩就绪/放货间隔 等核心约束；连批窗口、Chunk 优先级分批、冻结、Hungry 拉货等属增量建模（路线图）。
3. **单体规模**：演示 10 Lot/6 机台；200+ Lot 的求解性能与 chunk 分批策略需专项验证。

## 6. 路线图（按需求版三阶段对齐）

- **R1（阶段一收口）**：Barc Batch 组批、Hungry 派工、Ship/MoveTarget 加权、配置管理 API+UI、Fix Lot 冻结
- **R2（阶段二）**：IRIS/StarLight 计片余量动态推演、Chuck/大小片（需数据）、PiRun（需 MES）、Stacking Bond 接入（软约束→RunPath constraint）
- **R3（阶段三）**：APC 24 项检查卡控、Doma RunPath 与下游 Load Balance、QTMS 逐 Loop 水位联动
- **贯穿**：每补一项 → 对应 scenario + pytest 断言 + 覆盖矩阵状态更新（本文件随代码同步）
