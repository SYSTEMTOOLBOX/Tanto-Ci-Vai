from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
repls = {
    'manifest.webmanifest?v=2': 'manifest.webmanifest?v=3',
    'assets/tcv-splash-logo.jpg?v=2': 'assets/tcv-splash-logo.jpg?v=3',
    "const TCV_SPLASH_LOGO='assets/tcv-splash-logo.jpg?v=2';": "const TCV_SPLASH_LOGO='assets/tcv-splash-logo.jpg?v=3';",
    "navigator.serviceWorker.register('./sw.js?v=9'": "navigator.serviceWorker.register('./sw.js?v=10'",
}
for old, new in repls.items():
    s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
