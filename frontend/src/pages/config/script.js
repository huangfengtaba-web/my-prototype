// 数据配置页（真配置）：GET /api/config → 表单；PUT /api/config 保存/恢复
import { API_BASE, $, mountShell } from '../_shared/shell.js'

mountShell('config')

const DESC = {
  temp_change_min: 'T1↔T2 温层转换耗时（分钟），异温层相邻 Lot 间隔',
  release_gap_min: 'BARC 同 Stage 放货间隔（分钟，需求参考 2h）',
  iris_min: '光罩 IRIS 检测耗时（分钟）',
  transport_min: '光罩搬送耗时（分钟，AMHS）',
  load_min: '光罩装载耗时（分钟）',
  w_changeover: '②目标权重：每次换罩等效分钟数',
  w_makespan: '②目标权重：MakeSpan',
  time_limit_s: 'CBC 求解时限（秒）',
  stocker_phys: '光罩储位物理容量',
  stocker_water: '光罩储位用户管理水位',
  iris_reset_wafers: 'IRIS 检测后光罩恢复的可用片数（计片校准）',
  chunk_size: 'Lot 细排程 chunk 上限（设计版 ≤50）',
}

async function init() {
  try {
    const d = await (await fetch(`${API_BASE}/api/config`)).json()
    $('#cfgGrid').innerHTML = d.editable.map((k) => `
      <div class="cfg ${d.overridden.includes(k) ? 'overridden' : ''}">
        <label class="lab">${k}</label>
        <input id="cfg_${k}" value="${d.config[k] ?? ''}">
        <div class="desc">${DESC[k] || ''}</div>
      </div>`).join('')
  } catch {
    $('#cfgGrid').innerHTML = '<div class="empty">后端不可达：先跑 uvicorn backend.app.api:app</div>'
    return
  }
  $('#saveBtn').addEventListener('click', () => save(false))
  $('#resetBtn').addEventListener('click', () => save(true))
}

async function save(reset) {
  const patches = {}
  if (!reset) {
    document.querySelectorAll('#cfgGrid input').forEach((inp) => {
      const k = inp.id.replace('cfg_', '')
      const v = Number(inp.value)
      patches[k] = Number.isFinite(v) && inp.value !== '' ? v : inp.value
    })
  }
  $('#saveBtn').disabled = $('#resetBtn').disabled = true
  $('#cfgState').textContent = '保存中…'
  try {
    const res = await fetch(`${API_BASE}/api/config`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reset ? { reset: true } : { patches }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
    const d = await res.json()
    $('#cfgState').textContent = `已保存（覆盖项：${d.overridden.length ? d.overridden.join(', ') : '无'}），下一次求解生效`
    $('#cfgState').className = 'run-state ok'
    init()
  } catch (e) {
    $('#cfgState').textContent = `失败：${e.message}`
    $('#cfgState').className = 'run-state err'
  } finally {
    $('#saveBtn').disabled = $('#resetBtn').disabled = false
  }
}

init()
