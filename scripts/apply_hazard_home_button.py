from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')
old = 'openSheet(`<div class="sos-panel"><div class="sos-kicker">SEGNALAZIONE ALLA COMUNITÀ</div>'
new = 'openSheet(`<div class="sos-panel"><div class="sos-topbar"><button type="button" class="sos-home-top" style="grid-column:1/-1;width:100%" onclick="tcvGoHomeAfterAlert()">🏠 HOME</button></div><div class="sos-kicker">SEGNALAZIONE ALLA COMUNITÀ</div>'
if old not in text:
    raise SystemExit('Hazard report marker not found or already patched')
text = text.replace(old, new, 1)
text = text.replace("navigator.serviceWorker.register('./sw.js?v=8'", "navigator.serviceWorker.register('./sw.js?v=9'", 1)
path.write_text(text, encoding='utf-8')
