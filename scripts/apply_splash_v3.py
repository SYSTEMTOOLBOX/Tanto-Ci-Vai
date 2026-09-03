from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Keep cache-busting upgrades idempotent.
repls = {
    'manifest.webmanifest?v=2': 'manifest.webmanifest?v=3',
    'assets/tcv-splash-logo.jpg?v=2': 'assets/tcv-splash-logo.jpg?v=3',
    "const TCV_SPLASH_LOGO='assets/tcv-splash-logo.jpg?v=2';": "const TCV_SPLASH_LOGO='assets/tcv-splash-logo.jpg?v=3';",
    "navigator.serviceWorker.register('./sw.js?v=9'": "navigator.serviceWorker.register('./sw.js?v=10'",
    "navigator.serviceWorker.register('./sw.js?v=10'": "navigator.serviceWorker.register('./sw.js?v=11'",
}
for old, new in repls.items():
    s = s.replace(old, new)

old = '''    }else{
      wrap.innerHTML=`<img class="tcv-app-splash-logo" src="${TCV_SPLASH_LOGO}" alt="Tanto ci vai?">`;
      document.body.appendChild(wrap);
      setTimeout(()=>tcvFadeAndRemove(wrap,resolve),1000);
    }'''
new = '''    }else{
      // Returning opens use only the native PWA splash to avoid a double logo.
      resolve();
    }'''

if old in s:
    s = s.replace(old, new, 1)
elif 'Returning opens use only the native PWA splash' not in s:
    raise SystemExit('Startup splash block not found; refusing a silent patch')

p.write_text(s, encoding='utf-8')
