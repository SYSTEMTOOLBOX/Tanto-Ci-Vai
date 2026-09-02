from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

if '/* PACCO_ALTRO_V1 */' in s:
    print('Pacco/Altro flows already applied')
    raise SystemExit(0)

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

# Categories: Ritiro becomes PACCO; Pacco and Altro advertise the same GPS/city entry flow.
replace_once(
    "Per Farmacia puoi usare il GPS oppure cercare una città o frazione diversa da dove ti trovi.",
    "Per Spesa, Farmacia, Pacco e Altro puoi usare il GPS oppure scegliere una città o frazione.",
    'request chooser subtitle'
)
replace_once(
    "['ritiro','📦','Ritiro','Pacco, documento o altro ritiro'],",
    "['pacco','📦','Pacco','GPS o città/frazione · pacco, documento o ritiro'],",
    'Pacco category tile'
)
replace_once(
    "['altro','🤝','Altro','Una piccola commissione locale']",
    "['altro','🤝','Altro','GPS o città/frazione · commissione locale']",
    'Altro category tile'
)

# Route Pacco and Altro through the same proven place/GPS finder used by Spesa.
replace_once(
    "function chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;\n  if(cat==='farmacia'){openPharmacyFinder();return}\n  if(cat==='spesa'){openShopFinder();return}\n  openNewRequest(2)\n}",
    "/* PACCO_ALTRO_V1 */\nfunction chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;\n  if(cat==='farmacia'){openPharmacyFinder();return}\n  if(cat==='spesa'){openShopFinder('spesa');return}\n  if(cat==='pacco'||cat==='altro'){openShopFinder(cat);return}\n  openNewRequest(2)\n}",
    'category routing'
)

# Category-specific wording in the common request form.
replace_once(
    "ritiro:['Ritirare un pacco','Es. pacco, documento o ordine da ritirare']",
    "pacco:['Ritirare un pacco','Es. pacco, documento, codice di ritiro, nominativo o dettagli utili']",
    'Pacco preset'
)
replace_once(
    "let detailLabel=REQUEST_CATEGORY==='farmacia'?'ORDINE / PRENOTAZIONE / COSA RITIRARE':REQUEST_CATEGORY==='spesa'?'LISTA SPESA / COSA COMPRARE / NOTE':'NOTE PER IL RUNNER / PUNTO DI RITIRO';",
    "let detailLabel=REQUEST_CATEGORY==='farmacia'?'ORDINE / PRENOTAZIONE / COSA RITIRARE':REQUEST_CATEGORY==='spesa'?'LISTA SPESA / COSA COMPRARE / NOTE':REQUEST_CATEGORY==='pacco'?'PACCO / DOCUMENTO / CODICE RITIRO / NOTE':'COSA BISOGNA FARE / NOTE PER IL RUNNER';",
    'category detail label'
)
replace_once(
    "let fromValue=SELECTED_PLACE?pickupAddressWithoutCivic(SELECTED_PLACE):'';let pickupCivic=SELECTED_PLACE?.housenumber||'';let showPickupCivic=REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa';",
    "let fromValue=SELECTED_PLACE?pickupAddressWithoutCivic(SELECTED_PLACE):'';let pickupCivic=SELECTED_PLACE?.housenumber||'';let showPickupCivic=['farmacia','spesa','pacco','altro'].includes(REQUEST_CATEGORY);",
    'pickup civic for all request types'
)
replace_once(
    "${REQUEST_CATEGORY==='farmacia'?'💊':'🏪'}",
    "${REQUEST_CATEGORY==='farmacia'?'💊':REQUEST_CATEGORY==='pacco'?'📦':REQUEST_CATEGORY==='altro'?'📍':'🏪'}",
    'pickup summary icon'
)

# Broaden the generic nearby-place list so Pacco can find tabaccherie, locker and post offices too.
replace_once(
    "variety_store:'Emporio'};",
    "variety_store:'Emporio',tobacco:'Tabaccheria',kiosk:'Chiosco',stationery:'Cartoleria',copyshop:'Copisteria',mobile_phone:'Telefonia',chemist:'Parafarmacia',newsagent:'Edicola',post_office:'Ufficio postale',parcel_locker:'Locker pacchi'};",
    'shop type labels'
)
replace_once(
    "if(filter==='all')return ['supermarket','convenience','grocery','bakery','butcher','greengrocer','deli','cheese','pasta','farm','hardware','doityourself','paint','garden_centre','trade','general','department_store','variety_store'];",
    "if(filter==='all')return ['supermarket','convenience','grocery','bakery','butcher','greengrocer','deli','cheese','pasta','farm','hardware','doityourself','paint','garden_centre','trade','general','department_store','variety_store','tobacco','kiosk','stationery','copyshop','mobile_phone','chemist','newsagent'];",
    'all nearby place types'
)
replace_once(
    "  const values=shopFilterValues(filter).join('|');\n  const q=`[out:json][timeout:20];(node[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng});way[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng});relation[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng}););out center tags;`;",
    "  const values=shopFilterValues(filter).join('|');\n  const parcelPlaces=REQUEST_CATEGORY==='pacco'?`node[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});way[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});relation[\"amenity\"~\"^(post_office|parcel_locker)$\"](around:15000,${pos.lat},${pos.lng});`:'';\n  const q=`[out:json][timeout:20];(node[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng});way[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng});relation[\"shop\"~\"^(${values})$\"](around:15000,${pos.lat},${pos.lng});${parcelPlaces});out center tags;`;",
    'parcel pickup places query'
)
replace_once(
    "let t=el.tags||{},type=t.shop||'shop',name=t.name||t.brand||shopTypeLabel(type);",
    "let t=el.tags||{},type=t.shop||t.amenity||'shop',name=t.name||t.brand||shopTypeLabel(type);",
    'parcel place result type'
)

