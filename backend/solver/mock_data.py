# -*- coding: utf-8 -*-
"""
GTX FSO Litho · 算法 Demo mock 数据
口径与 02_原型（result_litho / result_reticle / 中间结果页签）完全一致：
急货故事线 LOT-A01 + RT-0101，日期 2026-10-24。
时间单位：分钟（自 2026-10-24 00:00 起），540 = 09:00，600 = 10:00。
设计书出处：《GTX FSO项目设计说明书-Litho-V0.1-1023.docx》
"""

DATE = "2026-10-24"

# ---------- 机台（SOURCE_EQP_INFO / SOURCE_EQP_STATUS） ----------
# wph = Wafer Per Hour（Wafer 加工时间示意口径）；group 对应原型 Eqp Group
MACHINES = {
    "IMM01": {"group": "L-IMMI-S",  "wph": 50, "products": ["P-A", "P-B", "P-C", "P-D", "P-E"]},
    "IMM02": {"group": "L-IMMI-S",  "wph": 50, "products": ["P-A", "P-B", "P-C", "P-D", "P-E"]},
    "IMM03": {"group": "L-YIMMI-S", "wph": 45, "products": ["P-A", "P-B", "P-C", "P-D", "P-E"]},
    "IMM04": {"group": "L-YIMMI-S", "wph": 45, "products": ["P-A", "P-B", "P-C", "P-D", "P-E"]},
    "IMM05": {"group": "L-YIMMI-S", "wph": 45, "products": ["P-B", "P-C", "P-D", "P-E"]},
    "IMM06": {"group": "L-IMMI-L",  "wph": 40, "products": ["P-C", "P-D", "P-E"]},
}

# ---------- Lot（SOURCE_LOT + SOURCE_PRODUCT_FLOW + SOURCE_LOT_REMAIN_QTIME + LOTHIST） ----------
# priority: 设计书 §5 Attribute Priority 1~4
# ready:    预计到站时间（①预处理宽表字段）
# barc_qt:  BARC QTime 上限（分钟，§2 BARC 联动）；pt: BARC Process Time
# tags:     属性打标（SHR=Super Bullet / KeyLot / Ship / Pilot）
# qtms_over: QTMS 储位水位超标（④后处理卡控用）
LOTS = [
    {"lot": "LOT-A01", "reticle": "RT-0101", "product": "P-A", "step": "SEQ-210",
     "qty": 25, "priority": 1, "temp": "T2", "ready": 600,  "remain_qt": 55,
     "barc_qt": 360, "pt": 30, "tags": ["SHR", "KeyLot"], "qtms_over": False},
    {"lot": "LOT-A02", "reticle": "RT-0101", "product": "P-A", "step": "SEQ-210",
     "qty": 25, "priority": 3, "temp": "T2", "ready": 540,  "remain_qt": None,
     "barc_qt": 360, "pt": 30, "tags": [], "qtms_over": False},
    {"lot": "LOT-B02", "reticle": "RT-0102", "product": "P-B", "step": "SEQ-305",
     "qty": 25, "priority": 2, "temp": "T1", "ready": 570,  "remain_qt": None,
     "barc_qt": 300, "pt": 25, "tags": ["NormalBullet"], "qtms_over": False},
    {"lot": "LOT-B05", "reticle": "RT-0102", "product": "P-B", "step": "SEQ-305",
     "qty": 25, "priority": 2, "temp": "T1", "ready": 640,  "remain_qt": None,
     "barc_qt": 300, "pt": 25, "tags": ["Ship"], "qtms_over": False},
    {"lot": "LOT-C01", "reticle": "RT-0203", "product": "P-C", "step": "SEQ-118",
     "qty": 25, "priority": 3, "temp": "T1", "ready": 540,  "remain_qt": None,
     "barc_qt": 240, "pt": 25, "tags": [], "qtms_over": False},
    {"lot": "LOT-C07", "reticle": "RT-0203", "product": "P-C", "step": "SEQ-118",
     "qty": 25, "priority": 3, "temp": "T2", "ready": 555,  "remain_qt": None,
     "barc_qt": 240, "pt": 25, "tags": [], "qtms_over": False},
    {"lot": "LOT-D02", "reticle": "RT-0204", "product": "P-D", "step": "SEQ-402",
     "qty": 25, "priority": 2, "temp": "T2", "ready": 560,  "remain_qt": None,
     "barc_qt": 300, "pt": 25, "tags": [], "qtms_over": False},
    {"lot": "LOT-D08", "reticle": "RT-0204", "product": "P-D", "step": "SEQ-402",
     "qty": 25, "priority": 3, "temp": "T2", "ready": 600,  "remain_qt": 120,
     "barc_qt": 300, "pt": 25, "tags": [], "qtms_over": True},
    {"lot": "LOT-E03", "reticle": "RT-0305", "product": "P-E", "step": "SEQ-507",
     "qty": 25, "priority": 4, "temp": "T1", "ready": 585,  "remain_qt": None,
     "barc_qt": 240, "pt": 20, "tags": [], "qtms_over": False},
    {"lot": "LOT-E09", "reticle": "RT-0305", "product": "P-E", "step": "SEQ-507",
     "qty": 25, "priority": 3, "temp": "T1", "ready": 610,  "remain_qt": None,
     "barc_qt": 240, "pt": 20, "tags": [], "qtms_over": False},
]

