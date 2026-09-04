from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')

# Marker + constants.
if 'TCV_ANTIPROFIT_COST_V1' not in s:
    s = s.replace('TCV_TOWN_PREFIX_FIX_V1', 'TCV_TOWN_PREFIX_FIX_V1\n   TCV_ANTIPROFIT_COST_V1', 1)

s = s.replace('transparent €0.35/km/person contribution and active routes on safety map.',
              'anti-profit Community contribution, recurring routes and active routes on safety map.')

old_consts = "  const RATE_PER_KM=0.35;\n  const PLATFORM_FEE=0.50;\n"
new_consts = """  // Community anti-profit model. The passenger contribution is capped so the\n  // total collected from at most 3 passengers cannot exceed an estimated all-in\n  // vehicle cost of €0.45/km (fuel + maintenance + tyres + insurance/tax + wear/depreciation).\n  const BASE_RATE_PER_KM=0.15;\n  const VEHICLE_COST_PER_KM=0.45;\n  const MAX_COMMUNITY_PASSENGERS=3;\n  const RATE_PER_KM=BASE_RATE_PER_KM;\n  const PLATFORM_FEE=0.50;\n  function antiProfitContribution(distanceKm,passengers=1){\n    const km=Math.max(0,num(distanceKm)),pax=Math.max(1,Math.min(MAX_COMMUNITY_PASSENGERS,Number(passengers)||1));\n    const rate=Math.min(BASE_RATE_PER_KM,VEHICLE_COST_PER_KM/pax);\n    const perPerson=km*rate,totalDriver=perPerson*pax,maxVehicleCost=km*VEHICLE_COST_PER_KM;\n    return {km,pax,rate,perPerson,totalDriver,maxVehicleCost};\n  }\n"""
if old_consts in s:
    s = s.replace(old_consts, new_consts, 1)
elif 'const BASE_RATE_PER_KM=0.15;' not in s:
    raise SystemExit('Community rate constants anchor not found')

# Limit Community paid seats to three so 3 x €0.15/km = €0.45/km max total recovery.
s = s.replace("${[1,2,3,4,5,6,7].map(n=>", "${[1,2,3].map(n=>", 1)
s = s.replace('<option value="1">1 persona</option><option value="2">2 persone</option><option value="3">3 persone</option><option value="4">4 persone</option><option value="5">5 persone</option><option value="6">6 persone</option>',
              '<option value="1">1 persona</option><option value="2">2 persone</option><option value="3">3 persone</option>', 1)
s = s.replace("Math.max(1,Math.min(6,Number(document.getElementById('ridePassengers')?.value||1)))",
              "Math.max(1,Math.min(MAX_COMMUNITY_PASSENGERS,Number(document.getElementById('ridePassengers')?.value||1)))", 1)

# Existing trip cards.
s = s.replace("<b>${money(num(t.distance_km)*RATE_PER_KM)}</b> a persona · €0,35/km",
              "<b>${money(antiProfitContribution(num(t.distance_km),Number(t.seats||1)).perPerson)}</b> a persona · fino a €0,15/km · tetto €0,45/km auto", 1)

# Main Community hero.
s = s.replace('CONTRIBUTO TRASPARENTE: € 0,35 / KM / PERSONA',
              'CONTRIBUTO ANTI-PROFITTO: FINO A € 0,15 / KM / PERSONA', 1)
s = s.replace('Tanto Ci Vai calcola la distanza stradale reale. Il contributo del passeggero e la commissione TCV da € 0,50 vengono mostrati separatamente.',
              'La app calcola la strada reale e applica un tetto: con massimo 3 passeggeri i contributi non superano € 0,45/km complessivi, costo auto stimato che comprende carburante, manutenzione, pneumatici, assicurazione/bollo, usura e svalutazione. Il servizio TCV da € 0,50 resta separato.', 1)

# Trip preview: calculate with currently selected seats and show the all-in cap.
old_preview = """  function tcvPreviewHtml(r){\n    if(!r||!num(r.distanceKm))return '<div class=\"notice\">Percorso non ancora calcolato.</div>';\n    const pp=num(r.distanceKm)*RATE_PER_KM;return `<div class=\"tcv-route-preview\"><strong>${num(r.distanceKm).toFixed(1)} km · ${money(pp)} a persona</strong><br>Contributo conducente: ${money(RATE_PER_KM)}/km/persona${r.durationMin?` · circa ${Math.round(r.durationMin)} min`:''}.<br>Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato al momento della prenotazione.</div>`\n  }\n"""
new_preview = """  function tcvPreviewHtml(r){\n    if(!r||!num(r.distanceKm))return '<div class=\"notice\">Percorso non ancora calcolato.</div>';\n    const seats=Math.max(1,Math.min(MAX_COMMUNITY_PASSENGERS,Number(document.getElementById('tcvTripSeats')?.value||3))),c=antiProfitContribution(r.distanceKm,seats);\n    return `<div class=\"tcv-route-preview\"><strong>${num(r.distanceKm).toFixed(1)} km · ${money(c.perPerson)} a persona</strong><br>Quota: ${money(c.rate)}/km/persona${r.durationMin?` · circa ${Math.round(r.durationMin)} min`:''}.<br>Con ${seats} ${seats===1?'passeggero':'passeggeri'}: massimo <b>${money(c.totalDriver)}</b> al conducente. Costo auto stimato: <b>${money(c.maxVehicleCost)}</b> (${money(VEHICLE_COST_PER_KM)}/km, incluse usura e spese auto).<br>Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato al momento della prenotazione.</div>`\n  }\n"""
if old_preview in s:
    s = s.replace(old_preview, new_preview, 1)
