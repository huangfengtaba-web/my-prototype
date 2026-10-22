/* ================= 视图 2：Capability 配置 ================= */
function viewConfig(){
  return `
  <div style="padding:16px 24px 24px">
    <div class="toolbar">
      ${ssHTML('cfgCap', state.fCfgCap, D.capMaster, '全部 Capability')}
      <button class="btn" onclick="queryCfg()">查询</button>
      <button class="btn" onclick="resetCfg()">重置</button>
      <span id="cfgCount"><span class="note">共 ${cfgList().length} 条</span></span>
      <span class="sp"></span>
      <button class="btn primary" onclick="openCapModal()">+ 新增配置</button>
    </div>
    <table class="tbl">
      <thead><tr>
        <th class="num">#</th>
        <th style="min-width:170px">Capability ${tip('下拉单选，取值来自 Capability 主数据，支持输入模糊搜索。')}</th>
        <th>TEM START ${tip('该 Capability 可控温度的下限（℃）。')}</th>
        <th>TEM END ${tip('该 Capability 可控温度的上限（℃），需大于 TEM START。')}</th>
        <th>花费时间 (s) ${tip('在该热板的 [TEM START, TEM END] 区间内完成一次温度切换所需的标准耗时（秒），用于排程换温成本。')}</th>
        <th>Update Time</th>
        <th>Update User</th>
        <th style="width:120px">操作</th>
      </tr></thead>
      <tbody id="cfgBody">${cfgRows()}</tbody>
    </table>
  </div>`;
}

const capKey = c => c.cap;
function cfgList(){
  return D.caps.filter(c=>!state.fCfgCap || c.cap===state.fCfgCap);
}
function readCfg(){ state.fCfgCap=($('#cfgCap_input').value||'').trim(); }
function queryCfg(){ readCfg(); render(); }
function resetCfg(){ state.fCfgCap=''; render(); }
function cfgRows(){
  const list=cfgList();
  if(!list.length) return '<tr><td colspan="8"><div class="empty">'+(D.caps.length?'当前筛选无匹配配置':'暂无配置，请点击「新增配置」')+'</div></td></tr>';
  return list.map((c,i)=>{
    const key=capKey(c);
    if(state.editingKey===key){
      const d=state.dirty;
      return `<tr>
        <td class="num">${i+1}</td>
        <td><b>${esc(c.cap)}</b></td>
        <td><input class="inp" style="width:88px" value="${d.start}" oninput="state.dirty.start=this.value"></td>
        <td><input class="inp" style="width:88px" value="${d.end}" oninput="state.dirty.end=this.value"></td>
        <td><input class="inp" style="width:96px" value="${d.cost}" oninput="state.dirty.cost=this.value"></td>
        <td class="note">保存后更新</td>
        <td class="note">${curUser}</td>
        <td>
          <button class="btn link" onclick="saveCap('${key}')">保存</button>
          <button class="btn link" onclick="cancelCap()">取消</button>
        </td>
      </tr>`;
    }
    return `<tr>
      <td class="num">${i+1}</td>
      <td><b>${esc(c.cap)}</b></td>
      <td>${c.start} ℃</td>
      <td>${c.end} ℃</td>
      <td>${c.cost} s</td>
      <td class="note">${c.ut}</td>
      <td>${esc(c.uu)}</td>
      <td>
        <button class="btn link" onclick="editCap('${key}')">编辑</button>
        <button class="btn link danger" onclick="delCap('${key}')">删除</button>
      </td>
    </tr>`;
  }).join('');
}
function editCap(key){
  const c=D.caps.find(x=>capKey(x)===key);
  state.editingKey=key;
  state.dirty={start:c.start,end:c.end,cost:c.cost};
  render();
}
function cancelCap(){ state.editingKey=null; state.dirty={}; render(); }
function saveCap(key){
  const d=state.dirty;
  const s=parseInt(d.start), e=parseInt(d.end), ct=parseInt(d.cost);
  if(isNaN(s)||isNaN(e)||isNaN(ct)) return toast('温度与花费时间必须为数字',true);
  if(s>=e) return toast('TEM START 必须小于 TEM END',true);
  if(ct<=0) return toast('花费时间需大于 0',true);
  const c=D.caps.find(x=>capKey(x)===key);
  Object.assign(c,{start:s,end:e,cost:ct,ut:now().slice(0,16),uu:curUser});
  state.editingKey=null; state.dirty={};
  toast('已保存：'+c.cap); render();
}
function delCap(key){
  const c=D.caps.find(x=>capKey(x)===key)||{};
  showModal('删除配置','确定删除 <b>'+esc(c.cap)+'</b> 的温层配置？删除后该 Capability 不参与换温成本计算。',
    '<button class="btn" onclick="closeModal()">取消</button><button class="btn primary" style="background:var(--colorError);border-color:var(--colorError)" onclick="doDelCap(\''+key+'\')">确认删除</button>');
}
function doDelCap(key){
  const c=D.caps.find(x=>capKey(x)===key)||{};
  D.caps=D.caps.filter(x=>capKey(x)!==key);
  closeModal(); toast('已删除：'+c.cap); render();
}