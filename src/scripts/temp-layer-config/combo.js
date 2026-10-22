/* ================= 通用模糊搜索下拉（列表筛选用） ================= */
function ssHTML(id, value, items, placeholder){
  const opts = items.map(v=>`<div class="combo-item" data-v="${esc(v)}" onclick="ssPick('${id}','${esc(v)}')">${esc(v)}</div>`).join('');
  return `<div class="combo" id="${id}">
    <input class="inp combo-input" id="${id}_input" placeholder="${esc(placeholder||'')}" value="${esc(value||'')}"
      readonly autocomplete="off" onfocus="ssOpen('${id}')" onclick="ssOpen('${id}')"
      oninput="ssFilter('${id}',this.value)" onkeydown="ssKey(event,'${id}')">
    <div class="combo-list" id="${id}_list">${opts||'<div class="combo-empty">无匹配</div>'}</div>
  </div>`;
}
function ssOpen(id){
  document.querySelectorAll('.combo-list.open').forEach(l=>l.classList.remove('open'));
  const l=$('#'+id+'_list'); if(l) l.classList.add('open');
}
function ssFilter(id, kw){
  const l=$('#'+id+'_list'); if(!l) return;
  kw=(kw||'').trim().toLowerCase();
  let any=false;
  l.querySelectorAll('.combo-item').forEach(el=>{
    const hit=!kw || el.dataset.v.toLowerCase().includes(kw);
    el.style.display=hit?'':'none';
    if(hit) any=true;
  });
  let empty=l.querySelector('.combo-empty');
  if(!any){ if(!empty) l.insertAdjacentHTML('beforeend','<div class="combo-empty">无匹配</div>'); }
  else if(empty) empty.remove();
  ssOpen(id);
}
function ssPick(id,v){
  const inp=$('#'+id+'_input'); if(inp) inp.value=v;
  const l=$('#'+id+'_list'); if(l) l.classList.remove('open');
}
function ssKey(e,id){
  const items=[...document.querySelectorAll('#'+id+'_list .combo-item')].filter(el=>el.style.display!=='none');
  let hl=parseInt(($('#'+id).dataset.hl)||'-1');
  if(e.key==='ArrowDown'){ e.preventDefault(); hl=Math.min(items.length-1,hl+1); }
  else if(e.key==='ArrowUp'){ e.preventDefault(); hl=Math.max(0,hl-1); }
  else if(e.key==='Enter'){ e.preventDefault(); if(items[hl]) ssPick(id,items[hl].dataset.v); return; }
  else if(e.key==='Escape'){ const l=$('#'+id+'_list'); if(l) l.classList.remove('open'); return; }
  items.forEach((el,i)=>el.classList.toggle('hl',i===hl));
  $('#'+id).dataset.hl=hl;
}
document.addEventListener('click', e=>{
  document.querySelectorAll('.combo-list.open').forEach(l=>{
    if(!l.closest('.combo').contains(e.target)) l.classList.remove('open');
  });
});