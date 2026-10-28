# 01 · Git 工作流：拉代码 / 推代码 / 分支策略

> 适用：Windows + Git Bash。工程根 `D:\codex\2026-10-28-23-35-39`
> 目标：把三个来源合成**一个** GitHub 仓库 `gtx-fso-litho`，并保持可增量同步。

---

## 0. 前置检查

```bash
git --version                    # 需 >= 2.30（subtree 稳定）
git config --global user.name
git config --global user.email
```

若未配置：

```bash
git config --global user.name "huangfengtaba"
git config --global user.email "你的邮箱@example.com"
```

### 网络（本机特有，重要）

本机 **直连 GitHub / PyPI 会失败**，需走代理 `http://127.0.0.1:10808`：

```bash
# 全局设置一次（推荐，之后不用每条命令带）
git config --global http.proxy  http://127.0.0.1:10808
git config --global https.proxy http://127.0.0.1:10808

# 取消代理（换网络环境时）
git config --global --unset http.proxy
git config --global --unset https.proxy
```

> 如果代理不通，先确认代理软件在运行。**不要**因为连不上就改用别的方式绕，先排查代理。

---

## 1. 在 GitHub 建空仓库

1. 打开 <https://github.com/new>
2. Repository name：`gtx-fso-litho`
3. **不要**勾选 Add a README / .gitignore / license（保持完全空仓库）
4. 记下地址：`https://github.com/huangfengtaba-web/gtx-fso-litho.git`

> 若提示需要认证：GitHub 已不支持密码，需 Personal Access Token。
> 生成路径：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
> 勾选 `repo` 权限。推送时用户名填 GitHub 账号，**密码填 token**。

---

## 2. 本地初始化

```bash
cd /d/codex/2026-10-28-23-35-39
git init
git branch -M main
git remote add origin https://github.com/huangfengtaba-web/gtx-fso-litho.git
```

验证：

```bash
git remote -v
# origin  https://github.com/huangfengtaba-web/gtx-fso-litho.git (fetch)
# origin  https://github.com/huangfengtaba-web/gtx-fso-litho.git (push)
```

---

## 3. 拉取资产 B：my-prototype（Vite 骨架）

**目的**：拿它的 `package.json` / `vite.config.js` 作为前端工程起点，两页原型并入 `frontend/`。

```bash
cd /d/codex/2026-10-28-23-35-39

# 加为第二个远端（不影响 origin）
git remote add upstream-mp https://github.com/huangfengtaba-web/my-prototype.git
git fetch upstream-mp

# 合并不相关历史（两个仓库无共同祖先，必须加 --allow-unrelated-histories）
git merge --allow-unrelated-histories upstream-mp/main -m "chore: 合并 my-prototype 前端骨架"
```

**处理冲突**：合并后 `frontend/` 下会同时出现 my-prototype 的 2 页与已迁入的 9 页。
保留策略：

| 文件 | 处理 |
|---|---|
| `temp-layer-config.html` | 与 `equip_temp_layer_config.html` 同源，**保留后者**，删前者 |
| `stacking-bond.html` | 与 `stacking_bond_ui_v6.html` 同源，**保留后者**，删前者 |
| `package.json` / `vite.config.js` | **保留 my-prototype 的**，作为前端工程起点 |
| 其余 9 页 | 保留已迁入版本 |

清理：

```bash
git rm frontend/temp-layer-config.html frontend/stacking-bond.html
git commit -m "chore: 去重 my-prototype 与交付物重复页面"
```

---

## 4. 拉取资产 C：SemiconFab（subtree）

**为什么用 subtree 而不是 submodule**：
- submodule 克隆后需要额外 `git submodule update`，接力 Agent 容易忘，导致 `vendor/` 是空目录
- subtree 把代码**真实写进**本仓库历史，任何人 clone 后直接可用
- 代价：后续同步上游需一条 subtree 命令（下面给出）

```bash
git remote add semiconfab https://github.com/jinjiefan2020/SemiconFab.git
git fetch semiconfab

# 拉入 vendor/semiconfab-fork/，--squash 压缩上游历史避免污染
git subtree add --prefix=vendor/semiconfab-fork semiconfab main --squash
```

### 验证 LICENSE 保留（合规硬性要求）

```bash
ls vendor/semiconfab-fork/LICENSE*
```

**必须存在**。若上游无 LICENSE 文件，手动在 `vendor/semiconfab-fork/LICENSE-NOTICE.md` 写明：

