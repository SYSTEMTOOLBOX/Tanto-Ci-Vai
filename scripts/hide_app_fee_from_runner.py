from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
old = '<span class="pill money">Compenso ${euro(r.compenso_rider)}</span><span class="pill">fee app ${euro(r.commissione_app)}</span>'
new = '<span class="pill money">Compenso ${euro(r.compenso_rider)}</span>${mine?`<span class="pill">Servizio app ${euro(r.commissione_app)}</span>`:``}'
if old not in s:
    raise SystemExit('fee app anchor not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('App fee hidden from runner views; visible only to requester')
