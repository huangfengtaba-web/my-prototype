# -*- coding: utf-8 -*-
"""算法精化档 · matplotlib 甘特图渲染（E3）。

配色复用原型 result_litho.html 的口径（docs/_DESIGN_SPEC.md §3）：
Process 主色 #1677FF；Setup/换罩用 Warning #FAAD14。

用法（脚本或 API 精化档均可）::

    from backend.solver.viz import draw_gantt
    draw_gantt(summary)                       # 弹窗显示
    draw_gantt(summary, "out/gantt.png")      # 存 PNG（utf-8 路径兼容 Windows）

MVP 档不依赖：matplotlib 缺失时抛出带安装提示的 ImportError。
"""
import os


def _require_mpl():
    try:
        import matplotlib
    except ImportError as e:
        raise ImportError(
            "需要 matplotlib：pip install matplotlib（backend/requirements.txt 已含）") from e
    matplotlib.use("Agg" if os.getenv("LITHO_VIZ_HEADLESS") else "TkAgg")
    # 中文字体（缺省会因 DejaVu Sans 无 CJK 字形刷一屏 warning）
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    return matplotlib


PRIMARY = "#1677FF"
WARNING = "#FAAD14"
TEXT_SUB = "rgba(0,0,0,.65)"


def draw_gantt(summary, out_png=None):
    """按 Eqp 分行画甘特。summary 是 run_summary.json 的结构（含 schedule 列表）。"""
    mpl = _require_mpl()
    import matplotlib.pyplot as plt

    def to_min(hm):
        if not hm:
            return None
        h, m = str(hm).split(":")
        return int(h) * 60 + int(m)

    sched = [r for r in summary.get("schedule", []) if r.get("eqp") and r.get("start")]
    if not sched:
        raise ValueError("summary.schedule 里没有可画的排程行")

    by_eqp = {}
    for r in sched:
        by_eqp.setdefault(r["eqp"], []).append(r)
    eqps = sorted(by_eqp)

    fig, ax = plt.subplots(figsize=(11, 0.6 * len(eqps) + 1.5))
    for y, eqp in enumerate(eqps):
        for r in sorted(by_eqp[eqp], key=lambda x: to_min(x["start"])):
            s, t = to_min(r["start"]), to_min(r["end"])
            # Setup/换罩行（post_note 标记）用 Warning 色，正常加工用主色
            color = WARNING if "换" in (r.get("post_note") or "") else PRIMARY
            ax.barh(y, t - s, left=s, height=0.55, color=color, edgecolor="white")
            ax.text(s + (t - s) / 2, y, r["lot"], ha="center", va="center",
                    color="white", fontsize=8)
    ax.set_yticks(range(len(eqps)), eqps)
    ax.invert_yaxis()
    ax.set_title(
        f"Litho Schedule · {summary.get('run', {}).get('batch', '')} · "
        f"MILP {summary.get('milp_status', {}).get('step3', '')}")
    ax.set_xlabel("时间（分钟，2026-10-24 当日）")
    ax.grid(axis="x", color="#F0F0F0")
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()

    if out_png:
        os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
        fig.savefig(out_png, dpi=150)
        plt.close(fig)
        return out_png
    plt.show()
    return None
