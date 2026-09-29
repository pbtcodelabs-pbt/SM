# 🥬 سبزی منڈی (جنرل ایپ) — صدام والی ماسٹر فائل سے خودکار تیاری
import re, sys, json, os
import os.path as _p
# 🥬 استعمال (SM ریپو کی جڑ سے):
#   python3 tools/build_general.py <FM ریپو کا فولڈر> 'SM299TU#003'
# FM (صدام) کی index.html + sw.js پڑھتا ہے → SM ریپو کی جڑ میں index.html, sw.js, manifest.json لکھتا ہے
ROOT=_p.dirname(_p.dirname(_p.abspath(__file__)))
SRC=sys.argv[1]; OUT=ROOT
VERSION=sys.argv[2]
os.makedirs(OUT, exist_ok=True)
s=open(f'{SRC}/index.html',encoding='utf-8').read()
def rep(old,new,cnt=1):
    global s
    n=s.count(old); assert n==cnt,(n,old[:90]); s=s.replace(old,new)

# ---------- 0) ورژن ----------
s=re.sub(r"const APP_BUILD_VERSION = '[^']*';", f"const APP_BUILD_VERSION = '{VERSION}';", s, count=1)

# ---------- 1) سب سے پہلے چلنے والا حفاظتی سکرپٹ: الگ اسٹوریج، کلاؤڈ بند ----------
boot = r'''<script>
/* 🥬 سبزی منڈی — جنرل ایڈیشن کا حفاظتی حصہ (ہر چیز سے پہلے چلتا ہے)
   1) اس ایپ کا سارا فون والا ڈیٹا "SM::" کے الگ خانے میں — کسی دوسری ایپ (مثلاً فروٹ منڈی) سے کبھی نہ ملے
   2) کلاؤڈ (فائربیس) مکمل بند — جب تک اس ایپ کا اپنا فائربیس پروجیکٹ نہ لگے، کوئی ڈیٹا کلاؤڈ پر نہیں جاتا */
const APP_EDITION = 'general';
(function(){
  const P = 'SM::';
  const SP = Storage.prototype;
  const g = SP.getItem, st = SP.setItem, rm = SP.removeItem, k0 = SP.key;
  const lenDesc = Object.getOwnPropertyDescriptor(SP, 'length');
  function rawKeys(store){ const out = []; const n = lenDesc.get.call(store); for(let i = 0; i < n; i++){ out.push(k0.call(store, i)); } return out; }
  function mine(store){ return rawKeys(store).filter(k => k && k.indexOf(P) === 0).map(k => k.slice(P.length)); }
  SP.getItem = function(k){ return g.call(this, P + k); };
  SP.setItem = function(k, v){ return st.call(this, P + k, v); };
  SP.removeItem = function(k){ return rm.call(this, P + k); };
  SP.key = function(i){ const a = mine(this); return i < a.length ? a[i] : null; };
  SP.clear = function(){ mine(this).forEach(k => rm.call(this, P + k)); };
  Object.defineProperty(SP, 'length', { get(){ return mine(this).length; }, configurable: true });
  window.smLsKeys = function(){ return mine(window.localStorage); };
  const of = window.fetch.bind(window);
  window.fetch = function(input, init){
    const u = (typeof input === 'string') ? input : (input && input.url) || '';
    if(/firestore\.googleapis\.com|identitytoolkit\.googleapis\.com|securetoken\.googleapis\.com|firebaseio\.com/.test(u)){
      return Promise.resolve(new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } }));
    }
    return of(input, init);
  };
})();
function smBiz(){ try{ return (AppState.settings.businessName || '').trim() || 'سبزی منڈی'; }catch(e){ return 'سبزی منڈی'; } }
function smPhone(){ try{ return AppState.settings.businessPhone || ''; }catch(e){ return ''; } }
function smOwner(){ try{ return AppState.settings.ownerName || 'مالک'; }catch(e){ return 'مالک'; } }
</script>
'''
i=s.index('<head>')+len('<head>')
# charset meta پہلے رہے
m=re.search(r'<meta charset[^>]*>', s)
ins = m.end() if m and m.start() < s.index('</head>') else i
s=s[:ins]+'\n'+boot+s[ins:]

rep('Object.keys(localStorage)','smLsKeys()',2)
s=s.replace('indexedDB.open(', "indexedDB.open('SM_'+")

# ---------- 2) آئیکن `icons/` اور فونٹ `fonts/` فولڈر میں (صاف ستھرا ریپو) ----------
for f in ['favicon-32.png','icon-180.png','icon-192.png']:
    rep(f'href="{f}"', f'href="icons/{f}"')
