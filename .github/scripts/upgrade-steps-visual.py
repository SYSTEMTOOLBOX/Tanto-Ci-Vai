from pathlib import Path
import re

p=Path('presentazione.html')
s=p.read_text(encoding='utf-8')

css='''
/* Visual how-it-works section */
#come{background:linear-gradient(180deg,#f5f8fd 0%,#eef6ff 48%,#f5fbf8 100%);position:relative;overflow:hidden}
#come:before{content:"";position:absolute;width:420px;height:420px;border-radius:50%;right:-220px;top:40px;background:radial-gradient(circle,rgba(8,205,176,.16),transparent 68%);pointer-events:none}
#come:after{content:"";position:absolute;width:360px;height:360px;border-radius:50%;left:-220px;bottom:10px;background:radial-gradient(circle,rgba(11,102,255,.13),transparent 68%);pointer-events:none}
.how-head{position:relative;z-index:1;display:grid;grid-template-columns:.9fr 1.1fr;gap:42px;align-items:end;margin-bottom:34px}
.how-head .sub{margin:0}
.step-cards{position:relative;z-index:1;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.step-card{position:relative;overflow:hidden;background:rgba(255,255,255,.96);border:1px solid rgba(214,227,243,.9);border-radius:30px;box-shadow:0 18px 48px rgba(7,26,61,.09);min-height:380px;display:grid;grid-template-rows:190px 1fr;transition:transform .2s ease,box-shadow .2s ease}
.step-card:hover{transform:translateY(-5px);box-shadow:0 26px 58px rgba(7,26,61,.14)}
.step-art{position:relative;overflow:hidden;display:grid;place-items:center;padding:20px}
.step-art:after{content:"";position:absolute;width:180px;height:180px;border-radius:50%;right:-55px;top:-65px;background:rgba(255,255,255,.16)}
.step-card:nth-child(1) .step-art{background:linear-gradient(135deg,#0b66ff,#41a4ff)}
.step-card:nth-child(2) .step-art{background:linear-gradient(135deg,#007f9f,#08cdb0)}
.step-card:nth-child(3) .step-art{background:linear-gradient(135deg,#5e44d8,#8a6cff)}
.step-card:nth-child(4) .step-art{background:linear-gradient(135deg,#0d8e5f,#58c942)}
.step-art svg{width:100%;max-width:260px;height:145px;filter:drop-shadow(0 12px 24px rgba(0,0,0,.14))}
.step-number{position:absolute;left:20px;top:18px;z-index:2;width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:#fff;color:#071a3d;font-weight:1000;font-size:18px;box-shadow:0 10px 24px rgba(7,26,61,.18)}
.step-copy{padding:25px 26px 28px}
.step-copy h3{font-size:25px;letter-spacing:-.04em;margin:0 0 10px;color:#091a38}
.step-copy p{font-size:15px;line-height:1.6;color:#68768e;margin:0}
.step-tags{display:flex;gap:7px;flex-wrap:wrap;margin-top:17px}
.step-chip{font-size:11px;font-weight:900;color:#315173;background:#eff5fb;border:1px solid #e0eaf5;border-radius:999px;padding:7px 10px}
.how-note{position:relative;z-index:1;margin-top:24px;padding:18px 20px;border:1px solid #d7e8df;background:rgba(255,255,255,.78);border-radius:22px;display:flex;gap:14px;align-items:center;color:#4c6570;font-size:14px;line-height:1.5}
.how-note-icon{flex:0 0 44px;width:44px;height:44px;border-radius:15px;display:grid;place-items:center;background:#e8fff4;color:#07926d;font-size:22px;font-weight:1000}
@media(max-width:800px){.how-head{grid-template-columns:1fr;gap:12px}.step-cards{grid-template-columns:1fr}.step-card{min-height:0;grid-template-rows:170px auto}.step-art svg{height:130px}}
@media(max-width:560px){#come.section{padding-top:58px;padding-bottom:64px}.step-cards{gap:16px}.step-card{border-radius:25px;grid-template-rows:156px auto}.step-copy{padding:21px 20px 23px}.step-copy h3{font-size:23px}.step-copy p{font-size:14px}.step-art svg{height:116px}.how-note{align-items:flex-start;font-size:13px}}
'''
if '/* Visual how-it-works section */' not in s:
    s=s.replace('</style>',css+'\n</style>')

