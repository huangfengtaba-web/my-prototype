/* ================= 工具 ================= */
const $ = s=>document.querySelector(s);
const esc = s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const capOf = eqp => (D.equips.find(e=>e.eqp===eqp)||{}).cap || 'Capability1';
function toast(msg, isErr){
  const el=document.createElement('div');
  el.className='toast'+(isErr?' err':'');
  el.innerHTML=(isErr?'⚠️':'✅')+' <span>'+esc(msg)+'</span>';
  document.body.appendChild(el);
  setTimeout(()=>el.remove(), 2200);
}
function now(){const d=new Date();const p=n=>String(n).padStart(2,'0');
  return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds());}
const curUser='huangjw';
function tip(txt){return '<span class="q" data-tip="'+esc(txt).replace(/"/g,'&quot;')+'">?</span>';}
function tempVisual(t){
  const cls = t>=35?'hot':(t>=28?'warm':'');
  const pct = Math.min(100, Math.max(8, Math.round((t-15)/(45-15)*100)));
  return '<span class="temp"><span class="bar '+cls+'"><i style="width:'+pct+'%"></i></span>'+t+' <em>℃</em></span>';
}
function syncCapsFromEquip(){
  // Capability 与设备数量的关联展示用（Capability 配置里展示覆盖设备数）
  return D.equips.map(e=>capOf(e.eqp));
}

/* ================= 通配符匹配（RECIPE_ID_LIST 搜索） ================= */
// 仅当关键字含 * 时按 glob 通配：* 转 .*，并自动锚定首尾；其余字符做正则转义。
function buildRe(kw){
  if(!kw || !kw.includes('*')) return null;
  const esc = kw.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*');
  try { return new RegExp('^'+esc+'$', 'i'); } catch(e){ return null; }
}
// 命中关键字时，返回高亮后的 Recipe 文本（仅高亮匹配子串）
function hlRecipe(r, re){
  if(!re) return esc(r);
  const m = re.exec(r);
  if(!m) return esc(r);
  const s=m.index, e=m.index+m[0].length;
  return esc(r.slice(0,s))+'<mark class="hl">'+esc(r.slice(s,e))+'</mark>'+esc(r.slice(e));
}