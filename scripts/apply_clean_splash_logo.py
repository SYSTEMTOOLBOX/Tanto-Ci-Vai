from pathlib import Path
import re

index = Path('index.html')
s = index.read_text(encoding='utf-8')
s = re.sub(r'assets/tcv-splash-logo\.jpg(?:\?v=\d+)?', 'assets/tcv-splash-logo.jpg?v=2', s)
s = re.sub(r'manifest\.webmanifest\?v=\d+', 'manifest.webmanifest?v=2', s)
s = re.sub(r'sw\.js\?v=\d+', 'sw.js?v=9', s)
index.write_text(s, encoding='utf-8')

manifest = Path('manifest.webmanifest')
m = manifest.read_text(encoding='utf-8')
m = re.sub(r'assets/tcv-splash-logo\.jpg(?:\?v=\d+)?', 'assets/tcv-splash-logo.jpg?v=2', m)
m = re.sub(r'"sizes"\s*:\s*"340x340"', '"sizes": "768x768"', m)
manifest.write_text(m, encoding='utf-8')

sw = Path('sw.js')
w = sw.read_text(encoding='utf-8')
w = re.sub(r'assets/tcv-splash-logo\.jpg(?:\?v=\d+)?', 'assets/tcv-splash-logo.jpg?v=2', w)
sw.write_text(w, encoding='utf-8')

print('clean splash logo cache-bust applied')
