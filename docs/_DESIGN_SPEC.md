# GTX FSO Litho 原型 · 共享设计规范 v1（所有分区 HTML 必须遵守）

> 目标：多个分区文件视觉与交互完全一致，看起来像一个系统。
> 基准：`stacking_bond_ui_v6.html` 与 `equip_temp_layer_config.html`（已随交付复制，可直接打开对照）。

## 1. 技术形态
- 单文件离线 HTML（无外部依赖、无 CDN、无后端）；内联 CSS + 原生 JS；数据为文件内 mock（确定性，勿用 Math.random，用种子伪随机或硬编码）。
- 中文界面，面包屑英文（与设计书一致）。

## 2. 布局骨架（每个分区文件统一）
```
.app{display:flex;height:100vh}
  .sider 左侧导航 208px（logo: Pxsemi FSO / 智能生产中心 · 光刻排程 + 分组菜单，当前分区高亮，含跨文件链接）
  .main → .header(48px 面包屑 Model Control / Production Config / <页面名> + 右侧时钟 + 💬评论模式按钮)
        → .content（页签 tabs + 卡片内容）
```
- 面包屑第一段按分区：数据配置=Model Control / Production Config；模型管理=Model Control；结果展示=Scheduling Result；日志=System Log。
- 侧边栏菜单必须包含全部 6 个文件的导航（当前文件页面展开、其他折叠为链接）：index(总览)、数据配置、模型管理、结果-Litho排程、结果-Reticle排程、日志；复用页（Stacking Bond、Temperature Config 详细版）放"扩展页面"组。

## 3. 设计 Token（CSS 变量，逐字复制）
```css
:root{
  --colorPrimary:#1677FF; --colorPrimaryHover:#4096FF; --colorPrimaryActive:#0958D9;
  --colorSuccess:#52C41A; --colorWarning:#FAAD14; --colorError:#FF4D4F;
  --colorText:rgba(0,0,0,.88); --colorTextSecondary:rgba(0,0,0,.65);
  --colorTextTertiary:rgba(0,0,0,.45); --colorTextQuaternary:rgba(0,0,0,.25);
  --bgContainer:#fff; --bgLayout:#F5F5F5;
  --colorBorder:#D9D9D9; --colorBorderSecondary:#F0F0F0; --colorSplit:rgba(5,5,5,.06);
  --primaryBg:#E6F4FF; --primaryBorder:#91CAFF;
  --successBg:#F6FFED; --successBorder:#B7EB7F;
  --warningBg:#FFFBE6; --warningBorder:#FFE58F;
  --errorBg:#FFF2F0; --errorBorder:#FFCCC7;
  --radiusSM:4px; --radius:6px; --radiusLG:8px;
  --siderW:208px; --headerH:48px;
  --shadow3:0 1px 2px 0 rgba(0,0,0,.03),0 1px 6px -1px rgba(0,0,0,.02),0 2px 4px 0 rgba(0,0,0,.02);
  --shadow:0 6px 16px 0 rgba(0,0,0,.08),0 3px 6px -4px rgba(0,0,0,.12),0 9px 28px 8px rgba(0,0,0,.05);
  --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Noto Sans',sans-serif;
}
```
- Reticle 五态色（甘特/图例统一）：Process #2D6CDF / Inspection #F5921B / StarLight #8B5CF6 / Stocker #9CA3AF / Transport #10B981。
- Stacking 四态色：已绑定 #F2BA02 / 待决策 #F0B95A / 本次决策 #4874CB / Free #C9CFD8（斜纹）。

## 4. 组件约定（类名与行为照抄基准文件）
- `.card .card-h .t .sub .right`、`.tabs .tab .cnt .on`、`.btn(.primary/.sm/.link)`、`.inp`、`.field .lab`、
  `.tag(.success/.processing/.warning/.error/.default)`、`.pill`、`table.tbl / table.dt`（th 底 #FAFAFA、hover 行 #FAFAFA）、
  `.toolbar .sp`、`.kpis .kpi`、`.legend .li i`、`.empty`、`.overlay .modal(-h/-b/-f)`、`.toast`、`.note`、`.hint`、`.err`。
- 甘特：`.ruler .rc .wk`（周刻度底 #F0F5FF）、`.grow .gh .gt`、`.seg`（绝对定位色块，宽度=时长×px/单位）、`.scrollx`。
- 通用交互：tooltip 用 `data-tip` + `#tt` 浮层（照抄 v6 的 mouseover 委托）；评论模式 `?` 徽章 + `.bubble` 气泡（照抄 equip_temp_layer_config 的 tip()/bindTips 模式或 v6 的 .q 模式，统一用 v6 的 `.q[data-cm]` 写法）；CSV 导出 `toCSV/dl` 函数（含 BOM \ufeff）。
- 表格列头可排序（`data-sort` 三角指示）、筛选栏 `.fbar`、分页（>8 行时分页或 .tscroll 滚动，二选一统一用 .tscroll）。

