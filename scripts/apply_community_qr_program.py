from pathlib import Path

index = Path('index.html')
html = index.read_text(encoding='utf-8')

qr_tag = '<script src="./community-qr.js?v=1"></script>'
notify_tag = '<script src="./community-notifications.js?v=1"></script>'

if qr_tag not in html:
    if notify_tag not in html:
        raise SystemExit('community notifications script tag not found')
    html = html.replace(notify_tag, qr_tag + '\n' + notify_tag, 1)
    index.write_text(html, encoding='utf-8')

qr = Path('community-qr.js')
text = qr.read_text(encoding='utf-8')
text = text.replace("'\\\"':'&quot',", "'\\\"':'&quot;',")
qr.write_text(text, encoding='utf-8')

print('Community QR program wired into index.html')