rep("url('./JameelNooriNastaleeq-Regular.ttf')","url('./fonts/JameelNooriNastaleeq-Regular.ttf')")
rep("url('./JameelNooriNastaleeq-Kasheeda.ttf')","url('./fonts/JameelNooriNastaleeq-Kasheeda.ttf')")

# ---------- 3) زبردستی والا صدام کا نام/نمبر ہٹائیں ----------
rep("AppState.settings.businessName = 'صدام حسین فروٹ منڈی';\nAppState.settings.businessPhone = '03425556364';",
    "AppState.settings.businessName = AppState.settings.businessName || '';\nAppState.settings.businessPhone = AppState.settings.businessPhone || '';")

# ---------- 4) صدام کا ڈیٹا (سیڈ) خالی ----------
for name in ['CUSTOMERS_SEED_DATA','SUPPLIERS_SEED_DATA','APPROVAL_REQUESTS_SEED_DATA','INVOICES_SEED_DATA','LEDGER_CUSTOMERS_SEED_V1','LEDGER_SUPPLIERS_SEED_V1']:
    a=s.index(f'const {name} = [')+len(f'const {name} = [')
    b=s.index('\n];',a)
    s=s[:a]+' /* 🥬 جنرل ایپ: کوئی پرانا ریکارڈ نہیں */'+s[b:]
a=s.index('const USERS_SEED_DATA = [')
b=s.index('\n];',a)+3
s=s[:b]+"\nUSERS_SEED_DATA.splice(1); USERS_SEED_DATA[0].name = 'مالک'; USERS_SEED_DATA[0].phone = ''; // 🥬 صرف مالک (ایڈمن)\n"+s[b:]

# ---------- 5) نام اور نمبر — ہر جگہ دکان کا اپنا ----------
NAMES=['صدام حسین فروٹ منڈی','صدام فروٹ منڈی']
lines=s.split('\n')
in_script=False
out=[]
def js_replace(line, name, fn):
    res=''; idx=0
    while True:
        p=line.find(name, idx)
        if p<0: res+=line[idx:]; break
        before=line[:p]
        bt=before.count('`')-before.count('\\`')
        if bt%2==1:
            res+=line[idx:p]+'${'+fn+'}'; idx=p+len(name); continue
        q=None
        for ch in ["'",'"']:
            cnt=len(re.findall(r'(?<!\\)'+re.escape(ch), before))
            if cnt%2==1: q=ch; break
        if q:
            # پورا لفظی جملہ یہی نام ہو؟
            if line[p-1:p]==q and line[p+len(name):p+len(name)+1]==q:
                res+=line[idx:p-1]+fn; idx=p+len(name)+1; continue
            res+=line[idx:p]+q+' + '+fn+' + '+q; idx=p+len(name); continue
        res+=line[idx:p]+'سبزی منڈی'; idx=p+len(name)
    return res
for ln in lines:
    stripped=ln.strip()
    if re.search(r'<script(?![^>]*src)[^>]*>', ln): in_script=True
    is_comment = stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('<!--')
    if not is_comment:
        if in_script and '<script' not in ln:
            for n in NAMES:
                if n in ln: ln=js_replace(ln, n, 'smBiz()')
            if '03425556364' in ln: ln=js_replace(ln, '📞 03425556364', "('📞 ' + smPhone())") if '📞 03425556364' in ln else js_replace(ln,'03425556364','smPhone()')
            if "'Saddam Hussain'" in ln and 'USERS_SEED_DATA' not in ln and "name:'Saddam Hussain'" not in ln: ln=ln.replace("'Saddam Hussain'","smOwner()")
        else:
            for n in NAMES: ln=ln.replace(n,'سبزی منڈی')
            ln=ln.replace('📞 03425556364','')
    if '</script>' in ln: in_script=False
    out.append(ln)
s='\n'.join(out)
s=s.replace('Fruit Mandi POS','Sabzi Mandi POS')
# ---------- ⚡ تیز اپڈیٹ ----------
rep("navigator.serviceWorker.register('./sw.js').then((reg) => {",
    "navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).then((reg) => {\n      document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible') reg.update().catch(()=>{}); });\n      window.addEventListener('focus', () => reg.update().catch(()=>{}));\n      setTimeout(() => reg.update().catch(()=>{}), 3000);")
