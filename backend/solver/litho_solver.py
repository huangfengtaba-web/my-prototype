# -*- coding: utf-8 -*-
"""
GTX FSO Litho · 六步算法链 Demo（PuLP + CBC 求解器）
====================================================
依据《GTX FSO项目设计说明书-Litho-V0.1-1023.docx》与《01_算法说明.md》：

  ① 预处理 → ② Reticle 预组批(MILP) → ③ Lot 细排程(MILP, chunk) → ④ 后处理
                                                                → ⑤ BARC 反推 → ⑥ 光罩五态推演

「求解器」说明：MILP 模型 = 带 0/1 决策变量的数学方程组；
CBC（COIN-OR Branch and Cut）是免费开源的**分支定界求解引擎**，
PuLP 负责把设计书 §3.3.2.1 / §4.3.2.1 的公式翻译成方程，求解由 CBC 完成。

运行：python litho_solver.py   →  output\step1..6_*.csv + run_summary.json
"""
import csv
import json
import os
import time

import pulp

try:                                    # 包模式：python -m backend.solver
    from .mock_data import (APC, APC_CHECKS_TOTAL, CHAMBERS, CHUCK, CONFIG, DATE,
                            DOMA, HUNGRY, LOTS, MACHINES, QTIME_URGENT_MIN,
                            QTMS_LOOPS, RETICLES, RUN, STACK_BIND, TAG_TIER, fmt)
except ImportError:                     # 脚本模式：python litho_solver.py
    from mock_data import (APC, APC_CHECKS_TOTAL, CHAMBERS, CHUCK, CONFIG, DATE,
                           DOMA, HUNGRY, LOTS, MACHINES, QTIME_URGENT_MIN,
                           QTMS_LOOPS, RETICLES, RUN, STACK_BIND, TAG_TIER, fmt)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

SUMMARY = {"run": RUN, "date": DATE, "steps": []}


def log_step(n, name, status, seconds, detail=""):
    SUMMARY["steps"].append({"step": n, "name": name, "status": status,
                             "seconds": round(seconds, 3), "detail": detail})
    print(f"[{n}/6] {name:<28s} {status:<8s} {seconds:5.2f}s  {detail}")


