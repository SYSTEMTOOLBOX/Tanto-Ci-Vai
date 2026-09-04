from pathlib import Path
import re

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')

if 'community-profile.js' not in html:
    pat = r'(<script\s+src=["\']\.?/community-safety\.js\?v=\d+["\']\s*></script>)'
    html, n = re.subn(pat, r'\1\n<script src="./community-profile.js?v=1"></script>', html, count=1)
    if n != 1:
        raise SystemExit('community-safety loader not found')
else:
    html = re.sub(r'community-profile\.js\?v=\d+', 'community-profile.js?v=1', html, count=1)

idx.write_text(html, encoding='utf-8')

routes = Path('community-routes.js')
js = routes.read_text(encoding='utf-8')
if 'TCV_PUBLIC_PROFILE_BUTTON_V1' not in js:
    old = "<div class=\"row\">Servizio TCV: ${money(PLATFORM_FEE)} separato</div><button onclick=\"tcvOpenRideFromTrip('${t.id}')\">RICHIEDI UN POSTO</button>"
    new = "<div class=\"row\">Servizio TCV: ${money(PLATFORM_FEE)} separato</div><button style=\"background:#fff;color:#0b66ff;border:1px solid #b9d2ff\" onclick=\"tcvOpenCommunityUserProfile('${t.user_id}')\">👤 VEDI PROFILO</button><button onclick=\"tcvOpenRideFromTrip('${t.id}')\">RICHIEDI UN POSTO</button>"
    if old not in js:
        raise SystemExit('Community trip popup target not found')
    js = js.replace(old, new, 1)
    js = js.replace('/* TCV_COMMUNITY_ROUTES_V1', '/* TCV_COMMUNITY_ROUTES_V1\n   TCV_PUBLIC_PROFILE_BUTTON_V1', 1)

routes.write_text(js, encoding='utf-8')
print('Community public profile enabled in Profile page and route popup')
