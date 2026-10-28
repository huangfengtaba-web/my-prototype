# GTX FSO Litho · API 接口设计 v1

> 范围：FSO 系统内部页面操作接口 + 对外联动接口（SDR/QTMS/MES/BAC）。
> 依据：设计书 §2/§3/§4/§6 + 《04_数据库设计.md》 + 原型 7 分区页面操作清单。
> 日期：2026-10-25（同日增补：排程结果区二级页面口径 + 中间结果溯源三接口）| **通用约定**：RESTful，JSON；Base `/api/v1`；统一响应 `{code, message, data}`（code=0 成功）；错误码沿用页面提示语（如 `FSO_dataExist`）；分页参数 `page/size`；时间格式 `yyyy-MM-dd HH:mm:ss`。
> ⚠ 对外联动报文设计书原文空白（缺口 **D8**），本章给出**最小字段集草案**，正式协议待需求方确认。

## 1. 数据配置（config_zone）

| 接口 | 方法 | 说明 | 关键参数/校验 |
|---|---|---|---|
| /lot-control | GET/PUT | Lot Type 复选 / Priority / Internal Priority 保存 | 数据源自基础数据表 |
| /priority-config | GET/POST/PUT/DELETE | Priority→Classify 映射 CRUD | Normal Bullet/Super Bullet 枚举 |
| /transport-config | GET/PUT | Eqp-Stocker-Maskroom 矩阵、Lot-Eqp 耗时 | 耗时钳位 0.01–999 两位小数 |
| /temp-config/recipe | GET/POST/PUT/DELETE | recipe_capability_temperature CRUD | EQP_ID/RECIPE_ID 支持通配 `*`/`%` |
| /temp-config/change | GET/POST/PUT/DELETE | capability_temperature_change CRUD | COST 单位秒 |
| /bullet-lot | GET/PUT | BULLET_CONFIG / NORMAL_BULLET_MAX_WAIT_TIME / SUPER_BULLET_ADVANCE_RESERVE_TIME | FSO_CFG_PARAM |
| /fix-lot | GET/PUT | Capability 筛选（仅 Litho）+ 机台固定数量 | 0–99 步长 1 |
| /reticle-config | GET/POST/PUT/DELETE | 9 参数 CRUD（TRANS/CLEAN/IRIS/OFFLINE_IRIS/STARLIGHT/LOAD/UNLOAD/ADVANCE_NOTIFY/LIBRARY_SIZE） | 通配符支持；重复提示 `FSO_dataExist` |
| /process-config | GET/PUT | SUM_LOT_QTY / SUM_WAFER_COUNT / MIN_LOT_QTY / MIN_LOT_WAFER_COUNT | 正整数 1–999 |
| /algo-switches | GET/PUT | 算法功能点开关（约束/组批 8 项）+ 目标权重（Σ=100 校验）+ 降级策略（FIFO/EDD/CR、timeLimit、chunk≤50） | 变更写入 CFG 版本（FSO_CFG_PARAM），支持 Run Trace 回放；2026-10-25 增（需求38） |

## 2. 模型管理（model_zone）

| 接口 | 方法 | 说明 | 关键校验 |
|---|---|---|---|
| /eqp-groups | GET/POST/PUT/DELETE | Eqp Group CRUD | 唯一性 Area+Eqp Type+Running Mode；Name 重复 `This Eqp Group Name is already exist`；Litho 区 Running Mode 置灰；被占用 `This Eqp Group is occupied by …` |
| /data-parameters | GET/POST/PUT/DELETE | Data Parameter CRUD | Item 唯一；Variable 仅字母+下划线 ≤5×20；占用禁改删 |
| /schedule-models | GET/POST/PUT/DELETE | Schedule Model CRUD | Name 唯一 `This Model Name already exists`；同 Eqp Group 仅一个 Auto Run=on `This Eqp Group has already running a Model.` |
| /schedule-models/{id}/run | POST | 单次执行 | Running 中禁用 `This Model is running` |
| /schedule-models/{id}/config | GET/PUT | Model Configuration（Model Selection / Data Selection / Config） | 未选 Model：`Please Select Model` |

## 3. 排程结果（result_litho / result_reticle）

> 2026-10-25 更新：排程结果区已重构为**一级导航 + 8 个二级菜单页面**（前端路由 `?page=`，非接口）；每页甘特图+列表**共用同一数据接口**，由前端双渲染，不另设视图接口。

