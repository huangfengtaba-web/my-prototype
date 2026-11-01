// CIM 集成中心：MES/QTMS/ELR/SDR 四个子系统对接视图（真数据 mock 版）
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('cim')

async function init() {
  try {
    const [ov, mes, qtms, elr, sdr] = await Promise.all([
      fetch(`${API_BASE}/api/cim/overview`).then((r) => r.json()),
      fetch(`${API_BASE}/api/cim/mes`).then((r) => r.json()),
      fetch(`${API_BASE}/api/cim/qtms`).then((r) => r.json()),
      fetch(`${API_BASE}/api/cim/elr`).then((r) => r.json()),
      fetch(`${API_BASE}/api/cim/sdr`).then((r) => r.json()),
    ])
    $('#ovTbl tbody').innerHTML = ov.modules.map((m) => `<tr>
      <td><b>${m.name}</b></td><td>${m.cn}</td><td>${m.role}</td>
      <td><span class="tag ${m.connected ? 'success' : 'default'}">${m.connected ? '已对接（mock）' : '路线图'}</span></td>
      <td>${m.api ? `<code>${m.api}</code>` : '—'}</td></tr>`).join('')

    $('#mesTbl tbody').innerHTML = mes.lots.map((l) => `<tr>
      <td><b>${l.lot}</b></td><td>${l.mes_priority}</td><td>${l.product}</td><td>${l.step}</td>
      <td>${l.qty}</td>
      <td>${l.pilot ? '<span class="tag processing">Pilot</span>' : '—'}</td>
      <td>${l.queue ? '<span class="tag warning">Queue</span>' : '—'}</td>
      <td>${l.hold ? `<span class="tag error">Hold ${l.hold_reason}</span>` : '—'}</td>
      <td>${l.tags.join(' / ') || '—'}</td></tr>`).join('')

    $('#qtmsTbl tbody').innerHTML = qtms.loops.map((l) => `<tr>
      <td>${l.loop}</td><td>${l.water}</td><td>${l.current}</td>
      <td>${l.over ? '<span class="tag error">超水位</span>' : '<span class="tag success">正常</span>'}</td>
      <td>${l.over_lots.join('、') || '—'}</td></tr>`).join('')

    $('#elrTbl tbody').innerHTML = elr.lots.map((l) => `<tr>
      <td><b>${l.lot}</b></td><td>${l.type}</td>
      <td>${l.checks_passed}/${l.checks_total}</td>
      <td>${l.ood ? '<span class="tag error">OOD 卡控</span>' : '—'}</td>
      <td>${l.failed.join('；') || '—'}</td>
      <td>${l.runpath.join('、')}</td></tr>`).join('')

    $('#sdrTbl tbody').innerHTML = sdr.commands.map((c) => `<tr>
      <td>${c.command_id}</td><td><b>${c.reticle}</b></td><td>${c.from}</td><td>${c.to}</td>
      <td>${c.vehicle}</td><td>${c.lot || '—'}</td>
      <td><span class="tag ${c.priority === 'High' ? 'error' : 'default'}">${c.priority}</span></td>
      <td>${c.pod}</td><td><span class="tag processing">${c.status}</span></td></tr>`).join('')
      || '<tr><td colspan="9" style="color:var(--colorTextQuaternary)">暂无指令（先跑一次求解）</td></tr>'
  } catch (e) {
    $('#ovTbl tbody').innerHTML =
      `<tr><td colspan="5" style="color:var(--colorError)">后端不可达：${e.message}</td></tr>`
  }
}

init()
