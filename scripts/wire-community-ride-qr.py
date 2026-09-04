from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
needle='<script src="./community-notifications.js?v=1"></script>'
tag='<script src="./community-ride-qr.js?v=1"></script>'
if tag not in s:
    if needle not in s:
        raise SystemExit('community notifications marker not found')
    s=s.replace(needle, tag+'\n'+needle,1)
p.write_text(s,encoding='utf-8')
print('community ride QR wired')
