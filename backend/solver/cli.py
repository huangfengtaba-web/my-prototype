# -*- coding: utf-8 -*-
"""GTX FSO Litho 求解器命令行工具。

用法
----
    python -m backend.solver run                      默认用例跑六步
    python -m backend.solver run --case urgent-A01    指定 scenario
    python -m backend.solver run --out ./output       指定输出目录
    python -m backend.solver cases                    列出所有 scenario
    python -m backend.solver diff A.json B.json       对比两次运行结果

scenario 文件格式见 tests/cases/*.yaml：
    name: 用例名
    config:           覆盖 mock_data.CONFIG 的键值
      w_makespan: 1.5
    lots:             按 LotId 覆盖字段
      LOT-A01: {priority: 1, tags: [SHR]}
    reticles:         按 ReticleId 覆盖字段
      RT-0101: {iris_at: 550}
"""
import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:                      # 没装 PyYAML 时降级为「仅支持默认用例」
    yaml = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # 仓库根
CASES_DIR = os.path.join(ROOT, "tests", "cases")


def load_case(name):
    """按名字加载 scenario，返回 dict。找不到就抛出带清单的异常。"""
    if not name:
        return {}
    path = os.path.join(CASES_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"找不到用例 {name}（应为 {path}）。可用：{', '.join(list_cases()) or '无'}")
    if yaml is None:
        raise RuntimeError("未安装 PyYAML，无法加载 scenario。请 pip install PyYAML")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_cases():
    if not os.path.isdir(CASES_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(CASES_DIR) if f.endswith(".yaml"))


def apply_case(case):
    """把 scenario 覆盖应用到 mock_data 的内存对象上。

    注意：mock_data 的 LOTS / RETICLES / CONFIG 是模块级可变对象，
    覆盖只对当前进程生效，不会写回磁盘。跑完想复原请重启进程。
    """
    from . import litho_solver as ls

    applied = []
    for k, v in (case.get("config") or {}).items():
        if k in ls.CONFIG:
            ls.CONFIG[k] = v
            applied.append(f"CONFIG.{k}={v}")
    for lot_id, patch in (case.get("lots") or {}).items():
        for l in ls.LOTS:
            if l["lot"] == lot_id:
                l.update(patch)
                applied.append(f"LOTS[{lot_id}]+={patch}")
    for r_id, patch in (case.get("reticles") or {}).items():
        if r_id in ls.RETICLES:
            ls.RETICLES[r_id].update(patch)
            applied.append(f"RETICLES[{r_id}]+={patch}")
    return applied


def cmd_run(args):
    from . import litho_solver as ls

    case = load_case(args.case)
    applied = apply_case(case)
    if args.out:
        ls.OUT = os.path.abspath(args.out)
        os.makedirs(ls.OUT, exist_ok=True)

    if applied:
        print(f"[case] {case.get('name', args.case)} 已应用 {len(applied)} 项覆盖：")
        for a in applied:
            print(f"       - {a}")

    summary = ls.main()
    print(f"\n[cli] 求解状态：{summary.get('milp_status')}")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_cases(args):
    names = list_cases()
    if not names:
        print(f"（暂无用例，请在 {CASES_DIR} 下新增 .yaml）")
        return 0
    if yaml is None:
        print("未安装 PyYAML，仅列出文件名：")
    for n in names:
        if yaml is None:
            print(f"  - {n}")
            continue
        d = load_case(n)
        print(f"  - {n}: {d.get('name', '')} — {d.get('desc', '')}")
    return 0


def cmd_diff(args):
    """对比两次 run_summary.json 的 MakeSpan 与排程结果差异。"""

    def load(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)

    a, b = load(args.base), load(args.new)
    print(f"base={os.path.basename(args.base)}  new={os.path.basename(args.new)}")
    print(f"  MILP: {a.get('milp_status')}  ->  {b.get('milp_status')}")

    def span(s):
        ends = [r["end"] for r in s.get("schedule", []) if r.get("end")]
        return max(ends) if ends else "-"

    print(f"  最晚完工: {span(a)}  ->  {span(b)}")

    ma = {r["lot"]: r for r in a.get("schedule", [])}
    mb = {r["lot"]: r for r in b.get("schedule", [])}
    changed = [k for k in ma if k in mb and ma[k].get("start") != mb[k].get("start")]
    print(f"  开工时间变化的 Lot: {len(changed)} 个")
    for k in changed[: args.limit]:
        print(f"    {k}: {ma[k].get('start')} -> {mb[k].get('start')}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="python -m backend.solver",
        description="GTX FSO Litho 六步算法链命令行工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="运行六步算法链")
    r.add_argument("--case", default=None, help="scenario 用例名（见 cases 子命令）")
    r.add_argument("--out", default=None, help="输出目录，默认 backend/solver/output")
    r.add_argument("--json", action="store_true", help="额外打印完整 JSON 结果")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("cases", help="列出所有 scenario 用例")
    c.set_defaults(func=cmd_cases)

    d = sub.add_parser("diff", help="对比两次 run_summary.json")
    d.add_argument("base")
    d.add_argument("new")
    d.add_argument("--limit", type=int, default=10, help="最多打印几条明细")
    d.set_defaults(func=cmd_diff)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