| 二级页面 | 接口 | 方法 | 说明 |
|---|---|---|---|
| barc | /barc-schedule | GET | 放货清单 12 列（BARC_RELEASE_BATCH ⨝ FSO_SCHEDULE_RESULT）+ 窗口字段（ER/LR/Start）供甘特渲染；CSV 导出 |
| scan | /scanner-schedule/chart<br>/scanner-schedule/list | GET | 三态甘特（Reticle 条/QTMS 标记/Recipe Mode 分组）；12 列列表 + CSV（全字段） |
| overlap | /litho-overlap | GET | ⚠ C 级缺口占位（源表确认前返回演示列）+ 重叠窗口字段 |
| flow | /lot-flow/{lotId} | GET | Lot 加工流（SOURCE_PRODUCT_FLOW + REMAIN_QTIME）+ 各站起止时间（甘特同源） |
| wafer | /wafer-process-time | GET | ⚠ C 级缺口占位 + WPH 示意（甘特按 WPH 折算） |
| mid | /mid-results?batch= | GET | 六步过程产物（FSO_MID_STEP_RESULT，按 STEP_NO 分组）+ 六步执行时间线 |
| mid | /mid-results/{batch}/trace/{resultId} | GET | **单条溯源**：CHECK 状态与说明 + CALC_TEXT 计算过程 + TRACE_SRC 源字段清单 + DOWN_LINK 下游反查目标 |
| mid | /mid-results/{batch}/verify | GET | 六步与下游出参一致性自动校验汇总（6/6 PASS 明细） |
| rsch | /reticle-schedule/chart<br>/reticle-schedule/list | GET | 五态甘特（hover 11 字段）；11 列列表 + CSV |
| trans | /reticle-transports | GET/POST | 搬送记录（含搬送作业时间供甘特）+ **下发 SDR** |

## 4. 日志（log_zone）

| 接口 | 方法 | 说明 | 筛选 |
|---|---|---|---|
| /scheduling-logs | GET | 调度日志 | Model Name 多选 / Model Type / End Time ≤90 天（含边界）/ Status 多选 |
| /errors | GET | Error Management | Create Time 必选（逆序）/ Error Type / Model Name / Model Type |
| /errors/{id} | GET | Detail 弹窗详情 | — |

## 5. 对外联动接口（⚠ 缺口 D8：最小字段集草案）

### 5.1 FSO → SDR（Reticle 搬送指令下发）
- 方案一：`POST /sdr/transport-plan` `{timeWindow:[T1,T2], reticleList:[{reticleId, fromLocation, toLocation, jobType}]}` —— SDR 自行定时刻。
- 方案二：`POST /sdr/transport-order` `{orderId, reticleId, fromLocation, toLocation, jobType(Clean|IRIS|StarLight|N2 Purge|Load|Unload|Move), priority(Super|High|Normal|Low), expectUseTime, podId, lotId?, eqpId?}` —— 提前 1~3h 定时即搬。
- 回执：`POST /api/v1/sdr/callback` `{orderId, status(已执行|失败), actualTime}`。
- 数据落 `FSO_RETICLE_TRANSPORT_CMD`（send_status 追踪）。

### 5.2 FSO → QTMS（水位标记）
`GET /qtms/loop-wip?product=&plan=` → `TARGET_WIP/ACTUAL_WIP/REMAIN_WIP/RESERVED_WIP`（FSO_LOOP_TARGET_WIP）；超水位时前端红框标记（数据同源，不单独推送；是否主动推送待 D8 确认）。

### 5.3 FSO ↔ MES/BAC
- 出站：`BARC_RELEASE_BATCH` 批次结果（BATCH_ID/LOT_ID/EARLIEST_RELEASE/LATEST_RELEASE/ERROR_MESSAGE）→ BAC 下货顺序调整（RFP 2.1.1~2.1.3）。
- 入站：SOURCE_* 同步接口（Lot/Flow/QTime/Eqp/Reticle Status/LOTHIST），增量方式（时间戳/CDC）待 D8 确认。

