/* ============================================================
   1. 配置与状态
   ============================================================ */
const CFG = { ct: 2, days: 120, nLots: 16, seed: 20261015, incFree: false };
const EQPS = ["E1", "E2", "E3", "E4", "E5", "E6"];
const PRODS = ["5002A", "5001A", "3006A"];
const FLOWS = ["AA", "POLY", "METAL", "VIA"];      // v4：段级 Flow（光刻层流程组，演示口径）
const STAGE_OF = { "E1": "FE", "E2": "FE", "E3": "ME", "E4": "ME", "E5": "BE", "E6": "BE" }; // v4：候选池层深 → Stage
const ST = {
  bound:   { n: "已绑定", c: "bound", pill: "bound" },
  pending: { n: "待决策", c: "pending", pill: "pending" },
  dec:     { n: "本次决策", c: "dec", pill: "dec" },
  free:    { n: "Free Layer", c: "free", pill: "free" }
};
const CW = 26;                     // 每日列宽 px
const HEAD_W = 150;                // 行头宽 px

const UI = {
  tab: "eqp",                        // v5：eqp | lot | detail（机台详情为新标签页）
  detailEqp: null,                   // v5：打开详情标签页的机台
  win: "all",                      // all | 1 | 2 | 3 | 4
  dayFrom: 1, dayTo: 0,            // V2.0：时间筛选（起止天，1-based；dayTo=0 表示到 DAYS）
  eqpQ: "", lotQ: "",
  gFilter: "",                     // Group 序号筛选，如 "10-15" / "10,11"
  eqpFilter: "all", stFilter: "all",
  eqpSort: { k: "eqp", dir: 1 },
  lotSort: { k: "id", dir: 1 },
  view: "matrix",                   // v5：eqp 页签内视图切换 matrix | cmp | load | gantt
  grpMetric: "pics",               // pics | cnt（机台 x Group 热力图格值口径）
  freeQ: "",                       // Free Layer 清单的 Lot 筛选
  freeSort: { k: "lot", dir: 1 },
  lotSegSort: { k: "lot", dir: 1 },
  lotAxis: "day",                  // day | grp（Lot 视图横轴切换）
  numMode: "lot",                  // v4：Group 编号口径 lot=Lot内(G1..Gn各Lot独立) | global=全局(按起始天)
  pFilter: { product: "all", flow: "all", stage: "all", step: "all" }, // v4：段级筛选（两页签共用）
  showCand: true,                  // 机台段带是否显示分配（待决策/Free）段
  cmpZoom: 30,                     // v4：折线图一屏可见天数（1~30）
  loadZoom: 30                     // v6：机台负载图一屏可见天数（1~30）
};

let LOTS = [], DAYS = 120, LOAD = null, SEGS = null, MET = null, LOADB = null, LOADD = null, NSTART = null;
let LOADP = null, LOADF = null;     // v6：待决策 / Free 分配逐日负载
let ALLSEGS = [], CANDL = null, CANDSEGS = null;   // v6：全局 Group 序列表 / 分配负载 / 各机台分配段
const CMP_COLORS = { E1:"#2F6FED", E2:"#16A34A", E3:"#E08A00", E4:"#9333EA", E5:"#0891B2", E6:"#DB2777" }; // v4：折线图机台配色