def save_csv(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


def _pick_solver():
    """求解器适配器位（设计书需求38 降级策略）：LITHO_SOLVER=CBC(默认)/GUROBI/COPT。

    未安装商业求解器时自动回退 CBC，保证 demo 永远能跑。
    """
    name = os.getenv("LITHO_SOLVER", "CBC").upper()
    limit = CONFIG["time_limit_s"]
    if name == "GUROBI":
        try:
            return pulp.GUROBI_CMD(msg=False, timeLimit=limit)
        except Exception:
            print("[solver] GUROBI 不可用，回退 CBC")
    elif name == "COPT":
        try:
            return pulp.COPT_CMD(msg=False, timeLimit=limit)
        except Exception:
            print("[solver] COPT 不可用，回退 CBC")
    return pulp.PULP_CBC_CMD(msg=False, timeLimit=limit)


def reticle_ready_lb(reticle_id, eqp):
    """光罩就绪时间下界（step3 用；step6 给出精确五态推演，此处为静态保守下界）。

    - 外部 IRIS 光罩（need_iris + iris_at）：iris_at + 检测20 + 搬送10 + 装载5
    - StarLight 计时光罩：iris_at 到期后可用
    - 在库/在别机：搬送 + 装载
    """
    meta = RETICLES[reticle_id]
    if meta.get("need_iris") and meta.get("iris_at"):
        return meta["iris_at"] + CONFIG["iris_min"] + CONFIG["transport_min"] + CONFIG["load_min"]
    if meta["status"] == "StarLight" and meta.get("iris_at"):
        return meta["iris_at"]
    if meta["location"] != eqp:
        return CONFIG["transport_min"] + CONFIG["load_min"]
    return 0


# =====================================================================
# ① 预处理（设计书 §2/§4.2）：Lot 属性打标 + 机台可用性 + 加工时长
# =====================================================================
def step1_preprocess():
    lots = LOTS
    apc_holds = []
    # 加工时长 + 属性→优先级四档推导（设计版：数字越小越优先，取最高档）+ Hungry 拉货
    for l in LOTS:
        wphs = [MACHINES[e]["wph"] for e in capable_machines(l)]
        l["dur_est"] = -(-l["qty"] * 60 // min(wphs))          # 向上取整
        eff = l["priority"]                                     # 显式优先级（MES 口径兜底）
        src = ["显式"]
        for t in l["tags"]:                                     # 属性映射（R1: Ship/MoveTarget/KeyStage/Queue/Quota…）
            tier = TAG_TIER.get(t)
            if tier and tier < eff:
                eff, src = tier, src + [f"{t}→档{tier}"]
        if l.get("remain_qt") is not None and l["remain_qt"] < QTIME_URGENT_MIN:
            if eff > 1:
                eff, src = 1, src + [f"QTime<{QTIME_URGENT_MIN}→档1"]
        boost = HUNGRY.get(l["product"], 0)                     # R1: 下游 Hungry 拉货
        if boost:
            eff = max(1, eff - boost)
            src.append(f"Hungry({l['product']})+{boost}")
        l["priority"], l["priority_src"] = eff, "+".join(src)
        l["pri_w"] = CONFIG["pri_flow_w"][eff]
        l["tag_str"] = "/".join(l["tags"]) if l["tags"] else "Normal"
        # R3: APC 校验（Normal/RunCard/SRC/Single 维度；OOD 卡控；24 项检查）
        #     scenario 可覆盖：lots.LOT-X: {apc_ood: true, apc_failed: [...]}
        apc = dict(APC.get(l["lot"], {"type": "Normal", "ood": False, "failed": []}))
        apc["ood"] = bool(l.get("apc_ood", apc["ood"]))
        apc["failed"] = l.get("apc_failed", apc["failed"])
        l["apc"] = apc
        if apc["ood"]:
            apc_holds.append(l["lot"])
    rows = [[l["lot"], l["tag_str"], f"PRI{l['priority']}({l['priority_src']})", l["temp"],
             str(l["remain_qt"]) if l["remain_qt"] else "-",
             l["reticle"], fmt(l["ready"]), str(l["dur_est"]),
             "APC OOD 卡控" if l["apc"]["ood"] else "完成"] for l in LOTS]
    save_csv("step1_preprocess.csv",
             ["LotId", "属性打标", "Priority(推导)", "温层", "RemainQTime(min)",
              "ReticleId", "预计到站", "加工时长估(min)", "状态"], rows)
    log_step(1, "① 预处理", "完成", 0.001,
             f"{len(LOTS)} lots 打标+计时, APC OOD 卡控 {len(apc_holds)} 批")
    SUMMARY["apc"] = {l["lot"]: {"type": l["apc"]["type"], "ood": l["apc"]["ood"],
                                 "checks_passed": APC_CHECKS_TOTAL - len(l["apc"]["failed"]),
                                 "checks_total": APC_CHECKS_TOTAL,
                                 "failed": l["apc"]["failed"]} for l in LOTS}
    return LOTS


def capable_machines(lot):
    # R2: Stacking Bond 首层绑定白名单（设计版口径：RunPath constraint）
    allowed = STACK_BIND.get(lot["product"])
    base = [e for e, m in MACHINES.items() if lot["product"] in m["products"]]
    return [e for e in base if not allowed or e in allowed]


# =====================================================================
# ② Reticle 预组批 MILP（设计书 §3.3.2.1）
#    决策变量：x[l,e]（Lot l → 机台 e）、mnt[r,e]（光罩 r 挂载于机台 e）
#    目标：min 换罩次数（Σmnt）×W1 + MakeSpan×W2
#    约束：每 Lot 恰配一机台；Capability 匹配；同一光罩被用到即产生挂载
# =====================================================================
def step2_reticle_grouping(lots):
    t0 = time.time()
    mach = list(MACHINES)
    prob = pulp.LpProblem("reticle_grouping", pulp.LpMinimize)
    x, mnt = {}, {}
    for l in lots:
        for e in capable_machines(l):
            x[l["lot"], e] = pulp.LpVariable(f"x_{l['lot']}_{e}", cat="Binary")
    for r in RETICLES:
        for e in mach:
            mnt[r, e] = pulp.LpVariable(f"mnt_{r}_{e}", cat="Binary")
    C = pulp.LpVariable("C", lowBound=0)   # MakeSpan（分钟负载）

    prob += (CONFIG["w_changeover"] * pulp.lpSum(mnt.values())
             + CONFIG["w_makespan"] * C)

    freeze = CONFIG.get("__freeze") or {}                   # R1: Fix Lot 冻结（相邻版本稳定）
    for l in lots:                                          # 每 Lot 恰分配一台
        prob += pulp.lpSum(x[l["lot"], e] for e in capable_machines(l)) == 1
        r = l["reticle"]
        for e in capable_machines(l):                       # 用到即挂载
            prob += x[l["lot"], e] <= mnt[r, e]
        if l["lot"] in freeze:                              # 冻结：锁定前序版本的机台
            fe = freeze[l["lot"]]["eqp"]
            if (l["lot"], fe) in x:
                prob += x[l["lot"], fe] == 1
    for e in mach:                                          # MakeSpan = 最大机台负载
        prob += C >= pulp.lpSum(x[l["lot"], e] * l["dur_est"] for l in lots
                                if (l["lot"], e) in x)

    solver = _pick_solver()
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]

    assign = {}
    for l in lots:
        for e in capable_machines(l):
            if x[l["lot"], e].value() > 0.5:
                assign[l["lot"]] = e
    mounts = [k for k, v in mnt.items() if v.value() > 0.5]

    rows = []
    for r in RETICLES:
        rl = [l for l in lots if l["reticle"] == r]
        es = sorted({assign[l["lot"]] for l in rl})
        rows.append([r, ";".join(l["lot"] for l in rl), str(len(rl)),
                     ",".join(es) if es else "-", "-", "-", status, RETICLES[r]["note"]])
    save_csv("step2_reticle_grouping.csv",
             ["ReticleId", "组批Lot", "Lot数", "分配机台", "预计换罩次数", "求解", "状态", "备注"], rows)
    log_step(2, "② Reticle 预组批 MILP", status, time.time() - t0,
             f"挂载 {len(mounts)} 次, MakeSpan={C.value():.0f}min")
    return assign, status


# =====================================================================
# ③ Lot 细排程 MILP（设计书 §4.3.2.1，chunk≤50）
#    决策变量：s[l]（开始时间）、o[l1,l2]（同机台先后序）
#    约束：s[l]≥ready；同机台不重叠；异温层换温耗时计入；QTime 下界
#    目标：min MakeSpan + Σ 优先级权×流时间
# =====================================================================
def step3_lot_scheduling(lots, assign):
    t0 = time.time()
    prob = pulp.LpProblem("lot_scheduling", pulp.LpMinimize)
    s, o = {}, {}
    gated = 0
    doma_ready = dict(CHAMBERS)                                   # R3: Doma Chamber 可用时间
    doma_ready.update(CONFIG.get("__doma_ready") or {})
    freeze = CONFIG.get("__freeze") or {}
    for l in lots:
        # 光罩就绪耦合：开工不得早于该 Lot 所配机台上光罩的就绪下界
        lb = max(l["ready"], reticle_ready_lb(l["reticle"], assign[l["lot"]]))
        d = DOMA.get(l["lot"])                                    # R3: Doma RunPath——下游 Chamber 可用性
        if d:
            lb = max(lb, doma_ready.get(d["chamber"], {}).get("ready", 0)
                     if isinstance(doma_ready.get(d["chamber"]), dict)
                     else doma_ready.get(d["chamber"], 0))
        if lb > l["ready"]:
            gated += 1
        s[l["lot"]] = pulp.LpVariable(f"s_{l['lot']}", lowBound=lb, cat="Integer")
    by_m = {}
    for l in lots:
        by_m.setdefault(assign[l["lot"]], []).append(l)
    BIGM = 3000
    for e, ls in by_m.items():
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                l1, l2 = ls[i], ls[j]
                chg = 0 if l1["temp"] == l2["temp"] else CONFIG["temp_change_min"]
                o[l1["lot"], l2["lot"]] = pulp.LpVariable(
                    f"o_{l1['lot']}_{l2['lot']}", cat="Binary")
                o[l2["lot"], l1["lot"]] = 1 - o[l1["lot"], l2["lot"]]
                d1 = dur_on(l1, e) + chg
                d2 = dur_on(l2, e) + chg
                prob += s[l1["lot"]] + d1 <= s[l2["lot"]] + BIGM * (1 - o[l1["lot"], l2["lot"]])
                prob += s[l2["lot"]] + d2 <= s[l1["lot"]] + BIGM * o[l1["lot"], l2["lot"]]
    C = pulp.LpVariable("C", lowBound=0)
    for e, ls in by_m.items():
        for l in ls:
            prob += C >= s[l["lot"]] + dur_on(l, e)
    # R2: Chuck 首尾衔接——同机台相邻 Lot 尾片/首片不相容时给软惩罚（并入目标，勿单独 prob+=）
    W = CONFIG.get("chuck_penalty", 15)
    chuck_terms = []
    chuck_pairs = 0
    for e, ls in by_m.items():
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                l1, l2 = ls[i], ls[j]
                c1, c2 = CHUCK.get(l1["lot"]), CHUCK.get(l2["lot"])
                if not (c1 and c2):
                    continue
                if c1["last"] != c2["first"]:                 # l1 → l2 方向不相容
                    chuck_terms.append(W * o[l1["lot"], l2["lot"]])
                    chuck_pairs += 1
                if c2["last"] != c1["first"]:                 # l2 → l1 方向不相容
                    chuck_terms.append(W * o[l2["lot"], l1["lot"]])
                    chuck_pairs += 1
    # 目标：MakeSpan（弱权）+ Σ 优先级权 × 超出 ready 的延迟（强权，保证急货优先）+ Chuck 惩罚
    prob += (0.05 * C
             + pulp.lpSum(l["pri_w"] * (s[l["lot"]] - l["ready"]) for l in lots)
             + pulp.lpSum(chuck_terms))
    # R1: Fix Lot 冻结——同机台上被冻结的 Lot 保持前序版本的先后顺序
    for e, ls in by_m.items():
        frozen = sorted([l for l in ls if l["lot"] in freeze],
                        key=lambda l: freeze[l["lot"]]["start"])
        for a, b in zip(frozen, frozen[1:]):
            prob += s[b["lot"]] >= s[a["lot"]] + dur_on(a, e)
    solver = _pick_solver()
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]
    for l in lots:
        l["assign"] = assign[l["lot"]]
        l["start"] = int(round(s[l["lot"]].value()))
        l["end"] = l["start"] + dur_on(l, l["assign"])

    rows = [[l["lot"], l["assign"], MACHINES[l["assign"]]["group"], l["product"],
             l["step"], l["reticle"], fmt(l["start"]), fmt(l["end"]),
             str(l["end"] - l["start"]), f"PRI{l['priority']}", l["temp"],
             "OK" if not l["qtms_over"] else "QTMS_OVER"] for l in lots]
    save_csv("step3_schedule_result.csv",
             ["LotId", "Litho Eqp", "Eqp Group", "ProductId", "Step Seq", "ReticleId",
              "Litho Start", "Litho End", "Process Time(min)", "Priority", "Temp", "Status"], rows)
    log_step(3, "③ Lot 细排程 MILP", status, time.time() - t0,
             f"MakeSpan={fmt(int(round(C.value())))}, 光罩就绪卡控 {gated} 条, Chuck 不相容对 {chuck_pairs}")
    SUMMARY["chuck_pairs"] = chuck_pairs
    return status