rep("setInterval(() => { reg.update(); }, 60 * 1000);","setInterval(() => { reg.update().catch(()=>{}); }, 30 * 1000);")
for a_,b_ in [("acc.name || 'صدام حسین'","acc.name || smOwner()"),("'شکریہ — صدام حسین'","'شکریہ — ' + smBiz()"),
              ('صرف صدام حسین (ایڈمن)','صرف ایڈمن'),('صرف ایڈمن (صدام)','صرف ایڈمن'),('صدام حسین جلد','ایڈمن جلد'),
              ('صدام کو','ایڈمن کو'),('Powered by Saddam Fruit Mandi','Powered by Sabzi Mandi'),("name:'Saddam Hussain'","name:'مالک'"),
              ('Saddam Fruit Mandi','Sabzi Mandi'),('Saddam Hussain','Owner'),('صدام کی ہدایت','ہدایت'),('صدام حسین','مالک'),('صدام','مالک'),('Saddam','Owner')]:
    s=s.replace(a_,b_)
s=s.replace('<title>سبزی منڈی</title>','<title>سبزی منڈی</title>')

# ---------- 6) ہیڈر عنوان / لوگو کو پہچان (id) ----------
rep('white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">سبزی منڈی</span>\n      <span id="connStatusBadge"',
    'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" id="smTopTitle">سبزی منڈی</span>\n      <span id="connStatusBadge"')
rep('<div class="brand">سبزی منڈی</div>','<div class="brand" id="smSideBrand">سبزی منڈی</div>')
k=s.index('<span id="connStatusBadge"')
j=s.rfind('<img src="data:image/png;base64,',0,k)
s=s[:j]+'<img id="smTopLogo" '+s[j+5:]

