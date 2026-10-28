# GTX FSO Litho · 算法能力 Demo（PuLP + CBC）

> 对应《01_算法说明.md》六步链与《GTX FSO项目设计说明书-Litho-V0.1-1023.docx》§2/§3/§4
> 数据口径与 02_原型 完全一致：急货故事线 LOT-A01 + RT-0101，2026-10-24。

## 1. 一分钟运行

```bash
D:\software\miniconda\anzhuang\python.exe -m pip install pulp --proxy http://127.0.0.1:10808
cd D:\工作\嘉定GTX\GTX_FSO_交付物\04_算法demo
D:\software\miniconda\anzhuang\python.exe litho_solver.py
```

输出 → `output\`：`step1_preprocess / step2_reticle_grouping / step3_schedule_result /
step4_postprocess / step5_barc_release / step6_reticle_deduction` 共 6 份 CSV +
`run_summary.json`（含 MILP 状态与急货故事线自检）。

预期控制台：②③ 均 **Optimal**；自检项 `LOT-A01 上机 10:00 / RT-0101 就绪 09:45 / 准备链 20+10+5=35min / 25片`。

## 2. 「求解器」是什么？（一句话 + 展开）

**一句话**：求解器（Solver）= 专门解"带 0/1 决策变量的数学方程组（MILP）"的**分支定界数学引擎**，本项目用的是免费开源的 **CBC**（COIN-OR Branch and Cut），随 PuLP 自带、零配置。

展开：
- **建模库（PuLP）**：把设计书公式翻译成方程——"每个 Lot 恰分配一台机台"写成 `Σ x[l,e] == 1`；
- **求解器（CBC）**：接手方程组，用分支定界+剪枝搜出**最优解**（控制台显示 `Optimal`）；
- **为什么要它**：排程组合爆炸（10 Lot × 6 机台已有百万级组合），人工规则只能给"可行解"，求解器给"最优解"且可证明。真实项目数据量大时，把 CBC 换成 Gurobi / COPT 等商用求解器即可，**建模代码不变**——这就是"算法能力"的可迁移部分。

## 3. 六步实现与设计书对照

| 步骤 | 代码位置（litho_solver.py） | 设计书出处 | 方法 |
|---|---|---|---|
| ① 预处理 | `step1_preprocess()` | §2 / §4.2 | 属性打标（SHR/KeyLot/Ship）、Remain QTime、温层、加工时长估计 |
| ② Reticle 预组批 | `step2_reticle_grouping()` | **§3.3.2.1 MILP** | 决策变量 x[l,e]、mnt[r,e]；目标 min 换罩次数×60 + MakeSpan；Capability 约束 |
| ③ Lot 细排程 | `step3_lot_scheduling()` | **§4.3.2.1 MILP** | 决策变量 s[l]、o[l1,l2]；不重叠+换温耗时；目标 MakeSpan + 优先级加权延迟 |
| ④ 后处理 | `step4_postprocess()` | §4.6 | 同光罩放货间隔 2h（急货豁免）、QTMS 水位卡控跳过 |
| ⑤ BARC 反推 | `step5_barc()` | §2.3 | `ER = LithoStart − QTime − PT`，`LR = LithoStart − PT` |
| ⑥ 光罩五态推演 | `step6_reticle_deduction()` | §3 / PPT P5-P6 | 急货链 09:10 IRIS 20min → 搬送 10min → 装载 5min → 09:45 就绪 |

## 4. 与原型的口径差异（诚实说明）

- **② 的机台分配由求解器决定**：demo 解出 RT-0101→IMM03（原型示意 mock 为 IMM01），两者都是 Capability 合法解；demo 以求解器输出为准。
- **⑤ 的数字**：原型页签示意值（09:45/09:55）与设计书公式不符；demo 严格按 §2.3 公式计算（LOT-A01：10:00 − 6h − 30min → **03:30 / 09:30**）。
- **③ 为 chunk 化简化版**：本 demo 10 个 Lot 单块求解；真实系统按 chunk≤50 分块滚动（架构位已留，见 CONFIG.chunk_size）。
- 规模扩展：Lot>50 或需 CP-SAT/Gurobi 时仅替换 solver 行，模型不用改。
