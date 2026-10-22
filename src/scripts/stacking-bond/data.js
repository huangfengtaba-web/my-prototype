/* ============================================================
   2. 数据生成（Lot 级异构 Group）
   ============================================================ */
function genLots() {
  const r = seedRnd(CFG.seed);
  const lots = [];
  for (let i = 0; i < CFG.nLots; i++) {
    const layers = 44 + Math.floor(r() * 17);          // 44~60 层
    const startDay = Math.floor(r() * 4);              // 0~3 错峰
    let nSeg = 8 + Math.floor(r() * 9);                // 8~16 段
    if (nSeg * 2 > layers) nSeg = Math.floor(layers / 2);
    const base = 2, rem = layers - nSeg * base;
    const extra = new Array(nSeg).fill(0);
    for (let k = 0; k < rem; k++) extra[Math.floor(r() * nSeg)]++;

    const groups = []; let lf = 0;
    for (let k = 0; k < nSeg; k++) {
      const cnt = base + extra[k];
      const lt = lf + cnt - 1;
      const ratio = lf / Math.max(1, layers);
      const pool = ratio < 0.34 ? ["E1", "E2"] : ratio < 0.67 ? ["E3", "E4"] : ["E5", "E6"];
      const cand = pool.slice();
      if (r() < 0.35) {                                 // 35% 概率跨机组交叉
        const nb = ratio < 0.34 ? "E3" : ratio < 0.67 ? "E5" : "E3";
        if (cand.indexOf(nb) < 0) cand.push(nb);
      }
      /* v4：取消「末段恒为 dec」——先按比例分配非 dec 状态，段组生成完再随机择 1 段置 dec */
      let st = "bound";
      { const rr = r(); if (rr < 0.15) st = "free"; else if (rr < 0.30) st = "pending"; }  // free≈15% / 待决策≈15%，bound 大头
      /* v6：待决策 / Free 也有指定机台（mock 分配表，后续由真实分配表加载），不再候选均分 */
      const eqp = cand[Math.floor(r() * cand.length)];
      const pics = 8 + Math.floor(r() * 19);            // 8~26 pics
      const stage = STAGE_OF[pool[0]];                  // v4：Stage 与候选池层深对齐 FE/ME/BE
      const flow = FLOWS[Math.floor(r() * FLOWS.length)]; // v4：Flow 演示口径
      const step = 1000 + Math.floor(r() * 80) * 10 + (k + 1) * 10; // v4：4 位步骤号，Lot 内按段递增
      groups.push({ idx: k + 1, name: "G" + (k + 1), lFrom: lf, lTo: lt, cand: cand, st: st, eqp: eqp, pics: pics, flow: flow, stage: stage, step: step });
      lf = lt + 1;
    }
    /* v4：每 Lot 恰 1 个「本次决策」段，位置三情形随机：开头 / 已绑定段之后 / 空白(pending/free)段之后；dec 之后仍可有其他段 */
    const pv = r();
    let decK = 0;
    if (pv < 0.30) {
      decK = 0;                                         // 情形①：以本次决策为开头
    } else {
      const afterB = [], afterW = [];
      for (let k = 1; k < nSeg; k++) (groups[k - 1].st === "bound" ? afterB : afterW).push(k);
      const pick = (pv < 0.65 || afterW.length === 0) ? afterB : (afterW.length ? afterW : afterB);
      const pool2 = pick.length ? pick : [0];
      decK = pool2[Math.floor(r() * pool2.length)];     // 情形②③：绑定后 / 空白后
    }
    groups[decK].st = "dec";
    groups[decK].eqp = groups[decK].cand[Math.floor(r() * groups[decK].cand.length)];
    lots.push({
      id: "LOT-" + String.fromCharCode(65 + (i % 8)) + String(i + 1).padStart(2, "0"),
      product: PRODS[i % PRODS.length], layers: layers, startDay: startDay, ct: CFG.ct, groups: groups
    });
  }
  return lots;
}

/* 段的天区间：dayFrom = startDay + lFrom*ct ；dayTo = startDay + lTo*ct + ct - 1 —— 占「层数 × ct」天 */
function segDays(lot, g) {
  const a = lot.startDay + g.lFrom * lot.ct;
  const b = lot.startDay + g.lTo * lot.ct + lot.ct - 1;
  return { a: a, b: b, span: b - a + 1 };
}

