from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')

if 'TCV_CAP_CONSISTENCY_V1' not in s:
    s = s.replace('TCV_TWO_STAGE_LOCATION_V1', 'TCV_TWO_STAGE_LOCATION_V1\n   TCV_CAP_CONSISTENCY_V1', 1)

s = s.replace(
"    return {lat:Number(c[1]),lng:Number(c[0]),label:featureLabel(f),town}\n",
"    return {lat:Number(c[1]),lng:Number(c[0]),label:featureLabel(f),town,postcode:p.postcode||''}\n",
1,
)

s = s.replace(
"    const town=tcvTownFromPoint(pt);if(town)townEl.value=town;\n    if(pt&&Number.isFinite(Number(pt.lat))&&Number.isFinite(Number(pt.lng))){townEl.dataset.lat=String(pt.lat);townEl.dataset.lng=String(pt.lng)}\n    townEl.dataset.town=town||'';if(placeEl)placeEl.disabled=!town\n",
"    const town=tcvTownFromPoint(pt);if(town)townEl.value=town;\n    if(pt&&Number.isFinite(Number(pt.lat))&&Number.isFinite(Number(pt.lng))){townEl.dataset.lat=String(pt.lat);townEl.dataset.lng=String(pt.lng)}\n    townEl.dataset.town=town||'';townEl.dataset.postcode=String(pt?.postcode||'');if(placeEl)placeEl.disabled=!town\n",
1,
)

s = s.replace(
"    const town=String(el.dataset.town||el.value||'').trim(),lat=Number(el.dataset.lat),lng=Number(el.dataset.lng);\n    if(!town)return null;\n    return {lat:Number.isFinite(lat)?lat:NaN,lng:Number.isFinite(lng)?lng:NaN,label:town,town}\n",
"    const town=String(el.dataset.town||el.value||'').trim(),lat=Number(el.dataset.lat),lng=Number(el.dataset.lng),postcode=String(el.dataset.postcode||'');\n    if(!town)return null;\n    return {lat:Number.isFinite(lat)?lat:NaN,lng:Number.isFinite(lng)?lng:NaN,label:town,town,postcode}\n",
1,
)

s = s.replace(
"      out.push({f,p,town,sub:featureSub(f)});if(out.length>=8)break\n",
"      out.push({f,p,town,postcode:String(f?.properties?.postcode||''),sub:featureSub(f)});if(out.length>=8)break\n",
1,
)

s = s.replace(
"            input.value=r.town;input.dataset.town=r.town;input.dataset.lat=String(r.p.lat);input.dataset.lng=String(r.p.lng);state[key]=r.p;clearBox(boxId);\n",
"            input.value=r.town;input.dataset.town=r.town;input.dataset.lat=String(r.p.lat);input.dataset.lng=String(r.p.lng);input.dataset.postcode=r.postcode||'';r.p.postcode=r.postcode||'';state[key]=r.p;clearBox(boxId);\n",
1,
)

needle = "  function bindLocalAutocomplete(townId,inputId,boxId,key,target='trip'){\n"
if 'function tcvLocalFeatureSub' not in s:
    helper = "  function tcvLocalFeatureSub(f,townPt){\n    const p=f?.properties||{},cap=String(townPt?.postcode||'').trim();\n    return [cap||p.postcode,p.county,p.country].filter(Boolean).join(' · ')\n  }\n"
    s = s.replace(needle, helper + needle, 1)

s = s.replace(
"<small>${safe(featureSub(f))}</small>",
"<small>${safe(tcvLocalFeatureSub(f,townPt))}</small>",
1,
)

s = s.replace(
"            input.value=tcvPlaceDetail(p)||featureLabel(f)||q;state[key]=p;clearBox(boxId);if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()\n",
"            p.town=town;p.postcode=townPt.postcode||p.postcode||'';input.value=tcvPlaceDetail(p)||featureLabel(f)||q;state[key]=p;clearBox(boxId);if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()\n",
1,
)

s = s.replace(
"    const p=featurePoint(exact[0]);state[key]=p;document.getElementById(inputId).value=tcvPlaceDetail(p)||featureLabel(exact[0]);return p\n",
"    const p=featurePoint(exact[0]);p.town=townPt.town;p.postcode=townPt.postcode||p.postcode||'';state[key]=p;document.getElementById(inputId).value=tcvPlaceDetail(p)||featureLabel(exact[0]);return p\n",
1,
)

p.write_text(s, encoding='utf-8')

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2 = re.sub(r'community-routes\.js\?v=\d+', 'community-routes.js?v=6', html, count=1)
if html2 == html and 'community-routes.js?v=6' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

print('Community CAP now follows the selected municipality, not a nearby street result')
