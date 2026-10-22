/* ================= 评论模式 ================= */
function bindTips(){
  document.querySelectorAll('.q').forEach(el=>{
    el.onclick=ev=>{
      ev.stopPropagation();
      document.querySelectorAll('.bubble').forEach(b=>b.remove());
      const b=document.createElement('div');
      b.className='bubble';
      b.innerHTML='<div class="bt">字段说明</div><div class="bd">'+esc(el.dataset.tip)+'</div>';
      document.body.appendChild(b);
      const r=el.getBoundingClientRect();
      b.style.left=Math.min(window.innerWidth-320, r.left)+'px';
      b.style.top=(r.bottom+8)+'px';
      setTimeout(()=>document.addEventListener('click',()=>b.remove(),{once:true}),0);
    };
  });
}

/* ================= 启动 ================= */
$('#cmtBtn').onclick=()=>{
  state.cmt=!state.cmt;
  document.body.classList.toggle('cmt-on', state.cmt);
  $('#cmtBtn').classList.toggle('primary', state.cmt);
  if(state.cmt) bindTips();
};
function clock(){ $('#clock').textContent=new Date().toLocaleString('zh-CN',{hour12:false}); }
render(); clock(); setInterval(clock,1000);