# Turn the existing Spesa finder into a shared finder while keeping Spesa's UI unchanged.
pattern = r"function openShopFinder\(\)\{\n.*?\n\}\nasync function searchShopsByGps\(\)\{"
replacement = """function openShopFinder(category='spesa'){
  REQUEST_CATEGORY=category;SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;SHOP_RESULTS=[];
  const isSpesa=category==='spesa';
  SHOP_FILTER=isSpesa?'supermarket':'all';
  const cfg=isSpesa?{
    kicker:'NEGOZI VICINI',title:'Dove devo fare la spesa?',
    desc:'Scegli la zona: troviamo supermercati, CRAI/Lidl se presenti nei dati della zona, alimentari, ferramenta e altri negozi reali.',
    search:'Es. CRAI, Lidl, ferramenta…',manual:'Non trovo il negozio · inserisco manualmente'
  }:category==='pacco'?{
    kicker:'PUNTI DI RITIRO',title:'Dove si trova il pacco?',
    desc:'Usa il GPS oppure cerca una città o frazione. Ti mostro uffici postali, locker, tabaccherie e altri punti vicini; se non compare puoi inserire l’indirizzo manualmente.',
    search:'Es. Poste, locker, tabaccheria…',manual:'Non trovo il punto · inserisco manualmente'
  }:{
    kicker:'PUNTI VICINI',title:'Dove bisogna andare?',
    desc:'Usa il GPS oppure cerca una città o frazione, poi scegli un’attività vicina oppure inserisci direttamente il punto di ritiro.',
    search:'Es. negozio, attività, punto di ritiro…',manual:'Non trovo il punto · inserisco manualmente'
  };
  const filters=isSpesa?`<div class=\"delivery-tools\" style=\"margin-top:10px\"><button id=\"shop-filter-supermarket\" class=\"nav-mode on\" onclick=\"setShopFilter('supermarket')\">🛒 Supermercati</button><button id=\"shop-filter-food\" class=\"nav-mode\" onclick=\"setShopFilter('food')\">🥖 Alimentari</button><button id=\"shop-filter-hardware\" class=\"nav-mode\" onclick=\"setShopFilter('hardware')\">🔧 Ferramenta</button><button id=\"shop-filter-all\" class=\"nav-mode\" onclick=\"setShopFilter('all')\">🏪 Tutti</button></div>`:'';
  openSheet(`${head(cfg.kicker,cfg.title,cfg.desc)}<button class=\"gpsbtn\" onclick=\"searchShopsByGps()\">📍 Usa la posizione GPS di questo telefono</button><div class=\"place-fallback\"><input id=\"shopTown\" placeholder=\"Oppure scrivi città o frazione · es. Cavagnolo\"><button class=\"btn outline\" onclick=\"searchShopsByText()\">Cerca</button></div>${filters}<div id=\"shopStatus\" class=\"pharmacy-location\">Raggio di ricerca: 15 km dalla posizione scelta.</div><div id=\"shopMap\" class=\"place-map hidden\"></div><div class=\"field\"><label>CERCA TRA I RISULTATI</label><input id=\"shopNameSearch\" placeholder=\"${cfg.search}\" oninput=\"renderShopList()\"></div><div id=\"shopList\" class=\"place-list\"></div><button class=\"btn outline full\" style=\"margin-top:10px\" onclick=\"SELECTED_PLACE=null;openNewRequest(2)\">${cfg.manual}</button>`)
}
async function searchShopsByGps(){"""
s2, n = re.subn(pattern, lambda m: replacement, s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('shared shop finder anchor not found')
s = s2

# When a point was selected from the shared finder, keep its exact coordinates for Pacco/Altro too.
replace_once(
    "let pickupAddress=formatPickupAddress(from,pickupNumber),selectedPickup=(REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa')&&SELECTED_PLACE;",
    "let pickupAddress=formatPickupAddress(from,pickupNumber),selectedPickup=['farmacia','spesa','pacco','altro'].includes(REQUEST_CATEGORY)&&SELECTED_PLACE;",
    'selected pickup coordinates'
)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Pacco and Altro GPS request flows applied')
