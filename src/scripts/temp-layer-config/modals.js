/* ================= 通用弹窗 ================= */
function showModal(title, body, footer, wide){
  $('#modalRoot').innerHTML=`
    <div class="overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal ${wide?'wide':''}">
        <div class="modal-h"><span class="t">${esc(title)}</span><span class="x" onclick="closeModal()">✕</span></div>
        <div class="modal-b">${body}</div>
        <div class="modal-f">${footer}</div>
      </div>
    </div>`;
}
function closeModal(){ $('#modalRoot').innerHTML=''; }

/* ================= 弹窗：新增 / 修改设备 ================= */
function openEquipModal(eqp){
  const isEdit = !!eqp;
  const e = isEdit ? D.equips.find(x=>x.eqp===eqp) : {eqp:'',recipes:[],temp:23};
  const body = `
    <div class="field"><div class="lab"><i>*</i>EQUIP_ID</div>
      <input class="inp" id="f_eqp" style="width:220px" value="${esc(e.eqp)}" ${isEdit?'readonly':''} placeholder="如 SC08">
      <span class="note">${isEdit?'设备编号不可修改':'唯一，重复则提示已存在'}</span></div>
    <div class="field" style="align-items:flex-start"><div class="lab" style="padding-top:6px"><i>*</i>RECIPE_ID_LIST</div>
      <div>
        <textarea class="inp" id="f_recipes" style="width:360px;height:70px" placeholder="多个 Recipe 用逗号分隔，如 RCP_A,RCP_B">${esc(e.recipes.join(','))}</textarea>
        <div class="hint">支持逗号 / 竖线 / 分号分隔；保存时自动去重</div>
      </div></div>
    <div class="field"><div class="lab"><i>*</i>TEMPERATURE</div>
      <input class="inp" id="f_temp" style="width:120px" value="${e.temp}"> <span class="note">℃　范围 15 ~ 45</span></div>
    <div class="err" id="f_err"></div>`;
  showModal(isEdit?'修改设备温层记录':'新增设备温层记录', body,
    `<button class="btn" onclick="closeModal()">取消</button>
     <button class="btn primary" onclick="submitEquip(${isEdit?"'"+eqp+"'":'null'})">${isEdit?'保存':'确定新增'}</button>`);
}

function submitEquip(eqp){
  const id=$('#f_eqp').value.trim().toUpperCase();
  const raw=$('#f_recipes').value.trim();
  const t=parseInt($('#f_temp').value);
  const err=$('#f_err');
  if(!id) return err.textContent='请输入 EQUIP_ID';
  if(!raw) return err.textContent='请至少填写一个 RECIPE_ID';
  if(isNaN(t)||t<15||t>45) return err.textContent='TEMPERATURE 需为 15~45 之间的数字';
  const recipes=[...new Set(raw.split(/[,，;；|]/).map(s=>s.trim().toUpperCase()).filter(Boolean))];
  if(eqp){
    const e=D.equips.find(x=>x.eqp===eqp);
    Object.assign(e,{recipes,temp:t,src:'手工维护'});
    toast('已修改 '+eqp);
  }else{
    if(D.equips.some(x=>x.eqp===id)) return err.textContent='EQUIP_ID 已存在，请通过「修改」维护';
    D.equips.push({eqp:id, cap:'Capability1', recipes, temp:t, src:'手工维护'});
    toast('已新增 '+id);
  }
  closeModal(); render();
}

/* ================= 弹窗：CSV 导入 ================= */
function openImport(){
  const body=`
    <div class="drop" onclick="document.getElementById('csvFile').click()">
      <div class="ic">📄</div>
      <div class="m">点击选择 CSV 文件，或将文件拖拽到此处</div>
      <div class="s">列顺序：EQUIP_ID, RECIPE_ID_LIST, TEMPERATURE（首行可为表头）</div>
    </div>
    <input type="file" id="csvFile" accept=".csv,text/csv" style="display:none" onchange="parseCsv(this)">
    <div class="hint" style="margin-top:10px">RECIPE_ID_LIST 支持 <code>,</code> <code>|</code> <code>;</code> 分隔；已存在 EQUIP_ID 按<b>覆盖更新</b>处理。</div>
    <div id="csvResult"></div>`;
  showModal('CSV 导入设备温层','<div>'+body+'</div>',
    `<button class="btn" onclick="downloadTpl()">下载模板</button>
     <span style="flex:1"></span>
     <button class="btn" onclick="closeModal()">取消</button>
     <button class="btn primary" id="csvOk" disabled onclick="confirmImport()">确认导入</button>`, true);
}

