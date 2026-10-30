// src/pages/ 共享壳层：侧栏导航 + 表头时钟 + 评论模式 + tooltip
// 用法（页面 index.html 里）：
//   <div class="app"><aside class="sider" id="sider"></aside><div class="main">…（header/content 自定义）</div></div>
//   import { mountShell } from '../_shared/shell.js'
//   mountShell('scheduling-test')   // 传当前页 key 高亮
const NAV = [
  ['系统导航', [
    ['/', '系统总览', 'dashboard'],
    ['/litho-schedule', 'Litho 排程', 'litho-schedule'],
    ['/reticle-schedule', 'Reticle 排程', 'reticle-schedule'],
    ['/prototypes/data_zone.html', '数据接入', ''],
    ['/prototypes/config_zone.html', '数据配置', ''],
    ['/prototypes/model_zone.html', '模型管理', ''],
    ['/logs', '系统日志', 'logs'],
  ]],
  ['智能应用（真后端）', [
    ['/simulation', '仿真验证', 'simulation'],
    ['/twin-control', '数字孪生回放', 'twin-control'],
    ['/twin', '数字孪生（原始场景）', 'twin'],
    ['/scheduling-test', '求解演示', 'scheduling-test'],
    ['/ai-agent', 'AI 助手', 'ai-agent'],
    ['/ai-workflow', 'AI 工作流', 'ai-workflow'],
    ['/reports', '报告生成', 'reports'],
  ]],
  ['原型参考（mock 数据，设计基线）', [
    ['/prototypes/index.html', '系统总览（原型）', ''],
    ['/prototypes/result_litho.html', 'Litho 排程（原型）', ''],
    ['/prototypes/result_reticle.html', 'Reticle 排程（原型）', ''],
    ['/prototypes/log_zone.html', '系统日志（原型）', ''],
    ['/prototypes/equip_temp_layer_config.html', '温层配置（原型）', ''],
    ['/prototypes/stacking_bond_ui_v6.html', 'EQP Loading（原型）', ''],
  ]],
]

export function mountShell(active) {
  const sider = document.getElementById('sider')
  sider.innerHTML = `
    <div class="logo"><b>Pxsemi FSO</b><span>智能生产中心 · 光刻排程</span></div>
    <nav>${NAV.map(([g, links]) => `
      <div class="nav-g">${g}</div>
      ${links.map(([href, label, key]) =>
        `<a href="${href}" class="${key === active ? 'on' : ''}">${label}</a>`).join('')}
    `).join('')}</nav>`

  const clock = document.getElementById('clock')
  if (clock) {
    const tick = () => clock.textContent = new Date().toLocaleString('zh-CN', { hour12: false })
    tick(); setInterval(tick, 1000)
  }
  const cmBtn = document.getElementById('cmBtn')
  if (cmBtn) cmBtn.addEventListener('click', () => document.body.classList.toggle('cm'))

  const tt = document.getElementById('tt')
  if (tt) {
    document.addEventListener('mouseover', (e) => {
      const q = e.target.closest('.q[data-cm]')
      if (!q) return tt.style.display = 'none'
      const r = q.getBoundingClientRect()
      tt.textContent = q.dataset.cm
      tt.style.display = 'block'
      tt.style.left = Math.min(r.left, innerWidth - 340) + 'px'
      tt.style.top = (r.bottom + 6) + 'px'
    })
  }
}

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const $ = (s) => document.querySelector(s)

export function statusTag(st) {
  const map = { done: 'success', failed: 'error', timeout: 'error', running: 'processing',
    pending: 'default', suboptimal: 'warning' }
  return `<span class="tag ${map[st] || 'default'}">${st}</span>`
}

export function toMin(hm) {
  if (!hm) return null
  const [h, m] = String(hm).split(':').map(Number)
  return Number.isFinite(h) && Number.isFinite(m) ? h * 60 + m : null
}

