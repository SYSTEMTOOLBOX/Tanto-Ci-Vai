from pathlib import Path
import re

# 1) SOS / hazard push: open Google Maps Directions (native app when installed) instead of a plain search page.
edge = Path('supabase/functions/send-help-push/index.ts')
text = edge.read_text(encoding='utf-8')
old = """    const mapUrl = hasPoint\n      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${claimed.lat},${claimed.lng}`)}`\n      : './';"""
new = """    const mapUrl = hasPoint\n      ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${claimed.lat},${claimed.lng}`)}&dir_action=navigate`\n      : './';"""
if old not in text:
    raise SystemExit('Expected mapUrl block not found in send-help-push')
edge.write_text(text.replace(old, new, 1), encoding='utf-8')

# 2) Treat hazard notifications like SOS notifications when the user taps them.
sw = Path('sw.js')
s = sw.read_text(encoding='utf-8')
s = s.replace("const isHelp=data.event==='help_alert';", "const isHelp=data.event==='help_alert'||data.event==='hazard_alert';")
s = s.replace("if(data.event==='help_alert'&&url&&url!=='./'){", "if((data.event==='help_alert'||data.event==='hazard_alert')&&url&&url!=='./'){")
sw.write_text(s, encoding='utf-8')

# 3) Bump the service-worker registration URL so phones fetch the new worker immediately.
index = Path('index.html')
i = index.read_text(encoding='utf-8')
i2, n = re.subn(r"sw\.js\?v=\d+", "sw.js?v=4", i)
if n == 0:
    # If the app registers sw.js without a version, add one.
    i2, n2 = re.subn(r"(['\"])sw\.js\1", r"\1sw.js?v=4\1", i, count=1)
    if n2 == 0:
        print('WARNING: service worker registration string not found; sw.js still updates normally on browser checks')
index.write_text(i2, encoding='utf-8')

print('Applied Maps navigation push update')