let csvParsed=[];
function parseCsv(input){
  const f=input.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=()=>{
    let txt=String(rd.result).replace(/^\uFEFF/,'');
    const lines=txt.split(/\r?\n/).filter(l=>l.trim());
    if(!lines.length) return $('#csvResult').innerHTML='<div class="err">文件为空</div>';
    const head=lines[0].toLowerCase();
    const startIdx = head.includes('equip')?1:0;
    csvParsed=[]; let bad=0;
    for(let i=startIdx;i<lines.length;i++){
      const cols=lines[i].split(',').map(s=>s.trim().replace(/^"|"$/g,''));
      const [id,rc,tp]=cols;
      const t=parseInt(tp);
      const ok=!!id && !!rc && !isNaN(t);
      if(!ok) bad++;
      csvParsed.push({eqp:(id||'').toUpperCase(), recipes:(rc||'').split(/[,，;；|]/).map(s=>s.trim().toUpperCase()).filter(Boolean),
        temp:t, ok});
    }
    const exist=csvParsed.filter(r=>r.ok && D.equips.some(x=>x.eqp===r.eqp)).length;
    const add=csvParsed.filter(r=>r.ok && !D.equips.some(x=>x.eqp===r.eqp)).length;
    $('#csvResult').innerHTML=`
      <div style="display:flex;gap:8px;margin:14px 0 8px;align-items:center">
        <span class="tag success">可导入 ${csvParsed.filter(r=>r.ok).length}</span>
        <span class="tag processing">新增 ${add}</span>
        <span class="tag warning">覆盖 ${exist}</span>
        ${bad?`<span class="tag error">异常行 ${bad}</span>`:''}
        <span class="note" style="margin-left:auto">${esc(f.name)}</span>
      </div>
      <div class="preview"><table class="tbl">
        <thead><tr><th>行</th><th>EQUIP_ID</th><th>RECIPE_ID_LIST</th><th>TEMPERATURE</th><th>校验</th></tr></thead>
        <tbody>${csvParsed.slice(0,20).map((r,i)=>`<tr>
          <td>${i+1}</td><td><b>${esc(r.eqp||'-')}</b></td>
          <td>${esc(r.recipes.join(', ')||'-')}</td>
          <td>${isNaN(r.temp)?'<span class="badge-err">-</span>':r.temp}</td>
          <td>${r.ok?'<span class="tag success">PASS</span>':(D.equips.some(x=>x.eqp===r.eqp)?'<span class="tag warning">WARN</span>':'<span class="tag error">FAIL</span>')}</td>
        </tr>`).join('')}</tbody>
      </table></div>
      ${csvParsed.length>20?`<div class="hint">仅预览前 20 行，共 ${csvParsed.length} 行</div>`:''}
      ${bad?`<div class="hint" style="color:var(--colorError)">存在 ${bad} 行字段缺失或温度非法，导入时将自动跳过</div>`:''}`;
    $('#csvOk').disabled = csvParsed.filter(r=>r.ok).length===0;
  };
  rd.readAsText(f,'UTF-8');
}

function confirmImport(){
  let add=0, upd=0, skip=0;
  csvParsed.forEach(r=>{
    if(!r.ok){ skip++; return; }
    const ex=D.equips.find(x=>x.eqp===r.eqp);
    if(ex){ Object.assign(ex,{recipes:r.recipes,temp:r.temp,src:'CSV 导入'}); upd++; }
    else { D.equips.push({eqp:r.eqp, cap:'Capability1', recipes:r.recipes,temp:r.temp,src:'CSV 导入'}); add++; }
  });
  closeModal();
  toast(`导入完成：新增 ${add} 条，覆盖 ${upd} 条${skip?`，跳过 ${skip} 条`:''}`);
  D.sync.last=now();
  render();
}

function downloadTpl(){
  const csv='EQUIP_ID,RECIPE_ID_LIST,TEMPERATURE\nSC08,"RCP_A|RCP_B",23\nSC09,"RCP_C",28\n';
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,\uFEFF'+encodeURIComponent(csv);
  a.download='equip_temp_layer_template.csv'; a.click();
  toast('模板已下载');
}

