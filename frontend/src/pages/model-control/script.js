// Model Control（真数据）：Eqp Group / Data Parameter / Schedule Model
import { API_BASE, $, mountShell } from '../_shared/shell.js'

mountShell('model-control')

async function init() {
  try {
    const d = await (await fetch(`${API_BASE}/api/cim/model-control`)).json()
    $('#egTbl tbody').innerHTML = d.eqp_groups.map((g) => `<tr>
      <td><b>${g.name}</b> ${g.in_use ? '<span class="tag processing">已占用</span>' : ''}</td>
      <td>${g.model}</td><td>${g.eqp_type}</td><td>${g.running_mode || '—'}</td>
      <td>${g.area}</td><td>${g.kpi_view}</td><td>${g.schedule_model}</td>
      <td>${g.machines.join('、') || '—'}</td>
      <td>${g.in_use ? '<span class="tag success">生效</span>' : '<span class="tag default">未生效</span>'}</td></tr>`).join('')
    $('#dpTbl tbody').innerHTML = d.data_parameters.map((p) => `<tr>
      <td>${p.model_type}</td><td>${p.set}</td><td>${p.item}</td><td>${p.type}</td>
      <td><span class="tag success">${p.status}</span></td><td>${p.scope}</td><td>${p.mo}</td>
      <td><code>${p.variable}</code></td><td><b>${p.value}</b></td><td>${p.description}</td></tr>`).join('')
    $('#smTbl tbody').innerHTML = d.schedule_models.map((m) => `<tr>
      <td><b>${m.name}</b></td><td>${m.version}</td><td>${m.eqp_group}</td>
      <td><span class="tag ${m.status === 'on' ? 'success' : 'default'}">${m.status === 'on' ? '生效' : '关闭'}</span></td>
      <td>${m.auto_run ? 'Yes' : 'No'}</td><td>${m.schedule_type}</td><td>${m.last_run}</td>
      <td>${m.description}</td></tr>`).join('')
  } catch {
    $('#egTbl tbody').innerHTML =
      '<tr><td colspan="9" style="color:var(--colorError)">后端不可达</td></tr>'
    return
  }
  const bind = (btn, view) => $(btn).addEventListener('click', () => {
    ['E', 'D', 'S'].forEach((v) => { $(`#view${v}`).style.display = v === view ? '' : 'none' })
    ;[['#tabE', 'E'], ['#tabD', 'D'], ['#tabS', 'S']].forEach(([b, v]) =>
      $(b).className = 'btn sm' + (v === view ? ' primary' : ''))
  })
  bind('#tabE', 'E'); bind('#tabD', 'D'); bind('#tabS', 'S')
}

init()