# ---------- 光罩（SOURCE_RETICLE_STATUS + FSO_RETICLE_INFO） ----------
# status: 五态 Process/Inspection/StarLight/Stocker/Transport（PPT 五态色板口径）
# wafer_to_iris / life_remain_min: 计片 / 计时余量（不足触发 IRIS，§2.3）
RETICLES = {
    "RT-0101": {"status": "Stocker", "location": "IMMLIB", "wafer_to_iris": 0,
                "life_remain_min": 0, "need_iris": True, "iris_at": 550,      # 外部 IRIS 09:10
                "note": "急货预留（Super）外部光罩"},
    "RT-0102": {"status": "Process", "location": "IMM02", "wafer_to_iris": 30,
                "life_remain_min": 600, "need_iris": False, "iris_at": None,
                "note": "内部 IRIS（IMM02），本机直用"},
    "RT-0203": {"status": "Stocker", "location": "IMMLIB", "wafer_to_iris": 8,
                "life_remain_min": 480, "need_iris": False, "iris_at": None,
                "note": "机台间接力（IMM03→IMM04）"},
    "RT-0204": {"status": "StarLight", "location": "IMM06", "wafer_to_iris": 5,
                "life_remain_min": 78, "need_iris": False, "iris_at": 678,    # 11:18 计时到期
                "note": "StarLight 计时到期后可用"},
    "RT-0305": {"status": "Stocker", "location": "IMMLIB", "wafer_to_iris": 12,
                "life_remain_min": 300, "need_iris": False, "iris_at": None,
                "note": "常规储位"},
}

# ---------- 工艺/配置参数（FSO_CFG_PARAM / capability_temperature_change） ----------
CONFIG = {
    "chunk_size": 50,          # Lot 细排程 chunk ≤ 50（§4.3.2.1）
    "temp_change_min": 20,     # 温层转换耗时（T1↔T2，capability_temperature_change）
    "iris_min": 20,            # IRIS 检测 20min（PPT P5 案例）
    "transport_min": 10,       # 搬送 10min
    "load_min": 5,             # 装载 5min
    "release_gap_min": 120,    # BARC_SAME_STAGE_RELEASE_GAP = 2h（④后处理）
    "stocker_phys": 12,        # 光罩储位物理容量
    "stocker_water": 10,       # 储位水位（满水位先搬出，RT-0204 案例）
    "w_changeover": 60.0,      # ②目标权重：每次换罩等效 60min
    "w_makespan": 1.0,         # ②目标权重：MakeSpan
    "pri_flow_w": {1: 4.0, 2: 2.0, 3: 1.0, 4: 0.5},   # ③目标权重：优先级加权流时间
    "time_limit_s": 30,        # CBC 求解时限
    "iris_reset_wafers": 100,  # R2：IRIS 检测后光罩恢复的可用片数
    "chuck_penalty": 15,       # R2：Chuck 首尾片不相容的相邻惩罚（目标函数）
}