section='''<section class="section" id="come"><div class="wrap">
<div class="how-head"><div><div class="eyebrow">Come funziona</div><h2 class="title">Quattro passaggi.<br>Facili da capire.</h2></div><p class="sub">Ogni richiesta segue un percorso semplice e visivo. L'obiettivo è far usare Tanto Ci Vai anche a chi non è abituato alle app.</p></div>
<div class="step-cards">
<article class="step-card"><div class="step-art"><div class="step-number">1</div><svg viewBox="0 0 280 150" aria-hidden="true"><rect x="34" y="32" width="92" height="88" rx="18" fill="#fff" opacity=".96"/><path d="M56 53h49l-6 42H63z" fill="#dff0ff"/><path d="M67 53c0-13 8-22 18-22s18 9 18 22" fill="none" stroke="#0b66ff" stroke-width="7" stroke-linecap="round"/><circle cx="82" cy="72" r="10" fill="#58c942"/><path d="M82 61c2-7 7-10 13-9" fill="none" stroke="#168b5b" stroke-width="4" stroke-linecap="round"/><rect x="142" y="45" width="98" height="64" rx="18" fill="#fff" opacity=".9"/><circle cx="168" cy="77" r="16" fill="#ffe7ec"/><path d="M168 67v20M158 77h20" stroke="#e53f61" stroke-width="6" stroke-linecap="round"/><path d="M193 65h27M193 79h22M193 93h17" stroke="#b8c8db" stroke-width="6" stroke-linecap="round"/></svg></div><div class="step-copy"><h3>Scegli il servizio</h3><p>Spesa, farmacia, pacco oppure una piccola commissione. Poche scelte grandi e chiare.</p><div class="step-tags"><span class="step-chip">Spesa</span><span class="step-chip">Farmacia</span><span class="step-chip">Pacco</span><span class="step-chip">Altro</span></div></div></article>
<article class="step-card"><div class="step-art"><div class="step-number">2</div><svg viewBox="0 0 280 150" aria-hidden="true"><path d="M28 32l66-16 57 17 72-17 29 14v91l-64 15-60-17-70 17-30-14z" fill="#fff" opacity=".94"/><path d="M94 17v101M151 34v83M222 17v104" stroke="#a8dcd8" stroke-width="4"/><path d="M56 99c34-41 63-49 91-25s49 23 77-11" fill="none" stroke="#08cdb0" stroke-width="8" stroke-linecap="round" stroke-dasharray="4 13"/><path d="M151 27c-20 0-35 15-35 34 0 27 35 55 35 55s35-28 35-55c0-19-15-34-35-34z" fill="#0b66ff"/><circle cx="151" cy="61" r="12" fill="#fff"/></svg></div><div class="step-copy"><h3>Indica il ritiro</h3><p>Cerca il luogo, usa il GPS oppure tocca direttamente il punto esatto sulla mappa.</p><div class="step-tags"><span class="step-chip">GPS</span><span class="step-chip">Mappa</span><span class="step-chip">Pin manuale</span></div></div></article>
<article class="step-card"><div class="step-art"><div class="step-number">3</div><svg viewBox="0 0 280 150" aria-hidden="true"><path d="M39 107c31-48 55-42 85-19s50 28 82-11" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-dasharray="2 15" opacity=".9"/><path d="M185 54l37-31 38 31v57h-75z" fill="#fff" opacity=".96"/><path d="M177 58l45-38 46 38" fill="none" stroke="#efeaff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/><rect x="213" y="78" width="20" height="33" rx="4" fill="#8a6cff"/><path d="M71 23c-18 0-32 14-32 31 0 25 32 51 32 51s32-26 32-51c0-17-14-31-32-31z" fill="#fff"/><circle cx="71" cy="54" r="11" fill="#8a6cff"/></svg></div><div class="step-copy"><h3>Inserisci la consegna</h3><p>Città, via e civico restano chiari. Il runner vede immediatamente dove deve arrivare.</p><div class="step-tags"><span class="step-chip">Città</span><span class="step-chip">Via</span><span class="step-chip">Civico</span></div></div></article>
<article class="step-card"><div class="step-art"><div class="step-number">4</div><svg viewBox="0 0 280 150" aria-hidden="true"><circle cx="80" cy="112" r="23" fill="#fff" opacity=".96"/><circle cx="80" cy="112" r="11" fill="#159264"/><circle cx="210" cy="112" r="23" fill="#fff" opacity=".96"/><circle cx="210" cy="112" r="11" fill="#159264"/><path d="M82 106l28-44h48l25 44h-45l-18-25-18 25z" fill="#fff" opacity=".96"/><path d="M154 62h41l17 28h-39z" fill="#dff8e8"/><rect x="126" y="38" width="48" height="31" rx="7" fill="#fff"/><path d="M139 53h22" stroke="#58c942" stroke-width="6" stroke-linecap="round"/><circle cx="105" cy="47" r="15" fill="#fff"/><path d="M106 62l17 25" stroke="#fff" stroke-width="11" stroke-linecap="round"/><path d="M93 73l23 3" stroke="#fff" stroke-width="10" stroke-linecap="round"/></svg></div><div class="step-copy"><h3>Un runner accetta</h3><p>Segue il percorso, conferma il ritiro e aggiorna la consegna fino all'arrivo.</p><div class="step-tags"><span class="step-chip">Ritiro</span><span class="step-chip">Navigazione</span><span class="step-chip">Consegna</span></div></div></article>
</div>
<div class="how-note"><div class="how-note-icon">✓</div><div><b>Pensato per essere semplice davvero.</b><br>Testi grandi, pochi passaggi e possibilità di correggere il punto sulla mappa quando un'attività non è aggiornata.</div></div>
</div></section>'''

pattern=r'<section class="section" id="come">.*?</section>'
ns,n=re.subn(pattern,section,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f'how section replacement count={n}')
p.write_text(ns,encoding='utf-8')
