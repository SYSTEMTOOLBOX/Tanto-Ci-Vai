from pathlib import Path
import re

p = Path('presentazione.html')
s = p.read_text(encoding='utf-8')

hero_old = '''<div class="phone-stage"><div class="glow"></div><div class="floating f1"><b>4 servizi</b>Spesa · Farmacia<br>Pacco · Altro</div><div class="phone"><div class="phone-screen logo-only"><img src="assets/tcv-splash-logo.jpg" alt="Tanto Ci Vai"></div></div><div class="floating f2"><b>GPS + mappa</b>Ritiro e consegna<br>con punti precisi</div></div>'''
hero_new = '''<div class="phone-stage phone-clean-stage"><div class="glow"></div><div class="phone"><div class="phone-screen logo-only"><img src="assets/tcv-splash-logo.jpg" alt="Tanto Ci Vai"></div></div><div class="phone-notes"><div class="phone-note"><b>4 servizi</b><span>Spesa · Farmacia · Pacco · Altro</span></div><div class="phone-note"><b>GPS + mappa</b><span>Ritiro e consegna con punti precisi</span></div></div></div>'''
if hero_old not in s:
    raise SystemExit('hero block not found')
s = s.replace(hero_old, hero_new, 1)

step_start = s.index('<div class="step-cards">')
step_end = s.index('<div class="how-note">', step_start)
steps_new = '''<div class="step-cards photo-step-cards">
<article class="step-card"><div class="step-art photo-art"><div class="step-number">1</div><img loading="lazy" src="https://images.pexels.com/photos/1298473/pexels-photo-1298473.jpeg?auto=compress&cs=tinysrgb&w=1400" alt="Persona che usa lo smartphone per scegliere un servizio"></div><div class="step-copy"><h3>Scegli il servizio</h3><p>Spesa, farmacia, pacco oppure una piccola commissione. Poche scelte grandi e chiare.</p><div class="step-tags"><span class="step-chip">Spesa</span><span class="step-chip">Farmacia</span><span class="step-chip">Pacco</span><span class="step-chip">Altro</span></div></div></article>
<article class="step-card"><div class="step-art photo-art"><div class="step-number">2</div><img loading="lazy" src="https://images.pexels.com/photos/36802400/pexels-photo-36802400.jpeg?auto=compress&cs=tinysrgb&w=1400" alt="Piccolo paese italiano dove indicare il punto di ritiro"></div><div class="step-copy"><h3>Indica il ritiro</h3><p>Cerca il luogo, usa il GPS oppure tocca direttamente il punto esatto sulla mappa.</p><div class="step-tags"><span class="step-chip">GPS</span><span class="step-chip">Mappa</span><span class="step-chip">Pin manuale</span></div></div></article>
<article class="step-card"><div class="step-art photo-art"><div class="step-number">3</div><img loading="lazy" src="https://images.pexels.com/photos/7345427/pexels-photo-7345427.jpeg?auto=compress&cs=tinysrgb&w=1400" alt="Consegna della spesa a una persona anziana a domicilio"></div><div class="step-copy"><h3>Inserisci la consegna</h3><p>Città, via e civico restano chiari. Il runner vede immediatamente dove deve arrivare.</p><div class="step-tags"><span class="step-chip">Città</span><span class="step-chip">Via</span><span class="step-chip">Civico</span></div></div></article>
<article class="step-card"><div class="step-art photo-art"><div class="step-number">4</div><img loading="lazy" src="https://images.pexels.com/photos/9461620/pexels-photo-9461620.jpeg?auto=compress&cs=tinysrgb&w=1400" alt="Ritiro di una pizza pronta da consegnare"></div><div class="step-copy"><h3>Un runner accetta</h3><p>Segue il percorso, conferma il ritiro e aggiorna la consegna fino all'arrivo.</p><div class="step-tags"><span class="step-chip">Ritiro</span><span class="step-chip">Navigazione</span><span class="step-chip">Consegna</span></div></div></article>
</div>
'''
s = s[:step_start] + steps_new + s[step_end:]

