// 数字孪生控制页：POST /api/solve/run → GET /api/twin/timeline → gtxTwinApi.loadSchedule
// 通过 iframe.contentWindow.gtxTwinApi（同源）驱动 play/pause/seek/setSpeed，200ms 轮询状态。
import { API_BASE, $, mountShell } from '../_shared/shell.js'

mountShell('twin-control')

const state = { timeline: null, busy: [], timer: null, duration: 0, dragging: false }

function api() {
  try {
    return document.getElementById('twinFrame').contentWindow.gtxTwinApi || null
  } catch {
    return null
  }
}

function setState(msg, isErr) {
  const el = $('#twinState')
  el.textContent = msg
  el.className = 'run-state ' + (isErr ? 'err' : 'ok')
}

const fmt = (s) => {
  s = Math.max(0, Math.floor(s))
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}

async function loadSchedule() {
  const btn = $('#loadBtn')
  btn.disabled = true
  setState('后端求解中…（六步 MILP 约 2~5s）')
  try {
    const solveRes = await fetch(`${API_BASE}/api/solve/run`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
    })
    if (!solveRes.ok) throw new Error(`solve HTTP ${solveRes.status}`)
    const solve = await solveRes.json()
    const tlRes = await fetch(`${API_BASE}/api/twin/timeline/${solve.run_id}`)
    if (!tlRes.ok) throw new Error(`timeline HTTP ${tlRes.status}`)
    state.timeline = await tlRes.json()

    const a = api()
    if (!a) throw new Error('孪生未就绪（gtxTwinApi 未注入，稍后重试）')
    const r = a.loadSchedule(state.timeline)
    state.duration = state.timeline.events.reduce((m, e) => Math.max(m, e.t), 0)
    $('#seek').max = state.duration
    $('#seek').disabled = false
    $('#speed').disabled = false
    setState(`已加载 ${r.events} 个事件（${state.timeline.t0}~${state.timeline.t1}）`)
    startLoop()
  } catch (err) {
    setState(`失败：${err.message}`, true)
  } finally {
    btn.disabled = false
  }
}

function startLoop() {
  clearInterval(state.timer)
  state.timer = setInterval(() => {
    const a = api()
    if (!a) return
    const st = a.getState()
    $('#playBtn').textContent = st.playing ? '⏸ 暂停' : '▶ 播放'
    $('#playBtn').disabled = !st.hasSchedule
    if (!state.dragging) $('#seek').value = st.timeSec
    $('#tlabel').textContent = `${fmt(st.timeSec)} / ${fmt(state.duration)}`
    renderLots(st.timeSec)
  }, 200)
}

// 当前时刻在机加工的 Lot：Busy 事件区间 [s,e) 覆盖 now
function renderLots(now) {
  if (!state.timeline) return
  const busy = state.busy.length
    ? state.busy
    : (state.busy = state.timeline.events
        .filter((e) => e.type === 'eqp_state' && e.state === 'Busy')
        .map((e) => {
          const idle = state.timeline.events.find(
            (x) => x.type === 'eqp_state' && x.target === e.target && x.state === 'Idle' && x.t >= e.t)
          return { eqp: e.target, lot: e.lot, s: e.t, e: idle ? idle.t : Infinity }
        }))
  const active = busy.filter((x) => now >= x.s && now < x.e)
  $('#lotList').innerHTML = active.length
    ? active.map((x) => `<div class="lot-row">
        <b>${x.lot}</b> <span class="busy">● 加工中</span><br>
        <span class="muted">${x.eqp} · ${fmt(x.s)}~${fmt(x.e)}</span></div>`).join('')
    : '<div class="empty">当前时刻无机台在加工</div>'
}

$('#loadBtn').addEventListener('click', loadSchedule)
$('#playBtn').addEventListener('click', () => {
  const a = api()
  if (!a) return
  const st = a.getState()
  ;(st.playing ? a.pause() : a.play())
})
$('#seek').addEventListener('mousedown', () => (state.dragging = true))
$('#seek').addEventListener('mouseup', () => (state.dragging = false))
$('#seek').addEventListener('input', (e) => {
  const a = api()
  if (a) {
    a.seek(Number(e.target.value))
    $('#tlabel').textContent = `${fmt(Number(e.target.value))} / ${fmt(state.duration)}`
  }
})
$('#speed').addEventListener('change', (e) => {
  const a = api()
  if (a) a.setSpeed(Number(e.target.value))
})
