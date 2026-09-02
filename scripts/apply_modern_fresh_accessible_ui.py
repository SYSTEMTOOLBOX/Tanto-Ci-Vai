from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

START = '/* MODERN_FRESH_ACCESSIBLE_V1_START */'
END = '/* MODERN_FRESH_ACCESSIBLE_V1_END */'

css = r'''/* MODERN_FRESH_ACCESSIBLE_V1_START */
:root{
  --navy:#09214a;
  --blue:#1769ff;
  --teal:#0bcbb0;
  --green:#20ad69;
  --red:#c83a4c;
  --ink:#10213d;
  --muted:#52647f;
  --bg:#f5f9ff;
  --line:#d7e4f2;
  --card:#ffffff;
  --shadow:0 14px 38px rgba(20,55,105,.11);
}
html{font-size:16px}
body{
  padding-bottom:94px;
  background:
    radial-gradient(circle at 5% 0%,rgba(23,105,255,.12),transparent 28%),
    radial-gradient(circle at 100% 8%,rgba(11,203,176,.11),transparent 25%),
    var(--bg);
}
button,input,textarea,select{font-size:16px}
.top{padding:14px 16px;background:rgba(245,249,255,.94)}
.logo{width:54px;height:54px;border-radius:18px;font-size:27px;box-shadow:0 10px 24px rgba(23,105,255,.22)}
.brand b{font-size:22px;line-height:1.05}
.brand small{font-size:13px;line-height:1.35;margin-top:3px;color:#5c6f8c}
.avatar{width:48px;height:48px;font-size:16px}
.loc{font-size:14px;line-height:1.35;padding:12px 14px;border-radius:17px}
.pilot{font-size:12px;padding:5px 9px}
main{padding:6px 16px 30px}
.hero{padding:25px 23px;border-radius:30px;box-shadow:0 18px 42px rgba(23,105,255,.22)}
.eyebrow{font-size:13px;letter-spacing:.11em}
.hero h1{font-size:36px;line-height:1.02;margin:9px 0 10px}
.hero p{font-size:16px;line-height:1.55;max-width:560px}
.stats{gap:10px;margin-top:20px}
.stat{padding:13px 11px;border-radius:17px}
.stat b{font-size:23px}
.stat span{font-size:13px;line-height:1.25}
.sect{margin:24px 3px 12px;align-items:center}
.sect h2{font-size:25px}
.sect span{font-size:14px;line-height:1.3}
.actions{gap:12px}
.action{min-height:188px;padding:19px;border-radius:25px;border-color:#d8e5f4;box-shadow:0 10px 28px rgba(17,52,105,.09)}
.action.help{background:linear-gradient(155deg,#fff 10%,#edf5ff 100%)}
.action.go{background:linear-gradient(155deg,#fff 10%,#eafff9 100%)}
.ico{width:58px;height:58px;border-radius:19px;font-size:27px;margin-bottom:18px}
.action b{font-size:21px;line-height:1.1}
.action p{font-size:14px;line-height:1.5;margin-top:8px;color:#566984}
.arrow{width:40px;height:40px;right:15px;bottom:15px;font-size:18px}
.feed{gap:12px}
.req{padding:18px;border-radius:23px;box-shadow:0 9px 26px rgba(20,55,105,.08)}
.reqhead{align-items:center}
.kind{font-size:12px;padding:7px 10px;letter-spacing:.045em}
.dist{font-size:13px;color:#60708a}
.req h3{font-size:21px;line-height:1.18;margin:10px 0 7px}
.req p{font-size:15px;line-height:1.55;color:#536680}
.route{margin:13px 0;padding:13px 14px;border-radius:17px;font-size:15px;line-height:1.5;background:#f8fbff}
.route small{font-size:12px;letter-spacing:.04em}
.meta{gap:8px}
.pill{padding:8px 10px;font-size:13px;line-height:1.25}
.btn{min-height:50px;border-radius:15px;padding:12px 14px;font-size:15px;line-height:1.2}
.full{padding:14px 15px;font-size:16px;min-height:54px}
.rowbtn{gap:9px;margin-top:13px}
.notice{padding:13px 14px;border-radius:16px;font-size:14px;line-height:1.5}
.empty{padding:24px 18px;font-size:15px;line-height:1.5;border-radius:20px}
.bottom{height:84px;padding:7px 7px 8px;box-shadow:0 -8px 26px rgba(15,42,80,.08)}
.nav{font-size:24px;gap:3px}
.nav small{font-size:12px;line-height:1.1}
.sheet{padding:12px 18px 30px;border-radius:30px 30px 0 0}
.handle{width:50px;height:6px;margin-bottom:17px}
.shead .k{font-size:12px;letter-spacing:.1em}
.shead h2{font-size:29px;line-height:1.08;margin:5px 0 7px}
.shead p{font-size:15px;line-height:1.5}
.close{width:44px;height:44px;font-size:26px}
.choices{gap:10px;margin:14px 0}
.choice{padding:16px;border-radius:18px;min-height:112px}
.choice .em{font-size:28px}
.choice b{font-size:17px;margin-top:7px}
.choice small{font-size:13px;line-height:1.35;margin-top:5px}
.backrow{gap:9px;margin-top:12px}
.place-map{border-radius:20px}
.place-list{gap:10px}
.place-card{padding:14px;border-radius:18px;gap:12px}
.place-card b{font-size:17px;line-height:1.25}
.place-card small{font-size:13px;line-height:1.45;margin-top:5px}
.place-distance{font-size:14px}
.favbtn{width:46px;height:46px;font-size:21px}
.pharmacy-location{padding:13px 14px;border-radius:16px;font-size:14px;line-height:1.5}
.place-fallback{gap:8px}
.nav-modes{gap:8px;margin:12px 0}
.nav-mode{min-height:50px;border-radius:15px;padding:12px 8px;font-size:15px}
.nav-summary{gap:9px;margin:12px 0}
.nav-summary>div{padding:13px;border-radius:16px}
.nav-summary b{font-size:22px}
.nav-summary span{font-size:12px;line-height:1.3}
.nav-steps{gap:8px;max-height:220px}
.nav-step{grid-template-columns:34px 1fr auto;gap:9px;padding:11px;border-radius:14px;font-size:14px}
.nav-step .turn{font-size:21px}
.nav-step small{font-size:12px}
.nav-actions{gap:9px}
.nav-live{padding:12px 13px;border-radius:15px;font-size:14px;line-height:1.45}
.route-map{border-radius:20px}
.delivery-smart{padding:14px;border-radius:20px}
.delivery-smart-title{font-size:15px;margin-bottom:9px}
.autocomplete-box{gap:6px}
.autocomplete-item{padding:12px;border-radius:14px;font-size:14px;line-height:1.45}
.autocomplete-item b{font-size:16px}
.autocomplete-item small{font-size:13px;margin-top:3px}
.delivery-tools{gap:9px;margin-top:10px}
.delivery-map{border-radius:19px}
.delivery-picked{padding:12px 13px;border-radius:14px;font-size:14px;line-height:1.45}
.field{margin:14px 0}
.field label{font-size:13px;line-height:1.3;margin-bottom:7px;letter-spacing:.025em}
input,textarea,select{
  min-height:54px;
  padding:14px 15px;
  border-radius:15px;
  font-size:17px;
  line-height:1.35;
  color:#132441;
  border-color:#d2e0ef;
}
textarea{min-height:110px}
.grid2{gap:10px}
.authcard{padding:24px;border-radius:30px}
.authlogo{width:78px;height:78px;border-radius:24px;font-size:37px}
.authcard h1{font-size:32px}
.authcard>p{font-size:15px;line-height:1.5}
.tab{min-height:48px;font-size:15px}
.gpsbtn{min-height:52px;font-size:15px;border-radius:16px;padding:12px 14px}
.pagehead .k{font-size:12px;letter-spacing:.1em}
.pagehead h2{font-size:29px;line-height:1.08}
.pagehead p{font-size:15px;line-height:1.5}
.map-plan-sheet{border-radius:22px;padding:12px;box-shadow:0 18px 42px rgba(8,29,62,.24)}
.map-plan-head{padding:12px 12px 10px;margin:-12px -12px 10px}
.map-plan-head b{font-size:16px}
.map-plan-head small{font-size:13px;line-height:1.35}
.map-plan-collapse{width:44px;height:40px;font-size:18px}
.map-plan-chip{font-size:14px;padding:12px 16px}

@media(max-width:520px){
  .hero h1{font-size:33px}
  .actions{gap:10px}
  .action{padding:17px;min-height:182px}
  .action b{font-size:20px}
  .action p{font-size:14px}
  .rowbtn{grid-template-columns:1fr 1fr}
}

@media(max-width:380px){
  main{padding-left:13px;padding-right:13px}
  .top{padding-left:13px;padding-right:13px}
  .hero{padding:22px 19px}
  .hero h1{font-size:31px}
  .action{padding:15px;min-height:178px}
  .ico{width:54px;height:54px}
  .action b{font-size:19px}
  .action p{font-size:13px}
  .pill{font-size:12px}
}
/* MODERN_FRESH_ACCESSIBLE_V1_END */'''

if START in s and END in s:
    s = re.sub(re.escape(START) + r'.*?' + re.escape(END), css, s, count=1, flags=re.S)
else:
    if '</style>' not in s:
        raise SystemExit('style closing tag not found')
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print('Modern fresh accessible UI applied')