pizza_section = '''
<section class="pizza-impact"><div class="wrap"><div class="pizza-shell"><div class="pizza-photo"><img loading="lazy" src="https://images.pexels.com/photos/9461620/pexels-photo-9461620.jpeg?auto=compress&cs=tinysrgb&w=1800" alt="Ritiro di una pizza in pizzeria"></div><div class="pizza-copy"><div class="pizza-kicker">UN CASO D'USO CHE NEI PICCOLI PAESI MANCA DAVVERO</div><h2>La pizza a domicilio.<br><span>Anche dove Glovo e Deliveroo non arrivano.</span></h2><p>Ordini la pizza alla tua pizzeria di fiducia. Un runner della zona che deve già passare da lì può ritirarla e portartela a casa.</p><div class="pizza-points"><div><b>🍕 Ritiro locale</b><span>Pizzeria, gastronomia o altro locale della zona.</span></div><div><b>🚗 Un viaggio può servire più persone</b><span>L'obiettivo del pilot è permettere di raggruppare richieste compatibili della stessa pizzeria nello stesso giro.</span></div><div><b>💶 Più convenienza per il runner</b><span>Una piccola consegna può trasformare uno spostamento che avrebbe fatto comunque in un'entrata extra.</span></div><div><b>🌱 Meno auto in giro</b><span>Più ordini nello stesso tragitto significano meno viaggi separati e potenzialmente meno CO₂.</span></div></div></div></div></div></section>
'''
marker = '<section class="section white" id="perchi">'
if marker not in s:
    raise SystemExit('perchi marker not found')
s = s.replace(marker, pizza_section + marker, 1)

css = '''
/* PHOTO_IMPACT_V1 */
.phone-clean-stage{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:650px;padding:20px 0 0}.phone-clean-stage .phone{z-index:2}.phone-notes{position:relative;z-index:4;width:min(440px,96%);display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:30px}.phone-note{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px 16px;box-shadow:0 14px 34px rgba(7,26,61,.11);text-align:left}.phone-note b{display:block;color:var(--blue);font-size:16px;margin-bottom:3px}.phone-note span{display:block;color:#465875;font-size:12px;font-weight:800;line-height:1.35}
.photo-step-cards .step-card{grid-template-rows:235px 1fr}.photo-art{padding:0!important;display:block!important;background:#0b1834!important}.photo-art:after{display:none}.photo-art:before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,17,38,.05),rgba(4,17,38,.08) 48%,rgba(4,17,38,.46));z-index:1}.photo-art img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(1.08) contrast(1.04)}.photo-art .step-number{z-index:3}.photo-step-cards .step-card:nth-child(2) .photo-art img{object-position:center 58%}.photo-step-cards .step-card:nth-child(3) .photo-art img{object-position:center 42%}.photo-step-cards .step-card:nth-child(4) .photo-art img{object-position:center 45%}
.pizza-impact{padding:92px 0;background:linear-gradient(180deg,#fff 0%,#fff6ef 100%)}.pizza-shell{overflow:hidden;display:grid;grid-template-columns:1.02fr .98fr;border-radius:38px;background:#fff;box-shadow:0 30px 80px rgba(83,38,7,.16);border:1px solid #f1dfd2}.pizza-photo{min-height:620px;position:relative;overflow:hidden}.pizza-photo:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent 60%,rgba(255,255,255,.12))}.pizza-photo img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(1.08) contrast(1.04)}.pizza-copy{padding:54px 50px;display:flex;flex-direction:column;justify-content:center}.pizza-kicker{font-size:11px;font-weight:1000;letter-spacing:.11em;color:#e86124}.pizza-copy h2{font-size:clamp(38px,5vw,58px);line-height:1;letter-spacing:-.055em;margin:12px 0 20px}.pizza-copy h2 span{color:#df5d21}.pizza-copy>p{font-size:18px;line-height:1.62;color:#675c57;margin:0}.pizza-points{display:grid;gap:12px;margin-top:28px}.pizza-points div{padding:16px 18px;border-radius:18px;background:#fff8f3;border:1px solid #f5e0d1}.pizza-points b{display:block;color:#2d211d;font-size:15px;margin-bottom:4px}.pizza-points span{display:block;color:#7b6a62;font-size:13px;line-height:1.45}
@media(max-width:900px){.phone-clean-stage{min-height:610px}.pizza-shell{grid-template-columns:1fr}.pizza-photo{min-height:420px}.pizza-copy{padding:38px 30px}.photo-step-cards .step-card{grid-template-rows:220px auto}}
@media(max-width:560px){.phone-clean-stage{min-height:600px}.phone-notes{grid-template-columns:1fr;width:min(360px,96%);margin-top:24px}.phone-note{text-align:center}.photo-step-cards .step-card{grid-template-rows:220px auto}.photo-art img{min-height:220px}.pizza-impact{padding:62px 0}.pizza-shell{border-radius:28px}.pizza-photo{min-height:330px}.pizza-copy{padding:30px 22px}.pizza-copy h2{font-size:38px}.pizza-copy>p{font-size:16px}}
'''
if '/* PHOTO_IMPACT_V1 */' not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print('photo/pizza landing patch applied')