/* ================= 弹窗：新增 Capability 配置 ================= */
function openCapModal(){
  const cnt = c => D.caps.filter(x=>x.cap===c).length;
  const opts=D.capMaster.map(c=>`<div class="combo-item" data-v="${c}">
      ${c}${cnt(c)?`<span class="tick" style="color:var(--colorTextQuaternary)">已配 ${cnt(c)} 个温层</span>`:''}</div>`).join('');
  const body=`
    <div class="field">
      <div class="lab"><i>*</i>Capability</div>
      <div class="combo" id="comboCap" style="flex:1;max-width:340px">
        <input class="inp" id="capInput" placeholder="输入关键字搜索，或点击选择" autocomplete="off"
          onfocus="openCombo()" oninput="filterCombo(this.value)" onkeydown="comboKey(event)">
        <span class="arrow">▾</span>
        <div class="combo-list" id="capList">${opts}</div>
      </div>
      <span class="note">单选，支持模糊搜索</span>
    </div>
    <div class="field"><div class="lab"><i>*</i>TEM START</div>
      <input class="inp" id="c_start" style="width:110px" placeholder="90"> <span class="note">℃　温度下限</span></div>
    <div class="field"><div class="lab"><i>*</i>TEM END</div>
      <input class="inp" id="c_end" style="width:110px" placeholder="110"> <span class="note">℃　温度上限，需大于 TEM START</span></div>
    <div class="field"><div class="lab"><i>*</i>花费时间</div>
      <input class="inp" id="c_cost" style="width:110px" placeholder="120"> <span class="note">s　区间内一次温度切换标准耗时</span></div>
    <div class="err" id="c_err"></div>`;
  showModal('新增 Capability 温层配置', body,
    `<button class="btn" onclick="closeModal()">取消</button>
     <button class="btn primary" onclick="submitCap()">确定</button>`);
  setTimeout(()=>$('#capInput').focus(),50);
}

let comboVal='', comboHl=-1;
function openCombo(){ $('#capList').classList.add('open'); }
function filterCombo(v){
  comboVal=v; comboHl=-1;
  const kw=v.trim().toLowerCase();
  [...document.querySelectorAll('#capList .combo-item')].forEach(el=>{
    el.style.display = !kw || el.dataset.v.toLowerCase().includes(kw) ? 'flex':'none';
  });
  const anyVisible=[...document.querySelectorAll('#capList .combo-item')].some(el=>el.style.display!=='none');
  let empty=$('#capList .combo-empty');
  if(!anyVisible){
    if(!empty){ $('#capList').insertAdjacentHTML('beforeend','<div class="combo-empty">无匹配的 Capability</div>'); }
  } else if(empty) empty.remove();
  openCombo();
}
function pickCombo(v){
  if(!v || v.dataset.dis) return;
  $('#capInput').value=v.dataset.v; comboVal=v.dataset.v;
  $('#capList').classList.remove('open');
}
function comboKey(e){
  const items=[...document.querySelectorAll('#capList .combo-item')].filter(el=>el.style.display!=='none'&&!el.dataset.dis);
  if(e.key==='ArrowDown'){ e.preventDefault(); comboHl=Math.min(items.length-1,comboHl+1); items.forEach((el,i)=>el.classList.toggle('hl',i===comboHl)); }
  else if(e.key==='ArrowUp'){ e.preventDefault(); comboHl=Math.max(0,comboHl-1); items.forEach((el,i)=>el.classList.toggle('hl',i===comboHl)); }
  else if(e.key==='Enter'){ e.preventDefault(); if(items[comboHl]) pickCombo(items[comboHl]); }
  else if(e.key==='Escape'){ $('#capList').classList.remove('open'); }
}
document.addEventListener('click', e=>{
  const list=$('#capList'); if(!list) return;
  const item=e.target.closest('#capList .combo-item'); if(item){ pickCombo(item); return; }
  if(!e.target.closest('#comboCap')) list.classList.remove('open');
});

function submitCap(){
  const cap=($('#capInput').value||'').trim();
  const s=parseInt($('#c_start').value), en=parseInt($('#c_end').value), ct=parseInt($('#c_cost').value);
  const err=$('#c_err');
  if(!cap) return err.textContent='请选择 Capability';
  if(!D.capMaster.includes(cap)) return err.textContent='Capability 不在可选值范围内';
  if(D.caps.some(c=>c.cap===cap)) return err.textContent='该 Capability 已配置，请直接编辑';
  if(isNaN(s)||isNaN(en)) return err.textContent='请填写 TEM START / TEM END';
  if(s>=en) return err.textContent='TEM START 必须小于 TEM END';
  if(isNaN(ct)||ct<=0) return err.textContent='花费时间需为大于 0 的秒数';
  D.caps.push({cap,start:s,end:en,cost:ct,ut:now().slice(0,16),uu:curUser});
  closeModal(); toast('已新增配置：'+cap); render();
}