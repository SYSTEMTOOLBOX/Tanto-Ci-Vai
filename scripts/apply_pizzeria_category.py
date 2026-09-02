from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

repls=[
("Per Spesa, Farmacia, Pacco e Altro puoi usare il GPS oppure scegliere una città o frazione.","Per Spesa, Farmacia, Pizzeria, Pacco e Altro puoi usare il GPS oppure scegliere una città o frazione."),
("['farmacia','💊','Farmacia','GPS oppure città/frazione · raggio 15 km'],\n      ['pacco','📦','Pacco'","['farmacia','💊','Farmacia','GPS oppure città/frazione · raggio 15 km'],\n      ['pizzeria','🍕','Pizzeria','GPS o città/frazione · ritiro pizza e cena'],\n      ['pacco','📦','Pacco'"),
("if(cat==='spesa'){openShopFinder('spesa');return}\n  if(cat==='pacco'||cat==='altro'){openShopFinder(cat);return}","if(cat==='spesa'){openShopFinder('spesa');return}\n  if(cat==='pizzeria'){openShopFinder('pizzeria');return}\n  if(cat==='pacco'||cat==='altro'){openShopFinder(cat);return}"),
("pacco:['Ritirare un pacco','Es. pacco, documento, codice di ritiro, nominativo o dettagli utili'],altro:","pacco:['Ritirare un pacco','Es. pacco, documento, codice di ritiro, nominativo o dettagli utili'],pizzeria:['Ritirare pizze / cena','Es. ordine a nome Mario, 3 pizze, orario previsto di ritiro, eventuali note'],altro:"),
("REQUEST_CATEGORY==='pacco'?'PACCO / DOCUMENTO / CODICE RITIRO / NOTE':'COSA BISOGNA FARE / NOTE PER IL RUNNER'","REQUEST_CATEGORY==='pacco'?'PACCO / DOCUMENTO / CODICE RITIRO / NOTE':REQUEST_CATEGORY==='pizzeria'?'ORDINE / PIZZE / ORARIO RITIRO / NOTE':'COSA BISOGNA FARE / NOTE PER IL RUNNER'"),
("['farmacia','spesa','pacco','altro'].includes(REQUEST_CATEGORY)","['farmacia','spesa','pizzeria','pacco','altro'].includes(REQUEST_CATEGORY)"),
("REQUEST_CATEGORY==='pacco'?'📦':REQUEST_CATEGORY==='altro'?'📍':'🏪'","REQUEST_CATEGORY==='pacco'?'📦':REQUEST_CATEGORY==='pizzeria'?'🍕':REQUEST_CATEGORY==='altro'?'📍':'🏪'"),
("post_office:'Ufficio postale',parcel_locker:'Locker pacchi'","post_office:'Ufficio postale',parcel_locker:'Locker pacchi',restaurant:'Pizzeria / Ristorante',fast_food:'Pizzeria / Asporto'"),
("const parcelPlaces=REQUEST_CATEGORY==='pacco'?`node[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});way[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});relation[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});`:'';\n  const q=", "const parcelPlaces=REQUEST_CATEGORY==='pacco'?`node[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});way[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});relation[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});`:'';\n  const pizzaPlaces=REQUEST_CATEGORY==='pizzeria'?`node[\"amenity\"~\"^(restaurant|fast_food)$\"][\"cuisine\"~\"pizza|italian\",i](around:15000,${pos.lat},${pos.lng});way[\"amenity\"~\"^(restaurant|fast_food)$\"][\"cuisine\"~\"pizza|italian\",i](around:15000,${pos.lat},${pos.lng});relation[\"amenity\"~\"^(restaurant|fast_food)$\"][\"cuisine\"~\"pizza|italian\",i](around:15000,${pos.lat},${pos.lng});node[\"amenity\"~\"^(restaurant|fast_food)$\"][\"name\"~\"pizz\",i](around:15000,${pos.lat},${pos.lng});way[\"amenity\"~\"^(restaurant|fast_food)$\"][\"name\"~\"pizz\",i](around:15000,${pos.lat},${pos.lng});relation[\"amenity\"~\"^(restaurant|fast_food)$\"][\"name\"~\"pizz\",i](around:15000,${pos.lat},${pos.lng});`:'';\n  const q="),
("${parcelPlaces});out center tags;`","${parcelPlaces}${pizzaPlaces});out center tags;`"),
("}:category==='pacco'?{\n    kicker:'PUNTI DI RITIRO'","}:category==='pizzeria'?{\n    kicker:'PIZZERIE VICINE',title:'Dove ritiriamo la pizza?',\n    desc:'Cerca la zona e scegli una pizzeria se compare. Se è nuova o non è ancora presente nei dati, indica direttamente il punto sulla mappa oppure usa il GPS se sei davanti al locale.',\n    search:'Es. nome pizzeria…',manual:'Pizzeria non presente · indica sulla mappa'\n  }:category==='pacco'?{\n    kicker:'PUNTI DI RITIRO'"),
("<button class=\"btn teal full\" style=\"margin-top:10px\" onclick=\"openFinderManualMap('shop')\">🗺️ Non lo trovo · INDICA SULLA MAPPA</button>","<button class=\"btn teal full\" style=\"margin-top:10px\" onclick=\"openFinderManualMap('shop')\">${category==='pizzeria'?'🍕 Pizzeria non presente? · INDICA SULLA MAPPA':'🗺️ Non lo trovo · INDICA SULLA MAPPA'}</button>")
]

for old,new in repls:
    if old not in s:
        raise SystemExit('Pattern not found: '+old[:120])
    s=s.replace(old,new,1)

s=s.replace("/* PACCO_ALTRO_V1 */","/* PACCO_ALTRO_V1 */\n/* PIZZERIA_V1 */",1) if "/* PACCO_ALTRO_V1 */" in s else s
p.write_text(s,encoding='utf-8')
print('Pizzeria category added')
