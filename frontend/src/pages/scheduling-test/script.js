// GTX FSO Litho · 求解演示页逻辑
// 数据流（docs/02_INTEGRATION_GUIDE.md §5.2）：
//   选 case → POST /api/solve/run → 子进程跑六步 MILP → 渲染 KPI/甘特/列表
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const $ = (s) => document.querySelector(s)
const state = { cases: [], lastSummary: null, history: [] }

// ---------- 初始化 ----------
async function init() {
  tickClock(); setInterval(tickClock, 1000)
  bindCommentMode(); bindTips()
  await loadCases()
  $('#runBtn').addEventListener('click', runSolve)
  $('#csvBtn').addEventListener('click', exportCSV)
}

function tickClock() {
  $('#clock').textContent = new Date().toLocaleString('zh-CN', { hour12: false })
}

// ---------- 评论模式（.q[data-cm]，照 v6 机制） ----------
function bindCommentMode() {
  $('#cmBtn').addEventListener('click', () => document.body.classList.toggle('cm'))
}
function bindTips() {
  const tt = $('#tt')
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

// ---------- 用例下拉 ----------
async function loadCases() {
  try {
    const res = await fetch(`${API_BASE}/api/cases`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    state.cases = (await res.json()).cases || []
  } catch (err) {
    $('#caseSel').innerHTML = '<option value="">（后端未启动：先跑 uvicorn）</option>'
    setRunState(`后端不可达：${err.message}（启动方法见 docs/03_ALGORITHM_DEMO.md §7）`, true)
    return
  }
  $('#caseSel').innerHTML = state.cases.map((c) => `<option value="${c}">${c}</option>`).join('')
    || '<option value="">（无用例，跑基线）</option>'
  $('#caseSel').addEventListener('change', showCaseDesc)
  showCaseDesc()
}

function showCaseDesc() {
  const c = $('#caseSel').value
  const box = $('#caseDesc')
  if (!c) return box.classList.remove('show')
  // 用例定义在仓库 tests/cases/<name>.yaml（YAML 覆盖规则见 docs/03_ALGORITHM_DEMO.md §5）
  box.textContent = `当前用例：${c} · 覆盖规则定义在仓库 tests/cases/${c}.yaml（只影响求解子进程内存，不写回 mock_data.py）`
  box.classList.add('show')
}

// ---------- 运行求解 ----------
async function runSolve() {
  const btn = $('#runBtn')
  btn.disabled = true
  setRunState('求解中…（子进程冷启动约 2~5s）')
  const started = Date.now()
  try {
    const res = await fetch(`${API_BASE}/api/solve/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case: $('#caseSel').value || null }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const data = await res.json()
    render(data)
    state.history.unshift({ run_id: data.run_id, case: data.case, status: data.status,
      started_at: data.started_at, finished_at: data.finished_at })
    renderHistory()
    setRunState(`完成，耗时 ${((Date.now() - started) / 1000).toFixed(1)}s · run_id=${data.run_id}`, data.status !== 'failed')
  } catch (err) {
    setRunState(`失败：${err.message}`, true)
  } finally {
    btn.disabled = false
  }
}

function setRunState(msg, isErr) {
  const el = $('#runState')
  el.textContent = msg
  el.className = 'run-state ' + (isErr ? 'err' : 'ok')
}

// ---------- 渲染 ----------
function render(data) {
  const s = data.summary
  if (!s) { $('#kMilp').textContent = data.status; return }
  const milp = s.milp_status || {}
  const milpEl = $('#kMilp')
  milpEl.textContent = `${milp.step2 || '-'} / ${milp.step3 || '-'}`
  milpEl.className = 'k-v ' + (milp.step2 === 'Optimal' && milp.step3 === 'Optimal' ? 'ok' : 'err')

  const sched = s.schedule || []
  const ends = sched.map((r) => toMin(r.end)).filter((v) => v != null)
  $('#kSpan').textContent = ends.length ? fmtMin(Math.max(...ends)) : '—'
  $('#kLots').textContent = sched.length
  const a01 = sched.find((r) => r.lot === 'LOT-A01')
  $('#kUrgent').textContent = a01?.start || '—'
  const rt = (s.reticles || {})['RT-0101']
  $('#kReticle').textContent = rt?.ready || '—'

  renderGantt(sched)
  renderTable(sched)
}

function renderGantt(sched) {
  const box = $('#gantt')
  const pts = sched.flatMap((r) => [toMin(r.start), toMin(r.end)]).filter((v) => v != null)
  if (!pts.length) return
  const t0 = Math.min(...pts), t1 = Math.max(...pts)
  const span = Math.max(t1 - t0, 1)

  const byEqp = {}
  for (const r of sched) {
    if (!r.eqp) continue
    ;(byEqp[r.eqp] ||= []).push(r)
  }
  let html = '<div class="gantt"><div class="g-ruler">'
  for (let m = t0; m <= t1; m += 60) {
    html += `<span style="position:absolute;left:${((m - t0) / span) * 100}%">${fmtMin(m)}</span>`
  }
  html += '</div>'
  for (const eqp of Object.keys(byEqp).sort()) {
    html += `<div class="g-row"><div class="g-name">${eqp}</div><div class="g-track">`
    for (const r of byEqp[eqp]) {
      const s0 = toMin(r.start), s1 = toMin(r.end)
      if (s0 == null || s1 == null) continue
      const left = ((s0 - t0) / span) * 100, width = Math.max(((s1 - s0) / span) * 100, 1.2)
      html += `<div class="g-seg" style="left:${left}%;width:${width}%"
        data-tip="${r.lot} · ${r.reticle} · ${r.start}~${r.end}">${r.lot}</div>`
    }
    html += '</div></div>'
  }
  box.innerHTML = html + '</div>'
  $('#ganttEmpty').style.display = 'none'
}

function renderTable(sched) {
  $('#tbl tbody').innerHTML = (sched || []).map((r) => `<tr>
    <td><b>${r.lot}</b></td><td>${r.eqp || '—'}</td><td>${r.eqp_group || '—'}</td>
    <td>${r.reticle}</td><td><span class="tag ${r.priority === 'PRI1' ? 'error' : 'default'}">${r.priority}</span></td>
    <td>${r.temp}</td><td>${r.start || '—'}</td><td>${r.end || '—'}</td>
    <td>${r.barc_er || '—'}</td><td>${r.barc_lr || '—'}</td><td>${r.post_note || '-'}</td>
  </tr>`).join('')
}

function renderHistory() {
  $('#histTbl tbody').innerHTML = state.history.map((h) => `<tr>
    <td>${h.run_id}</td><td>${h.case || '基线'}</td><td>${statusTag(h.status)}</td>
    <td>${h.started_at || ''}</td><td>${h.finished_at || ''}</td>
    <td></td></tr>`).join('')
}

function statusTag(st) {
  const map = { done: 'success', suboptimal: 'warning', failed: 'error', timeout: 'error', running: 'processing' }
  return `<span class="tag ${map[st] || 'default'}">${st}</span>`
}

// ---------- 工具 ----------
function toMin(hm) {
  if (!hm) return null
  const [h, m] = String(hm).split(':').map(Number)
  return Number.isFinite(h) && Number.isFinite(m) ? h * 60 + m : null
}
function fmtMin(m) { return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(Math.round(m % 60)).padStart(2, '0')}` }

function exportCSV() {
  const rows = [['LotId', 'Eqp', 'EqpGroup', 'Reticle', 'Priority', 'Temp', 'Start', 'End', 'BarcER', 'BarcLR', 'Note']]
  document.querySelectorAll('#tbl tbody tr').forEach((tr) =>
    rows.push([...tr.children].map((td) => td.textContent.trim())))
  const csv = '\ufeff' + rows.map((r) => r.map((v) => `"${v}"`).join(',')).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
  a.download = 'scheduling-test.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

init()