## 5. mock 数据规范
- 机台：IMM01~IMM08（Immersion）、BARC01~06、IRIS01~02（独立检测）、STK01~03（Stocker）。
- Lot：`LOT-A01` 格式，25 片/批；产品 5001A/5002A/3006A；Recipe `RCP_XXX`。
- Reticle：`RT-0001` 格式；时间统一 `2026-10-24 HH:MM`。
- 同一故事线贯穿结果区：急货 LOT-A01（10:00 加工、RT-0101 需外部 IRIS 20min→搬送10min→装载5min→09:45 就绪）。
- 每页数据量：表格 8~15 行，甘特 4~6 行机台 × 24h 窗口。

## 6. 交付文件与页面清单（8 文件 + 2 复用；排程结果区为一级导航 + 二级菜单页面，每页甘特图+列表双视图；2026-10-25 增 data_zone 4 页签 / Run Trace / 计划 vs 实际）
| 文件 | 页面 |
|---|---|
| index.html | 总览：系统功能架构图（HTML/SVG）、模块入口卡片（6 文件导航）、13 条 RFP 覆盖矩阵表、交付物索引 |
| config_zone.html | Lot Control / Priority Config / Transport Config / Temperature Config(简版，链接详细版) / Bullet Lot / Fix Lot / Reticle Config / Process Config / 算法开关(需求38：约束开关+目标权重+降级策略) |
| model_zone.html | Eqp Group / Data Parameter / Schedule Model（列表+编辑+Model Configuration 子页弹窗或页签） |
| result_litho.html | 二级页面（URL ?page= 直达）：barc=Barc Schedule（放货窗口甘特+列表）/ scan=Scanner Schedule（三态甘特+列表，原 Chart/List 合并）/ overlap=Litho OverLap（重叠示意甘特+列表）/ flow=Lot 加工流（流程带+各站时间甘特）/ wafer=Wafer 加工时间（WPH 示意甘特+列表占位）/ mid=中间结果（六步产物表+溯源+执行时间线甘特） |
| result_reticle.html | 二级页面：rsch=Reticle Schedule（五态甘特+列表，原 Chart/List 合并）/ trans=Reticle Transport（搬送记录列表+SVG 路径+搬送作业甘特） |
| log_zone.html | Scheduling Log / Error Management |
| 复用 | stacking_bond_ui_v6.html（EQP Loading + Lot Stacking Bond）、equip_temp_layer_config.html（温层配置详细版） |

