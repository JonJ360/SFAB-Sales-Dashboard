/* No embedded data: reads the authenticated/live snapshot already loaded by the dashboard. */
function updateReportScope() {
  const rebar = state.view === 'rebar';
  document.querySelector('.periods').style.display=rebar?'none':'';
  document.getElementById('monthSelect').style.display=rebar?'none':'';
  document.getElementById('periodLabel').textContent=rebar?'Monthly history by selected rebar year · validated subset only':`${periodName()} · net of returns · compared with prior year`;
}
function exactPounds(value) {
  if (value === null || value === undefined) return 'Not available';
  const [whole, fraction] = String(value).split('.');
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (fraction === undefined ? '' : '.' + fraction);
}
function rebarRows() {
  return (state.data?.rebar?.monthly || []).filter(r => r.period.startsWith(document.getElementById('rebarYear').value + '-'));
}
function renderRebar() {
  const report=state.data?.rebar, select=document.getElementById('rebarYear');
  for (const id of ['rebarCommodity','rebarFabricated']) {
    if (state.charts[id]) {state.charts[id].destroy(); delete state.charts[id];}
  }
  document.getElementById('rebarBody').textContent='';
  document.getElementById('rebarCoverage').textContent='';
  document.getElementById('rebarExport').disabled=!report;
  document.getElementById('fiberglassPanel').hidden=true;
  document.getElementById('fiberglassBody').innerHTML='';
  document.getElementById('fiberglassExport').disabled=true;
  document.getElementById('fiberglassExport').onclick=null;
  if (!report) {
    select.innerHTML='';
    document.getElementById('rebarStatus').textContent='Rebar history unavailable in this snapshot. No pounds assumed; financial reports remain live.';
    return;
  }
  const years=[...new Set(report.monthly.map(r=>r.period.slice(0,4)))].sort();
  const previous=select.value;
  select.innerHTML=years.map(y=>`<option value="${esc(y)}">${esc(y)}</option>`).join('');
  select.value=years.includes(previous)?previous:years.at(-1);
  select.onchange=renderRebar;
  const rows=rebarRows();
  document.getElementById('rebarStatus').textContent=`${report.status}. Through ${report.through}. ${report.validated_count} validated / ${report.candidate_count} candidate lines; ${report.unknown_count} unresolved; ${report.classified_count ?? 0} separately classified fiberglass; ${report.excluded_count ?? 0} excluded non-rebar/financial lines. ${report.basis}`;
  document.getElementById('rebarCoverage').textContent=report.coverage_warning;
  for (const [id,group] of [['rebarCommodity','Commodity rebar'],['rebarFabricated','Fabricated rebar']]) {
    const groupRows=rows.filter(r=>r.group===group);
    chart(id,{type:'bar',data:{labels:groupRows.map(r=>r.period),datasets:[['Sold','sold_lbs','#2E6FD9'],['Returned','returned_lbs','#B5821F']].map(([label,key,color])=>({label:label+' lb',data:groupRows.map(r=>r[key]===null?null:Number(r[key])),backgroundColor:color,borderRadius:4,maxBarThickness:22,exact:groupRows.map(r=>r[key])}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+exactPounds(ctx.dataset.exact[ctx.dataIndex])}}},scales:{y:{beginAtZero:true,title:{display:true,text:'Pounds (validated subset)'}}}}});
  }
  document.getElementById('rebarBody').innerHTML=rows.map(r=>`<tr><td>${esc(r.period)}</td><td>${esc(r.group)}</td>${['sold_lbs','returned_lbs','net_lbs','prepaid_sold_lbs','prepaid_returned_lbs'].map(k=>`<td class="num">${esc(exactPounds(r[k]))}</td>`).join('')}<td class="num">${r.validated_count}</td><td class="num">${r.unknown_count_month}</td><td class="num">${r.excluded_count_month ?? 0}</td></tr>`).join('');
  document.getElementById('rebarExport').onclick=exportRebar;
  renderFiberglass();
}
function renderFiberglass() {
  const report=state.data.rebar?.fiberglass, panel=document.getElementById('fiberglassPanel');
  panel.hidden=!report;
  if (!report) return;
  const rows=report.monthly.filter(r=>r.period.startsWith(document.getElementById('rebarYear').value+'-'));
  document.getElementById('fiberglassBody').innerHTML=rows.map(r=>`<tr><td>${esc(r.period)}</td>${['sold_each','returned_each','net_each','gross_sales','return_sales','net_sales','sold_lbs','returned_lbs','net_lbs'].map(k=>`<td class="num">${esc(r[k] ?? 'Not available')}</td>`).join('')}</tr>`).join('');
  document.getElementById('fiberglassExport').disabled=false;
  document.getElementById('fiberglassExport').onclick=exportFiberglass;
}
function exportFiberglass() {
  const fields=['period','sold_each','returned_each','net_each','gross_sales','return_sales','net_sales','sold_lbs','returned_lbs','net_lbs'];
  const rows=state.data.rebar.fiberglass.monthly.filter(r=>r.period.startsWith(document.getElementById('rebarYear').value+'-'));
  const quote=v=>'"'+String(v??'Not available').replace(/"/g,'""')+'"';
  const records=[['Fiberglass Rebar; quantities EA (pieces); sales USD; pounds: CURRENT GP ITEM MASTER weight basis 3.60 lb/EA, not measured shipment weight; unsupported weights unavailable'],fields,...rows.map(r=>fields.map(k=>r[k]))];
  const blob=new Blob(['\uFEFF'+records.map(r=>r.map(quote).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='SFAB-fiberglass-'+document.getElementById('rebarYear').value+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function exportRebar() {
  const report=state.data.rebar;
  const fields=['period','group','sold_lbs','returned_lbs','net_lbs','prepaid_sold_lbs','prepaid_returned_lbs','validated_count','candidate_count_month','unknown_count_month','excluded_count_month'];
  const quote=v=>'"'+String(v??'Not available').replace(/"/g,'""')+'"';
  const records=[['SFAB direct-LBS validated subset; not complete totals'],[report.basis],[report.coverage_warning],[report.prepaid_policy],['Through',report.through],['Whole-month candidate/unknown/excluded counts repeat per group; do not sum across groups.'],fields,...rebarRows().map(r=>fields.map(k=>r[k]))];
  const blob=new Blob(['\uFEFF'+records.map(r=>r.map(quote).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='SFAB-monthly-rebar-'+document.getElementById('rebarYear').value+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
