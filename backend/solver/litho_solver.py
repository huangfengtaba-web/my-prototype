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
    from .mock_data import (CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN, fmt)
except ImportError:                     # 脚本模式：python litho_solver.py
    from mock_data import (CONFIG, DATE, LOTS, MACHINES, RETICLES, RUN, fmt)

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


# =====================================================================
# ① 预处理（设计书 §2/§4.2）：Lot 属性打标 + 机台可用性 + 加工时长
# =====================================================================
def step1_preprocess():
    lots = LOTS
    # 加工时长：qty / wph（取分配前各机台最短可能时长作为估计，③按实际机台重算）
    for l in LOTS:
        wphs = [MACHINES[e]["wph"] for e in capable_machines(l)]
        l["dur_est"] = -(-l["qty"] * 60 // min(wphs))          # 向上取整
        l["pri_w"] = CONFIG["pri_flow_w"][l["priority"]]
        l["tag_str"] = "/".join(l["tags"]) if l["tags"] else "Normal"
    rows = [[l["lot"], l["tag_str"], f"PRI{l['priority']}", l["temp"],
             str(l["remain_qt"]) if l["remain_qt"] else "-",
             l["reticle"], fmt(l["ready"]), str(l["dur_est"]), "完成"] for l in LOTS]
    save_csv("step1_preprocess.csv",
             ["LotId", "属性打标", "Priority", "温层", "RemainQTime(min)",
              "ReticleId", "预计到站", "加工时长估(min)", "状态"], rows)
    log_step(1, "① 预处理", "完成", 0.001, f"{len(LOTS)} lots 打标+计时")
    return LOTS


def capable_machines(lot):
    return [e for e, m in MACHINES.items() if lot["product"] in m["products"]]


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

    for l in lots:                                          # 每 Lot 恰分配一台
        prob += pulp.lpSum(x[l["lot"], e] for e in capable_machines(l)) == 1
        r = l["reticle"]
        for e in capable_machines(l):                       # 用到即挂载
            prob += x[l["lot"], e] <= mnt[r, e]
    for e in mach:                                          # MakeSpan = 最大机台负载
        prob += C >= pulp.lpSum(x[l["lot"], e] * l["dur_est"] for l in lots
                                if (l["lot"], e) in x)

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=CONFIG["time_limit_s"])
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
    for l in lots:
        s[l["lot"]] = pulp.LpVariable(f"s_{l['lot']}", lowBound=l["ready"], cat="Integer")
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
    # 目标：MakeSpan（弱权）+ Σ 优先级权 × 超出 ready 的延迟（强权，保证急货优先）
    prob += 0.05 * C + pulp.lpSum(l["pri_w"] * (s[l["lot"]] - l["ready"]) for l in lots)
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=CONFIG["time_limit_s"])
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
             f"MakeSpan={fmt(int(round(C.value())))}")
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
    rows = [[l["lot"], l["reticle"], fmt(l["start"]) if l["start"] else "-",
             ("推至 " + fmt(l["start"])) if "卡控" in l["post_note"] else
             ("跳过本 Loop" if l["qtms_over"] else "无调整"),
             ("BARC_SAME_STAGE_RELEASE_GAP=2h" if "卡控" in l["post_note"] else
              "QTMS 超水位" if l["qtms_over"] else "-"), "已应用"] for l in lots]
    save_csv("step4_postprocess.csv",
             ["LotId", "ReticleId", "调整后Litho Start", "调整", "规则", "状态"], rows)
    log_step(4, "④ 后处理", "完成", time.time() - t0,
             f"卡控 {sum(1 for l in lots if '卡控' in l['post_note'])} 条, 跳过 {len(skipped)} 条")
    return skipped


# =====================================================================
# ⑤ BARC 反推（设计书 §2.3）：ER = LithoStart − QTime − PT；LR = LithoStart − PT
# =====================================================================
def step5_barc(lots):
    t0 = time.time()
    rows, batch_id = [], {}
    for l in sorted(lots, key=lambda x: x["reticle"]):
        bid = f"B-{DATE.replace('-', '')}-{l['reticle'][-4:]}"
        batch_id[l["lot"]] = bid
        if l["start"] is None:
            rows.append([bid, l["lot"], "-", "-", "-", "FAIL",
                         "QTMS 超水位，无法计算放货窗口"])
            continue
        er = l["start"] - l["barc_qt"] - l["pt"]
        lr = l["start"] - l["pt"]
        l["barc_er"], l["barc_lr"] = er, lr
        rows.append([bid, l["lot"], fmt(er), fmt(lr),
                     f"LithoStart {fmt(l['start'])} − QTime {l['barc_qt'] // 60}h − PT {l['pt']}min",
                     "OK", ""])
    save_csv("step5_barc_release.csv",
             ["BatchId", "LotId", "Earliest Release", "Latest Release", "计算依据", "状态", "错误信息"], rows)
    log_step(5, "⑤ BARC 反推", "完成", time.time() - t0, f"{len(rows)} 行")
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
def main():
    SUMMARY["steps"] = []               # 支持被 API 反复调用，先清空历史步骤
    print(f"=== GTX FSO Litho 六步算法链 Demo · {RUN['model']} {RUN['version']} · {RUN['batch']} ===")
    lots = step1_preprocess()
    assign, s2 = step2_reticle_grouping(lots)
    s3 = step3_lot_scheduling(lots, assign)
    step4_postprocess(lots)
    step5_barc(lots)
    step6_reticle_deduction(lots)

    SUMMARY["milp_status"] = {"step2": s2, "step3": s3}
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