def dur_on(lot, eqp):
    return -(-lot["qty"] * 60 // MACHINES[eqp]["wph"])   # ceil(qty*60/wph)


# =====================================================================
# ④ 后处理（设计书 §4.6 / SDR 联动）：同光罩放货间隔、QTMS 水位卡控、SDR 指令
# =====================================================================
def step4_postprocess(lots):
    t0 = time.time()
    skipped = [l for l in lots if l["qtms_over"]]
    for l in skipped:
        l["start"], l["end"], l["post_note"] = None, None, "QTMS 超水位，跳过本 Loop"
    # R3: APC OOD 卡控——整批不可派工（需求版：已有 OOD 的货应阻止派工）
    for l in lots:
        if l["apc"]["ood"] and not l["qtms_over"]:
            l["start"], l["end"] = None, None
            l["post_note"] = "APC OOD 卡控，本 Loop 不可派工"
            skipped.append(l)
    # 同光罩放货间隔（BARC_SAME_STAGE_RELEASE_GAP）
    by_r = {}
    for l in lots:
        if l["start"] is not None:
            by_r.setdefault(l["reticle"], []).append(l)
    for r, ls in by_r.items():
        ls.sort(key=lambda x: x["start"])
        prev = None
        for l in ls:
            if prev is not None and l["start"] - prev < CONFIG["release_gap_min"] \
                    and "SHR" not in l["tags"]:      # 急货（SHR）不受间隔推移
                push = CONFIG["release_gap_min"] - (l["start"] - prev)
                l["start"] += push
                l["end"] = l["start"] + dur_on(l, l["assign"])
                l["post_note"] = f"放货间隔卡控 +{push}min"
            prev = l["start"]
    for l in lots:
        l.setdefault("post_note", "-")
    # R3: QTMS 逐 Loop 水位校验——每个 Loop 放货量超水位时，延后超出部分（排程后校准标记）
    qtms_out = []
    for loop in QTMS_LOOPS:
        members = [l for l in lots
                   if l["product"] in loop["products"] and l["start"] is not None]
        water_override = (CONFIG.get("__qtms_water") or {}).get(loop["loop"])
        water = water_override if water_override is not None else loop["water"]
        members.sort(key=lambda x: x["start"])
        excess = members[water:]
        for k, l in enumerate(excess, 1):
            push = CONFIG["release_gap_min"] * k
            l["start"] += push
            l["end"] = l["start"] + dur_on(l, l["assign"])
            l["post_note"] = f"QTMS {loop['loop']} 水位卡控 +{push}min"
        qtms_out.append({"loop": loop["loop"], "water": water,
                         "released": len(members), "deferred": len(excess)})
    SUMMARY["qtms_loops"] = qtms_out
    rows = [[l["lot"], l["reticle"], fmt(l["start"]) if l["start"] else "-",
             ("推至 " + fmt(l["start"])) if "卡控" in l["post_note"] else
             ("跳过本 Loop" if (l["qtms_over"] or l["apc"]["ood"]) else "无调整"),
             ("BARC_SAME_STAGE_RELEASE_GAP=2h" if "放货间隔" in l["post_note"] else
              "QTMS 超水位" if l["qtms_over"] else
              "APC OOD" if l["apc"]["ood"] else "-"), "已应用"] for l in lots]
    save_csv("step4_postprocess.csv",
             ["LotId", "ReticleId", "调整后Litho Start", "调整", "规则", "状态"], rows)
    log_step(4, "④ 后处理", "完成", time.time() - t0,
             f"卡控 {sum(1 for l in lots if '卡控' in l['post_note'])} 条, 跳过 {len(skipped)} 条, "
             f"QTMS Loop 延后 {sum(o['deferred'] for o in qtms_out)} 条")
    return skipped


# =====================================================================
# ④+ 光罩计片/寿命动态校准（R2, RFP 2.1.8）：
#     沿时间轴维护每枚光罩的剩余可用片数与检测有效期；余量不足或寿命到期时
#     触发一次 IRIS（检测20+搬送10+装载5=35min）并顺延同机台后续 Lot。
#     这是 MILP 之后的确定性校准步：不改变 MILP 状态，只对执行时间做可行性修正。
# =====================================================================
def step45_reticle_calibration(lots):
    t0 = time.time()
    reset_wafers = CONFIG["iris_reset_wafers"]
    chain = CONFIG["iris_min"] + CONFIG["transport_min"] + CONFIG["load_min"]  # 35min

    def expiry_of(meta):
        if meta.get("need_iris"):
            return 10 ** 9          # 外部 IRIS 刚重置（就绪链路已含检测），无计时约束
        if meta["status"] == "StarLight" and meta.get("iris_at"):
            return meta["iris_at"]  # StarLight 到期后才可用
        return 540 + meta.get("life_remain_min", 10 ** 9)       # 计时余量自 09:00 起

    state = {}
    for l in sorted([x for x in lots if x.get("start") is not None],
                    key=lambda x: x["start"]):
        r = l["reticle"]
        meta = RETICLES[r]
        st = state.setdefault(r, {
            "remain": reset_wafers if meta.get("need_iris") else meta.get("wafer_to_iris", 0),
            "expiry": expiry_of(meta), "free": 0, "last_eqp": None,
        })
        notes = []
        # 1) 计时：寿命到期 → 触发 IRIS 重置
        if l["start"] > st["expiry"]:
            st["remain"] = reset_wafers
            st["expiry"] = 10 ** 9 if meta.get("need_iris") else l["start"] + meta.get("life_remain_min", 0)
            l["start"] = max(l["start"], st["free"]) + chain
            l["end"] = l["start"] + dur_on(l, l["assign"])
            notes.append(f"光罩寿命到期，IRIS 重置 +{chain}min")
        # 2) 计片：剩余可用片数不足本 Lot → 触发 IRIS 重置
        elif st["remain"] < l["qty"]:
            pre = st["remain"]
            base = max(l["start"], st["free"])
            l["start"] = base + chain
            l["end"] = l["start"] + dur_on(l, l["assign"])
            st["remain"] = reset_wafers
            st["expiry"] = 10 ** 9 if meta.get("need_iris") else l["start"] + meta.get("life_remain_min", 0)
            notes.append(f"计片不足（余{pre}<{l['qty']}），IRIS +{chain}min")
        # 3) 光罩跨机接力：上一使用机台不同 → 搬送+装载
        earliest = st["free"] + (CONFIG["transport_min"] + CONFIG["load_min"]
                                 if st["last_eqp"] not in (None, l["assign"]) else 0)
        if l["start"] < earliest:
            notes.append(f"光罩接力等待 +{earliest - l['start']:.0f}min")
            l["start"] = int(earliest)
            l["end"] = l["start"] + dur_on(l, l["assign"])
        st["remain"] -= l["qty"]
        st["free"] = l["end"]
        st["last_eqp"] = l["assign"]
        if notes:
            l["post_note"] = (l["post_note"] + "；" if l.get("post_note", "-") != "-" else "") + \
                             "；".join(notes)

    # 同机台去重叠：校准顺延后保证机台内不重叠（含异温层换温间隔）
    for e in MACHINES:
        ml = sorted([l for l in lots if l.get("assign") == e and l.get("start") is not None],
                    key=lambda x: x["start"])
        prev = None
        for l in ml:
            if prev is not None:
                gap = 0 if prev["temp"] == l["temp"] else CONFIG["temp_change_min"]
                if l["start"] < prev["end"] + gap:
                    push = prev["end"] + gap - l["start"]
                    l["start"] += push
                    l["end"] = l["start"] + dur_on(l, e)
                    l["post_note"] = (l["post_note"] + "；" if l.get("post_note", "-") != "-" else "") + \
                                     f"机台顺延 +{push}min"
            prev = l

    SUMMARY["reticle_calib"] = {
        r: {"remain_wafers": s["remain"], "expiry": fmt(s["expiry"]) if s["expiry"] < 10 ** 8 else "-",
            "free_at": fmt(s["free"])} for r, s in state.items()}
    n_cal = sum(1 for l in lots if "IRIS" in (l.get("post_note") or ""))
    log_step("4.5", "④+ 光罩计片/寿命校准", "完成", time.time() - t0,
             f"IRIS 触发 {n_cal} 批, 光罩 {len(state)} 枚")
    return lots


# =====================================================================
# ⑤ BARC 反推（设计书 §2.3）：ER = LithoStart − QTime − PT；LR = LithoStart − PT
# =====================================================================
def step5_barc(lots):
    t0 = time.time()
    rows, batch_id = [], {}
    batches = []
    # R1: BARC 预组批——同 Reticle 且放货窗口相容（ER ≤ 批次最晚窗口）的 Lot 归入同一 Batch
    for ret in sorted({l["reticle"] for l in lots}):
        members = sorted([l for l in lots if l["reticle"] == ret and l["start"] is not None],
                         key=lambda x: x["start"] - x["barc_qt"] - x["pt"])
        cur, k = None, 0
        for l in members:
            er = l["start"] - l["barc_qt"] - l["pt"]
            lr = l["start"] - l["pt"]
            l["barc_er"], l["barc_lr"] = er, lr
            if cur is None or er > cur["lr_max"]:               # 窗口不相容 → 新开 Batch
                k += 1
                cur = {"batch_id": f"B-{DATE.replace('-', '')}-{ret[-4:]}-{k}",
                       "reticle": ret, "lots": [], "er_min": er, "lr_max": lr}
                batches.append(cur)
            cur["lots"].append(l["lot"])
            cur["er_min"] = max(cur["er_min"], er)              # 批次窗口取交集
            cur["lr_max"] = min(cur["lr_max"], lr)
            batch_id[l["lot"]] = cur["batch_id"]
        for l in [l for l in lots if l["reticle"] == ret and l["start"] is None]:
            batches.append({"batch_id": f"B-{DATE.replace('-', '')}-{ret[-4:]}-X",
                            "reticle": ret, "lots": [l["lot"]], "er_min": None,
                            "lr_max": None})
            batch_id[l["lot"]] = f"B-{DATE.replace('-', '')}-{ret[-4:]}-X"
    for l in sorted(lots, key=lambda x: x["reticle"]):
        bid = batch_id[l["lot"]]
        if l["start"] is None:
            reason = "QTMS 超水位" if l["qtms_over"] else ("APC OOD 卡控" if l["apc"]["ood"] else "-")
            rows.append([bid, l["lot"], "-", "-", "-", "FAIL", reason])
            continue
        rows.append([bid, l["lot"], fmt(l["barc_er"]), fmt(l["barc_lr"]),
                     f"LithoStart {fmt(l['start'])} − QTime {l['barc_qt'] // 60}h − PT {l['pt']}min",
                     "OK", ""])
    SUMMARY["barc_batches"] = [
        {"batch_id": b["batch_id"], "reticle": b["reticle"], "lots": b["lots"],
         "window": (f"{fmt(b['er_min'])}~{fmt(b['lr_max'])}" if b["er_min"] is not None else "-")}
        for b in batches]
    save_csv("step5_barc_release.csv",
             ["BatchId", "LotId", "Earliest Release", "Latest Release", "计算依据", "状态", "错误信息"], rows)
    log_step(5, "⑤ BARC 反推", "完成", time.time() - t0,
             f"{len(rows)} 行, 组批 {len(SUMMARY['barc_batches'])} 个")
    return batch_id


# =====================================================================
# ⑥ 光罩五态推演（设计书 §3 / PPT P5-P6）：
#    五态 Process→Inspection→StarLight→Stocker→Transport；急货链 20+10+5=35min
# =====================================================================
def step6_reticle_deduction(lots):
    t0 = time.time()
    segs = []
    for r, meta in RETICLES.items():
        rl = sorted([l for l in lots if l["reticle"] == r and l["start"] is not None],
                    key=lambda x: x["start"])
        if meta["need_iris"] and rl:                     # 外部光罩：IRIS→搬送→装载→就绪
            t = meta["iris_at"]
            segs += [[r, "Inspection", "IRIS01", fmt(t), fmt(t + CONFIG["iris_min"]), f"{CONFIG['iris_min']}min"],
                     [r, "Transport", "AMHS", fmt(t + CONFIG["iris_min"]),
                      fmt(t + CONFIG["iris_min"] + CONFIG["transport_min"]), f"{CONFIG['transport_min']}min"]]
            t += CONFIG["iris_min"] + CONFIG["transport_min"]
            segs.append([r, "Stocker→装载", rl[0]["assign"], fmt(t),
                         fmt(t + CONFIG["load_min"]), f"{CONFIG['load_min']}min"])
            ready = t + CONFIG["load_min"]
            segs.append([r, "Process", rl[0]["assign"], fmt(rl[0]["start"]),
                         fmt(rl[0]["end"]), f"{rl[0]['end'] - rl[0]['start']}min"])
        elif meta["status"] == "StarLight" and rl:       # 计时到期后直上
            ready = meta["iris_at"]
            segs.append([r, "StarLight", meta["location"], fmt(rl[0]["start"] - 60),
                         fmt(ready), "至 11:18 到期"])
            segs.append([r, "Process", rl[0]["assign"], fmt(rl[0]["start"]),
                         fmt(rl[0]["end"]), f"{rl[0]['end'] - rl[0]['start']}min"])
        elif rl:
            ready = rl[0]["start"] - CONFIG["load_min"]
            segs.append([r, "Process", rl[0]["assign"], fmt(rl[0]["start"]),
                         fmt(rl[0]["end"]), f"{rl[0]['end'] - rl[0]['start']}min"])
        else:
            ready = None
            segs.append([r, meta["status"], meta["location"], "-", "-", "本 Loop 无需求"])
        meta["ready"] = ready
        segs.append([r, "→就绪", "-", "-", fmt(ready) if ready else "-",
                     f"EARLIEST_AVAILABLE={fmt(ready) if ready else '-'}"])
    save_csv("step6_reticle_deduction.csv",
             ["ReticleId", "状态(五态)", "Location/Equip", "Start", "End", "Cost/说明"], segs)
    log_step(6, "⑥ 光罩五态推演", "完成", time.time() - t0,
             f"RT-0101 就绪 {fmt(RETICLES['RT-0101']['ready'])}（09:10+20+10+5）")
    return segs


# =====================================================================
# 主流程：六步串联 + run_summary.json
# =====================================================================
def main(fix=None):
    SUMMARY["steps"] = []               # 支持被 API 反复调用，先清空历史步骤
    if fix:
        CONFIG["__freeze"] = fix        # R1: Fix Lot 冻结（相邻版本机台与顺序保持）
    print(f"=== GTX FSO Litho 六步算法链 Demo · {RUN['model']} {RUN['version']} · {RUN['batch']} ===")
    lots = step1_preprocess()
    assign, s2 = step2_reticle_grouping(lots)
    s3 = step3_lot_scheduling(lots, assign)
    step4_postprocess(lots)
    step45_reticle_calibration(lots)
    step5_barc(lots)
    step6_reticle_deduction(lots)

    SUMMARY["milp_status"] = {"step2": s2, "step3": s3}
    SUMMARY["stacking_load"] = {e: sum(dur_on(l, e) for l in lots
                                       if l.get("assign") == e and l.get("start"))
                                for e in MACHINES}          # R2: Stacking 30 天负载推演输入
    SUMMARY["story_check"] = {                      # 急货故事线一致性自检
        "LOT-A01 上机时间": fmt(next(l["start"] for l in lots if l["lot"] == "LOT-A01")),
        "RT-0101 就绪时间": fmt(RETICLES["RT-0101"]["ready"]),
        "准备链": "09:10 IRIS 20min → 搬送 10min → 装载 5min = 35min",
        "LOT-A01 片数": 25,
    }
    print("--- 急货故事线自检 ---")
    for k, v in SUMMARY["story_check"].items():
        print(f"  {k}: {v}")
    print(f"=== 完成：output\\ 共 {len(os.listdir(OUT))} 个文件 ===")
    SUMMARY["schedule"] = [            # 结构化结果，供 FastAPI / 前端直接消费
        {"lot": l["lot"], "eqp": l.get("assign"), "eqp_group":
         MACHINES[l["assign"]]["group"] if l.get("assign") else None,
         "reticle": l["reticle"], "priority": f"PRI{l['priority']}", "temp": l["temp"],
         "start": fmt(l["start"]) if l["start"] is not None else None,
         "end": fmt(l["end"]) if l.get("end") is not None else None,
         "barc_er": fmt(l["barc_er"]) if l.get("barc_er") is not None else None,
         "barc_lr": fmt(l["barc_lr"]) if l.get("barc_lr") is not None else None,
         "post_note": l.get("post_note", "-")}
        for l in sorted(LOTS, key=lambda x: (x["start"] is None, x.get("start") or 0))
    ]
    SUMMARY["reticles"] = {
        r: {"status": m["status"], "note": m["note"],
            "ready": fmt(m["ready"]) if m.get("ready") is not None else None}
        for r, m in RETICLES.items()
    }
    # 写盘放最后：确保文件版也包含 schedule / reticles（stdout 版本本来就带）
    with open(os.path.join(OUT, "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(SUMMARY, f, ensure_ascii=False, indent=2)
    return SUMMARY


if __name__ == "__main__":
    main()
