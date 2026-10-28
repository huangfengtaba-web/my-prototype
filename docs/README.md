<!-- GTX FSO Litho 原型 · README（交付物总索引） · v1 · 2026-10-24 定稿于 2026-10-25 · 对应设计书：全局 / 缺口对照表 v1 -->

# GTX FSO Litho · 交付物总索引

> 本目录为单文件离线 HTML 原型集：无外部依赖、无 CDN、无后端；中文界面、面包屑英文；mock 数据确定性可复现。
> 共享设计规范见 `_DESIGN_SPEC.md`（§2 布局骨架 / §3 设计 Token / §4 组件类名 / §5 mock 规范 / §6 页签清单 / §7 字段清单 / §8 质量红线）。
> 组件写法基准：`stacking_bond_ui_v6.html`、`equip_temp_layer_config.html`（只读参照，禁止修改）。

## 入口

**`index.html`（总览 Dashboard）** 是全原型的唯一导航入口：
- 顶部 4 KPI（在线机台 8 / 待排 Lot 120 / 在库 Reticle 156 / QTMS 超水位 3）；
- 系统功能架构 SVG（数据层 → 前处理 → 算法层 → 后处理 → 结果层 → 联动层）；
- 模块入口卡片 8 张（直达全部 6 个分区文件 + 2 个复用页）；
- 13 条 RFP 覆盖矩阵（可排序、可导出 CSV）；
- 交付物索引（相对路径，含 00_素材 / 01_PPT / 03_文档 链接）。
- 左侧边栏在每个分区文件中同样提供全量导航（当前分区高亮、其余折叠为链接；扩展页面组放 2 个复用页）。

## 文件清单（9 个文件 = 7 分区 + 2 复用）

| # | 文件 | 分区（面包屑第一段） | 页签清单 | 对应设计书章节 | 状态 |
|---|---|---|---|---|---|
| 1 | `index.html` | 总览（System Overview） | 总览 Dashboard（KPI / 架构图 / 模块入口 / RFP 矩阵 / 交付物索引） | RFP 汇总表 t:5/t:9/t:13；LITHO功能介绍 slide 2/5；缺口对照表 v1 | ✅ 已产出（B3 重派版校验通过） |
| 2 | `config_zone.html` | 数据配置（Model Control / Production Config） | Lot Control / Priority Config / Transport Config / Temperature Config(简版→链接详细版) / Bullet Lot / Fix Lot / Reticle Config / Process Config（8 页签） | 4.7.1 数据配置 Config | ✅ 已产出（旧进程并发版，B3 抽检头部规范通过） |
| 3 | `model_zone.html` | 模型管理（Model Control） | Eqp Group / Data Parameter / Schedule Model / Model Configuration（4 页签） | 4.7.2 模型管理（缺口 A1，P0） | ✅ 已产出（旧进程并发版，B3 抽检通过） |
| 4 | `result_litho.html` | 结果-Litho 排程（Scheduling Result） | 一级导航下 6 个二级页面（?page= 直达，每页甘特图+列表双视图）：Barc Schedule / Scanner Schedule（原 Chart+List 合并）/ Litho OverLap / Lot 加工流 / Wafer 加工时间 / 中间结果（六步溯源） | 2.7.1 Barc Schedule；4.7.3 Scanner Schedule；计划序号37 中间结果输出 | ✅ 已产出（2026-10-25 晚重构：排程结果一级导航+二级菜单页面） |
| 5 | `result_reticle.html` | 结果-Reticle 排程（Scheduling Result） | 2 个二级页面：Reticle Schedule（五态甘特+列表）/ Reticle Transport（搬送记录+SVG 路径+搬送作业甘特） | 4.7.3 Reticle Schedule / Reticle Transport | ✅ 已产出（2026-10-25 晚重构同上） |
| 6 | `log_zone.html` | 日志（System Log） | Scheduling Log / Error Management（2 页签） | 4.7.4 日志（缺口 A2，P0-2） | ✅ 已产出（B3 重派版校验通过） |
| 7 | `stacking_bond_ui_v6.html` | 复用页 · 扩展（Stacking Bond） | EQP Loading（30 天负载）+ Lot Stacking Bond（绑定推演） | 4.7.3 相关；RFP 2.1.5 / 2.2.1 界面载体 | ✅ 复用（组件写法基准之一，只读） |
| 8 | `equip_temp_layer_config.html` | 复用页 · 扩展（温层配置详细版） | Recipe-Eqp-Temperature 匹配 + Capability 转温成本时间 | 4.7.1 Temperature Config 详细版 | ✅ 复用（组件写法基准之一，只读） |
| 9 | `_DESIGN_SPEC.md` | 共享设计规范 | ——（非页面） | 全局规范 v1 | ✅ 只读规范文件 |

