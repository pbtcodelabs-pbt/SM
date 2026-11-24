/* PBT WebView APK — ویب سائٹ کے لیے فون کی سہولتیں (پرنٹ، شیئر، ڈاؤن لوڈ، پرنٹ ونڈو، بلوٹوتھ پرنٹر)
   صرف APK کے اندر چلتا ہے (window.PBTAppNative)؛ کروم میں کچھ نہیں بدلتا۔ */
(function () {
  if (window.__pbtApp || !window.PBTAppNative) return; window.__pbtApp = 1;
  var N = window.PBTAppNative, cbs = {}, seq = 0;
  function b64(blob) { return new Promise(function (res, rej) { var r = new FileReader(); r.onload = function () { res(String(r.result).split(',')[1] || ''); }; r.onerror = rej; r.readAsDataURL(blob); }); }
  window.__pbtCb = function (id, ok, msg) { var f = cbs[id]; delete cbs[id]; if (f) f(ok, msg); };
  function call(fn) { return new Promise(function (res) { var id = 'c' + (++seq); cbs[id] = function (ok, msg) { res({ ok: !!ok, msg: msg || '' }); }; fn(id); }); }
  window.PBTApp = {
    native: true,
    ver: (function () { try { return N.ver(); } catch (e) { return ''; } })(),
    /* بلوٹوتھ تھرمل پرنٹر (کلاسک SPP — زیادہ تر سستے پرنٹر) — bytes: Uint8Array */
    btPrint: function (bytes) { var s = ''; for (var i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192)); var x = btoa(s); return call(function (id) { N.btPrint(x, id); }); },
    btForget: function () { try { N.btForget(); } catch (e) {} },
    openExternal: function (u) { try { N.openExternal(String(u)); } catch (e) {} }
  };
  window.print = function () { try { N.print(document.title || 'Print'); } catch (e) {} };
  try {
    Object.defineProperty(navigator, 'share', { configurable: true, value: function (d) {
      d = d || {}; var fs = d.files || [];
      return Promise.all(fs.map(function (f) { return b64(f).then(function (x) { return { name: f.name || 'file', type: f.type || 'application/octet-stream', b64: x }; }); }))
        .then(function (arr) { N.share(JSON.stringify({ title: d.title || '', text: d.text || '', url: d.url || '', files: arr })); });
    } });
    Object.defineProperty(navigator, 'canShare', { configurable: true, value: function () { return true; } });
  } catch (e) {}
  function saveHref(href, name) {
    if (!href || !/^(blob:|data:)/.test(href)) return false;
    fetch(href).then(function (r) { return r.blob(); }).then(function (bl) { return b64(bl).then(function (x) { N.save(name || 'file', bl.type || 'application/octet-stream', x); }); })
      .catch(function (e) { alert('❌ ' + e); });
    return true;
  }
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[download]');
    if (a && saveHref(a.href, a.getAttribute('download') || '')) { e.preventDefault(); e.stopPropagation(); }
  }, true);
  var oc = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () { if (this.hasAttribute('download') && saveHref(this.href, this.getAttribute('download'))) return; return oc.apply(this, arguments); };
  /* پرنٹ / رپورٹ والی نئی ونڈو (window.open('') + document.write) → APK کی اپنی اسکرین */
  var oo = window.open;
  window.open = function (u, t, f) {
    if (!u || u === 'about:blank') {
      var buf = '', w = { closed: false, opener: window, name: t || '', location: { href: 'about:blank' },
        document: { write: function (h) { buf += h; }, writeln: function (h) { buf += h + '\n'; }, open: function () { buf = ''; }, close: function () { try { N.showHtml(buf, document.title || ''); } catch (e) {} }, title: '', body: null },
        print: function () {}, close: function () { w.closed = true; }, focus: function () {}, blur: function () {}, addEventListener: function () {}, removeEventListener: function () {} };
      return w;
    }
    return oo.call(window, u, t, f);
  };
  try { document.documentElement.classList.add('pbt-apk'); } catch (e) {}
})();
