from pathlib import Path

p = Path('index.html')
text = p.read_text(encoding='utf-8')
tag = '<script src="./community-routes.js?v=1"></script>'

if tag not in text:
    if '</body>' not in text:
        raise SystemExit('Cannot find </body> in index.html')
    text = text.replace('</body>', f'{tag}\n</body>', 1)
    p.write_text(text, encoding='utf-8')
    print('Community routes script installed')
else:
    print('Community routes script already installed')
