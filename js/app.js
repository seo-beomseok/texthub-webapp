(() => {
  'use strict';
  const DARK = '#1e2130';
  const TEXT = '#f3f5f4';
  const GRID = '#3c4252';
  const config = {responsive:true, displaylogo:false, scrollZoom:true, modeBarButtonsToRemove:['lasso2d']};
  const cache = new Map();
  let newsManifest=[], marketManifest=[], factorManifest=[], eventManifest=[], treemapData=null;

  const $ = id => document.getElementById(id);
  async function getJSON(path){
    if(cache.has(path)) return cache.get(path);
    const response = await fetch(`./${path.replace(/^\.\//,'')}`);
    if(!response.ok) throw new Error(`${response.status} ${response.statusText}: ${path}`);
    const data = await response.json(); cache.set(path,data); return data;
  }
  function plotIsReady(id){ const el=$(id); return Boolean(el && el._fullLayout); }
  function setLoading(id, text='Loading…'){
    const el=$(id); if(!el) return;
    el.setAttribute('aria-busy','true');
    if(plotIsReady(id)) el.classList.add('is-loading');
    else el.innerHTML=`<div class="status">${text}</div>`;
  }
  function clearLoading(id){ const el=$(id); if(!el) return; el.classList.remove('is-loading'); el.removeAttribute('aria-busy'); }
  function setError(id, err){
    console.error(err); const el=$(id); if(!el) return;
    try{ if(plotIsReady(id)) Plotly.purge(el); }catch(_e){}
    clearLoading(id); el.innerHTML=`<div class="status error">Could not load this view.<br>${String(err.message||err)}</div>`;
  }
  async function drawPlot(id,traces,layout){
    const el=$(id); const ready=plotIsReady(id);
    if(!ready) el.replaceChildren();
    if(ready) await Plotly.react(el,traces,layout,config); else await Plotly.newPlot(el,traces,layout,config);
    clearLoading(id);
  }
  async function runButton(id,fn){
    const btn=$(id); const label=btn.textContent; btn.disabled=true; btn.textContent='Loading…';
    try{ await fn(); } finally { btn.disabled=false; btn.textContent=label; }
  }
  function fillSelect(select, items, valueKey='id', labelKey='label'){
    select.innerHTML=''; items.forEach(item=>{const o=document.createElement('option');o.value=item[valueKey];o.textContent=item[labelKey];select.appendChild(o);});
  }
  function baseLayout(extra={}){
    return Object.assign({
      paper_bgcolor:DARK, plot_bgcolor:DARK, font:{color:TEXT, family:'Inter, Segoe UI, Arial, sans-serif'},
      hovermode:'x unified', margin:{t:70,b:70,l:70,r:70},
      legend:{orientation:'h',yanchor:'bottom',y:1.02,xanchor:'left',x:0,title:{text:'Field'}},
      xaxis:{gridcolor:GRID,zerolinecolor:GRID,automargin:true}, yaxis:{gridcolor:GRID,zerolinecolor:GRID,automargin:true}
    }, extra);
  }
  function lineTraces(traces){
    return traces.map(t=>({type:'scatter',mode:'lines',name:t.name,x:(t.x||[]).map(v=>String(v)),y:t.y,yaxis:t.axis==='y2'?'y2':'y',connectgaps:true,line:t.dash?{dash:t.dash}:{}}));
  }

  async function renderNews(){
    setLoading('news-graph');
    try{
      const field=$('news-field').value, period=$('news-period').value;
      const entry=newsManifest.find(x=>x.id===field); const path=entry?.periods?.[period];
      if(!path) throw new Error('No data for the selected field/period.');
      const d=await getJSON(path); const traces=lineTraces(d.traces);
      const hasY2=d.traces.some(t=>t.axis==='y2');
      const categoryX=[...new Set(d.traces.flatMap(t=>(t.x||[]).map(v=>String(v))))].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
      const layout=baseLayout({height:500,xaxis:{type:'category',categoryorder:'array',categoryarray:categoryX,title:period.charAt(0).toUpperCase()+period.slice(1),tickangle:-90,gridcolor:GRID,rangeslider:{visible:true,bgcolor:'#171b29',bordercolor:'#4b5460',borderwidth:1}},yaxis:{title:'TFNI',gridcolor:GRID},legend:{orientation:'h',yanchor:'bottom',y:1.08,xanchor:'left',x:0,title:{text:'Field'}}});
      if(hasY2) layout.yaxis2={title:'Related statistic',overlaying:'y',side:'right',showgrid:false,automargin:true};
      await drawPlot('news-graph',traces,layout);
    }catch(err){setError('news-graph',err)}
  }

  async function renderMarket(){
    setLoading('market-graph');
    try{
      const period=$('market-period').value, field=$('market-field').value;
      const entry=marketManifest.find(x=>x.id===field && x.period===period); if(!entry) throw new Error('No market data for this selection.');
      const d=await getJSON(entry.path); const traces=lineTraces(d.traces);
      const layout=baseLayout({height:500,xaxis:{title:period.charAt(0).toUpperCase()+period.slice(1),tickangle:-90,gridcolor:GRID},yaxis:{title:'TBCI',gridcolor:GRID},yaxis2:{title:'Points in KRX',overlaying:'y',side:'right',showgrid:false,automargin:true},legend:{orientation:'h',yanchor:'bottom',y:1.02,xanchor:'left',x:0,title:{text:'Field'}}});
      await drawPlot('market-graph',traces,layout);
    }catch(err){setError('market-graph',err)}
  }

  function renderFactorTableData(d){
    const rows=d.table; if(!rows?.length){$('factor-table').innerHTML='<div class="status">No table data.</div>';return;}
    const header=rows[0]; const body=rows.slice(1);
    const colorMap=new Map((d.colorCells||[]).map(c=>[`${c[1]-1}:${c[0]}`,d.palette[c[2]]||'#969696']));
    const table=document.createElement('table'); table.className='factor-table';
    const thead=document.createElement('thead'), trh=document.createElement('tr');
    header.forEach(v=>{const th=document.createElement('th');th.textContent=v;th.title=v;trh.appendChild(th)});thead.appendChild(trh);table.appendChild(thead);
    const tbody=document.createElement('tbody');
    body.forEach((row,ri)=>{const tr=document.createElement('tr');row.forEach((v,ci)=>{const td=document.createElement('td');td.textContent=v;td.title=v;const c=colorMap.get(`${ri}:${ci}`);if(c)td.style.backgroundColor=c;tr.appendChild(td)});tbody.appendChild(tr)});table.appendChild(tbody);
    $('factor-table').replaceChildren(table);
  }
  async function renderFactor(){
    $('factor-table').innerHTML='<div class="status">Loading…</div>';
    try{const entry=factorManifest.find(x=>x.id===$('factor-field').value);if(!entry)throw new Error('No factor table for this selection.');renderFactorTableData(await getJSON(entry.path));}catch(err){setError('factor-table',err)}
  }
  async function renderTreemap(){
    setLoading('treemap-graph');
    try{
      treemapData=treemapData||await getJSON('data/factor/treemap-2022q4.json'); const depth=Number($('treemap-depth').value); $('treemap-depth-value').textContent=depth;
      const trace={type:'treemap',labels:treemapData.labels,parents:treemapData.parents,values:treemapData.values,maxdepth:depth,marker:{colors:treemapData.colors,colorscale:'RdBu',cmid:0,colorbar:{title:'Change'}},root:{color:'lightgrey'},hovertemplate:'%{label}<br>Count: %{value}<extra></extra>'};
      const layout=baseLayout({height:650,margin:{t:45,l:25,r:25,b:25},hovermode:'closest'}); delete layout.xaxis; delete layout.yaxis;
      await drawPlot('treemap-graph',[trace],layout);
    }catch(err){setError('treemap-graph',err)}
  }

  async function renderEvent(){
    setLoading('event-graph');
    try{
      const entry=eventManifest.find(x=>x.id===$('event-name').value), item=$('event-item').value, path=entry?.items?.[item]; if(!path)throw new Error('No event data for this selection.');
      const d=await getJSON(path); const traces=lineTraces(d.traces);
      const layout=baseLayout({height:500,xaxis:{title:'Quarter',tickangle:-90,gridcolor:GRID},yaxis:{title:item==='Impact'?'TIEI':'TEEI',gridcolor:GRID},legend:{orientation:'h',yanchor:'bottom',y:1.05,xanchor:'left',x:0,title:{text:'Field'}}});
      if(item==='Evaluation') layout.shapes=[{type:'line',xref:'paper',x0:0,x1:1,y0:100,y1:100,line:{color:'#EF553B',width:1,dash:'dash'}}];
      await drawPlot('event-graph',traces,layout);
    }catch(err){setError('event-graph',err)}
  }

  function bindUI(){
    document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{
      document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));
      btn.classList.add('active');$(btn.dataset.tab).classList.add('active');
      setTimeout(()=>window.dispatchEvent(new Event('resize')),0);
    }));
    $('news-update').addEventListener('click',()=>runButton('news-update',renderNews)); $('market-update').addEventListener('click',()=>runButton('market-update',renderMarket)); $('factor-update').addEventListener('click',()=>runButton('factor-update',renderFactor)); $('event-update').addEventListener('click',()=>runButton('event-update',renderEvent));
    $('treemap-depth').addEventListener('input',renderTreemap);
    const modal=$('modal'); $('learn-more-button').addEventListener('click',()=>{modal.classList.add('open');modal.setAttribute('aria-hidden','false')}); $('modal-close').addEventListener('click',()=>{modal.classList.remove('open');modal.setAttribute('aria-hidden','true')}); modal.addEventListener('click',e=>{if(e.target===modal)$('modal-close').click()});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal.classList.contains('open'))$('modal-close').click()});
  }

  async function init(){
    try{
      [newsManifest,marketManifest,factorManifest,eventManifest]=await Promise.all([getJSON('data/news/manifest.json'),getJSON('data/market/manifest.json'),getJSON('data/factor/manifest.json'),getJSON('data/event/manifest.json')]);
      fillSelect($('news-field'),newsManifest); const quarterFields=marketManifest.filter(x=>x.period==='quarter'); fillSelect($('market-field'),quarterFields); fillSelect($('factor-field'),factorManifest); fillSelect($('event-name'),eventManifest);
      $('news-field').value='production'; $('market-field').value='kospi'; $('factor-field').value='electronic-video-communication'; $('event-name').value='covid-19';
      bindUI(); await Promise.all([renderNews(),renderMarket(),renderFactor(),renderTreemap(),renderEvent()]);
    }catch(err){console.error(err);['news-graph','market-graph','factor-table','treemap-graph','event-graph'].forEach(id=>setError(id,err));}
  }
  window.addEventListener('DOMContentLoaded',()=>{
    const wait=()=>{if(window.Plotly) init(); else setTimeout(wait,30)}; wait();
  });
})();
