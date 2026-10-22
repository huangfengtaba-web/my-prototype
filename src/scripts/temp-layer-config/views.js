/* ================= 渲染：外框 ================= */
function render(){
  $('#content').innerHTML = `
    <div class="card np">
      <div style="padding:0 24px">
        <div class="tabs">
          <div class="tab ${state.tab==='display'?'on':''}" onclick="switchTab('display')">设备温层展示<span class="cnt">${D.equips.length}</span></div>
          <div class="tab ${state.tab==='config'?'on':''}" onclick="switchTab('config')">Capability 温层配置<span class="cnt">${D.caps.length}</span></div>
        </div>
      </div>
      ${state.tab==='display' ? viewDisplay() : viewConfig()}
    </div>`;
  if(state.cmt) bindTips();
}

function switchTab(t){ state.tab=t; state.kw=''; state.fCap=''; state.tMin=''; state.tMax=''; state.fCfgCap=''; render(); }
function readDisp(){
  state.kw=($('#kwInput').value||'').trim();
  state.fCap=($('#dispCap_input').value||'').trim();
  state.tMin=($('#tMin').value||'').trim();
  state.tMax=($('#tMax').value||'').trim();
}
function queryDisp(){ readDisp(); state.page=1; render(); }
function resetDisp(){ state.kw=''; state.fCap=''; state.tMin=''; state.tMax=''; state.page=1; render(); }

/* ================= 视图 1：展示 ================= */
function viewDisplay(){
  const list = currentList();
  const re = buildRe(state.kw.trim());
  const total = list.length, maxPage=Math.max(1,Math.ceil(total/PAGE_SIZE));
  if(state.page>maxPage) state.page=maxPage;
  const rows = list.slice((state.page-1)*PAGE_SIZE, state.page*PAGE_SIZE);
  const kwTag = re ? `<span class="tag processing" style="margin-right:6px">通配 ${esc(state.kw.trim())}</span>` : '';

  return `
  <div style="padding:16px 24px 24px">
    <div class="toolbar">
      <input class="inp" id="kwInput" placeholder="搜索 EQUIP_ID / RECIPE_ID（支持 * 通配，如 RCP_A*）" value="${esc(state.kw)}">
      ${ssHTML('dispCap', state.fCap, D.capMaster, '全部 Capability')}
      <span style="display:inline-flex;align-items:center;gap:4px">温度
        <input class="inp" id="tMin" style="width:72px" placeholder="min" value="${esc(state.tMin)}"> ~
        <input class="inp" id="tMax" style="width:72px" placeholder="max" value="${esc(state.tMax)}"> ℃
      </span>
      <button class="btn" onclick="queryDisp()">查询</button>
      <button class="btn" onclick="resetDisp()">重置</button>
      <span id="rowCount">${kwTag}<span class="note">共 ${total} 条</span></span>
      <span class="sp"></span>
      <button class="btn" onclick="openImport()">⬆ CSV 导入</button>
      <button class="btn primary" onclick="openEquipModal(null)">+ 新增设备记录</button>
    </div>
    <table class="tbl">
      <thead><tr>
        <th class="num">#</th>
        <th>EQUIP_ID ${tip('设备编号，来自 EAP 设备主数据；同编号唯一，重复导入按覆盖处理。')}</th>
        <th>RECIPE_ID_LIST ${tip('该设备可加工的 Recipe 列表，源系统以分隔符拼接同步；排程时按 Recipe 命中设备。列表中的 Recipe 本身也可为通配模式（如 RCP_A* 表示所有 RCP_A 开头的配方），以橙色虚线标签「⊛」显示。搜索框亦支持 * 通配定位。')}</th>
        <th>TEMPERATURE ${tip('设备温层当前温度（℃）。与 Capability 配置的温度区间比对，超出区间则不可排入。')}</th>
        <th>Capability</th>
        <th style="width:100px">操作</th>
      </tr></thead>
      <tbody id="dspBody">${rowsHtml(rows, re)}</tbody>
    </table>
    ${pagerHTML(total,maxPage)}
  </div>`;
}
function currentList(){
  const kw=state.kw.trim();
  const re=buildRe(kw);
  const tMin=state.tMin==='' ? null : parseInt(state.tMin);
  const tMax=state.tMax==='' ? null : parseInt(state.tMax);
  return D.equips.filter(e=>{
    let hit;
    if(re){
      hit = re.test(e.eqp) || e.recipes.some(r=>re.test(r));
    } else {
      const l=kw.toLowerCase();
      hit = !l || e.eqp.toLowerCase().includes(l) || e.recipes.join(',').toLowerCase().includes(l);
    }
    const tHit = (tMin===null||e.temp>=tMin) && (tMax===null||e.temp<=tMax);
    return hit && (!state.fCap || e.cap===state.fCap) && tHit;
  });
}

