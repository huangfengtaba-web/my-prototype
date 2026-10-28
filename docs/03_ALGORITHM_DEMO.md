# 03 · 算法 Demo 打开与测试方案

> 回答：**用什么打开、怎么跑、怎么调参、怎么断点、怎么验证结果对不对。**

---

## 1. 方案选型：为什么用 VSCode

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| **VSCode + venv** | 轻量、断点调试完整、Tasks 一键跑、与前端同窗口 | 需配一次 launch.json | ✅ **推荐** |
| PyCharm | Python 调试最强，开箱即用 | 重（1G+ 内存）、前端支持弱 | 备选 |
| Jupyter Notebook | 分步执行，适合讲解算法 | 断点调试弱、与 FastAPI 联调麻烦 | 适合演示，不适合开发 |
| 纯命令行 | 零配置 | 无法断点、查变量靠 print | 只适合 CI |

**结论：VSCode + venv。**
理由：算法要**断点看中间变量**（比如 step2 里 `x[l,e]` 的决策值），又要跟前端联调，VSCode 一个窗口全搞定。

**不用本机 miniconda 全局 Python 直接跑**，因为要把依赖隔离在项目里避免污染全局；但如果你更习惯 conda，§3.2 给了 conda 方案。

---

## 2. 第一次打开（10 分钟，只做一次）

### 步骤 1：用 VSCode 打开工程根

```
VSCode → File → Open Folder → 选择 D:\codex\2026-10-28-23-35-39
```

⚠️ **注意**：打开的是**工程根目录**，不是 `backend/solver/`。
原因：`python -m backend.solver` 需要以仓库根为工作目录才能正确导入包。

### 步骤 2：安装 VSCode 扩展

- **Python**（Microsoft，必装）
- **Pylance**（随 Python 扩展装）
- 可选：Chinese (Simplified) 中文语言包

### 步骤 3：创建虚拟环境

`Ctrl+Shift+P` → 输入 `Tasks: Run Task` → 选 `venv:create`

等价命令行（Tasks 没配好时用）：

```bash
cd /d/codex/2026-10-28-23-35-39
python -m venv .venv
```

激活（二选一）：

```bash
# Git Bash
source .venv/Scripts/activate

# PowerShell
.venv\Scripts\Activate.ps1
# 若报禁止运行脚本：
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 步骤 4：选解释器

`Ctrl+Shift+P` → `Python: Select Interpreter` → 选 `./.venv/Scripts/python.exe`

### 步骤 5：装依赖

`Ctrl+Shift+P` → `Tasks: Run Task` → `install:pip`

等价命令行：

```bash
pip install -r backend/requirements.txt

# 若直连超时，用清华源
pip install -r backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 若需要代理
pip install -r backend/requirements.txt --proxy http://127.0.0.1:10808
```

**装完验证**：

```bash
python -c "import pulp; print('pulp', pulp.__version__)"
python -c "import fastapi, uvicorn, yaml; print('backend deps OK')"
```

---

## 3. 跑起来

### 3.1 最简：直接跑六步算法

```bash
cd /d/codex/2026-10-28-23-35-39
python -m backend.solver run
```

**预期输出**：

```
=== GTX FSO Litho 六步算法链 Demo · Litho-FSO v0.1 · BATCH-20251023 ===
[1/6] ① 预处理                        完成     0.00s  10 lots 打标+计时
[2/6] ② Reticle 预组批 MILP           Optimal  0.16s  挂载 5 次, MakeSpan=76min
[3/6] ③ Lot 细排程 MILP               Optimal  0.07s  MakeSpan=11:10
[4/6] ④ 后处理                        完成     0.00s  卡控 N 条, 跳过 M 条
[5/6] ⑤ BARC 反推                     完成     0.00s  10 行
[6/6] ⑥ 光罩五态推演                  完成     0.00s  RT-0101 就绪 09:45
--- 急货故事线自检 ---
  LOT-A01 上机时间: 10:00
  RT-0101 就绪时间: 09:45
  准备链: 09:10 IRIS 20min → 搬送 10min → 装载 5min = 35min
  LOT-A01 片数: 25
