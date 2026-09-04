from pathlib import Path

index_path = Path('index.html')
ui_path = Path('community-ui-v2.js')

html = index_path.read_text(encoding='utf-8')
marker = "function renderProfile(){let pushState=tcvPushStatusText();profile.innerHTML=`"
end_marker = "// TCV_SHARE_PROFILE_V1"
if marker not in html or end_marker not in html:
    raise SystemExit('renderProfile markers not found')
start = html.index(marker)
end = html.index(end_marker, start)
block = html[start:end]

card = '''<div id="tcvCommunityProfileMainCard" class="req" style="margin:0 0 12px;border:2px solid #87b8ff;background:linear-gradient(180deg,#eef6ff,#fff)"><div style="display:flex;align-items:center;gap:12px"><div style="width:58px;height:58px;border-radius:50%;display:grid;place-items:center;background:#0b1834;color:#fff;font-size:24px">👤</div><div style="min-width:0;flex:1"><div style="font-size:9px;color:#0b66ff;font-weight:950;letter-spacing:.1em">PROFILO COMMUNITY</div><h3 style="margin:4px 0 3px;font-size:18px">Foto e identità per i passaggi</h3><p style="margin:0;font-size:10px;color:#69758d;line-height:1.45">Qui registri chi sei e carichi la fotografia reale che vedranno guidatori e passeggeri.</p></div></div><button class="btn primary full" style="margin-top:10px;padding:14px;font-size:12px" onclick="typeof tcvOpenCommunitySafetyProfile==='function'?tcvOpenCommunitySafetyProfile():alert('Profilo Community in caricamento. Riprova tra un istante.')">📸 CREA / MODIFICA PROFILO COMMUNITY</button></div>'''

needle = "</p></div>${walletMiniCard()}"
if 'id="tcvCommunityProfileMainCard"' not in block:
    if needle not in block:
        raise SystemExit('renderProfile insertion point not found')
    block = block.replace(needle, f"</p></div>{card}${{walletMiniCard()}}", 1)
    html = html[:start] + block + html[end:]

# Always force a fresh UI helper URL too, but the card now lives directly in index.html.
html = html.replace('community-ui-v2.js?v=3', 'community-ui-v2.js?v=4', 1)
index_path.write_text(html, encoding='utf-8')

ui = ui_path.read_text(encoding='utf-8')
needle_ui = "if(!host||host.classList.contains('hidden')||!window.SESSION?.user?.id)return;\n    if(document.getElementById('tcvMainCommunityProfileCard'))return;"
replacement_ui = "if(!host||host.classList.contains('hidden')||!window.SESSION?.user?.id)return;\n    if(document.getElementById('tcvCommunityProfileMainCard')||document.getElementById('tcvMainCommunityProfileCard'))return;"
if needle_ui in ui:
    ui = ui.replace(needle_ui, replacement_ui, 1)
elif 'tcvCommunityProfileMainCard' not in ui:
    raise SystemExit('Community UI duplicate guard not found')
ui_path.write_text(ui, encoding='utf-8')

print('Direct Community profile card embedded in renderProfile; helper cache bumped to v4')
