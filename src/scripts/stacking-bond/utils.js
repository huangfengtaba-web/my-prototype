/* ============================================================
   0. 工具
   ============================================================ */
const $  = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = s => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const n1 = v => (Math.round(v * 10) / 10).toFixed(1);
const n2 = v => (Math.round(v * 100) / 100).toFixed(2);
const f0 = v => (v == null || isNaN(v)) ? "—" : Number(v).toLocaleString("zh-CN");

/* 确定性伪随机：保证刷新数据一致 */
function seedRnd(seed) {
  let s = (seed >>> 0) || 1;
  return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

/* 统计（总体口径，除 n） */
function stats(arr) {
  const n = arr.length; if (!n) return { n: 0, mean: 0, varr: 0, sd: 0, cv: 0, mad: 0, range: 0, pm: 0, mx: 0, mn: 0, sum: 0 };
  const sum = arr.reduce((a, b) => a + b, 0), mean = sum / n;
  const varr = arr.reduce((a, b) => a + (b - mean) * (b - mean), 0) / n;
  const sd = Math.sqrt(varr);
  const mad = arr.reduce((a, b) => a + Math.abs(b - mean), 0) / n;
  const mx = Math.max.apply(null, arr), mn = Math.min.apply(null, arr);
  return { n, sum, mean, varr, sd, cv: mean ? sd / mean : 0, mad, range: mx - mn, pm: mean ? mx / mean : 0, mx, mn };
}