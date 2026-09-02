from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = '/* leaflet-modal-stacking-fix */'
if marker in s:
    print('Leaflet modal stacking fix already present')
    raise SystemExit(0)

fix = '''\n/* leaflet-modal-stacking-fix */\n.map-shell{isolation:isolate;z-index:0}\n.leaflet-container{z-index:1}\n.overlay{z-index:5000!important}\n.sheet{z-index:5100!important}\n'''

if '</style>' not in s:
    raise SystemExit('style closing tag not found')
s = s.replace('</style>', fix + '\n</style>', 1)
p.write_text(s, encoding='utf-8')
print('Applied Leaflet/modal z-index fix')
# trigger 2