> 计数说明：规范 §6 标题口径为「7 文件 + 2 复用」，其中分区 HTML 实际为 index + 5 分区共 6 个；本 README 按「7 分区 = 6 分区 HTML + _DESIGN_SPEC.md」凑齐 9 个文件口径列出。

## 复用页角色

- `stacking_bond_ui_v6.html`：同时承担两个角色——① 被导航「扩展页面」组直接访问的业务页（EQP Loading / Lot Stacking Bond）；② 全原型的**组件写法基准**（卡片 / 页签 / 表格 / 甘特 / tooltip / 评论模式 .q[data-cm] 等）。
- `equip_temp_layer_config.html`：① config_zone 中「Temperature Config(简版)」页签的两个入口卡链接到本详细版；② 评论模式 tip()/bindTips 的第二写法参照（原型统一采用 v6 的 .q[data-cm] 模式）。

## 日志区与模型管理的命名一致性（B3 校验项）

`log_zone.html` 两个页签中的 **Model Name 与 `model_zone.html`「Schedule Model」页签 mock 命名完全一致**：`Litho_Main` / `Litho_BARC_Rel` / `Etch_A_V1`；Scheduling Log 的 Error/Abnormal 行「View Error」会切换至 Error Management 并带入 Model Name / Create Time(=End Time) / Error Type 查询条件。

## 配套文档（../03_文档/，index.html 交付物索引链接均已生效）

| 文件 | 内容 |
|---|---|
| `01_算法说明.md` | 六步算法链（预处理→Reticle预组批MILP→Lot细排程→后处理→BARC反推→光罩状态推演）+ 优先级体系 |
| `02_数据流转.md` | 客户侧→SOURCE_*→算法层→结果与 SDR/QTMS/MES 联动全链路 |
| `03_页面流转.md` | 站点地图、各分区页签流转、主用户路径（场景串联）、缺口占位说明 |
| `04_数据库设计.md` | 25 张表（设计书 17 + 隐含补齐 5 + 缺口新增 3）、页面↔表映射、D8 接口占位 |
| `05_API接口设计.md` | 页面操作接口全覆盖 + SDR 两方案/QTMS/MES 联动（正式协议待 D8） |

## 培训交付物（../01_PPT/）
`光罩状态推演_培训_v1.pptx`（8 页，讲稿入备注）+ 同名 PDF + `render/slide_01~08.png` 逐页渲染图。

## 历史校验记录
- index.html / log_zone.html：B3 重派版按 _DESIGN_SPEC a-i 校验项逐条通过（2026-10-24）。
- config_zone.html / model_zone.html：B1 逐条校验 + 修复（Process Config key 错位、Auto Run 三元语法错误、tip 误入 select；补 data-sort 排序与空态）（2026-10-24）。
- result_litho.html / result_reticle.html：B2 主线程直修（补 Scanner hover Stage、Reticle hover ProductId/StepSeq/Recipe、修 CSV 导出列错位、补 4 张表 data-sort）（2026-10-24）。

---
*本 README 由 B3 任务创建，随 D 任务（文档交付）于 2026-10-25 定稿。*