function rebuild() {
  LOTS = genLots();
  let maxD = CFG.days;
  LOTS.forEach(l => l.groups.forEach(g => { const d = segDays(l, g); if (d.b + 1 > maxD) maxD = d.b + 1; }));
  DAYS = maxD;

  const L = {}; const LB = {}; const LD = {}; const S = {}; const NS = {};
  EQPS.forEach(e => { L[e] = new Array(DAYS).fill(0); LB[e] = new Array(DAYS).fill(0); LD[e] = new Array(DAYS).fill(0); S[e] = []; NS[e] = new Array(DAYS).fill(0); });
  let freePics = 0;

  LOTS.forEach(l => l.groups.forEach(g => {
    const d = segDays(l, g);
    if (g.st === "free" || g.st === "pending") {
      if (g.st === "free") freePics += g.pics;
      return;                 // v6：负载统一由 recalcByFilter 按分配表（mock）计入
    }
    const e = g.eqp; if (!e || !L[e]) return;
    for (let t = d.a; t <= d.b && t < DAYS; t++) {
      L[e][t] += g.pics;                                  // ★ 段内每天值完全相同
      if (g.st === "bound") LB[e][t] += g.pics; else if (g.st === "dec") LD[e][t] += g.pics;
    }
    if (d.a < DAYS) NS[e][d.a]++;                         // 段起始日：当日才有新的「已绑 / 决策」发生
    S[e].push({ lot: l, g: g, d: d });
  }));
  EQPS.forEach(e => S[e].sort((x, y) => x.d.a - y.d.a || x.g.idx - y.g.idx));

  /* v3：全局 Group 编号 —— 全部段按起始天排序，G1 连续编到 GN */
  ALLSEGS = [];
  LOTS.forEach(function (l) { l.groups.forEach(function (g) { ALLSEGS.push({ lot: l, g: g, d: segDays(l, g) }); }); });
  ALLSEGS.sort(function (x, y) { return x.d.a - y.d.a || x.lot.id.localeCompare(y.lot.id) || x.g.idx - y.g.idx; });
  /* v4：双编号 —— lname=Lot 内序号（各 Lot 独立，主显示口径）；gname=全局序号（按起始天排序，跨 Lot 唯一） */
  ALLSEGS.forEach(function (x, i) { x.gn = i + 1; x.g.gn = i + 1; x.g.lname = x.g.name = "G" + x.g.idx; x.g.gname = "G" + (i + 1); });

  /* v6：待决策/Free 分配负载 + 各机台分配段 */
  CANDL = {}; CANDSEGS = {};
  EQPS.forEach(function (e) { CANDL[e] = new Array(DAYS).fill(0); CANDSEGS[e] = []; });
  ALLSEGS.forEach(function (x) {
    if (x.g.st !== "free" && x.g.st !== "pending") return;
    const per = x.g.pics / x.g.cand.length;
    x.g.cand.forEach(function (e) {
      if (!CANDL[e]) return;
      for (let t = x.d.a; t <= x.d.b && t < DAYS; t++) CANDL[e][t] += per;
      CANDSEGS[e].push(x);
    });
  });

  LOAD = L; SEGS = S; LOADB = LB; LOADD = LD; NSTART = NS;

  /* 机台间口径（目标 1） */
  const tot = {}; EQPS.forEach(e => tot[e] = L[e].reduce((a, b) => a + b, 0));
  const tv = EQPS.map(e => tot[e]);
  const between = stats(tv);
  /* 单机逐日（目标 3） */
  const per = {}; EQPS.forEach(e => per[e] = stats(L[e]));
  /* 日峰值（目标 2）：单机单日峰值 */
  const dailyPeak = []; for (let t = 0; t < DAYS; t++) dailyPeak.push(Math.max.apply(null, EQPS.map(e => L[e][t])));
  const globalPeak = dailyPeak.length ? Math.max.apply(null, dailyPeak) : 0;

  let nBound = 0, nFree = 0, nPending = 0, nDec = 0, nSegAll = 0, pendPics = 0;
  LOTS.forEach(l => l.groups.forEach(g => {
    nSegAll++;
    if (g.st === "bound") nBound++;
    else if (g.st === "free") nFree++;
    else if (g.st === "pending") { nPending++; pendPics += g.pics; }
    else nDec++;
  }));

  MET = { tot: tot, between: between, per: per, dailyPeak: dailyPeak, globalPeak: globalPeak,
          freePics: freePics, nBound: nBound, nFree: nFree, nPending: nPending, pendPics: pendPics, nDec: nDec, nSegAll: nSegAll };

  /* v5：按当前字段筛选（Product/Flow/Stage/Step + 状态）重算负载矩阵 */
  recalcByFilter();
}