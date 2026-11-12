# 领域专著能力映射 · 《数据驱动的半导体制造系统调度》

> 书：**《数据驱动的半导体制造系统调度》**
> 作者：李莉 / 于青云 / 马玉敏 / 乔非　化学工业出版社 2020-12
> 微信读书 bookId `41807543`　[打开阅读](https://weread.qq.com/book-detail?type=1&v=02332b60727deeb7023a1d7)
> 分析依据：全书 125 节目录 + 用户已划的 103 条划线（19 个章节）

---

## 一、一句话结论

这本书的**理论骨架几乎逐条对应我们系统的现有能力**，但有 3 个方法论我们完全没实现，且恰好是「从排程工具升级为调度平台」的关键：

1. **调度环境向量 Xse**（用环境特征而非固定规则驱动决策）
2. **数据驱动性能指标预测模型**（先预测再优化，避免反复仿真）
3. **数据预处理四件套**（规范化 / 缺失值填补 / 聚类异常值 / 冗余变量检测）

---

## 二、章节 → 系统能力映射

| 书章节 | 核心方法论 | 我们已有的 | 对应代码 / 页面 | 差距 |
|---|---|---|---|---|
| **1.1 半导体制造流程** | 光刻占成本 1/3、时间 40~60%；多重入加工；混合加工 | 六步 MILP 专攻光刻工段 | `backend/solver/litho_solver.py` | 只覆盖光刻，未做多重入 |
| **1.2.1 调度特点** | 非零初始状态；三类不确定性（任务总数/加工时间/事件）；双重约束（工艺路径 + 资源） | ✅ 全部覆盖：非零初始（`ready` 到站时间）、不确定性（`fab_sim` 故障扰动）、双重约束（`MACHINES.products` + `reticles`） | `mock_data.py` LOTS/MACHINES/RETICLES | — |
| **1.2.2 调度类型** | 投料控制 / 工件调度 / 瓶颈设备调度 | ✅ 投料（BARC 放货 `step5`）、工件调度（`step3`）、瓶颈（ISSUE：无独立瓶颈调度） | `litho_solver.py` step3/step5 | 缺瓶颈设备调度专项 |
| **1.2.3 调度方法** | 运筹学 / DES / **5 类启发式规则**（交货期·加工周期·等待时间·程序相同·负载平衡） | MILP（运筹学）+ DES（`fab_sim`）+ 优先级规则（PRI1~4 加权） | `litho_solver.py`、`backend/sim/fab_sim.py` | **只有"交货期"类规则**，其余 4 类未实现 |
| **1.2.4 评价指标** | 加工周期 CT / WIP / 总移动量 Mov / 移动速率 Turn / 设备利用率 Util / 生产率 Prod / 脱期率 | ✅ MakeSpan、机台负载、准时率；❌ **无 WIP / Mov / Turn / CT** | `fact_run`、`fact_schedule`（计划中的星型模型） | **缺 4 个核心 KPI** |
| **2.1 调度框架** | 多 Agent 形式；APS 的三大局限：理论与应用鸿沟 / 智能化不高 / 只做仿真不做自适应 | ✅ 我们已用 Agent + Dify 双编排 | `backend/app/agent/`、`workflow.py` | — |
| **2.2 DSACMS 体系结构** | ETL / ORM / PreProcData / **BuildPredictionModel** / MHO 五个方法集 | ❌ 只有 ETL 雏形（`store.py`） | — | **缺预测建模与元启发式优化** |
| **2.2.2 形式化描述** | **调度环境向量 Xse**（生产线级 + 加工区级共 15+ 维）+ 调度方法编码 Xsch | ❌ 完全缺失 | — | **这是最大的方法论缺口** |
| **3.2~3.5 数据预处理** | 数据规范化 / 缺失值填补（GS-MPSO-KNN）/ 聚类异常值探测（KMEANS）/ 冗余变量检测（MCLPSO-KMEANSVAR） | 🟡 只有 3 条基础校验 | `workflow.step_validate_data` L34-45 | **缺四件套中的三件** |
| **4.x 性能指标相关性** | 短期 vs 长期指标；皮尔逊系数（日在制品数-日移动步数、日排队队长-日移动步数、日设备利用率-日移动步数） | ❌ 无 | — | **可挂到 DAX 度量** |
| **5.x 投料控制** | CONWIP 固定投料 → 极限学习机定投料时刻/顺序 → 属性选择优化 | 🟡 有 BARC 放货间隔 + QTMS 水位，属"被动限流" | `litho_solver.py` step5 | **缺主动投料控制策略** |
| **6.x 动态派工** | **模拟信息素机制的动态派工规则** + 数据挖掘优化算法参数 | 🟡 有静态优先级（PRI1~4） | `litho_solver.py` step3 | **缺动态自适应派工** |
| **7.x 性能驱动调度** | 性能指标预测 → 基于负载均衡的动态调度 → 性能指标驱动的调度模型 | ✅ 负载均衡（`w_makespan` 权重 + 机台容量校验） | `CONFIG.w_makespan` | **缺"预测-优化"闭环** |
| **8.x 大数据趋势** | 工业 4.0 / 工业大数据 / 基于数据的 Petri 网 / 动态仿真 / 预测模型 | 🟡 有 3D 孪生回放（可视化，非 Petri 网） | `vendor/semiconfab-gtx` | 可视化有了，形式化模型没有 |

---

## 三、可直接落地的 5 项能力增强（按性价比排序）

### P0 · 补齐 4 个核心 KPI（1 天，纯增量）

书 1.2.4 定义的指标我们只有 3 个。缺的 4 个直接从现有 `schedule` 算得出：

| 指标 | 定义（书中） | 我们的算法 | 落地位置 |
|---|---|---|---|
| **CT 加工周期** | 工件进入系统到离开的总时间 | `end - dim_lot.ready_min` | `fact_schedule.cycle_time_min` |
| **WIP 在制品** | 某时刻未完成加工的工件数 | 按 `start_min` 累积计数 | `fact_schedule` 衍生表 或 DAX |
| **Mov 总移动量** | 单位时间内所有工件的移动步数 | `COUNT(lot) × step_seq` | `fact_run.total_moves` |
| **Turn 移动速率** | 单位时间单个工件平均移动步数 | `Mov / WIP` | DAX 度量 |

**价值**：这 4 个是半导体行业的标准语言。面试 / 客户沟通时说得出 CT、WIP、Mov、Turn，专业度立刻不同。

**验收**：PowerBI 里 4 个新度量能出数，且与 `run_summary.json` 手算一致。

---

### P1 · 调度环境向量 Xse（3 天，方法论核心）

**书里的定义**（2.2.2 划线）：

> **生产线级**：在制品数量、在制品分类数量、紧急工件数量及其占比、可用设备数、瓶颈设备数及其占比、工件到理论交货期的平均剩余时间及标准差、系统加工产能比
>
> **加工区级**：各区在制品数量、各区在制品占比、各区加工产能比、各区可用设备数、各区瓶颈设备数及其占比

**我们的现状**：派工完全靠固定优先级 `PRI1~4` + 权重 `pri_flow_w`，**不看环境**。

**落地设计**：

```python
# backend/solver/xse.py（新增）
def build_xse(date, lots, machines, reticles, schedule=None) -> dict:
    """构造调度环境向量 Xse（15 维），用于后续规则选择/预测模型输入"""
    return {
        # 生产线级 8 维
        "wip_total": len(lots),
        "wip_by_priority": {p: sum(1 for l in lots if l["priority"] == p) for p in (1,2,3,4)},
        "urgent_count": sum(1 for l in lots if "SHR" in l["tags"] or "KeyLot" in l["tags"]),
        "urgent_ratio": ...,
        "avail_eqp": sum(1 for m in machines if m["status"] == "idle"),
        "bottleneck_eqp": ...,
        "avg_remain_to_due": ...,
        "capacity_ratio": ...,
        # 加工区级 7 维（按 eqp_group 聚合）
        "zone_wip": {...},
        "zone_wip_ratio": {...},
        "zone_capacity_ratio": {...},
        "zone_avail_eqp": {...},
        "zone_bottleneck": {...},
    }
```

**落地点**：
- 求解时计算并存入 `run_summary.xse`（一条 JSON 字段）
- 星型模型加 `dim_env` 或 `fact_run.xse`（jsonb）
- Agent 工具新增 `get_env_vector`（read），让 LLM 能"看环境再决策"

**价值**：这是本书最核心的方法论。有了 Xse，才能做"自适应调度"；没有它，永远只能跑固定规则。

---

### P2 · 数据预处理四件套（2 天，接真实数据的前提）

书第 3 章给了完整方法论，我们现在只有 3 条校验（光罩存在 / 产品有机台 / 到站时间合法）。

| 书中方法 | 我们的现状 | 落地建议 |
|---|---|---|
| **数据规范化** | 无 | 不同量纲（分钟 / 片数 / 权重）归一化到 [0,1]，作为 Xse 的输入 |
| **缺失值填补** | 无（`ready=None` 会直接崩） | 先做最简单的：中位数填补 + 标记 `imputed` 字段；书里的 GS-MPSO-KNN 留作 V3 |
| **聚类异常值探测** | 无 | K-Means 或简化版 3σ 规则，标出异常 Lot，**不阻断求解，只打标** |
| **冗余变量检测** | 无 | 相关系数 > 0.95 的变量对告警（如 `barc_er` 与 `start` 强相关） |

**价值**：这是"接真实客户数据"的必备能力。客户数据一定脏，没有预处理就无法落地。

**注意**：书中算法（GS-MPSO-KNN、MCLPSO-KMEANSVAR）都是论文级复杂算法，**不要照搬**。先做工程可用的简化版（中位数+BOM 校验+3σ），把接口留好，算法后替换。

---

### P3 · 主动投料控制（2 天，直接提升准时率）

书第 5 章：CONWIP（固定在制品）→ 极限学习机定投料时刻 → 属性选择优化。

**我们的现状**：`step5` 只做 BARC 反推放货时刻（被动满足约束），不是主动控制投料。

**落地设计**：加一个投料策略参数：

```python
CONFIG["release_policy"] = "CONWIP"   # CONWIP | DUE_DATE | WIP_TARGET | ADAPTIVE
CONFIG["wip_target"] = 9              # 目标在制品数
```

然后在 `step3` 前插入投料决策：

```python
def decide_release(xse, policy, config):
    """按环境向量决定这一轮放多少个 Lot 进线"""
    if policy == "CONWIP": return config["wip_target"] - xse["wip_total"]
    if policy == "DUE_DATE": return [l for l in lots if 剩余时间 < 阈值]
    ...
```

**价值**：投料控制是半导体调度里**收益最大**的杠杆（书里花了整整一章）。我们的系统目前"所有 Lot 一起排"，不符合真实产线（非零初始状态）。

---

### P4 · 动态派工规则（3 天，书里的创新点）

书第 6 章：**模拟信息素机制的动态派工规则**（借鉴蚁群算法的信息素挥发机制，让"最近表现好的规则"权重上升）。

**落地设计**（简化版，不照搬蚁群）：

```python
# 维护一个规则权重表，每次求解后按结果反馈更新
RULE_WEIGHTS = {"PRI": 0.4, "EDD": 0.3, "SPT": 0.2, "LOAD_BAL": 0.1}

def update_rule_weights(result, weights, decay=0.9):
    """info素挥发 + 强化：表现好的规则权重上升，其余按 decay 衰减"""
    score = {"PRI": ..., "EDD": ..., "SPT": ..., "LOAD_BAL": ...}   # 按本次 KPI 打分
    for k in weights:
        weights[k] = weights[k] * decay + score[k] * (1 - decay)
    return normalize(weights)
```

**价值**：这是书里唯一"原创算法"，也最容易做出差异化。而且**天然适合 Agent**：让 Agent 每次求解后调用 `update_rule_weights`，形成"越跑越准"的闭环。

---

## 四、我们已经做到、书里没强调的

| 我们的能力 | 书里的对应 | 我们的优势 |
|---|---|---|
| **六步 MILP 精确求解**（chunk ≤50） | 书主要用启发式 + 仿真，未强调精确 MILP | 我们的解质量更高、可证明最优 |
| **3D 数字孪生回放** | 书第 8 章提到"动态仿真"但只到形式化 | 我们有可演示的可视化 |
| **LLM Agent + Dify 双编排** | 书 2.1 提"多 Agent 形式"但无 LLM | 我们是 2026 年的实现方式 |

**结论**：我们在"求解精度"和"交互层"领先；书在"环境感知"和"数据驱动闭环"领先。两者结合才是完整产品。

---

## 五、书里有、我们完全缺的 3 个

1. **性能指标预测模型（PPM）**
   书 7.1：预测 CT / 准时率 / 等待时间，避免反复仿真。
   → 我们需要：`predict_kpi(xse, xsch)` 模型。**最小可行**：用现有 542 个 run 的历史数据做线性回归（`numpy` 都不需要，纯 Python 最小二乘）。

2. **调度方法编码 Xsch**
   书 2.2.2：把"投料策略 + 派工规则 + 参数"编码成向量，才能做优化搜索。
   → 我们需要：`encode_schedule_method(config) -> list[float]`，让 Agent 能"搜索参数空间"。

3. **Petri 网形式化模型**
   书 1.3.2 / 8.3.1：把产线映射为 Petri 网，可做可达性分析。
   → **建议放弃**：投入产出比低，我们已有 DES 仿真替代。

---

## 六、落地路线（挂到已批准的 V1→V3 路线）

| 版本 | 从书里吸收什么 | 工作量 |
|---|---|---|
| **V1**（当前冲刺中） | P0 四个 KPI（CT/WIP/Mov/Turn）补进 DAX 度量 | 1 天 |
| **V2**（阶段 4-5） | P1 调度环境向量 Xse + P2 数据预处理简化版 | 5 天 |
| **V3**（阶段 7） | P3 主动投料控制 + P4 动态派工规则 + 性能指标预测模型 | 8 天 |

**建议插入点**：P0 现在就能做（只加 4 个 DAX 度量 + 2 个 `fact_schedule` 字段），不阻塞任何阶段。

---

## 七、给面试 / 客户讲的三句话

1. **「我们不是排程工具，是数据驱动的调度决策系统」** —— 对应书 2.2 DSACMS 框架
2. **「派工不看固定规则，看当前调度环境」** —— 对应 Xse（15 维环境向量）
3. **「每次求解都在训练下一轮的规则权重」** —— 对应书第 6 章信息素机制

> 这三句话都有代码支撑（现有 6 步算法 + 待建的 Xse + 规则权重表），不是空话。

---

## 附：数据来源

- 划线原文：`.runtime/book/marks.txt`（103 条，19 章节）
- 完整目录：`.runtime/book/chapters.json`（125 节）
- 获取方式：微信读书 Skill 1.0.5 · `/book/bookmarklist` + `/book/chapterinfo`