export function fmtMin(m) {
  return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(Math.round(m % 60)).padStart(2, '0')}`
}

// 通用单轨甘特：rows=[{name, segs:[{s,e,label,color,tip}]}]（s/e 单位分钟），返回 HTML
export function seqGantt(rows, opts = {}) {
  const pts = rows.flatMap((r) => r.segs.flatMap((g) => [g.s, g.e])).filter((v) => v != null)
  if (!pts.length) return '<div class="empty">无数据</div>'
  const t0 = Math.min(...pts), t1 = Math.max(...pts), span = Math.max(t1 - t0, 1)
  let html = `<div class="gantt"><div class="g-ruler">`
  const step = opts.hourStep || 60
  for (let m = Math.ceil(t0 / step) * step; m <= t1; m += step)
    html += `<span style="left:${((m - t0) / span) * 100}%">${fmtMin(m)}</span>`
  html += `</div>`
  for (const row of rows) {
    html += `<div class="g-row"><div class="g-name">${row.name}</div><div class="g-track">`
    for (const g of row.segs) {
      const left = ((g.s - t0) / span) * 100
      const width = Math.max(((g.e - g.s) / span) * 100, 0.8)
      const color = g.color ? `background:${g.color};` : ''
      html += `<div class="g-seg" style="left:${left}%;width:${width}%;${color}"
        title="${g.tip || g.label || ''}">${g.label || ''}</div>`
    }
    html += `</div></div>`
  }
  return html + `</div>`
}

// Lot 全景抽屉：ensureDrawer() 建一次，showLotDrawer(html) 填内容并弹出
export function ensureDrawer() {
  if (document.getElementById('gtxDrawer')) return
  const mask = document.createElement('div')
  mask.className = 'drawer-mask'
  mask.id = 'gtxDrawerMask'
  const d = document.createElement('div')
  d.className = 'drawer'
  d.id = 'gtxDrawer'
  d.innerHTML = `<div class="d-h"><div class="t" id="gtxDrawerTitle"></div>
    <button class="btn sm" id="gtxDrawerClose">✕</button></div>
    <div class="d-b" id="gtxDrawerBody"></div>`
  document.body.append(mask, d)
  const close = () => { mask.classList.remove('show'); d.classList.remove('show') }
  mask.addEventListener('click', close)
  d.querySelector('#gtxDrawerClose').addEventListener('click', close)
}

export function showLotDrawer(title, bodyHtml) {
  ensureDrawer()
  document.getElementById('gtxDrawerTitle').textContent = title
  document.getElementById('gtxDrawerBody').innerHTML = bodyHtml
  document.getElementById('gtxDrawerMask').classList.add('show')
  document.getElementById('gtxDrawer').classList.add('show')
}

// 单 Lot 全景（调 GET /api/solve/lot/{run_id}/{lot_id}）并弹出
export async function openLotPanorama(runId, lotId) {
  showLotDrawer(`Lot 全景 · ${lotId}`, '<div class="empty">加载中…</div>')
  try {
    const res = await fetch(`${API_BASE}/api/solve/lot/${runId}/${lotId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const p = await res.json()
    const b = p.base || {}, s = p.schedule || {}, r = p.reticle || {}
    const kv = (k, v) => `<div class="k">${k}</div><div>${v == null || v === '' ? '—' : v}</div>`
    showLotDrawer(`Lot 全景 · ${lotId}（${p.case || '基线'} · run ${p.run_id}）`, `
      <div class="d-sec">① 基础属性（宽表口径）</div>
      <div class="d-kv">${kv('产品 / Step', `${b.product} / ${b.step}`)}${kv('片数', b.qty)}
        ${kv('Priority', 'PRI' + b.priority)}${kv('温层', b.temp)}
        ${kv('到站时间', fmtMin(b.ready))}${kv('Remain QTime', b.remain_qt ? b.remain_qt + 'min' : '—')}
        ${kv('BARC QTime / PT', (b.barc_qt || '—') + 'min / ' + (b.pt || '—') + 'min')}
        ${kv('属性打标', (b.tags || []).join(' / ') || 'Normal')}</div>
      <div class="d-sec">③ 排程结果（细排程 MILP）</div>
      <div class="d-kv">${kv('机台', s.eqp || '—')}${kv('机台组', (s.eqp_group) || '—')}
        ${kv('开工 / 完工', `${s.start || '—'} ~ ${s.end || '—'}`)}
        ${kv('后处理说明', s.post_note || '-')}</div>
      <div class="d-sec">⑤ BARC 放货窗口（反推）</div>
      <div class="d-kv">${kv('Batch', p.barc?.batch_id || '—')}${kv('ER / LR', `${p.barc?.er || '—'} / ${p.barc?.lr || '—'}`)}</div>
      <div class="d-sec">⑥ 所属光罩（五态推演）</div>
      <div class="d-kv">${kv('Reticle', r.id || '—')}${kv('状态', r.status || '—')}
        ${kv('就绪时间', r.ready || '—')}${kv('备注', r.note || '—')}</div>
      <div class="d-sec">六步执行（${p.milp ? `②${p.milp.step2} ③${p.milp.step3}` : ''}）</div>
      ${(p.steps || []).map((st) => `<div>${st.name} · ${st.status} · ${st.seconds}s · ${st.detail || ''}</div>`).join('')}
      ${p.qtms_over ? '<div style="color:var(--colorError)">⚠ QTMS 超水位：④后处理已跳过本 Loop</div>' : ''}
    `)
  } catch (e) {
    showLotDrawer(`Lot 全景 · ${lotId}`, `<div style="color:var(--colorError)">加载失败：${e.message}</div>`)
  }
}
