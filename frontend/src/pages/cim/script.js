// CIM 集成中心：MES/QTMS/ELR/SDR 四个子系统（可操作：Hold/同步/水位/OOD/指令下发）
import { API_BASE, $, mountShell, statusTag } from '../_shared/shell.js'

mountShell('cim')

async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status} ${(await res.json()).detail || ''}`)
  return res.json()
}

function toast(msg, ok = true) {
  const el = $('#cimToast')
  el.textContent = msg
  el.className = 'run-state ' + (ok ? 'ok' : 'err')
  el.style.display = 'block'
  clearTimeout(el._t)
  el._t = setTimeout(() => { el.style.display = 'none' }, 4000)
}

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

    $('#mesSync').textContent = `最近同步：${mes.last_sync || '—'} · 同步对象：${(mes.synced_objects || []).join('、')}`
    $('#mesSyncBtn').addEventListener('click', async () => {
      $('#mesSyncBtn').disabled = true
      try {
        const d = await post('/api/cim/mes/sync', {})
        toast(`MES 同步完成：${d.synced} 个 Lot · ${d.last_sync}`)
        init()
      } catch (e) { toast(e.message, false) }
    })
    $('#mesTbl tbody').innerHTML = mes.lots.map((l) => `<tr>
      <td><b>${l.lot}</b></td><td>${l.mes_priority}</td><td>${l.product}</td><td>${l.step}</td>
      <td>${l.qty}</td>
      <td>${l.pilot ? '<span class="tag processing">Pilot</span>' : '—'}</td>
      <td>${l.queue ? '<span class="tag warning">Queue</span>' : '—'}</td>
      <td>${l.hold ? `<span class="tag error">${l.hold_reason}</span>` : '—'}</td>
      <td>${l.tags.join(' / ') || '—'}</td>
      <td><button class="btn sm ${l.hold && l.hold_reason.startsWith('MES') ? '' : 'primary'}"
        data-hold="${l.lot}" data-to="${l.hold && l.hold_reason.startsWith('MES') ? 'release' : 'hold'}">
        ${l.hold && l.hold_reason.startsWith('MES') ? '释放' : 'Hold'}</button></td></tr>`).join('')
    document.querySelectorAll('#mesTbl [data-hold]').forEach((b) =>
      b.addEventListener('click', async () => {
        b.disabled = true
        try {
          const d = await post('/api/cim/mes/hold', { lot: b.dataset.hold, hold: b.dataset.to === 'hold' })
          toast(`${d.lot}：${d.hold ? '已 MES Hold' : '已释放'}——${d.note}`)
          init()
        } catch (e) { toast(e.message, false) }
      }))
    $('#mesSyncBtn').addEventListener('click', async () => {
      $('#mesSyncBtn').disabled = true
      try {
        const d = await post('/api/cim/mes/sync')
        toast(`MES 同步完成：${d.synced} 个 Lot · ${d.last_sync}`)
        init()
      } catch (e) { toast(e.message, false) }
    })

    $('#qtmsTbl tbody').innerHTML = qtms.loops.map((l) => `<tr>
      <td>${l.loop}</td>
      <td><input class="inp" style="width:70px" data-loop="${l.loop}" value="${l.water}"></td>
      <td>${l.current}</td>
      <td>${l.over ? '<span class="tag error">超水位</span>' : '<span class="tag success">正常</span>'}</td>
      <td>${l.over_lots.join('、') || '—'}</td>
      <td><button class="btn sm" data-water="${l.loop}">保存水位</button></td></tr>`).join('')
    document.querySelectorAll('#qtmsTbl [data-water]').forEach((b) =>
      b.addEventListener('click', async () => {
        const loop = b.dataset.water
        const water = Number(document.querySelector(`input[data-loop="${loop}"]`).value)
        b.disabled = true
        try {
          const d = await post('/api/cim/qtms/water', { loop, water })
          toast(`${loop}：水位已设为 ${d.water}——${d.note}`)
          init()
        } catch (e) { toast(e.message, false) }
      }))

    $('#elrTbl tbody').innerHTML = elr.lots.map((l) => `<tr>
      <td><b>${l.lot}</b></td><td>${l.type}</td>
      <td>${l.checks_passed}/${l.checks_total}</td>
      <td>${l.ood ? '<span class="tag error">OOD 卡控</span>' : '—'}</td>
      <td>${l.failed.join('；') || '—'}</td>
      <td>${l.runpath.join('、')}</td>
      <td><button class="btn sm ${l.ood ? '' : 'primary'}" data-ood="${l.lot}"
        data-to="${l.ood ? 'clear' : 'ood'}">${l.ood ? '解除 OOD' : '注入 OOD'}</button></td></tr>`).join('')
    document.querySelectorAll('#elrTbl [data-ood]').forEach((b) =>
      b.addEventListener('click', async () => {
        b.disabled = true
        try {
          const d = await post('/api/cim/elr/check', {
            lot: b.dataset.ood, ood: b.dataset.to === 'ood',
            failed: b.dataset.to === 'ood' ? ['CHK-07 OOD 计时'] : [],
          })
          toast(`${d.lot}：${d.ood ? '已注入 OOD（整批卡控）' : '已解除 OOD'}——${d.note}`)
          init()
        } catch (e) { toast(e.message, false) }
      }))

    $('#sdrMeta').textContent = sdr.note + (sdr.issued_at ? ` · 下发时间 ${sdr.issued_at}` : '')
    $('#sdrTbl tbody').innerHTML = (sdr.commands || []).map((c) => `<tr>
      <td>${c.command_id}</td><td><b>${c.reticle}</b></td><td>${c.from}</td><td>${c.to}</td>
      <td>${c.vehicle}</td><td>${c.lot || '—'}</td>
      <td><span class="tag ${c.priority === 'High' ? 'error' : 'default'}">${c.priority}</span></td>
      <td>${c.pod}</td>
      <td><span class="tag ${c.status === 'issued' ? 'success' : 'processing'}">${c.status}</span></td></tr>`).join('')
      || '<tr><td colspan="9" style="color:var(--colorTextQuaternary)">暂无指令（先跑一次求解）</td></tr>'
    $('#sdrIssueBtn').style.display = (sdr.commands || []).length ? '' : 'none'
  } catch (e) {
    $('#ovTbl tbody').innerHTML =
      `<tr><td colspan="5" style="color:var(--colorError)">后端不可达：${e.message}</td></tr>`
  }
}

async function issueSdr() {
  $('#sdrIssueBtn').disabled = true
  try {
    const d = await post('/api/cim/sdr/issue', {})
    toast(`SDR 指令已下发：${d.issued} 条（run ${d.run_id}）`)
    init()
  } catch (e) { toast(e.message, false) }
}

init()