function rowsHtml(rows, re){
  if(!rows.length) return '<tr><td colspan="6"><div class="empty">暂无匹配数据</div></td></tr>';
  return rows.map((e,i)=>{
    const start=(state.page-1)*PAGE_SIZE+i+1;
    const shown=e.recipes.slice(0,3), rest=e.recipes.length-shown.length;
    return `<tr>
      <td class="num">${start}</td>
      <td><b>${esc(e.eqp)}</b></td>
      <td><div class="recips">${shown.map(r=>{
        const wild=/[*?]/.test(r);
        const m=re&&re.test(r)&&!wild;
        const cls=wild?'wild':(m?'match':'');
        const title=wild?'通配模式配方（如 RCP_A* 表示所有 RCP_A 开头的配方）':'';
        return `<span class="tag ${cls}" title="${title}">${wild?'⊛ ':''}${hlRecipe(r,re)}</span>`;
      }).join('')}${rest>0?`<span class="more">+${rest}</span>`:''}</div></td>
      <td>${e.temp} ℃</td>
      <td><span class="tag processing">${esc(e.cap)}</span></td>
      <td><button class="btn link" onclick="openEquipModal('${esc(e.eqp)}')">修改</button></td>
    </tr>`;
  }).join('');
}

function pagerHTML(total,maxPage){
  if(total<=PAGE_SIZE) return `<div id="pagerBox" class="note" style="padding:12px 0 0">共 ${total} 条 · 单页展示</div>`;
  return `<div id="pagerBox" style="display:flex;align-items:center;gap:8px;padding:14px 0 0">
    <span class="note">共 ${total} 条 · 第 ${state.page}/${maxPage} 页</span>
    <span style="margin-left:auto;display:flex;gap:6px">
      <button class="btn sm" ${state.page<=1?'disabled':''} onclick="state.page--;refreshDisplayRows()">上一页</button>
      <button class="btn sm" ${state.page>=maxPage?'disabled':''} onclick="state.page++;refreshDisplayRows()">下一页</button>
    </span></div>`;
}
function refreshDisplayRows(){
  const host=$('#dspBody'); if(!host) return;
  const re=buildRe(state.kw.trim());
  const list=currentList(), total=list.length, maxPage=Math.max(1,Math.ceil(total/PAGE_SIZE));
  if(state.page>maxPage) state.page=maxPage;
  const rows=list.slice((state.page-1)*PAGE_SIZE,state.page*PAGE_SIZE);
  host.innerHTML=rowsHtml(rows, re);
  const old=document.querySelector('#pagerBox'); if(old) old.remove();
  host.closest('table').insertAdjacentHTML('afterend', pagerHTML(total,maxPage));
  const rc=$('#rowCount');
  if(rc) rc.innerHTML=(re?`<span class="tag processing" style="margin-right:6px">通配 ${esc(state.kw.trim())}</span>`:'')+'<span class="note">共 '+total+' 条</span>';
}

function doSync(btn){
  btn.disabled=true; btn.textContent='同步中…';
  setTimeout(()=>{
    D.sync.last=now();
    toast('同步完成：7 台设备温层数据已更新');
    render();
  },900);
}