# 求解运行批次标识（对齐 FSO_MID_RUN_BATCH / 原型中间结果页）
RUN = {"model": "Litho_Main", "version": "V1.3", "batch": "RUN-20261024-01"}

# =====================================================================
# 扩展能力 mock（R1/R2/R3，口径来源：需求 V0.5 + 设计 V0.1-0922 + 总体计划 39 项功能点）
# =====================================================================

# --- R1: 属性→优先级四档映射（设计版：数字越小越优先，取最高档） ---
TAG_TIER = {
    "SHR": 1, "SSHR": 1, "Pilot": 1, "KeyLot": 1, "PiRun": 1,          # 档1
    "NormalBullet": 2, "MoveTarget": 2, "KeyStage": 2, "Ship": 2,      # 档2
    "MESQueue": 2, "ModuleQuota": 2,
}
QTIME_URGENT_MIN = 60          # Remain QTime < 60min → 档1

# --- R1: 下游 Hungry（Next Loop 缺货拉货）：产品 → 优先级提升档数 ---
HUNGRY = {"P-C": 1}

# --- R2: Chuck 首尾片绑定（相邻 Lot：前序尾片 == 后序首片 才免双工件台等待） ---
CHUCK = {
    "LOT-A01": {"first": "A", "last": "A"}, "LOT-A02": {"first": "B", "last": "A"},
    "LOT-B02": {"first": "A", "last": "B"}, "LOT-B05": {"first": "B", "last": "B"},
    "LOT-C01": {"first": "A", "last": "A"}, "LOT-C07": {"first": "B", "last": "B"},
    "LOT-D02": {"first": "A", "last": "B"}, "LOT-D08": {"first": "B", "last": "A"},
    "LOT-E03": {"first": "A", "last": "A"}, "LOT-E09": {"first": "A", "last": "B"},
}

# --- R2: Stacking Bond 首层绑定白名单（设计版口径：RunPath constraint） ---
STACK_BIND = {"P-A": ["IMM03", "IMM04"], "P-D": ["IMM06"]}

# --- R3: APC 校验（Normal/RunCard/SRC/Single 类型；OOD 卡控；24 项检查） ---
APC = {
    "LOT-A01": {"type": "Normal", "ood": False, "failed": []},
    "LOT-A02": {"type": "RunCard", "ood": False, "failed": []},
    "LOT-B02": {"type": "Normal", "ood": False, "failed": []},
    "LOT-B05": {"type": "SRC", "ood": False, "failed": []},
    "LOT-C01": {"type": "Normal", "ood": False, "failed": []},
    "LOT-C07": {"type": "Single", "ood": False, "failed": []},
    "LOT-D02": {"type": "Normal", "ood": False, "failed": []},
    "LOT-D08": {"type": "Normal", "ood": False, "failed": []},
    "LOT-E03": {"type": "RunCard", "ood": False, "failed": []},
    "LOT-E09": {"type": "Normal", "ood": False, "failed": []},
}
APC_CHECKS_TOTAL = 24          # RFP 方案列出 24 项检查

# --- R3: Doma RunPath（Immersion 绑定下游 Etch Chamber） ---
DOMA = {
    "LOT-D02": {"chamber": "ETCH-C1", "recipe": "DOMA-R1"},
    "LOT-D08": {"chamber": "ETCH-C1", "recipe": "DOMA-R1"},
}
CHAMBERS = {"ETCH-C1": {"ready": 600}, "ETCH-C2": {"ready": 540}}

# --- R3: QTMS 逐 Loop 水位（BARC→Immersion Loop 的放货量管控） ---
QTMS_LOOPS = [
    {"loop": "Loop-A (BARC→IMM, P-A)", "products": ["P-A"], "water": 2},
    {"loop": "Loop-C (BARC→IMM, P-C)", "products": ["P-C"], "water": 2},
]


def fmt(minute):
    """分钟 → HH:MM 字符串（2026-10-24 当日）。"""
    if minute is None:
        return ""
    return f"{int(minute) // 60:02d}:{int(minute) % 60:02d}"