elif 'function tcvPreviewHtml' in s and 'Costo auto stimato' not in s:
    raise SystemExit('Trip preview anchor changed')

# Re-render preview when seats change.
s = s.replace('<select id="tcvTripSeats">', '<select id="tcvTripSeats" onchange="if(draft.route){document.getElementById(\'tcvTripPreview\').innerHTML=tcvPreviewHtml(draft.route)}">', 1)

# Saved trip confirmation.
s = s.replace("${money(payload.distance_km*RATE_PER_KM)} a persona · €0,35/km/persona",
              "${money(antiProfitContribution(payload.distance_km,payload.seats).perPerson)} a persona · fino a €0,15/km/persona · tetto anti-profitto €0,45/km auto", 1)

# Ride-request hero.
s = s.replace('€ 0,35/km a persona · chi passa di lì può offrirti un posto',
              'fino a € 0,15/km a persona · tetto anti-profitto sui costi auto', 1)

# Ride price box.
old_ride = """  function ridePriceHtml(r){\n    if(!r||!num(r.distanceKm))return '<div class=\"notice\">Percorso non ancora calcolato.</div>';\n    const persons=Math.max(1,Number(document.getElementById('ridePassengers')?.value||1)),per=num(r.distanceKm)*RATE_PER_KM,driver=per*persons,total=driver+PLATFORM_FEE;\n    return `<div class=\"tcv-ride-price\"><b>${num(r.distanceKm).toFixed(1)} km</b><br>Contributo: <b>${money(per)} a persona</b> (${money(RATE_PER_KM)}/km).<br>${persons>1?`${persons} persone → contributo totale conducente <b>${money(driver)}</b>.<br>`:''}Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato.<br>Totale previsto: <b>${money(total)}</b>.</div>`\n  }\n"""
new_ride = """  function ridePriceHtml(r){\n    if(!r||!num(r.distanceKm))return '<div class=\"notice\">Percorso non ancora calcolato.</div>';\n    const persons=Math.max(1,Math.min(MAX_COMMUNITY_PASSENGERS,Number(document.getElementById('ridePassengers')?.value||1))),c=antiProfitContribution(r.distanceKm,persons),total=c.totalDriver+PLATFORM_FEE;\n    return `<div class=\"tcv-ride-price\"><b>${num(r.distanceKm).toFixed(1)} km</b><br>Contributo: <b>${money(c.perPerson)} a persona</b> (${money(c.rate)}/km).<br>${persons>1?`${persons} persone → contributo totale conducente <b>${money(c.totalDriver)}</b>.<br>`:''}Tetto anti-profitto: costo auto stimato <b>${money(c.maxVehicleCost)}</b> (${money(VEHICLE_COST_PER_KM)}/km: carburante + manutenzione + gomme + assicurazione/bollo + usura/svalutazione).<br>Servizio Tanto Ci Vai: <b>${money(PLATFORM_FEE)}</b> separato.<br>Totale previsto: <b>${money(total)}</b>.</div>`\n  }\n"""
if old_ride in s:
    s = s.replace(old_ride, new_ride, 1)
elif 'function ridePriceHtml' in s and 'Tetto anti-profitto: costo auto stimato' not in s:
    raise SystemExit('Ride price anchor changed')

# Persist new contribution per person using the anti-profit function.
s = s.replace("per=num(rideDraft.route.distanceKm)*RATE_PER_KM;\n      const payload=",
              "per=antiProfitContribution(rideDraft.route.distanceKm,passengers).perPerson;\n      const payload=", 1)

# Map popup.
s = s.replace("const per=num(t.distance_km)*RATE_PER_KM;return `<div class=\"tcv-map-popup\"",
              "const c=antiProfitContribution(t.distance_km,Number(t.seats||1)),per=c.perPerson;return `<div class=\"tcv-map-popup\"", 1)
s = s.replace('<div class="row">📏 ${num(t.distance_km).toFixed(1)} km · 💶 ${money(per)} / persona</div>',
              '<div class="row">📏 ${num(t.distance_km).toFixed(1)} km · 💶 ${money(per)} / persona · anti-profitto</div>', 1)

# Cache-bust Community JS without assuming the current version.
idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2, n = re.subn(r'community-routes\.js\?v=\d+', 'community-routes.js?v=8', html, count=1)
if n == 0:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

p.write_text(s, encoding='utf-8')
print('Applied Community anti-profit model: €0.15/km/person, max 3 passengers, €0.45/km all-in vehicle-cost cap')
