/* ================= 数据 ================= */
const D = {
  sync:{last:'2026-10-19 14:25:03', auto:'每 5 min', src:'EAP / MES'},
  equips:[
    {eqp:'SC01', cap:'Capability1', recipes:['RCP_A','RCP_B','RCP_C'], temp:23, src:'EAP'},
    {eqp:'SC02', cap:'Capability1', recipes:['RCP_A','RCP_C'],        temp:23, src:'EAP'},
    {eqp:'SC03', cap:'Capability2', recipes:['RCP_B','RCP_D'],        temp:35, src:'MES'},
    {eqp:'SC04', cap:'Capability1', recipes:['RCP_A','RCP_B','RCP_C*','RCP_D'], temp:28, src:'EAP'},
    {eqp:'SC05', cap:'Capability3', recipes:['RCP_C'],               temp:28, src:'MES'},
    {eqp:'SC06', cap:'Capability2', recipes:['RCP_A','RCP_D'],        temp:35, src:'EAP'},
    {eqp:'SC07', cap:'Capability3', recipes:['RCP_B'],               temp:23, src:'EAP'},
  ],
  // Capability 主数据（来自其他系统，作为下拉可配置值）
  capMaster:['Capability1','Capability2','Capability3','Capability4','Capability5','Capability6'],
  caps:[
    {cap:'Capability1', start:90,  end:110, cost:120, ut:'2026-10-18 14:20', uu:'huangjw'},
    {cap:'Capability2', start:100, end:120, cost:150, ut:'2026-10-17 09:05', uu:'zhangq'},
    {cap:'Capability3', start:80,  end:95,  cost:90,  ut:'2026-10-15 18:42', uu:'liwei'},
    {cap:'Capability4', start:105, end:125, cost:140, ut:'2026-10-16 11:30', uu:'wangl'},
  ],
};
const PAGE_SIZE = 8;
const state = {tab:'display', cmt:false, kw:'', fCap:'', tMin:'', tMax:'', fCfgCap:'', page:1, dirty:{}, editingKey:null};