# ---------- 7) رجسٹریشن فارم + برانڈنگ ----------
reg = r'''
<style>
  /* 🥬 ورژن نمبر — صرف مالک کی پہچان کے لیے، مدھم (دکاندار کی توجہ نہ کھینچے) */
  #loginVersionBadge{ background:#15803d !important; color:#fff !important; box-shadow:none !important; border:none !important;
    padding:3px 12px !important; border-radius:999px !important; font-family:Arial,sans-serif !important; font-size:12px !important; font-weight:700 !important; letter-spacing:.4px; }
</style>
<!-- 🥬 سبزی منڈی — پہلی بار: دکان کی رجسٹریشن -->
<div id="smRegOverlay" dir="rtl" style="display:none; position:fixed; inset:0; z-index:2147483000; background:linear-gradient(160deg,#065f46,#022c22); overflow:auto; font-family:'JameelNooriNastaleeqKasheeda','JameelNooriNastaleeq','Noto Nastaliq Urdu',serif;">
  <style>
    #smRegOverlay .smWrap{ min-height:100dvh; box-sizing:border-box; padding:14px; display:flex; align-items:center; justify-content:center; }
    #smRegOverlay .smCard{ box-sizing:border-box; width:100%; max-width:420px; background:#fff; border-radius:18px; padding:14px 16px; box-shadow:0 10px 30px rgba(0,0,0,.35); display:flex; flex-direction:column; gap:10px; }
    #smRegOverlay label.smL{ display:block; font-weight:800; color:#0f172a; font-size:14px; margin:2px 0 2px; }
    #smRegOverlay input.smI{ width:100%; box-sizing:border-box; padding:9px 10px; margin:0; border:2px solid #86efac; border-radius:10px; font-family:inherit; font-size:16px; }
    #smRegOverlay .smPics{ display:flex; gap:8px; }
    #smRegOverlay .smPic{ flex:1; display:flex; align-items:center; gap:8px; background:#f8fafc; border:1.5px dashed #cbd5e1; border-radius:12px; padding:6px 8px; cursor:pointer; }
    #smRegOverlay .smPic img{ width:40px; height:40px; object-fit:cover; background:#e2e8f0; flex:0 0 auto; }
    #smRegOverlay .smPic b{ display:block; font-size:13px; color:#1e3a8a; line-height:1.6; }
    #smRegOverlay .smPic small{ display:block; font-size:10.5px; color:#64748b; line-height:1.5; }
  </style>
  <div class="smWrap"><div class="smCard">
    <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
      <img src="icons/icon-192.png" alt="" style="width:58px; height:58px; border-radius:14px; box-shadow:0 4px 10px rgba(0,0,0,.25); object-fit:cover;">
      <div style="text-align:right;">
        <div style="font-size:24px; font-weight:800; color:#065f46; line-height:1.5;">سبزی منڈی</div>
        <div style="font-size:13px; color:#475569; line-height:1.6;">اپنی دکان رجسٹر کریں</div>
      </div>
    </div>
    <div>
      <label class="smL">🏪 دکان کا نام *</label>
      <input id="smRegShop" class="smI" type="text" dir="rtl" placeholder="مثلاً رحمان سبزی منڈی">
    </div>
    <div>
      <label class="smL">👤 مالک کا نام *</label>
      <input id="smRegOwner" class="smI" type="text" dir="rtl" placeholder="مالک کا پورا نام">
    </div>
    <div>
      <label class="smL">📱 مالک کا موبائل نمبر *</label>
      <input id="smRegPhone" class="smI" type="tel" inputmode="numeric" dir="ltr" placeholder="03XXXXXXXXX" maxlength="13" style="font-family:'Arial Black',Arial,sans-serif; font-size:17px; text-align:center;">
    </div>
    <div>
      <label class="smL">🖼️ تصویریں <span style="font-size:11px; color:#64748b; font-weight:400;">(اختیاری)</span></label>
      <div class="smPics">
        <label class="smPic"><img id="smRegLogoPrev" alt="" style="border-radius:10px;"><span><b>🏪 دکان کا لوگو</b><small>بل، رسید، رپورٹ</small></span>
          <input type="file" accept="image/*" style="display:none;" onchange="smRegPick(this,'Logo')"></label>
        <label class="smPic"><img id="smRegOwnerPrev" alt="" style="border-radius:50%;"><span><b>👤 مالک کی تصویر</b><small>اوپر ہیڈر میں</small></span>
          <input type="file" accept="image/*" style="display:none;" onchange="smRegPick(this,'Owner')"></label>
      </div>
    </div>
    <div>
      <button type="button" onclick="smRegSave()" style="width:100%; padding:10px; border:none; border-radius:12px; background:linear-gradient(135deg,#16a34a,#065f46); color:#fff; font-family:inherit; font-size:18px; font-weight:800; cursor:pointer; box-shadow:0 4px 0 rgba(0,0,0,.25);">✅ رجسٹر کریں</button>
      <div style="display:flex; align-items:center; justify-content:center; gap:10px; margin-top:8px; flex-wrap:wrap;">
        <span style="font-size:12px; color:#64748b;">ابتدائی پن: <b dir="ltr">1234</b></span>
        <span id="smRegVersion" dir="ltr" style="display:inline-block; background:#15803d; color:#fff; font-family:Arial,sans-serif; font-size:12px; font-weight:700; letter-spacing:.4px; padding:3px 12px; border-radius:999px;"></span>
      </div>
    </div>
  </div></div>
</div>
<script>
const smRegImgs = { Logo: '', Owner: '' };
// ---------- تصویر چھوٹی کر کے (256px) محفوظ — ایپ ہلکی رہے ----------
function smShrinkImage(file, cb){
  const r = new FileReader();
  r.onload = () => {
    const img = new Image();
    img.onload = () => {
      const M = 256, sc = Math.min(1, M / Math.max(img.width, img.height));
      const c = document.createElement('canvas'); c.width = Math.round(img.width * sc); c.height = Math.round(img.height * sc);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      cb(c.toDataURL('image/jpeg', 0.85));
    };
    img.src = r.result;
  };
  r.readAsDataURL(file);
}
function smRegPick(inp, kind){
  const f = inp.files && inp.files[0]; if(!f) return;
  smShrinkImage(f, d => { smRegImgs[kind] = d; document.getElementById('smReg' + kind + 'Prev').src = d; });
}
// ---------- بعد میں بدلنا: ہیڈر کی تصویر پر ٹیپ (صرف ایڈمن) → مالک کی تصویر؛ لوگو "My Account" سے ----------
function smChangeOwnerPhoto(){
  if(!document.body.classList.contains('role-admin')) return;
  const inp = document.createElement('input'); inp.type = 'file'; inp.accept = 'image/*';
  inp.onchange = () => { const f = inp.files && inp.files[0]; if(!f) return;
    smShrinkImage(f, d => { AppState.settings.ownerPhoto = d; saveToStorage('settings', AppState.settings); smApplyBranding(); }); };
  inp.click();
}
function smApplyBranding(){
  const n = smBiz();
  document.title = n;
  const set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
  set('smRegVersion', (typeof APP_BUILD_VERSION !== 'undefined') ? APP_BUILD_VERSION : '');
  set('smTopTitle', n); set('smSideBrand', n); set('mobileBrandText', n); set('hbcBusinessName', n); set('smLoginShop', n);
  const st = AppState.settings;
  const im = document.getElementById('smTopLogo');
  if(im){ im.src = st.ownerPhoto || st.businessLogo || 'icons/icon-192.png'; im.style.objectFit = 'cover'; im.style.cursor = 'pointer'; im.onclick = smChangeOwnerPhoto; }
}
function smRegSave(){
  const shop = document.getElementById('smRegShop').value.trim();
  const owner = document.getElementById('smRegOwner').value.trim();
  const phone = document.getElementById('smRegPhone').value.replace(/[^0-9]/g, '');
  if(!shop){ alert('دکان کا نام لکھیں'); return; }
  if(!owner){ alert('مالک کا نام لکھیں'); return; }
  if(!/^03\d{9}$/.test(phone)){ alert('درست موبائل نمبر لکھیں (03XXXXXXXXX)'); return; }
  AppState.settings.businessName = shop;
  AppState.settings.ownerName = owner;
  AppState.settings.businessPhone = phone;
  if(smRegImgs.Logo) AppState.settings.businessLogo = smRegImgs.Logo;
  if(smRegImgs.Owner) AppState.settings.ownerPhoto = smRegImgs.Owner;
  AppState.settings.smRegistered = true;
  AppState.settings.smRegisteredAt = new Date().toISOString();
  saveToStorage('settings', AppState.settings);
  try{
    const adm = usersData.find(u => u.role === 'admin');
    if(adm){ adm.name = owner; adm.phone = phone; saveToStorage('users', usersData); }
  }catch(e){}
  document.getElementById('smRegOverlay').style.display = 'none';
  smApplyBranding();
  try{ setupLoginScreen(); }catch(e){}
}
window.addEventListener('DOMContentLoaded', () => {
  smApplyBranding();
  if(!AppState.settings.smRegistered) document.getElementById('smRegOverlay').style.display = 'block';
});
</script>
'''
k=s.rindex('</body>')
s=s[:k]+reg+s[k:]
# لاگ ان سکرین پر دکان کا نام
k=s.index('<div id="loginScreen">'); k2=s.index('>🥬</div>',k)
k1=s.rfind('<div style="width:56px;',k,k2)
s=s[:k1]+'<img src="icons/icon-192.png" alt="" style="display:block; width:64px; height:64px; border-radius:16px; box-shadow:0 4px 12px rgba(0,0,0,.35); object-fit:cover; margin:0 auto 6px;">'+s[k2+len('>🥬</div>'):]
rep('    <div id="loginVersionBadge"','    <div id="smLoginShop" style="text-align:center; color:#fff; font-size:22px; font-weight:800; margin:4px 0 8px; font-family:\'JameelNooriNastaleeqKasheeda\',\'JameelNooriNastaleeq\',serif; text-shadow:0 2px 4px rgba(0,0,0,.4);">سبزی منڈی</div>\n    <div id="loginVersionBadge"')
open(f'{OUT}/index.html','w',encoding='utf-8').write(s)