=== 完成：output\ 共 7 个文件 ===
```

**关键检查点**：
- ② ③ 必须是 `Optimal`（不是 `Infeasible` / `Undefined`）
- 急货 LOT-A01 上机 **10:00**
- RT-0101 就绪 **09:45**（= 09:10 + 20 + 10 + 5 = 35min 链路）

任一项不符 = 回归，见 §6 排查。

### 3.2 用 conda 环境（可选）

用本机已有的 miniconda Python 3.11：

```bash
"D:/software/miniconda/anzhuang/python.exe" -m backend.solver run
```

或建独立 conda 环境：

```bash
conda create -n gtx-litho python=3.11 -y
conda activate gtx-litho
pip install -r backend/requirements.txt
```

> 用 conda 时，VSCode 解释器要选 conda 环境路径，不是 `.venv`。

### 3.3 带参数跑

```bash
# 列出所有 scenario
python -m backend.solver cases

# 跑指定 scenario
python -m backend.solver run --case urgent-A01

# 输出完整 JSON（给前端/调试用）
python -m backend.solver run --json

# 指定输出目录
python -m backend.solver run --out ./my-output

# 对比两次结果
python -m backend.solver diff a/run_summary.json b/run_summary.json
```

---

## 4. 断点调试（核心用法）

### 4.1 启动调试

按 `F5` → 选 **`Python: litho_solver`** → 程序在断点处停下。

### 4.2 建议打的 5 个断点

| 位置 | 文件位置 | 看什么 |
|---|---|---|
| 建模完成 | step2 的 `prob.solve(solver)` 前 | Variables 面板展开 `prob`，看约束数量 |
| 求解结果 | step2 的 `assign = {}` 处 | `x[l,e]` 哪些取 1，即 Lot 分到哪台机 |
| 挂载判定 | step2 的 `mounts = [...]` 处 | 换罩次数，验证「同光罩尽量同机台」 |
| 细排程 | step3 的 `l["start"] = ...` 处 | 每个 Lot 开工时间，验证急货是否排最前 |
| 急货链路 | `main()` 里 `SUMMARY["story_check"]` 处 | LOT-A01 上机时间、RT-0101 就绪时间 |

### 4.3 调试时怎么查 MILP 变量

在 Debug Console 里输入：

```python
# 看某个 Lot 分到哪台机
[k for k, v in x.items() if v.value() > 0.5]

# 看目标函数值
pulp.value(prob.objective)

# 看 MakeSpan 变量
C.value()

# 看所有挂载
[(r, e) for (r, e), v in mnt.items() if v.value() > 0.5]
```

### 4.4 调试 FastAPI

`F5` → 选 **`Python: FastAPI`** → 服务起在 `http://127.0.0.1:8000`
在 `api.py` 的 `run_solve()` 里打断点，前端点按钮即可触发断点。

---

## 5. 调参：改 mock 数据验证算法行为

### 5.1 用 scenario（推荐，不污染原始 mock）

在 `tests/cases/` 建 YAML：

```yaml
# tests/cases/urgent-A01.yaml
name: 急货插单
desc: LOT-A01 提为 PRI1 且带 SHR 标签，验证是否被优先排产
config:
  w_makespan: 1.5          # 提高 MakeSpan 权重，看排程如何变化
lots:
  LOT-A01:
    priority: 1
    tags: [SHR]
    qty: 25
reticles:
  RT-0101:
    iris_at: 550           # 光罩 IRIS 时间推迟（分钟）
```

跑：

```bash
python -m backend.solver run --case urgent-A01
```

**可用覆盖字段**：

| 区块 | 可覆盖字段 | 来源 |
|---|---|---|
| `config` | `w_changeover` `w_makespan` `time_limit_s` `temp_change_min` `release_gap_min` `iris_min` `transport_min` `load_min` `pri_flow_w` | `mock_data.CONFIG` |
| `lots` | `priority` `tags` `qty` `temp` `ready` `reticle` `remain_qt` `barc_qt` `pt` `qtms_over` | `mock_data.LOTS` |
| `reticles` | `status` `location` `need_iris` `iris_at` | `mock_data.RETICLES` |

### 5.2 四个建议建的 scenario

| 文件名 | 场景 | 验证目标 |
|---|---|---|
| `default.yaml` | 基线 | 与原始输出一致，作为回归基准 |
| `urgent-A01.yaml` | 急货插单 | PRI1 + SHR 是否排最前、是否不受放货间隔推移 |
| `reticle-delay.yaml` | 光罩延迟 | RT-0101 推迟后，依赖它的 Lot 是否顺延 |
| `temp-conflict.yaml` | 温层冲突 | 相邻 Lot 异温层时，`temp_change_min` 是否计入换温耗时 |

