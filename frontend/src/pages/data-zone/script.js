// 数据接入页（真数据）：源表总览 + 客户字段字典（litho系统.xlsx）
import { API_BASE, $, mountShell } from '../_shared/shell.js'

mountShell('data-zone')

const SOURCES = [
  ['SOURCE_LOT / SOURCE_PRODUCT_FLOW', 'Lot、流程、优先级、产品', '前处理', '✅ mock 已入模'],
  ['SOURCE_EQP_STATUS / Capability', '机台状态、Capability、Running Mode', '前处理', '✅ mock 已入模'],
  ['SOURCE_LOT_REMAIN_QTIME', 'Remain QTime 余量', '前处理 + 算法', '✅ mock 已入模'],
  ['SOURCE_RETICLE_STATUS', '光罩五态/计片/计时/储位', '前处理 + 算法', '✅ mock 已入模'],
  ['QTMS', 'Loop 放货水位', '后处理校验', '✅ mock 已入模（逐 Loop）'],
  ['MES', 'Priority/Hold/Queue/Pilot 标识', '前处理', '✅ mock 已入模（/cim MES 视图）'],
  ['ELR / APC', '24 项工艺校验、OOD', '前处理（RunPath）', '✅ mock 已入模（/cim ELR 视图）'],
  ['SDR/EMA', '光罩搬送指令执行', '后处理输出', '✅ 指令队列已生成（/cim SDR 视图）'],
  ['Chuck / 大小片', '双工件台绑定、首尾片', '算法（R2）', '🟡 相容惩罚已入模，真数据待接'],
  ['Stacking Bond', '首层绑定、30 天负载', '算法（R2）', '🟡 RunPath 白名单已入模'],
  ['Doma / Chamber', '剂量 Mapping 绑定', '前处理 + 算法', '✅ mock 已入模（Chamber 下界）'],
]

async function init() {
  $('#srcTbl tbody').innerHTML = SOURCES.map(([s, c, p, st]) => {
    const cls = st.startsWith('✅') ? 'success' : 'warning'
    return `<tr><td><b>${s}</b></td><td>${c}</td><td>${p}</td>
      <td><span class="tag ${cls}">${st}</span></td></tr>`
  }).join('')
  try {
    const { pages } = await (await fetch(`${API_BASE}/api/cim/dictionary`)).json()
    $('#pageTabs').innerHTML = pages.map((p, i) =>
      `<button class="btn sm ${i === 0 ? 'primary' : ''}" data-i="${i}">${p.page}</button>`).join(' ')
    const show = (i) => {
      const p = pages[i]
      $('#dictBody').innerHTML = `
        <div style="margin:8px 0"><span class="tag processing">真系统覆盖位置</span>
          <span style="font-size:12px">${p.source}</span></div>
        ${p.fields.length ? `<div class="tscroll" style="max-height:260px"><table class="dt">
          <thead><tr><th>#</th><th>字段（客户口径）</th></tr></thead>
          <tbody>${p.fields.map((f, j) => `<tr><td>${j + 1}</td><td>${f}</td></tr>`).join('')}</tbody>
        </table></div>` : '<div class="empty">源表暂无数据（缺口，待客户补数）</div>'}
        ${p.kpi ? `<div style="margin-top:6px"><span class="tag processing">KPI 指标</span> ${p.kpi.join(' / ')}</div>` : ''}
        ${p.states ? `<div style="margin-top:6px"><span class="tag processing">状态图例</span> ${p.states.join(' / ')}</div>` : ''}
        ${p.legend ? `<div style="margin-top:6px"><span class="tag processing">图例</span> ${p.legend.join(' / ')}</div>` : ''}
        ${p.sources ? `<div style="margin-top:6px"><span class="tag processing">机台来源</span> ${p.sources.join(' / ')}</div>` : ''}`
      document.querySelectorAll('#pageTabs button').forEach((b, j) =>
        b.className = 'btn sm' + (j === i ? ' primary' : ''))
    }
    show(0)
    document.querySelectorAll('#pageTabs button').forEach((b) =>
      b.addEventListener('click', () => show(Number(b.dataset.i))))
  } catch {
    $('#dictBody').innerHTML = '<div class="empty">后端不可达</div>'
  }
}

init()
