from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s
marker = '/* TCV_ULTRA_CLEAN_HOME_V1 */'

if marker in s:
    print('Ultra clean Home patch already applied')
    raise SystemExit(0)

old_home = '''<main id="home"><button class="urgent-help" onclick="openCommunityHelp()"><div class="sosico">🆘</div><div><b>AIUTO SUBITO</b><span>1 tocco · prende il GPS · se non annulli parte automaticamente tra 30 secondi</span></div><div class="sosarrow">→</div></button><div class="sect"><h2>Cosa vuoi fare?</h2><span>Servizio attivo</span></div><section class="actions"><button class="action help" onclick="openNewRequest()"><div class="ico">🙋</div><b>Mi serve una mano</b><p>Pubblica una commissione con ritiro, consegna e compenso.</p><div class="arrow">→</div></button><button class="action go" onclick="openTripSearch()"><div class="ico">🚗</div><b>Sto già andando</b><p>Calcola la tua strada reale e trova richieste compatibili.</p><div class="arrow">→</div></button></section><div class="sect"><h2>Richieste disponibili</h2><span id="feedStatus">Sincronizzate</span></div><section id="feed" class="feed"></section></main>
<main id="missions" class="hidden"></main><main id="myreq" class="hidden"></main><main id="mapPage" class="hidden"></main><main id="wallet" class="hidden"></main><main id="profile" class="hidden"></main>'''

new_home = '''<main id="home" class="home-clean"><div class="home-sos-wrap"><button class="home-sos-round" onclick="openCommunityHelp()" aria-label="SOS aiuto subito"><span class="home-sos-icon">🆘</span><b>SOS</b><small>30 SEC</small></button></div><section class="home-clean-actions"><button class="home-clean-action pickup" onclick="page('available')"><span class="home-clean-ico">📦</span><div><b>Fai un ritiro</b><small>Vedi le richieste disponibili</small></div><span class="home-clean-arrow">→</span></button><button class="home-clean-action trip" onclick="openTripSearch()"><span class="home-clean-ico">🚗</span><div><b>Sto già andando</b><small>Trova richieste sulla tua strada</small></div><span class="home-clean-arrow">→</span></button><button class="home-clean-action helpme" onclick="openNewRequest()"><span class="home-clean-ico">🙋</span><div><b>Mi serve una mano</b><small>Pubblica una richiesta</small></div><span class="home-clean-arrow">→</span></button></section></main>
<main id="available" class="hidden"><div class="pagehead"><div class="k">RITIRI DISPONIBILI</div><h2>📦 Fai un ritiro</h2><p>Qui trovi le richieste aperte della comunità.</p></div><button class="btn outline full" style="margin-bottom:12px" onclick="page('home')">← Torna alla Home</button><div class="sect"><h2>Richieste disponibili</h2><span id="feedStatus">Sincronizzate</span></div><section id="feed" class="feed"></section></main>
<main id="missions" class="hidden"></main><main id="myreq" class="hidden"></main><main id="mapPage" class="hidden"></main><main id="wallet" class="hidden"></main><main id="profile" class="hidden"></main>'''

if old_home not in s:
    raise SystemExit('Home anchor not found')
s = s.replace(old_home, new_home, 1)

old_page = "function page(p){['home','missions','myreq','mapPage','wallet','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='missions')renderMissions();if(p==='myreq')renderMyRequests();if(p==='mapPage')renderMapPage();if(p==='wallet'){renderWallet();loadWallet().then(renderWallet).catch(e=>console.warn(e))}if(p==='profile')renderProfile();scrollTo(0,0)}"
new_page = "function page(p){['home','available','missions','myreq','mapPage','wallet','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='available')renderFeed();if(p==='missions')renderMissions();if(p==='myreq')renderMyRequests();if(p==='mapPage')renderMapPage();if(p==='wallet'){renderWallet();loadWallet().then(renderWallet).catch(e=>console.warn(e))}if(p==='profile')renderProfile();scrollTo(0,0)}"
if old_page not in s:
    raise SystemExit('page() anchor not found')
s = s.replace(old_page, new_page, 1)

old_render = "function renderAll(){renderFeed();renderStats();if(!missions.classList.contains('hidden'))renderMissions();if(!myreq.classList.contains('hidden'))renderMyRequests();if(!document.getElementById('wallet').classList.contains('hidden'))renderWallet();if(!profile.classList.contains('hidden'))renderProfile()}"
new_render = "function renderAll(){renderFeed();if(!missions.classList.contains('hidden'))renderMissions();if(!myreq.classList.contains('hidden'))renderMyRequests();if(!document.getElementById('wallet').classList.contains('hidden'))renderWallet();if(!profile.classList.contains('hidden'))renderProfile()}"
if old_render not in s:
    raise SystemExit('renderAll() anchor not found')
s = s.replace(old_render, new_render, 1)

css = r'''
/* TCV_ULTRA_CLEAN_HOME_V1 */
.home-clean{padding-top:10px!important}
.home-sos-wrap{display:grid;place-items:center;padding:8px 0 22px}
.home-sos-round{width:122px;height:122px;border-radius:50%;border:6px solid #fff;background:radial-gradient(circle at 35% 28%,#ff5267,#d71836 58%,#a60720);color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 14px 34px rgba(183,18,45,.34),inset 0 0 0 2px rgba(255,255,255,.22);padding:0;line-height:1;cursor:pointer}
.home-sos-round:active{transform:scale(.97)}
.home-sos-icon{font-size:35px;line-height:1;margin-bottom:4px}.home-sos-round b{font-size:24px;letter-spacing:.04em}.home-sos-round small{font-size:8px;font-weight:950;letter-spacing:.12em;margin-top:5px;opacity:.92}
.home-clean-actions{display:grid;gap:11px}.home-clean-action{width:100%;min-height:88px;border:1px solid var(--line);border-radius:22px;background:#fff;box-shadow:0 9px 24px rgba(13,38,84,.07);padding:13px 15px;display:grid;grid-template-columns:58px 1fr 28px;align-items:center;gap:12px;text-align:left;color:var(--ink)}
.home-clean-action:active{transform:scale(.99)}.home-clean-ico{width:58px;height:58px;border-radius:18px;display:grid;place-items:center;font-size:28px;background:#eef5ff}.home-clean-action.trip .home-clean-ico{background:#eafff9}.home-clean-action.helpme .home-clean-ico{background:#fff4dc}
.home-clean-action b{display:block;font-size:18px;letter-spacing:-.025em}.home-clean-action small{display:block;color:var(--muted);font-size:9px;font-weight:750;margin-top:4px;line-height:1.35}.home-clean-arrow{font-size:24px;font-weight:950;color:var(--blue);text-align:right}
@media(max-width:380px){.home-sos-round{width:112px;height:112px}.home-clean-action{min-height:82px;grid-template-columns:52px 1fr 24px}.home-clean-ico{width:52px;height:52px;font-size:25px}}
'''
if '</style>' not in s:
    raise SystemExit('style close tag not found')
s = s.replace('</style>', css + '</style>', 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Home reduced to SOS + Fai un ritiro + Sto gia andando + Mi serve una mano; feed moved to separate page')