### 5.4 数据接入接口组（2026-10-25 增：data_zone 4 页签；底层连接载体仍待客户环境确认）
| 接口 | 方法 | 说明 |
|---|---|---|
| /integration/sources | GET | 数据源列表：SRC_ID/PROTO/SYNC_FREQ/CONN_STATUS/LATENCY/LAST_OK_TIME（页签①） |
| /integration/sources/{id}/ping | POST | 连通性测试 / 重连 |
| /integration/tasks | GET | 同步任务列表：TBL_NAME/SYNC_MODE/WATER_FIELD/WATER_VALUE/DELTA_ROWS/RETRY/LAST_STATUS（页签②） |
| /integration/tasks/{tbl}/run | POST | 手动触发增量/全量同步（入队返回批次号） |
| /integration/tasks/{tbl}/logs | GET | 任务同步日志（水位/耗时/重试/校验和） |
| /integration/mappings?ver= | GET | 字段映射清单（版本化 MAP-LOT/MAP-RTS…）（页签③） |
| /integration/mappings | PUT | 生成新映射草稿版本（不即时生效，随全量刷新切换） |
| /integration/reconciliation | GET/POST | 对账批次查询 / 立即对账（WIP 当站、在库 Reticle、QTime 行数、Eqp 状态）（页签④） |
| /integration/quarantine | GET | 隔离区清单（QUAR_ID/TBL/ROW_KEY/HIT_RULE/DISPOSE_STATUS） |
| /integration/quarantine/{id}/refix | POST | 修复重导（成功后状态 CLOSED，写 FSO_DQ_AUDIT） |
| /integration/quarantine/{id}/exempt | POST | 豁免入正式表（写审计，需高权限） |

### 5.5 溯源闭环接口组（2026-10-25 增：Run Trace + 计划 vs 实际）
| 接口 | 方法 | 说明 |
|---|---|---|
| /runs?date=&model=&status= | GET | 运行列表（Scheduling Log 的 RUN_ID 联动来源） |
| /runs/{runId}/trace | GET | 四级版本链：RUN → SNAP_ID（含对账批次 RC-*）+ CFG_VER + ALGO_VER → RESULT_VER，含与上轮 diff |
| /runs/{runId}/audit | GET | 决策审计：Lot→机台 reason_code + 评分因子 + 约束命中（FSO_DECISION_AUDIT） |
| /runs/{runId}/replay | POST | 重放对比：同 SNAP+CFG+ALGO 重算，输出与原结果一致率（算法未变证明） |
| /snapshots/{snapId} | GET | 快照内容、行数与对账批次引用（数据水位证明） |
| /actuals?resultVer=&date= | GET | 计划 vs 实绩：PLAN/ACT 起止、DEV_START/END、ACC_STATUS、QTIME_VIOLATION（FSO_PLAN_ACTUAL） |
| /actuals/calibration | POST | 偏差超阈值生成校准建议（WPH/搬送耗时/温层代价），审批后下轮排程生效 |

> 与 §5.1–5.3 的关系：SDR/QTMS/MES 出站接口不变；MES 入站从「协议待 D8」升级为本组接口（同步触发/水位/对账/隔离处置），**D8 残留项仅剩底层抓取载体（DB Link / Kafka / CDC）与认证方式由客户环境决定**。

## 6. 验收对照（HANDOFF §5）
- ✅ 覆盖全部页面操作（7 分区 + 排程结果区 8 个二级页面，所有按钮/表单/筛选/导出/溯源均有对应接口；甘特+列表共用数据接口双渲染）。
- ✅ SDR 两方案 + QTMS 水位 + MES/BAC 出入站覆盖（报文正式化待 D8）。
- ✅ 中间结果溯源闭环：/mid-results 三接口（产物/单条溯源/一致性校验）对应 FSO_MID_* 三表（04_数据库设计 §4.8）。
- ✅ 溯源闭环全量（2026-10-25 增）：/runs/{id}/trace+audit+replay、/snapshots、/actuals+calibration 对应 FSO_RUN_SNAPSHOT / FSO_DECISION_AUDIT / FSO_PLAN_ACTUAL（04 §4.10）——任意结果条目可反查"用了哪批数据（对账批次）、哪个配置、哪个算法版本、为什么这样排（决策审计）、实际做得如何（偏差闭环）"。
- ✅ 数据接入闭环（2026-10-25 增）：/integration/* 11 接口对应 data_zone 4 页签与 FSO_SYNC_SOURCE / FSO_SYNC_TASK / FSO_FIELD_MAPPING / FSO_DATA_QUARANTINE（04 §4.9）——同步监控、字段映射、对账与隔离处置全部有 API 载体。
- ✅ 与 04_数据库设计.md 表名互相引用一致。
