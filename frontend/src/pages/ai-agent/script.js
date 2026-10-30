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
