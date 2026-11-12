// AI 助手页逻辑：POST /api/agent/chat（多轮，session_id 维持）；工具调用以 chip 展示
import { API_BASE, $, mountShell } from '../_shared/shell.js'

mountShell('ai-agent')

const state = { sessionId: null, busy: false }

const QUICK = ['有哪些用例？', '跑一下 urgent-A01 看看急货排得怎么样',
  '帮我仿真一下 reticle-delay', '对比一下几个场景', '跑日计划工作流', '看一下机台数据']

async function init() {
  try {
    const st = await (await fetch(`${API_BASE}/api/agent/status`)).json()
    const badge = $('#modeBadge')
    badge.textContent = st.mode === 'llm' ? `LLM · ${st.model}` : '规则模式（未配置 LLM）'
    badge.className = `mode-badge ${st.mode}`
    // 能力与调试面板
    $('#capMode').textContent = st.mode === 'llm'
      ? `模式 LLM · 模型 ${st.model}（OpenAI 兼容，.env 的 LLM_MODEL 可换）`
      : '模式 规则兜底（.env 配 LLM_API_BASE/KEY/MODEL 后切自主决策）'
    $('#capTools').innerHTML = (st.tools || [])
      .map((t) => `<span class="cap-tool">${t}</span>`).join(' ')
  } catch { /* 后端未起：发送时再报错 */ }
  $('#quick').innerHTML = QUICK.map((q) => `<button data-q="${q}">${q}</button>`).join('')
  document.querySelectorAll('.quick button').forEach((b) =>
    b.addEventListener('click', () => send(b.dataset.q)))
  $('#sendBtn').addEventListener('click', () => send())
  $('#capBtn').addEventListener('click', () => {
    const p = $('#capPanel')
    p.style.display = p.style.display === 'none' ? '' : 'none'
  })
  $('#input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  })

  // 自主规划面板（阶段四 Loop Engineering）
  $('#loopBtn').addEventListener('click', () => {
    const p = $('#loopPanel')
    p.style.display = p.style.display === 'none' ? '' : 'none'
  })
  $('#loopRun').addEventListener('click', runLoop)
  $('#loopGoal').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); runLoop() }
  })
}

// ---------------------------------------------------------------- 自主规划
async function runLoop() {
  const goal = ($('#loopGoal').value || '').trim()
  if (!goal) return
  const out = $('#loopOut')
  const btn = $('#loopRun')
  btn.disabled = true
  out.innerHTML = '规划中…（可能要跑多次求解，约 5~20 秒）'
  try {
    const res = await fetch(`${API_BASE}/api/agent/loop`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal, enabled: true, max_rounds: 5 }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    renderLoop(await res.json())
  } catch (err) {
    out.innerHTML = `<span style="color:#c0392b">执行失败：${err.message}</span>`
  } finally {
    btn.disabled = false
  }
}

function renderLoop(d) {
  const out = $('#loopOut')
  if (d.status === 'disabled') {
    out.innerHTML = `<span style="color:#c0392b">未开启</span>：${d.stopped_reason}<br>${d.hint || ''}`
    return
  }
  const ok = d.goal_met
  const icon = ok ? '✅' : (d.status === 'done' ? '⚠️' : '⏹')
  const lines = []

  lines.push(`<b>目标</b>：${d.goal}`)
  lines.push(`<b>${icon} 判定</b>：${ok ? '达成' : '未达成'}　`
    + `<span class="muted">${d.rounds} 轮 / 重规划 ${d.replans} 次 / ${d.elapsed_s}s</span>`)

  const ev = d.evidence || {}
  const bits = []
  if (ev.start) bits.push(`上机 ${ev.start} @ ${ev.eqp || '-'}`)
  if (ev.deadline_min != null && ev.actual_min != null) {
    const fmt = (m) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`
    bits.push(`截止 ${fmt(ev.deadline_min)} / 实际 ${fmt(ev.actual_min)}`)
    if (ev.slack_min != null) bits.push(`余量 ${ev.slack_min > 0 ? '+' : ''}${ev.slack_min} 分钟`)
  }
  if (ev.actual != null && ev.target != null) {
    bits.push(`准时率 ${(ev.actual * 100).toFixed(1)}% / 目标 ${(ev.target * 100).toFixed(0)}%`)
  }
  if (bits.length) lines.push(`<b>证据</b>：${bits.join('　')}`)
  if (d.explanation) lines.push(`<b>解读</b>：${d.explanation}`)
  if (d.stopped_reason) lines.push(`<b>停止原因</b>：${d.stopped_reason}`)

  // 阶段时间线
  const steps = (d.observations || []).map((o) => {
    const key = o.urgent_start || o.on_time_rate != null
      ? (o.urgent_start ? `上机 ${o.urgent_start}` : '')
        + (o.on_time_rate != null ? ` 准时率 ${(o.on_time_rate * 100).toFixed(1)}%` : '')
      : (o.error ? `错误 ${String(o.error).slice(0, 40)}` : 'ok')
    return `R${o.round} ${o.skill}${o.ok === false ? ' ❌' : ' →'} ${key}`
  })
  if (steps.length) {
    lines.push(`<b>执行轨迹</b>：<br>${steps.map((s) => '· ' + s).join('<br>')}`)
  }
  const plans = (d.plan || []).map((p, i) =>
    `第${i + 1}套：${p.map((s) => s.skill + '(' + Object.entries(s.args || {}).map(([k, v]) => `${k}=${v}`).join(',') + ')').join(' → ')}`)
  if (plans.length > 1) lines.push(`<b>尝试过的方案</b>：<br>${plans.join('<br>')}`)

  lines.push(`<span class="muted">trace_id：${d.trace_id}（GET /api/agent/trace/${d.trace_id}）</span>`)
  out.innerHTML = lines.join('<br>')
}

function addMsg(cls, text) {
  const el = document.createElement('div')
  el.className = `msg ${cls}`
  el.textContent = text
  $('#msgs').appendChild(el)
  $('#msgs').scrollTop = $('#msgs').scrollHeight
  return el
}

function addToolChips(trace) {
  for (const t of trace || []) {
    const el = document.createElement('div')
    el.className = 'toolchip'
    el.innerHTML = `<span class="tname">🔧 ${t.name}</span>
      <span class="tsum">${(t.summary || '').slice(0, 120)}…</span>`
    el.title = `${t.name}(${JSON.stringify(t.args)})\n${t.summary || ''}`
    $('#msgs').appendChild(el)
  }
  $('#msgs').scrollTop = $('#msgs').scrollHeight
}

async function send(preset) {
  if (state.busy) return
  const text = (preset ?? $('#input').value).trim()
  if (!text) return
  $('#input').value = ''
  addMsg('user', text)
  state.busy = true
  $('#sendBtn').disabled = true
  const pending = addMsg('bot', '思考中…')
  try {
    const res = await fetch(`${API_BASE}/api/agent/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: state.sessionId }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const data = await res.json()
    state.sessionId = data.session_id
    pending.remove()
    addToolChips(data.tool_calls)
    addMsg('bot', data.reply)
  } catch (err) {
    pending.remove()
    addMsg('bot', `调用失败：${err.message}\n（后端起了吗？uvicorn backend.app.api:app --port 8000）`)
  } finally {
    state.busy = false
    $('#sendBtn').disabled = false
  }
}

init()