```markdown
# 第三方代码声明

本目录代码来自 https://github.com/jinjiefan2020/SemiconFab
License: PolyForm Noncommercial License 1.0.0（禁止商用）
引入方式: git subtree
引入日期: 2026-10-29
用途: 非商用的甲方演示

**若本项目转为商用，必须删除整个 vendor/ 目录。**
```

### 后续同步上游（可选）

```bash
git subtree pull --prefix=vendor/semiconfab-fork semiconfab main --squash
```

> 有本地改动时可能冲突。简单处理：先 `git checkout` 掉本地对 vendor 的修改再 pull。

---

## 5. 引入资产 A：本地交付物（复制，不走 git）

`D:\工作\嘉定GTX\GTX_FSO_交付物` **不是 git 仓库**，用文件复制引入。

```bash
SRC="D:/工作/嘉定GTX/GTX_FSO_交付物"

# ① 原型 9 页 → frontend/
cp "$SRC/02_原型/index.html" frontend/index.html
cp "$SRC/02_原型/"{config_zone,data_zone,equip_temp_layer_config,log_zone,model_zone,result_litho,result_reticle,stacking_bond_ui_v6}.html frontend/prototypes/

# ② 算法 → backend/solver/
cp "$SRC/04_算法demo/"{litho_solver,mock_data}.py backend/solver/

# ③ 设计文档 → docs/specs/
cp "$SRC/03_文档/"*.md docs/specs/
cp "$SRC/02_原型/_DESIGN_SPEC.md" docs/
```

> **坑**：`cp "目录/"a.html b.html`（引号在斜杠后结束）会导致后续文件找不到路径，
> 必须写成 `"目录/"{a,b}.html` 花括号展开形式。

**不入版本库的文件**（写进 `.gitignore`）：

```
01_PPT/            # build_ppt.py 含硬编码 D:/工作/... 绝对路径
tools/             # PPT 引擎，与本工程无关
*.pptx *.docx      # 大二进制
00_素材/           # 原始素材，需要时到交付物目录取
```

---

## 6. 首次提交与推送

```bash
cd /d/codex/2026-10-28-23-35-39
git add .
git status                       # 确认没有混入 output/ node_modules/ .venv/

git commit -m "feat: 融合 SemiconFab + GTX 原型 + litho_solver 为 monorepo

- frontend/: 9 页 Litho 原型（Vite 多页）
- backend/solver/: 六步 MILP 算法链（PuLP+CBC）
- vendor/semiconfab-fork/: SemiconFab（PolyForm 非商用，subtree 引入）
- docs/specs/: 8 份设计文档"

git push -u origin main
```

---

## 7. 日常推送

```bash
git status                       # 看改了什么
git add <具体文件>                # 不要用 git add . 盲加
git commit -m "类型: 简述"
git push
```

### Commit 类型前缀

| 前缀 | 用途 |
|---|---|
| `feat:` | 新功能 |
| `fix:` | 修 bug |
| `docs:` | 只改文档 |
| `refactor:` | 重构，无功能变化 |
| `chore:` | 依赖、配置、杂项 |

---

## 8. 分支策略

```
main        ← 保护分支，只接受 PR，始终保持可部署
  └── feat/xxx    功能分支，从 main 切出
  └── fix/xxx     修复分支
```

**Zcode 初版建议开独立分支**，避免半成品污染 main：

```bash
git checkout -b feat/zcode-mvp
# ... 开发 ...
git push -u origin feat/zcode-mvp
# 验收通过后合并
git checkout main
git merge feat/zcode-mvp
git push
```

---

## 9. 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `fatal: unable to access ... Failed to connect` | 没走代理 | 见 §0 设置 `http.proxy` |
| `fatal: refusing to merge unrelated histories` | 合并 my-prototype 时缺参数 | 加 `--allow-unrelated-histories` |
| `cp: cannot stat 'xxx.html'` | 引号边界错误 | 改用 `"目录/"{a,b}.html` 花括号 |
| subtree 报 `Working tree has modifications` | 有未提交改动 | 先 `git commit` 或 `git stash` |
| push 报 403 | 用了密码而非 token | 密码栏填 Personal Access Token |
| `vendor/` 空目录 | 用了 submodule 且未 update | 本项目用 subtree，不应出现；若出现说明步骤 4 失败 |

---

## 10. 命令速查

```bash
git remote -v                                    # 看远端
git log --oneline --graph -20                    # 看历史图
git subtree pull --prefix=vendor/semiconfab-fork semiconfab main --squash   # 同步 SemiconFab
git fetch upstream-mp && git merge upstream-mp/main                          # 同步 my-prototype
git checkout -b feat/xxx                         # 开分支
git stash / git stash pop                        # 暂存/恢复
```