## 7. 各页字段要求（依据设计说明书，必须逐字段实现）
- **Barc Schedule**：LotId/BatchId/ProductId/Recipe/Step Seq/Is Release/Earliest Release/Latest Release/Litho Eqp/Litho Capability/Litho Start/Reason（2.7.1 t:8）
- **Scanner Schedule-Chart**：行=EQP；条=Lot（Running/Jobprepare/Scheduling 三态），Lot 条上方 Reticle 条（Trainsize hover）；Setup/Down 上方无 Reticle；hover 字段集 4.7.3（ReticleId/Trainsize/Process Lot/Start/End/CostTime；Lot: LotId/EqpId/ProductId/Stage/StepSeq/Recipe/ReticleId/WaferNum/Start/End/Status）；Key Lot Info 标签（Bullet/LotId/LotType/Reticle Name/Recipe）；Recipe Mode 开关（5 色循环，Recipe 取 @ 前段分组）；QTMS 超水位标记（红框/角标）；Eqp 详情弹窗（Lot 视角时间轴 Running/Jobprepare/Scheduling）
- **Scanner Schedule-List**：EqpId/Eqp Type/Eqp Status/Process Type/Recipe/ReticleId/LotId/ProductId/Step Seq/Start Time/End Time/Process Time + 筛选 + CSV
- **Litho OverLap**：占位页——表头 12 列待客户源表确认，做 3 列演示 + 醒目"源表缺口"警示卡
- **Lot 加工流**：选 Lot → 横向 step 流程带（当前站高亮、QTime 约束弧线、预计到达时间）
- **Wafer 加工时间**：占位页——空表 + "源表空白（缺口 C 级）"警示 + WPH 字段示意
- **中间结果**（2026-10-25 增，对应计划序号37 工程化-中间结果输出/需求37）：运行批次选择器（Litho_Main V1.3 · RUN-*）+ 六步切换（预处理/Reticle预组批 MILP/Lot细排程 chunk≤50/后处理/BARC 反推/光罩状态推演）+ 各步过程产物表（急货故事线 LOT-A01/RT-0101 贯穿）+ 当前步骤 CSV 导出 + 产物→数据库表对照提示（04_数据库设计 §5）
- **Reticle Schedule-Chart**：行=Reticle；五态色块；hover：LotId/EqpId/ProductId/StepSeq/Recipe/ReticleId/Start/End/CostTime/Status(Process|Inspection|StarLight|Stocker|Transport)/Location
- **Reticle Schedule-List**：ReticleId/Status/LotId/ProductId/Step Seq/Recipe/EqpId/Eqp Group/Start Time/End Time/Cost Time
- **Reticle Transport**：搬送记录表（ReticleId/当前位置/目的地/Job Type(清洗/IRIS/StarLight/N2 Purge/Load/Unload)/原因/优先级/Pod/预计使用时间/关联LotEqpId）+ 当日路径示意（SVG 节点图）
- **Scheduling Log**：Model Name/Version/Model Type/Status(Error|Abnormal|Success)/Error Type/Start/End；筛选（Model Name 多选、Model Type、End Time 90 天、Status 多选）；Error/Abnormal 行"View Error"跳 Error Management（带查询条件）
- **Error Management**：Model Name/Version/Model Type/Create Time/Error Type(DATA_ERROR|UNKNOWN_ERROR|MODEL_ERROR)/Error Info/Detail；Create Time 逆序
- **Lot Control**：Lot Type 复选（PI/PB/PC/PE/PR/EF/ES/TF/BK/PA）、Priority 单选+Internal Priority 多选（1-9）；History 入口说明
- **Priority Config**：Priority→Classify(Bullet|Normal) 映射表（含 Normal Bullet/Super Bullet）
- **Transport Config**：Eqp-Stocker-Maskroom 矩阵 + Lot-Eqp 搬送耗时（两位小数 0.01-999）
- **Temperature Config(简版)**：两入口卡（Recipe-Eqp-Temperature / Capability-Temperature Change Cost Time）→ 链接 equip_temp_layer_config.html
- **Bullet Lot**：BULLET_CONFIG(NormalBullet/SuperBullet)/NORMAL_BULLET_MAX_WAIT_TIME/SUPER_BULLET_ADVANCE_RESERVE_TIME
- **Fix Lot**：Capability 筛选（默认第一项、仅 Litho）→ 机台固定数量表（0-99 步长 1）
- **Reticle Config**：RETICLE_TRANS_COST_TIME(单值)/CLEAN_COST_TIME/IRIS_COST_TIME(机组+机台+时间)/OFFLINE_IRIS_COST_TIME(机台+时间)/STARLIGHT_COST_TIME/RETICLE_LOAD_COST_TIME/RETICLE_UNLOAD_COST_TIME/RETICLE_ADVANCE_NOTIFY_TIME/RETICLE_LIBRARY_SIZE(机组+机台+水位)；通配符 *、% 支持；重复校验 FSO_dataExist 提示
- **Process Config**：SUM_LOT_QTY/SUM_WAFER_COUNT/MIN_LOT_QTY/MIN_LOT_WAFER_COUNT（正整数 1-999）
- **Eqp Group**：列表(Eqp Group Name/Model/Eqp Type/Running Mode/Area/KPI View/Schedule Model)+新增弹窗（唯一性：Area+Eqp Type+Running Mode；Litho 区 Running Mode 置灰）+编辑/删除（被 Model 占用不可改/删，提示语照设计书）+查询
- **Data Parameter**：列表(Model Type/Set/Item/Type/Status/Scope/M/O/Variable/Description/Model)+新增（Scheduling 显示 Set/Type/Scope，Planning 隐藏）+被占用不可改删
- **Schedule Model**：列表(Model Name/Model/Eqp Group Name/Status/Auto Run/Schedule Type/Execution)+编辑(Auto Run 校验、同 Eqp Group 仅一个 on：This Eqp Group has already running a Model.)+Run 单次执行（Running 禁用：This Model is running）+配置入口→Model Configuration（Basic Info/Model Selection：Diffusion/Etch/Litho/Reticle Inspection/Wet/Data Selection：Eqp Group+Data Parameter 变量配置/Config）
- **index 总览**：顶部 4 KPI（机台 8 台/Lot 待排 120/Reticle 156/超水位 3）；功能架构 SVG（数据层→前处理→算法层→后处理→结果层→联动 SDR/QTMS）；模块入口卡 8 张（含 2 复用）；RFP 覆盖矩阵（13 条 RFP → 页面/状态 ✅🟡）

## 8. 质量红线
- 每个文件 ≤ 3500 行；无外部请求；`<!doctype html>` + `<meta charset="utf-8">`；文件顶部 HTML 注释写明"GTX FSO Litho 原型 · 分区名 · v1 · 2026-10-24 · 对应设计书章节号"。
- 所有按钮有行为（至少 toast 提示）；空态有 `.empty`；表格有 hover；关键字段有评论模式 `?` 说明。
- 跨文件导航用相对路径 `<a href="xxx.html">`。
