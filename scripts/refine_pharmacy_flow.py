from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Make the pharmacy flow unmistakably specific after a pharmacy is selected.
old = "  let pr=presets[REQUEST_CATEGORY]||presets.altro;\n  let fromValue=SELECTED_PLACE?(SELECTED_PLACE.address||SELECTED_PLACE.name):'';"
new = "  let pr=presets[REQUEST_CATEGORY]||presets.altro;\n  let detailLabel=REQUEST_CATEGORY==='farmacia'?'ORDINE / PRENOTAZIONE / COSA RITIRARE':'NOTE PER IL RUNNER / PUNTO DI RITIRO';\n  let fromValue=SELECTED_PLACE?(SELECTED_PLACE.address||SELECTED_PLACE.name):'';"
if old in s and 'let detailLabel=' not in s:
    s = s.replace(old, new, 1)

s = s.replace('<div class=\"field\"><label>NOTE PER IL RUNNER / PUNTO DI RITIRO</label><textarea id=\"nrDesc\" rows=\"3\" placeholder=\"${pr[1]}\"></textarea></div>',
              '<div class=\"field\"><label>${detailLabel}</label><textarea id=\"nrDesc\" rows=\"3\" placeholder=\"${pr[1]}\"></textarea></div>')

# Stronger pharmacy-specific helper text.
s = s.replace("farmacia:['Ritiro in farmacia','Es. ordine già pronto, nominativo al banco, numero ordine']",
              "farmacia:['Ritiro in farmacia','Es. Ordine n. 123, prenotazione a nome Mario, oppure prodotto da ritirare']")

# Ensure the pharmacy category always jumps directly to the locator/map.
old_choose = "function chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;\n  if(cat==='farmacia'){openPharmacyFinder();return}\n  openNewRequest(2)\n}"
new_choose = "function chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;\n  if(cat==='farmacia'){openPharmacyFinder();return}\n  openNewRequest(2)\n}"
if old_choose in s:
    s = s.replace(old_choose, new_choose, 1)

# Remove obsolete prototype/demo wording if any old fragment ever survived a patch.
for old_text, new_text in {
    'Nella versione reale useremo GPS e geocodifica per trovare persone che passano già vicino a entrambe le tappe.':'GPS e mappa sono attivi per ritiro e consegna.',
    'Nella versione reale':'',
    'Demo interattiva':'Tanto ci vai?',
    '● DEMO':'● ONLINE',
}.items():
    s = s.replace(old_text, new_text)

# Add cache-control hints to reduce stale HTML when revisiting the live page.
if 'http-equiv="Cache-Control"' not in s:
    s = s.replace('<meta name="theme-color" content="#0b66ff">', '<meta name="theme-color" content="#0b66ff">\n<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="Expires" content="0">', 1)

p.write_text(s, encoding='utf-8')
print('Pharmacy flow refined')