# ---------- 8) sw.js ----------
w=open(f'{SRC}/sw.js',encoding='utf-8').read()
w=re.sub(r"const CACHE_VERSION = '[^']*';", f"const CACHE_VERSION = '{VERSION}';", w, count=1)
w=w.replace('saddam-fruit-mandi-','sabzi-mandi-general-')  # کیش کا نام اور صفائی — دونوں صرف سبزی منڈی کے اپنے
w=w.replace("// ---------- 🏷️ صدام فروٹ منڈی — Service Worker ----------","// ---------- 🥬 سبزی منڈی (جنرل ایپ) — Service Worker ----------")
for f in ['favicon-32.png','icon-180.png','icon-192.png','icon-512.png']:
    w=w.replace(f"'./{f}'", f"'./icons/{f}'")
for f in ['JameelNooriNastaleeq-Regular.ttf','JameelNooriNastaleeq-Kasheeda.ttf']:
    w=w.replace(f"'./{f}'", f"'./fonts/{f}'")
w=w.replace('صدام کی ہدایت','ہدایت').replace('صدام','مالک')
open(f'{OUT}/sw.js','w',encoding='utf-8').write(w)

# ---------- 9) manifest ----------
man={"name":"سبزی منڈی","short_name":"سبزی منڈی","start_url":"./index.html","scope":"./","orientation":"portrait","description":"سبزی منڈی — بلنگ اور حساب کتاب","display":"standalone","background_color":"#065f46","theme_color":"#065f46","dir":"rtl","lang":"ur",
     "icons":[{"src":"icons/favicon-32.png","sizes":"32x32","type":"image/png"},{"src":"icons/icon-180.png","sizes":"180x180","type":"image/png","purpose":"any"},{"src":"icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},{"src":"icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}
open(f'{OUT}/manifest.json','w',encoding='utf-8').write(json.dumps(man,ensure_ascii=False,indent=2))
print('built', VERSION)
