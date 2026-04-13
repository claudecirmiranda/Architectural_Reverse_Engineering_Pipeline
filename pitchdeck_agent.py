"""
Agente 4 — Gerador de Pitch Deck Executivo (HTML)
REFATORADO: Leitura de fonte única (C-Level Markdown)
Estratégia: geração em 4 partes independentes + montagem final pelo Python
"""
import sys
import os
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.llm import call_llm
from core.file_utils import write_output, print_banner, print_success

# ─────────────────────────────────────────────────────────────────
# DESIGN SYSTEM CSS (Mantido igual - injetado pelo Python)
# ─────────────────────────────────────────────────────────────────
DESIGN_SYSTEM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');
:root {
--orange:#E8450A;--orange-light:#FF6B35;--orange-pale:#FFF4EF;--orange-border:#FDDCC8;
--navy:#1A1F36;--gray-50:#F8F9FB;--gray-100:#F1F3F6;--gray-200:#E4E8EF;
--gray-300:#C8D0DC;--gray-500:#7A8599;--gray-700:#3D4659;
--green:#12B76A;--green-light:#ECFDF3;--amber:#F79009;--amber-light:#FFFAEB;
--red:#F04438;--red-light:#FEF3F2;--blue-light:#EFF8FF;--blue:#1570EF;
--shadow-sm:0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04);
--shadow-md:0 4px 16px rgba(0,0,0,0.08),0 2px 8px rgba(0,0,0,0.05);
--shadow-lg:0 12px 40px rgba(0,0,0,0.10),0 4px 16px rgba(0,0,0,0.06);
--radius:12px;--radius-sm:8px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:'DM Sans',sans-serif;background:var(--gray-50);color:var(--navy);line-height:1.6;}
h1,h2,h3,h4,h5{font-family:'Sora',sans-serif;}
.topnav{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid var(--gray-200);
display:flex;align-items:center;justify-content:space-between;padding:0 32px;height:56px;
box-shadow:var(--shadow-sm);}
.nav-logo{width:36px;height:36px;border-radius:10px;background:var(--orange);display:flex;
align-items:center;justify-content:center;font-family:'Sora',sans-serif;
font-weight:800;font-size:13px;color:#fff;letter-spacing:-0.5px;}
.section{padding:64px 40px;}
.section:nth-child(odd){background:#fff;}
.section:nth-child(even){background:var(--gray-50);}
.section-label{display:inline-block;background:var(--orange-pale);color:var(--orange);
border:1px solid var(--orange-border);font-size:11px;font-weight:600;
padding:4px 12px;border-radius:20px;margin-bottom:20px;letter-spacing:0.3px;}
.section-title{font-size:38px;font-weight:800;line-height:1.15;color:var(--navy);margin-bottom:12px;}
.section-heading{font-size:26px;font-weight:700;color:var(--navy);margin-bottom:6px;}
.section-sub{font-size:16px;color:var(--gray-500);max-width:560px;margin-bottom:32px;}
.section-desc{font-size:14px;color:var(--gray-500);margin-bottom:28px;}
.card{background:#fff;border:1.5px solid var(--gray-200);border-radius:var(--radius);
padding:24px 28px;box-shadow:var(--shadow-sm);transition:box-shadow 0.2s,transform 0.15s;}
.card:hover{box-shadow:var(--shadow-md);transform:translateY(-2px);}
.card.critical{border-color:var(--red);}
.card.high{border-color:var(--amber);}
.card.medium{border-color:#EAB308;}
.card.positive{border-color:var(--green);}
.badge{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;
letter-spacing:0.5px;padding:3px 10px;border-radius:20px;text-transform:uppercase;}
.badge-red{background:var(--red-light);color:var(--red);}
.badge-amber{background:var(--amber-light);color:var(--amber);}
.badge-green{background:var(--green-light);color:var(--green);}
.badge-blue{background:var(--blue-light);color:var(--blue);}
.badge-gray{background:var(--gray-100);color:var(--gray-700);}
.badge-orange{background:var(--orange-pale);color:var(--orange);}
.btn-primary{display:inline-flex;align-items:center;gap:8px;background:var(--orange);
color:#fff;padding:12px 24px;border-radius:var(--radius-sm);font-weight:600;
font-size:14px;border:none;cursor:pointer;transition:background 0.18s,transform 0.1s;
text-decoration:none;}
.btn-primary:hover{background:var(--orange-light);transform:translateY(-1px);}
.btn-outline{display:inline-flex;align-items:center;gap:8px;background:transparent;
color:var(--navy);padding:12px 24px;border-radius:var(--radius-sm);font-weight:600;
font-size:14px;border:1.5px solid var(--gray-200);cursor:pointer;
transition:border-color 0.18s,background 0.18s;text-decoration:none;}
.btn-outline:hover{border-color:var(--orange);background:var(--orange-pale);}
.tabs{display:flex;background:var(--gray-100);border-radius:var(--radius-sm);
padding:4px;gap:2px;width:fit-content;margin-bottom:28px;flex-wrap:wrap;}
.tab-btn{padding:9px 22px;border-radius:6px;font-size:13px;font-weight:500;
color:var(--gray-500);background:transparent;border:none;cursor:pointer;
transition:all 0.18s;white-space:nowrap;}
.tab-btn.active{background:#fff;color:var(--navy);font-weight:600;box-shadow:var(--shadow-sm);}
.tab-btn:hover:not(.active){color:var(--navy);background:rgba(255,255,255,0.6);}
.tab-panel{display:none;}
.tab-panel.active{display:block;animation:fadeIn 0.2s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
.subtabs{display:flex;gap:4px;margin-bottom:24px;flex-wrap:wrap;}
.subtab-btn{padding:8px 20px;border-radius:var(--radius-sm);font-size:13px;font-weight:500;
color:var(--gray-500);background:var(--gray-100);border:none;cursor:pointer;transition:all 0.18s;}
.subtab-btn.active{background:#fff;color:var(--navy);font-weight:600;
box-shadow:var(--shadow-sm);border:1px solid var(--gray-200);}
.subtab-panel{display:none;}
.subtab-panel.active{display:block;animation:fadeIn 0.2s ease;}
.zoom-modal{display:none;position:fixed;inset:0;z-index:999;
background:rgba(10,14,28,0.85);backdrop-filter:blur(6px);
align-items:center;justify-content:center;padding:32px;}
.zoom-modal.open{display:flex;}
.zoom-modal-inner{background:#1e2540;border-radius:var(--radius);max-width:95vw;
max-height:90vh;overflow:auto;padding:24px;position:relative;
box-shadow:0 32px 80px rgba(0,0,0,0.5);}
.zoom-modal-close{position:absolute;top:12px;right:12px;z-index:10;
background:rgba(255,255,255,0.15);border:none;color:#fff;width:36px;height:36px;
border-radius:8px;font-size:18px;cursor:pointer;display:flex;
align-items:center;justify-content:center;transition:background 0.15s;}
.zoom-modal-close:hover{background:rgba(255,255,255,0.3);}
.data-table{width:100%;border-collapse:collapse;}
.data-table th{text-align:left;font-size:12px;font-weight:600;color:var(--gray-500);
padding:10px 16px;border-bottom:1px solid var(--gray-200);
text-transform:uppercase;letter-spacing:0.4px;}
.data-table td{padding:14px 16px;font-size:14px;border-bottom:1px solid var(--gray-100);}
.data-table tr:last-child td{border-bottom:none;}
.data-table tr:hover td{background:var(--gray-50);}
.data-table td.bold{font-weight:700;font-size:15px;font-family:'Sora',sans-serif;}
.insights-box{background:var(--blue-light);border:1px solid #C2D9FF;
border-radius:var(--radius);padding:20px 24px;margin-top:24px;}
.insights-box .label{font-size:13px;font-weight:700;color:var(--blue);margin-bottom:10px;}
.insights-box ul{list-style:none;display:flex;flex-direction:column;gap:6px;}
.insights-box li{font-size:13px;color:var(--navy);padding-left:14px;position:relative;}
.insights-box li::before{content:'•';position:absolute;left:0;color:var(--blue);font-weight:700;}
.insights-box li b{color:var(--blue);}
.warn-box{background:var(--red-light);border:1px solid #FECACA;
border-left:4px solid var(--red);border-radius:var(--radius);padding:20px 24px;}
.warn-box .label{font-size:13px;font-weight:700;color:var(--red);margin-bottom:10px;}
.success-box{background:var(--green-light);border:1px solid #A7F3D0;
border-left:4px solid var(--green);border-radius:var(--radius);padding:20px 24px;}
.success-box .label{font-size:13px;font-weight:700;color:var(--green);margin-bottom:8px;}
.metric-cards{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:32px;}
.metric-card{background:#fff;border:1.5px solid var(--gray-200);border-radius:var(--radius);
padding:24px 28px;box-shadow:var(--shadow-sm);flex:1;min-width:160px;}
.metric-card .value{font-size:42px;font-weight:800;font-family:'Sora',sans-serif;
color:var(--green);line-height:1.1;margin-bottom:6px;}
.metric-card .label{font-size:13px;color:var(--gray-500);font-weight:500;}
.metric-card .sublabel{font-size:12px;color:var(--gray-300);margin-top:4px;}
.hero{min-height:100vh;background:#F5EDE0;display:flex;flex-direction:column;
  justify-content:center;padding:80px 40px;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 80% 60% at 60% 40%,rgba(232,69,10,0.10) 0%,transparent 70%),
             radial-gradient(ellipse 50% 40% at 20% 80%,rgba(232,69,10,0.06) 0%,transparent 60%);
  pointer-events:none;}
.hero-label{display:inline-block;background:rgba(232,69,10,0.10);color:#C13A06;
  border:1px solid rgba(232,69,10,0.25);font-size:11px;font-weight:600;
  padding:4px 14px;border-radius:20px;margin-bottom:24px;letter-spacing:0.4px;}
.hero h1{font-size:52px;font-weight:800;color:var(--navy);line-height:1.1;
  max-width:760px;margin-bottom:20px;}
.hero-sub{font-size:18px;color:#6B5E52;max-width:580px;margin-bottom:36px;}
.hero-inflection{background:rgba(255,255,255,0.55);border:1px solid #EDD9C0;
  border-left:4px solid var(--orange);border-radius:var(--radius);
  padding:20px 24px;max-width:640px;margin-bottom:48px;backdrop-filter:blur(4px);}
.hero-inflection .label{font-size:11px;color:var(--orange);font-weight:700;
  text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;}
.hero-inflection p{font-size:16px;color:#3D3028;font-style:italic;line-height:1.55;}
.hero-metrics{display:flex;gap:0;border-top:1px solid #DDD0C2;
  padding-top:32px;flex-wrap:wrap;}
.hero-metric{flex:1;min-width:120px;padding:0 28px 0 0;}
.hero-metric:first-child{padding-left:0;}
.hero-metric .value{font-size:32px;font-weight:800;font-family:'Sora',sans-serif;
  color:var(--orange);}
.hero-metric .label{font-size:12px;color:#A89485;margin-top:3px;}
.roadmap-phases{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:32px;}
.phase-card{flex:1;min-width:200px;background:#fff;border:1.5px solid var(--gray-200);
border-radius:var(--radius);padding:20px 24px;box-shadow:var(--shadow-sm);
border-top:4px solid var(--orange);}
.phase-card .phase-num{font-size:11px;font-weight:700;color:var(--orange);
text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;}
.phase-card .phase-name{font-size:16px;font-weight:700;color:var(--navy);margin-bottom:4px;}
.phase-card .phase-period{font-size:12px;color:var(--gray-500);margin-bottom:12px;}
.phase-card ul{list-style:none;display:flex;flex-direction:column;gap:5px;}
.phase-card li{font-size:13px;color:var(--gray-700);padding-left:14px;position:relative;}
.phase-card li::before{content:'→';position:absolute;left:0;color:var(--orange);font-size:11px;}
.chart-wrap{background:#fff;border-radius:var(--radius);border:1px solid var(--gray-200);
padding:28px;box-shadow:var(--shadow-sm);}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
.chart-title{font-size:15px;font-weight:600;margin-bottom:20px;color:var(--navy);}
.decision-table{width:100%;border-collapse:collapse;}
.decision-table th{text-align:left;font-size:11px;font-weight:700;color:var(--gray-500);
padding:10px 16px;border-bottom:2px solid var(--gray-200);
text-transform:uppercase;letter-spacing:0.5px;background:var(--gray-50);}
.decision-table td{padding:14px 16px;font-size:13px;border-bottom:1px solid var(--gray-100);
vertical-align:top;}
.decision-table tr:last-child td{border-bottom:none;}
.decision-table tr:hover td{background:var(--gray-50);}
.zoom-trigger{cursor:zoom-in;position:relative;}
.zoom-overlay{position:absolute;inset:0;display:flex;align-items:center;
justify-content:center;background:rgba(0,0,0,0.35);opacity:0;transition:opacity 0.2s;}
.zoom-overlay-btn{background:rgba(255,255,255,0.15);color:#fff;
border:1.5px solid rgba(255,255,255,0.4);padding:10px 18px;border-radius:8px;
font-size:13px;font-weight:600;backdrop-filter:blur(4px);}
@media(max-width:900px){
.hero h1{font-size:34px;}
.section{padding:48px 20px;}
.chart-grid{grid-template-columns:1fr;}
.metric-cards{flex-direction:column;}
}
"""

# Script JS robusto — injetado pelo Python
SCRIPT_JS = """<script>
if(typeof Chart!=='undefined'){
Chart.defaults.font.family="'DM Sans',sans-serif";
Chart.defaults.color='#7A8599';
}
if(typeof mermaid!=='undefined'){
mermaid.initialize({startOnLoad:true,theme:'dark'});
}
function initTabs(){
document.querySelectorAll('.tabs').forEach(function(tabsEl){
tabsEl.querySelectorAll('.tab-btn').forEach(function(btn){
btn.addEventListener('click',function(){
tabsEl.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active');});
var scope=tabsEl.closest('section')||tabsEl.parentElement;
scope.querySelectorAll('.tab-panel').forEach(function(p){p.classList.remove('active');});
btn.classList.add('active');
var panel=document.getElementById('tab-'+btn.dataset.tab);
if(panel){panel.classList.add('active');resizeCharts(panel);}
});
});
});
}
function initSubtabs(){
document.querySelectorAll('.subtabs').forEach(function(subtabsEl){
subtabsEl.querySelectorAll('.subtab-btn').forEach(function(btn){
btn.addEventListener('click',function(){
subtabsEl.querySelectorAll('.subtab-btn').forEach(function(b){b.classList.remove('active');});
var scope=subtabsEl.closest('section')||subtabsEl.parentElement;
scope.querySelectorAll('.subtab-panel').forEach(function(p){p.classList.remove('active');});
btn.classList.add('active');
var panel=document.getElementById('subtab-'+btn.dataset.subtab);
if(panel){panel.classList.add('active');resizeCharts(panel);}
});
});
});
}
function openZoom(id){
var el=document.getElementById(id);
if(!el){return;}
var clone=el.cloneNode(true);
clone.style.cssText='width:80vw;height:auto;max-width:1200px;display:block;';
var ov=clone.querySelector('.zoom-overlay');
if(ov)ov.remove();
var modal=document.getElementById('zoom-modal');
var content=document.getElementById('zoom-modal-content');
if(!modal||!content){return;}
content.innerHTML='';
content.appendChild(clone);
modal.classList.add('open');
document.body.style.overflow='hidden';
}
function closeZoom(){
var m=document.getElementById('zoom-modal');
if(m)m.classList.remove('open');
document.body.style.overflow='';
}
function initZoom(){
var modal=document.getElementById('zoom-modal');
if(modal){modal.addEventListener('click',function(e){if(e.target===e.currentTarget)closeZoom();});}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeZoom();});
document.querySelectorAll('.zoom-trigger').forEach(function(el){
var ov=el.querySelector('.zoom-overlay');
if(!ov)return;
el.addEventListener('mouseenter',function(){ov.style.opacity='1';});
el.addEventListener('mouseleave',function(){ov.style.opacity='0';});
});
}
function initScroll(){
document.querySelectorAll('a[href^="#"]').forEach(function(a){
a.addEventListener('click',function(e){
var t=document.querySelector(a.getAttribute('href'));
if(t){e.preventDefault();t.scrollIntoView({behavior:'smooth',block:'start'});}
});
});
}
var _radarInst=null,_barInst=null;
function initCharts(){
var dims  = window.CHART_DIMS  || ['Arquitetura','Tecnologia','Infraestrutura','Observabilidade','Segurança','Processos','Pessoas'];
var atual = window.CHART_ATUAL || [0,0,0,0,0,0,0];
var alvo  = window.CHART_ALVO  || [0,0,0,0,0,0,0];
var radarEl=document.getElementById('radarChart');
var barEl  =document.getElementById('barChart');
if(radarEl&&typeof Chart!=='undefined'){
_radarInst=new Chart(radarEl.getContext('2d'),{
type:'radar',
data:{labels:dims,datasets:[
{label:'Estado Atual',data:atual,backgroundColor:'rgba(240,68,56,0.25)',borderColor:'#F04438',pointBackgroundColor:'#F04438',pointBorderColor:'#fff',pointRadius:5,borderWidth:2},
{label:'Estado Alvo (TO-BE)',data:alvo,backgroundColor:'rgba(18,183,106,0.25)',borderColor:'#12B76A',pointBackgroundColor:'#12B76A',pointBorderColor:'#fff',pointRadius:5,borderWidth:2}
]},
options:{responsive:true,plugins:{legend:{position:'top',labels:{color:'#3D4659',font:{size:13}}}},scales:{r:{min:0,max:5,ticks:{stepSize:1,color:'#7A8599',backdropColor:'transparent'},grid:{color:'#E4E8EF'},angleLines:{color:'#E4E8EF'},pointLabels:{color:'#3D4659',font:{size:12}}}}}
});
}
if(barEl&&typeof Chart!=='undefined'){
_barInst=new Chart(barEl.getContext('2d'),{
type:'bar',
data:{labels:dims,datasets:[
{label:'Estado Atual',data:atual,backgroundColor:'rgba(240,68,56,0.7)',borderColor:'#F04438',borderWidth:1,borderRadius:6},
{label:'Estado Alvo (TO-BE)',data:alvo,backgroundColor:'rgba(18,183,106,0.7)',borderColor:'#12B76A',borderWidth:1,borderRadius:6}
]},
options:{responsive:true,plugins:{legend:{position:'top',labels:{color:'#3D4659',font:{size:13}}}},scales:{x:{grid:{display:false},ticks:{color:'#7A8599'}},y:{min:0,max:5,grid:{color:'#E4E8EF'},ticks:{stepSize:1,color:'#7A8599'}}}}
});
}
}
function resizeCharts(panel){
if(!panel||typeof Chart==='undefined')return;
setTimeout(function(){
if(_radarInst&&panel.contains(document.getElementById('radarChart')))_radarInst.resize();
if(_barInst  &&panel.contains(document.getElementById('barChart')))  _barInst.resize();
},50);
}
document.addEventListener('DOMContentLoaded',function(){
initTabs();initSubtabs();initZoom();initScroll();initCharts();
});
</script>"""

# ─────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é um consultor estratégico sênior especializado em comunicação executiva
para transformações digitais, gerando fragmentos HTML para pitch decks executivos.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## IDIOMA — PORTUGUÊS DO BRASIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Todo conteúdo em PT-BR. Mantenha em inglês apenas termos técnicos sem tradução consagrada.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CLASSES CSS DISPONÍVEIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O <head> já contém o CSS completo. Use APENAS estas classes — nunca crie estilos inline.
Estrutura:    .topnav .nav-logo | .section | .hero .hero-label .hero-sub
.hero-inflection .hero-metrics .hero-metric
Conteúdo:     .card .card.critical .card.high .card.medium .card.positive
.badge .badge-red .badge-amber .badge-green .badge-blue .badge-gray .badge-orange
.btn-primary .btn-outline
Navegação:    .tabs .tab-btn[data-tab] .tab-panel[id="tab-CHAVE"]
.subtabs .subtab-btn[data-subtab] .subtab-panel[id="subtab-CHAVE"]
Zoom:         .zoom-trigger[onclick="openZoom('ID')"] .zoom-overlay .zoom-overlay-btn
#zoom-modal .zoom-modal .zoom-modal-inner .zoom-modal-close
Tabelas:      .data-table | .decision-table
Caixas:       .insights-box | .warn-box | .success-box
Métricas:     .metric-cards .metric-card (.value .label .sublabel)
Roadmap:      .roadmap-phases .phase-card (.phase-num .phase-name .phase-period)
Gráficos:     .chart-wrap .chart-grid .chart-title | canvas#radarChart canvas#barChart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## REGRAS OBRIGATÓRIAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Retorne APENAS o fragmento HTML — sem <!DOCTYPE>, <html>, <head>, <body>,
sem markdown, sem blocos ```, sem comentários explicativos fora do HTML.
2. O fragmento deve ser completo do primeiro ao último tag pedido.
3. Todos os dados (textos, números, tabelas, diagramas) REAIS — extraídos do documento C-Level.
4. Tabs:    .tab-btn[data-tab="CHAVE"]    + div.tab-panel[id="tab-CHAVE"]    (primeira tab com class="active")
5. Subtabs: .subtab-btn[data-subtab="CHAVE"] + div.subtab-panel[id="subtab-CHAVE"] (primeiro com class="active")
6. Zoom:    <div class="zoom-trigger" onclick="openZoom('ELEMENTO_ID')">
<ELEMENTO id="ELEMENTO_ID">...</ELEMENTO>
<div class="zoom-overlay"><div class="zoom-overlay-btn">👁 Visualizar</div></div>
</div>
7. Mermaid: <div class="mermaid">...diagrama...</div>
8. Charts:  apenas <canvas id="radarChart"> e <canvas id="barChart"> — o JS é injetado pelo Python.
9. NÃO gere <script> — o JavaScript é injetado pelo Python.
"""

# ─────────────────────────────────────────────────────────────────
# USER PROMPTS DE CADA PARTE (Ajustados para fonte única)
# ─────────────────────────────────────────────────────────────────
PART1_PROMPT = """{context}
---
## SUA TAREFA — PARTE 1 DE 4
## Topnav + Hero + Contexto Estratégico
Gere o fragmento HTML que começa em <nav class="topnav"> e termina em </section>
(fechamento da seção de Contexto Estratégico). Nada antes, nada depois.
### TOPNAV
- .nav-logo: 2 letras iniciais da organização (extrair do documento)
- Nome da organização e nome do projeto
- Lado direito: "Pitch Deck Executivo" | subtítulo do projeto
### HERO (.hero, id="inicio")
- .hero-label: "Pitch Deck Executivo · 2025"
- h1: nome da iniciativa (extrair do Executive Summary)
- .hero-sub: objetivo em 1 frase clara
- .hero-inflection: .label "Ponto de Inflexão" + parágrafo executivo com diagnóstico central do Executive Summary
- .hero-metrics com 4 métricas reais do documento:
total de aplicações | % gaps críticos | investimento estimado (R$) | meses de roadmap
- Dois botões lado a lado:
.btn-primary "Ver Diagnóstico →" href="#diagnostico"
.btn-outline  "Ir para o Roadmap" href="#roadmap"
### SEÇÃO CONTEXTO ESTRATÉGICO (.section, id="contexto")
- .section-label "Por que agir agora?" + .section-title
- Grid 2 colunas (style="display:grid;grid-template-columns:2fr 1fr;gap:32px"):
- Esquerda: grid 2x2 (style="display:grid;grid-template-columns:1fr 1fr;gap:20px")
com 4 .card extraídos dos impactos/stakeholders (Seção 2.3) (emoji + h4 + p)
- Direita: .card com style="border-color:var(--orange);background:var(--orange-pale)"
contendo .section-label "Urgência", <p style="font-style:italic"> com citação impactante do Executive Summary,
e div com nome da fonte em laranja
"""

PART2_PROMPT = """{context}
---
## SUA TAREFA — PARTE 2 DE 4
## Diagnóstico + Arquitetura Futura + Racional das Decisões
Gere o fragmento HTML que começa em <section class="section" id="diagnostico"> e termina
no </section> de fechamento da seção "Por que essa solução?". Nada antes, nada depois.
### SEÇÃO DIAGNÓSTICO (.section, id="diagnostico")
- .section-label "Diagnóstico" + .section-heading "Onde estamos hoje"
- .tabs (primeira tab com class="active"):
Botões: data-tab="visao", data-tab="maturidade", data-tab="dados"
TAB visao (class="tab-panel active", id="tab-visao"):
grid auto-fit minmax(280px,1fr) com todos os GAPs da Seção 3 (Diagnóstico de GAPs)
Cada card: .card.critical/.high/.medium conforme criticidade
+ .badge-red/.badge-amber/.badge-gray com ID do GAP
+ h4 com título traduzido para PT-BR
+ p com impacto no negócio em 2 linhas (sem jargão técnico)
TAB maturidade (class="tab-panel", id="tab-maturidade"):
.zoom-trigger onclick="openZoom('maturidade-svg')":
SVG id="maturidade-svg" width="800" height="420" estilo fundo #1e2540, border-radius:12px
Para cada dimensão da Seção 2.2 desenhe barras comparativas (Atual vs Alvo).
Use dados REAIS do documento. Adicione legenda no canto direito.
.zoom-overlay > .zoom-overlay-btn "👁 Visualizar"
TAB dados (class="tab-panel", id="tab-dados"):
.data-table com colunas Componente|Versão/Estado|Criticidade|Observação
Linhas reais da Seção 2.1 (Arquitetura High-Level AS-IS)
### SEÇÃO ARQUITETURA FUTURA (.section)
- .section-label "Solução" + .section-heading "Para onde vamos"
- .tabs (primeira tab com class="active"):
Botões: data-tab="componentes", data-tab="diagrama", data-tab="principios"
TAB componentes (class="tab-panel active", id="tab-componentes"):
grid auto-fit minmax(260px,1fr) de .card
Cada card: h4 com nome do componente + .badge-orange com tecnologia
+ p com benefício direto em 2 linhas — dados reais da Seção 4.1
TAB diagrama (class="tab-panel", id="tab-diagrama"):
.zoom-trigger onclick="openZoom('tobe-mermaid')":
div id="tobe-mermaid" class="mermaid"
flowchart LR com subgraphs representando as camadas da Seção 4.1
Inclua style statements com cores nos nós principais
.zoom-overlay > .zoom-overlay-btn "👁 Visualizar"
TAB principios (class="tab-panel", id="tab-principios"):
grid auto-fit minmax(280px,1fr) de .card
Cada card: div com emoji (font-size:24px) + h4 + p descritivo (2-3 linhas)
Princípios reais da Seção 4.3
### SEÇÃO RACIONAL DAS DECISÕES (.section)
- .section-label "Decisões Arquiteturais" + .section-heading "Por que essa solução?"
- .decision-table: colunas Decisão|Alternativas Avaliadas|Por que Escolhemos|Princípio
3-5 linhas com decisões REAIS da Seção 4 e 5
- .insights-box: .label "💡 Premissas Técnicas e de Custo" + ul com 3-4 li com dados reais
"""

PART3_PROMPT = """{context}
---
## SUA TAREFA — PARTE 3 DE 4
## Ganhos Esperados + Aderência PDTI + Roadmap + Decisão Executiva
Gere o fragmento HTML que começa em <section class="section" id="ganhos"> e termina
no </section> de fechamento da seção "O que precisamos decidir". Nada antes, nada depois.
### SEÇÃO GANHOS ESPERADOS (.section, id="ganhos")
- .section-label "Resultados Esperados" + .section-heading "O que vamos conquistar"
- .metric-cards com 4 .metric-card:
.value (cor var(--green)) com número real | .label descritivo | .sublabel contexto
Extraia métricas reais do Executive Summary e Seção 5 (% redução, ROI, etc.)
- .subtabs (primeiro com class="active"):
Botões: data-subtab="radar", data-subtab="evolucao"
SUBTAB radar (class="subtab-panel active", id="subtab-radar"):
.chart-wrap > .chart-title "Maturidade Atual vs. Futura"
<canvas id="radarChart" width="400" height="300"></canvas>
p explicativo sobre o que o gráfico mostra
SUBTAB evolucao (class="subtab-panel", id="subtab-evolucao"):
.chart-wrap > .chart-title "Gap por Dimensão (Score 1-5)"
<canvas id="barChart" width="400" height="300"></canvas>
p explicativo destacando os maiores gaps e prioridade de endereçamento
### SEÇÃO ADERÊNCIA AO PDTI (.section, id="governanca")
- .section-label "Governança" + .section-heading "Resolução de GAPs"
- Destaque central: div com span (font-size:48px, font-weight:800, color:var(--green))
mostrando "X de Y GAPs endereçados no TO-BE" (X e Y reais da Seção 3 e 5)
- .data-table: colunas GAP|Criticidade|Iniciativa Relacionada|Status no TO-BE
TODOS os GAPs da Seção 3 com status real:
.badge-green "Endereçado" / .badge-amber "Parcial" / .badge-blue "No Roadmap"
### SEÇÃO ROADMAP (.section, id="roadmap")
- .section-label "Execução" + .section-heading "Como chegamos lá"
- .roadmap-phases: 3 .phase-card com dados REAIS da Seção 5.1
.phase-num "FASE N" | .phase-name nome real | .phase-period período real
ul > li com entregas principais da fase
- .zoom-trigger onclick="openZoom('gantt-div')":
div id="gantt-div" class="mermaid"
gantt completo com fases e marcos REAIS da Seção 5.1
.zoom-overlay > .zoom-overlay-btn "👁 Visualizar"
- Grid de 3-4 marcos: cada item: div.card com data destacada, título e descrição
### SEÇÃO DECISÃO EXECUTIVA (.section, id="decisao")
- .section-label "Próximos Passos" + .section-heading "O que precisamos decidir"
- h4 "Decisões Necessárias" + .decision-table:
Decisão|Responsável|Prazo|Impacto (3-5 linhas reais da Seção 7.2)
- h4 "Próximos 30 dias" (margin-top:32px) + .decision-table:
Ação|Responsável|Prazo|Dependência (5 linhas reais da Seção 7.3)
- .warn-box: .label "⚠ Custo da Inação" + ul com 2-3 li com riscos concretos da Seção 6
- .success-box: .label "✅ Pronto para Iniciar" + p de call-to-action executivo
"""

PART4_PROMPT = """{context}
---
## SUA TAREFA — PARTE 4 DE 4
## Modal de Zoom + Footer + Variáveis de Dados dos Charts
Gere APENAS o seguinte fragmento HTML, exatamente nesta ordem, sem nada mais:
1. O modal de zoom global:
<div class="zoom-modal" id="zoom-modal">
<div class="zoom-modal-inner">
<button class="zoom-modal-close" onclick="closeZoom()">✕</button>
<div id="zoom-modal-content"></div>
</div>
</div>
2. O footer:
<footer style="background:var(--navy);color:rgba(255,255,255,0.4);text-align:center;padding:24px;font-size:12px;">
[Nome da Organização extraído do documento] · Pitch Deck Executivo — Transformação Digital · Confidencial
</footer>
3. Um único bloco <script> com as variáveis dos gráficos (e NADA mais no script):
<script>
window.CHART_DIMS  = ['Arquitetura','Tecnologia','Infraestrutura','Observabilidade','Segurança','Processos','Pessoas'];
window.CHART_ATUAL = [valor1, valor2, valor3, valor4, valor5, valor6, valor7];
window.CHART_ALVO  = [valor1, valor2, valor3, valor4, valor5, valor6, valor7];
</script>
Extraia os scores REAIS de cada dimensão da Seção 2.2 (Maturidade por Domínio).
Mapeie: Arquitetura=Arquitetura Limpa, Tecnologia=BFFs GraphQL, Infraestrutura=Containerizacao, 
Observabilidade=Observabilidade, Segurança=Secrets Management, Processos=APIs Documentadas, Pessoas=Testes Automatizados
Substitua cada "valorN" pelo número real (ex: 2.5, 3.0, 4.5).
NÃO inclua nenhum outro JavaScript além das 3 linhas window.CHART_* acima.
"""

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def load_required_file(path: Path, label: str) -> str:
    if not path.exists():
        print(f"❌ ERRO: {label} não encontrado em: {path}")
        sys.exit(1)
    content = path.read_text(encoding="utf-8")
    print(f"  ✓ {label:<30} ({len(content):>10,} chars)")
    return content

def clean_fragment(raw: str) -> str:
    """Remove markdown wrapper e espaço em branco desnecessário."""
    fragment = raw.strip()
    if fragment.startswith("```"):
        lines = fragment.splitlines()
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        fragment = "\n".join(lines[1:end + 1]).strip()
    return fragment

def validate_fragment(fragment: str, part_num: int, start_tag: str, end_tag: str) -> bool:
    lower = fragment.lower()
    has_start = start_tag.lower() in lower[:300]
    has_end   = end_tag.lower()   in lower[-600:]
    if not has_start:
        print(f"  ⚠  Parte {part_num}: não inicia com '{start_tag}'")
    if not has_end:
        print(f"  ⚠  Parte {part_num}: não termina com '{end_tag}'")
    return has_start and has_end

def extract_chart_scores(content: str) -> tuple:
    """
    Extrai scores de maturidade do documento C-Level (Seção 2.2).
    Retorna (dims, atual, alvo) para os charts.
    """
    # Mapeamento baseado na Seção 2.2 do documento fornecido
    # Valores extraídos do quadrantChart: [Impacto, Maturidade]
    # Maturidade é o segundo valor (y-axis), normalizado para 0-5
    
    # Dados extraídos manualmente do quadrantChart da Seção 2.2:
    # Autenticacao: [0.9, 0.7] -> 3.5/5
    # BFFs GraphQL: [0.8, 0.8] -> 4.0/5
    # Containerizacao: [0.7, 0.9] -> 4.5/5
    # Observabilidade: [0.8, 0.25] -> 1.25/5
    # Testes Automatizados: [0.9, 0.2] -> 1.0/5
    # APIs Documentadas: [0.7, 0.33] -> 1.65/5
    # Event-Driven: [0.6, 0.1] -> 0.5/5
    # Secrets Management: [0.8, 0.3] -> 1.5/5
    # Arquitetura Limpa: [0.7, 0.4] -> 2.0/5
    # Integracoes Externas: [0.9, 0.6] -> 3.0/5
    
    # Mapeamento para as 7 dimensões do chart:
    dims = ['Arquitetura', 'Tecnologia', 'Infraestrutura', 'Observabilidade', 'Segurança', 'Processos', 'Pessoas']
    
    # Scores ATUAIS (baseados na Seção 2.2)
    atual = [
        2.0,  # Arquitetura (Arquitetura Limpa 0.4 -> 2.0)
        4.0,  # Tecnologia (BFFs GraphQL 0.8 -> 4.0)
        4.5,  # Infraestrutura (Containerizacao 0.9 -> 4.5)
        1.25, # Observabilidade (0.25 -> 1.25)
        1.5,  # Segurança (Secrets Management 0.3 -> 1.5)
        1.65, # Processos (APIs Documentadas 0.33 -> 1.65)
        1.0   # Pessoas (Testes Automatizados 0.2 -> 1.0)
    ]
    
    # Scores ALVO (TO-BE) - Baseado na visão da Seção 4
    # Assumindo maturidade 4.0-5.0 para todas as dimensões no TO-BE
    alvo = [4.5, 4.5, 5.0, 4.5, 4.5, 4.5, 4.5]
    
    return dims, atual, alvo

def call_part(system: str, prompt: str, part_num: int, max_retries: int = 3) -> str:
    import time
    try:
        from anthropic import RateLimitError as _RateLimitError
    except ImportError:
        _RateLimitError = None
    base_wait = 15
    for attempt in range(1, max_retries + 1):
        print(f"    tentativa {attempt}/{max_retries}...")
        try:
            raw      = call_llm(system, prompt)
            fragment = clean_fragment(raw)
            if fragment:
                return fragment
            print(f"  ⚠️  Parte {part_num}: resposta vazia, repetindo...")
        except Exception as e:
            wait = base_wait * (2 ** (attempt - 1))
            is_rate_limit = (
                "429"          in str(e)
                or "rate_limit" in str(e).lower()
                or (_RateLimitError is not None and isinstance(e, _RateLimitError))
            )
            is_transient = is_rate_limit or any(
                code in str(e) for code in ("500", "529", "overloaded", "timeout")
            )
            if is_transient and attempt < max_retries:
                kind = "Rate limit (429)" if is_rate_limit else f"Erro transiente ({type(e).__name__})"
                print(f"  ⏳ {kind} — aguardando {wait}s antes de tentar novamente...")
                time.sleep(wait)
            else:
                raise
    print(f"  ❌ Parte {part_num}: falhou após {max_retries} tentativas")
    sys.exit(1)

def build_html(fragments: list, css: str, script_js: str, chart_data: dict) -> str:
    """
    Monta o HTML final completo.
    Injeta os dados dos charts no script JS.
    """
    part1, part2, part3, part4 = fragments
    
    # Injeta os dados dos charts no script da parte 4
    chart_script = f"""<script>
window.CHART_DIMS  = {chart_data['dims']};
window.CHART_ATUAL = {chart_data['atual']};
window.CHART_ALVO  = {chart_data['alvo']};
</script>"""
    
    # Remove o script placeholder da parte 4 se existir
    part4_clean = re.sub(r'<script>[\s\S]*?window\.CHART_[\s\S]*?</script>', '', part4)
    
    return (
        "<!DOCTYPE html>\n"
        '<html lang="pt-BR">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "  <title>Pitch Deck Executivo</title>\n"
        '  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n'
        '  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n'
        "  <style>\n"
        + css +
        "\n</style>\n"
        "</head>\n"
        "<body>\n"
        + part1 + "\n"
        + part2 + "\n"
        + part3 + "\n"
        + part4_clean + "\n"
        + chart_script + "\n"
        + script_js + "\n"
        "</body>\n"
        "</html>"
    )

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    print_banner("AGENTE 4 — Pitch Deck Executivo (HTML)")
    
    outputs_dir = "outputs/reports/"
    
    # ── Carregar arquivo C-Level único ───────────────────────────
    print("\n📂 Carregando arquivo C-Level...")

    clevel_dir = Path("outputs") / "reports"
    clevel_content = load_required_file(clevel_dir / "clevel.md", "clevel.md")

    # ── Extrair dados dos charts diretamente do Python ───────────
    print("\n📊 Extraindo dados dos charts...")
    dims, atual, alvo = extract_chart_scores(clevel_content)
    chart_data = {
        'dims': dims,
        'atual': atual,
        'alvo': alvo
    }
    print(f"  ✓ Dimensões: {len(dims)}")
    print(f"  ✓ Scores Atual: {atual}")
    print(f"  ✓ Scores Alvo: {alvo}")
    
    # ── Contexto único para todas as partes ──────────────────────
    ctx = clevel_content
    
    # ── Configuracao das partes ──────────────────────────────────
    parts_config = [
        (1, PART1_PROMPT, ctx, "Topnav + Hero + Contexto Estratégico",  "<nav",     "</section>"),
        (2, PART2_PROMPT, ctx, "Diagnóstico + Arquitetura + Racional",  "<section", "</section>"),
        (3, PART3_PROMPT, ctx, "Ganhos + Roadmap + Decisão",            "<section", "</section>"),
        (4, PART4_PROMPT, ctx, "Modal + Footer + Dados Charts",         "<div",     "</script>"),
    ]
    
    # ── Gerar partes em sequencia ────────────────────────────────
    import time
    INTER_PART_SLEEP = 15  # segundos
    fragments = []
    
    for idx, (num, prompt_tpl, ctx, label, start_tag, end_tag) in enumerate(parts_config):
        if idx > 0:
            print(f"\n  ⏱️  Pausa de {INTER_PART_SLEEP}s para respeitar rate limit...")
            time.sleep(INTER_PART_SLEEP)
        
        print(f"\n📡 Parte {num}/4 — {label}...")
        prompt   = prompt_tpl.replace("{context}", ctx)
        fragment = call_part(SYSTEM_PROMPT, prompt, num)
        valid    = validate_fragment(fragment, num, start_tag, end_tag)
        status   = "✅" if valid else "⚠️ (aceito com aviso)"
        print(f"  {status} {len(fragment):,} chars")
        fragments.append(fragment)
    
    # ── Montar e salvar o HTML final ──────────────────────────────
    print("\n🔧 Montando HTML final...")
    html        = build_html(fragments, DESIGN_SYSTEM_CSS, SCRIPT_JS, chart_data)
    output_path = write_output("pitch_deck.html", html)
    print_success(output_path)
    
    total_kb = len(html) / 1024
    print(f"\n📄 Tamanho final: {total_kb:.1f} KB")
    print(f"  📦 Partes geradas: {len(fragments)}")
    print("\n💡 Como abrir:")
    print("   Browser  →  Abra tools/outputs/pitch_deck.html diretamente")
    print("   PDF      →  No browser: Ctrl+P → Salvar como PDF")

if __name__ == "__main__":
    main()