### 5.3 直接改 mock_data.py（快速试，但会污染基线）

改完跑一次看效果。改完记得 `git diff` 确认，不需要就回滚。

---

## 6. 结果验证与排查

### 6.1 看输出

```bash
ls backend/solver/output/
# step1_preprocess.csv  step2_reticle_grouping.csv  step3_schedule_result.csv
# step4_postprocess.csv  step5_barc_release.csv  step6_reticle_deduction.csv
# run_summary.json
```

CSV 是 `utf-8-sig` 编码，**Excel 双击直接打开不乱码**。

### 6.2 三项硬性自检

```bash
python -c "
import json
d = json.load(open('backend/solver/output/run_summary.json', encoding='utf-8'))
print('MILP:', d['milp_status'])
print('急货:', d['story_check'])
"
```

必须满足：

- [ ] `milp_status.step2 == "Optimal"`
- [ ] `milp_status.step3 == "Optimal"`
- [ ] LOT-A01 上机 `10:00`
- [ ] RT-0101 就绪 `09:45`

### 6.3 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'pulp'` | venv 没激活或没装依赖 | 激活 `.venv` 后重装 |
| `ModuleNotFoundError: No module named 'mock_data'` | import 没改成兼容模式 | 见 [`02_INTEGRATION_GUIDE.md` §2](02_INTEGRATION_GUIDE.md) |
| `ModuleNotFoundError: No module named 'backend'` | 工作目录不对 | `cd` 到仓库根再跑 |
| 求解状态 `Infeasible` | 约束互相矛盾（如 ready 晚于上界） | 检查 `mock_data` 的 `ready` 与 `CONFIG.time_limit_s` |
| 求解状态 `Undefined` | 超时 | 调大 `CONFIG["time_limit_s"]`，或减小问题规模 |
| 结果与原型页面数字不一致 | 原型是 mock 示意值，算法是严格计算 | **已知差异**，以算法为准 |
| 第二次调用结果变了 | 同进程状态污染 | 用 `/api/solve/run`（子进程隔离），不要循环调 `main()` |

---

## 7. 与前端联调

### 7.1 起后端

`Ctrl+Shift+P` → `Tasks: Run Task` → `run:api`

或：

```bash
cd /d/codex/2026-10-28-23-35-39
uvicorn backend.app.api:app --reload --port 8000
```

验证：

```bash
curl http://127.0.0.1:8000/api/health
# {"ok":true,"solver":"CBC"}
```

### 7.2 起前端

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### 7.3 联调路径

浏览器开 `http://localhost:5173/scheduling-test`：

1. 用例下拉选 `urgent-A01`
2. 点「运行求解」
3. 观察：Network 面板 `POST /api/solve/run` → 200，约 2s
4. 页面回填排程列表与甘特条

**若报 CORS 错误**：检查 `api.py` 的 `allow_origins` 是否包含 `http://localhost:5173`。

### 7.4 VSCode 同时调试前后端

- 窗口 A：工程根，`F5` 跑 `Python: FastAPI`（后端 :8000）
- 窗口 B：`cd frontend && npm run dev`（前端 :5173）

---

## 8. 给 AI Agent 的最小指令模板

需要别的 Agent 改算法时，把这段贴给它：

```
项目根：D:\codex\2026-10-28-23-35-39
算法主程序：backend\solver\litho_solver.py（六步 MILP，PuLP + CBC）
mock 数据：backend\solver\mock_data.py
跑测试：python -m backend.solver run
预期：step2/step3 = Optimal，LOT-A01 上机 10:00，RT-0101 就绪 09:45

改完必须跑上面命令验证这三项，任一不符视为回归。
不要改 docs/specs/ 下的设计文档。
```

---

## 9. 速查卡

```bash
# 环境
source .venv/Scripts/activate            # Git Bash
pip install -r backend/requirements.txt  # 装依赖

# 跑
python -m backend.solver run                      # 基线
python -m backend.solver cases                    # 看用例
python -m backend.solver run --case urgent-A01    # 跑用例
python -m backend.solver run --json               # 输出 JSON
python -m backend.solver diff a.json b.json       # 对比

# 服务
uvicorn backend.app.api:app --reload --port 8000  # 后端
cd frontend && npm run dev                        # 前端

# 验证
python -c "import json;d=json.load(open('backend/solver/output/run_summary.json',encoding='utf-8'));print(d['milp_status'],d['story_check'])"
```
