package com.pbtcodelabs.sabzimandi;

/* سبزی منڈی — ویب ویو APK (مالک کا حکم، 24 نومبر 2026):
   ڈیٹا اس APK کے اپنے خانے میں — کروم کا ڈیٹا صاف کرنے سے نہیں مٹتا۔
   ویب سائٹ ہی کھلتی ہے، اس لیے ہر اپڈیٹ خود آتی ہے؛ نئی APK صرف تب جب یہ ڈبہ بدلے۔ */

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.ActivityNotFoundException;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.print.PrintAttributes;
import android.print.PrintManager;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.core.content.FileProvider;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends Activity {
    static final String START = BuildConfig.START_URL;
    static final String HOST = Uri.parse(START).getHost();
    static final String PATH = Uri.parse(START).getPath().replaceAll("[^/]*$", "");
    static final UUID SPP = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    static final int REQ_FILE = 11, REQ_CAM = 12, REQ_BT = 13;

    WebView web;
    String polyfill = "";
    ValueCallback<Uri[]> fileCb;
    Uri camUri;
    PermissionRequest pendingPerm;
    Runnable afterBt;
    final Handler ui = new Handler(Looper.getMainLooper());

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        try { getWindow().setStatusBarColor(Color.parseColor(BuildConfig.THEME)); } catch (Exception e) {}
        try (InputStream in = getAssets().open("pbtapp.js")) { byte[] buf = new byte[in.available()]; int n = in.read(buf); polyfill = new String(buf, 0, Math.max(n, 0), "UTF-8"); } catch (Exception e) {}
        web = new WebView(this);
        setContentView(web);
        setup(web, true);
        if (b != null) web.restoreState(b); else web.loadUrl(START);
    }

    @Override protected void onSaveInstanceState(Bundle o) { super.onSaveInstanceState(o); if (web != null) web.saveState(o); }

    void setup(final WebView w, final boolean main) {
        WebSettings s = w.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setTextZoom(100);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSupportMultipleWindows(false);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        s.setUserAgentString(s.getUserAgentString() + " PBTApp/" + BuildConfig.VERSION_NAME);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(w, true);
        w.addJavascriptInterface(new Bridge(w), "PBTAppNative");
        if (WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) {
            WebViewCompat.addDocumentStartJavaScript(w, polyfill, Collections.singleton("*"));
        }
        w.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return route(r.getUrl()); }
            @Override public void onPageStarted(WebView v, String url, android.graphics.Bitmap f) { if (!WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) v.evaluateJavascript(polyfill, null); }
            @Override public void onPageFinished(WebView v, String url) { v.evaluateJavascript(polyfill, null); }
        });
        w.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) { return chooseFile(cb, p); }
            @Override public void onPermissionRequest(final PermissionRequest r) {
                ui.post(() -> {
                    if (has(Manifest.permission.CAMERA)) r.grant(r.getResources());
                    else { pendingPerm = r; requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAM); }
                });
            }
        });
        w.setDownloadListener(new DownloadListener() {
            @Override public void onDownloadStart(String url, String ua, String cd, String mime, long len) {
                if (url.startsWith("http")) {
                    try {
                        android.app.DownloadManager.Request q = new android.app.DownloadManager.Request(Uri.parse(url));
                        q.setNotificationVisibility(android.app.DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                        q.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, URLUtil.guessFileName(url, cd, mime));
                        ((android.app.DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(q);
                        toast("⬇️ ڈاؤن لوڈ شروع");
                    } catch (Exception e) { openExternal(url); }
                }
            }
        });
    }

    /* اپنی ویب سائٹ اندر، باقی (واٹس ایپ، فون، گوگل، پلے اسٹور…) فون کی اپنی ایپ میں */
    boolean route(Uri u) {
        String sc = u.getScheme() == null ? "" : u.getScheme();
        if ((sc.equals("https") || sc.equals("http")) && HOST.equals(u.getHost())) {
            String p = u.getPath() == null ? "/" : u.getPath();
            if (p.startsWith(PATH) || p.startsWith("/help/")) return false;
        }
        if (sc.equals("blob") || sc.equals("data") || sc.equals("about") || sc.equals("javascript")) return false;
        openExternal(u.toString());
        return true;
    }

    void openExternal(String url) {
        try {
            Intent i = url.startsWith("intent:") ? Intent.parseUri(url, Intent.URI_INTENT_SCHEME) : new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (ActivityNotFoundException e) {
            if (url.contains("whatsapp") || url.contains("wa.me")) toast("واٹس ایپ انسٹال نہیں"); else toast("یہ لنک کھولنے والی ایپ نہیں ملی");
        } catch (Exception e) { toast("❌ " + e.getMessage()); }
    }

    boolean has(String p) { return Build.VERSION.SDK_INT < 23 || checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED; }
    void toast(final String t) { ui.post(() -> Toast.makeText(this, t, Toast.LENGTH_LONG).show()); }

    /* تصویر / فائل چننا — کیمرہ + گیلری */
    boolean chooseFile(ValueCallback<Uri[]> cb, WebChromeClient.FileChooserParams p) {
        if (fileCb != null) fileCb.onReceiveValue(null);
        fileCb = cb;
        Intent pick;
        try { pick = p.createIntent(); } catch (Exception e) { pick = new Intent(Intent.ACTION_GET_CONTENT).setType("*/*"); }
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        if (p.getMode() == WebChromeClient.FileChooserParams.MODE_OPEN_MULTIPLE) pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        List<Intent> extra = new ArrayList<>();
        boolean img = false; for (String a : p.getAcceptTypes()) if (a == null || a.isEmpty() || a.startsWith("image") || a.equals("*/*")) img = true;
        camUri = null;
        if (img && has(Manifest.permission.CAMERA)) {
            try {
                File f = new File(new File(getCacheDir(), "share"), "cam_" + System.currentTimeMillis() + ".jpg"); f.getParentFile().mkdirs();
                camUri = FileProvider.getUriForFile(this, getPackageName() + ".files", f);
                Intent cam = new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT, camUri).addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                if (p.isCaptureEnabled()) { startActivityForResult(cam, REQ_FILE); return true; }
                extra.add(cam);
            } catch (Exception e) { camUri = null; }
        } else if (img) requestPermissions(new String[]{Manifest.permission.CAMERA}, 99);
        Intent ch = Intent.createChooser(pick, "تصویر / فائل");
        if (!extra.isEmpty()) ch.putExtra(Intent.EXTRA_INITIAL_INTENTS, extra.toArray(new Intent[0]));
        try { startActivityForResult(ch, REQ_FILE); } catch (Exception e) { fileCb = null; return false; }
        return true;
    }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != REQ_FILE || fileCb == null) return;
        Uri[] out = null;
        if (res == RESULT_OK) {
            if (data != null && data.getClipData() != null) { int n = data.getClipData().getItemCount(); out = new Uri[n]; for (int i = 0; i < n; i++) out[i] = data.getClipData().getItemAt(i).getUri(); }
            else if (data != null && data.getData() != null) out = new Uri[]{data.getData()};
            else if (camUri != null) out = new Uri[]{camUri};
        }
        fileCb.onReceiveValue(out); fileCb = null;
    }

    @Override public void onRequestPermissionsResult(int req, String[] p, int[] r) {
        boolean ok = r.length > 0 && r[0] == PackageManager.PERMISSION_GRANTED;
        if (req == REQ_CAM && pendingPerm != null) { if (ok) pendingPerm.grant(pendingPerm.getResources()); else pendingPerm.deny(); pendingPerm = null; }
        if (req == REQ_BT && afterBt != null) { Runnable a = afterBt; afterBt = null; a.run(); }
    }

    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) { web.goBack(); return; }
        new AlertDialog.Builder(this).setMessage("ایپ بند کریں؟").setPositiveButton("ہاں", (d, i) -> finish()).setNegativeButton("نہیں", null).show();
    }

    /* پرنٹ ونڈو (رپورٹ / چالان) — الگ اسکرین، اوپر «🖨️ پرنٹ» اور «✕ بند» */
    void showHtml(final String html, final String title) {
        final Dialog d = new Dialog(this, android.R.style.Theme_Material_Light_NoActionBar);
        LinearLayout box = new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL);
        LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER); bar.setBackgroundColor(Color.parseColor(BuildConfig.THEME)); bar.setPadding(8, 8, 8, 8);
        final WebView w = new WebView(this);
        Button pr = new Button(this); pr.setText("🖨️ پرنٹ / PDF"); pr.setOnClickListener(v -> printWeb(w, title));
        Button cl = new Button(this); cl.setText("✕ بند"); cl.setOnClickListener(v -> { d.dismiss(); w.destroy(); });
        bar.addView(pr); bar.addView(cl);
        box.addView(bar, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        box.addView(w, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        setup(w, false);
        w.loadDataWithBaseURL(START, html, "text/html", "UTF-8", null);
        d.setContentView(box);
        d.setOnCancelListener(x -> w.destroy());
        d.show();
    }

    void printWeb(WebView w, String title) {
        try {
            String t = (title == null || title.isEmpty()) ? "Print" : title;
            PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
            pm.print(t, w.createPrintDocumentAdapter(t), new PrintAttributes.Builder().build());
        } catch (Exception e) { toast("❌ پرنٹ: " + e.getMessage()); }
    }

    File writeTemp(String name, byte[] data) throws Exception {
        File dir = new File(getCacheDir(), "share"); dir.mkdirs();
        String safe = name.replaceAll("[\\\\/:*?\"<>|]", "_"); if (safe.isEmpty()) safe = "file";
        File f = new File(dir, safe);
        try (FileOutputStream o = new FileOutputStream(f)) { o.write(data); }
        return f;
    }

    /* جاوا اسکرپٹ ↔ فون */
    class Bridge {
        final WebView w;
        Bridge(WebView w) { this.w = w; }

        @JavascriptInterface public String ver() { return BuildConfig.VERSION_NAME; }

        @JavascriptInterface public void print(final String title) { ui.post(() -> printWeb(w, title)); }

        @JavascriptInterface public void showHtml(final String html, final String title) { ui.post(() -> MainActivity.this.showHtml(html, title)); }

        @JavascriptInterface public void openExternal(final String url) { ui.post(() -> MainActivity.this.openExternal(url)); }

        @JavascriptInterface public void share(String json) {
            try {
                JSONObject o = new JSONObject(json);
                JSONArray fs = o.optJSONArray("files");
                ArrayList<Uri> uris = new ArrayList<>(); String type = null;
                if (fs != null) for (int i = 0; i < fs.length(); i++) {
                    JSONObject f = fs.getJSONObject(i);
                    File file = writeTemp(f.optString("name", "file"), Base64.decode(f.optString("b64", ""), Base64.DEFAULT));
                    uris.add(FileProvider.getUriForFile(MainActivity.this, getPackageName() + ".files", file));
                    String t = f.optString("type", "*/*"); type = type == null ? t : (type.equals(t) ? type : "*/*");
                }
                String text = (o.optString("text", "") + (o.optString("url", "").isEmpty() ? "" : "\n" + o.optString("url"))).trim();
                Intent i;
                if (uris.size() > 1) { i = new Intent(Intent.ACTION_SEND_MULTIPLE).putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris).setType(type); }
                else if (uris.size() == 1) { i = new Intent(Intent.ACTION_SEND).putExtra(Intent.EXTRA_STREAM, uris.get(0)).setType(type); }
                else { i = new Intent(Intent.ACTION_SEND).setType("text/plain"); }
                if (!text.isEmpty()) i.putExtra(Intent.EXTRA_TEXT, text);
                if (!o.optString("title", "").isEmpty()) i.putExtra(Intent.EXTRA_SUBJECT, o.optString("title"));
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                final Intent ch = Intent.createChooser(i, "شیئر کریں");
                ui.post(() -> startActivity(ch));
            } catch (Exception e) { toast("❌ شیئر: " + e.getMessage()); }
        }

        @JavascriptInterface public void save(String name, String mime, String b64) {
            try {
                byte[] data = Base64.decode(b64, Base64.DEFAULT);
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.Downloads.DISPLAY_NAME, name); v.put(MediaStore.Downloads.MIME_TYPE, mime);
                    v.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri u = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    try (OutputStream o = getContentResolver().openOutputStream(u)) { o.write(data); }
                } else {
                    File d = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS); d.mkdirs();
                    try (FileOutputStream o = new FileOutputStream(new File(d, name))) { o.write(data); }
                }
                toast("✅ Downloads میں محفوظ: " + name);
            } catch (Exception e) { toast("❌ محفوظ نہیں ہوا: " + e.getMessage()); }
        }

        @JavascriptInterface public void btForget() { prefs().edit().remove("bt").apply(); toast("پرنٹر بھلا دیا — اگلی بار نیا چنیں"); }

        @JavascriptInterface public void btPrint(final String b64, final String cb) {
            final byte[] data = Base64.decode(b64, Base64.DEFAULT);
            ui.post(() -> {
                if (Build.VERSION.SDK_INT >= 31 && !has(Manifest.permission.BLUETOOTH_CONNECT)) {
                    afterBt = () -> { if (has(Manifest.permission.BLUETOOTH_CONNECT)) pickAndPrint(w, data, cb); else done(w, cb, false, "بلوٹوتھ کی اجازت نہیں ملی"); };
                    requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT}, REQ_BT);
                } else pickAndPrint(w, data, cb);
            });
        }
    }

    SharedPreferences prefs() { return getSharedPreferences("pbtapp", MODE_PRIVATE); }

    void done(WebView w, String cb, boolean ok, String msg) {
        final String js = "window.__pbtCb&&__pbtCb(" + JSONObject.quote(cb) + "," + ok + "," + JSONObject.quote(msg) + ")";
        ui.post(() -> w.evaluateJavascript(js, null));
    }

    @SuppressWarnings("MissingPermission")
    void pickAndPrint(final WebView w, final byte[] data, final String cb) {
        final BluetoothAdapter ad = BluetoothAdapter.getDefaultAdapter();
        if (ad == null) { done(w, cb, false, "اس فون میں بلوٹوتھ نہیں"); return; }
        if (!ad.isEnabled()) { done(w, cb, false, "فون کا بلوٹوتھ بند ہے — آن کر کے دوبارہ"); return; }
        final List<BluetoothDevice> L = new ArrayList<>(ad.getBondedDevices());
        String saved = prefs().getString("bt", "");
        for (BluetoothDevice d : L) if (d.getAddress().equals(saved)) { send(w, d, data, cb); return; }
        if (L.isEmpty()) { done(w, cb, false, "کوئی جوڑا ہوا (Paired) پرنٹر نہیں — فون کی بلوٹوتھ سیٹنگ میں پرنٹر جوڑیں"); return; }
        String[] names = new String[L.size()];
        for (int i = 0; i < L.size(); i++) { String n = L.get(i).getName(); names[i] = (n == null ? "?" : n) + "  " + L.get(i).getAddress(); }
        new AlertDialog.Builder(this).setTitle("🖨️ پرنٹر چنیں").setItems(names, (dd, i) -> { prefs().edit().putString("bt", L.get(i).getAddress()).apply(); send(w, L.get(i), data, cb); })
            .setOnCancelListener(x -> done(w, cb, false, "")).show();
    }

    @SuppressWarnings("MissingPermission")
    void send(final WebView w, final BluetoothDevice d, final byte[] data, final String cb) {
        toast("🖨️ پرنٹ ہو رہا ہے…");
        new Thread(() -> {
            BluetoothSocket s = null;
            try {
                try { BluetoothAdapter.getDefaultAdapter().cancelDiscovery(); } catch (Exception e) {}
                s = d.createRfcommSocketToServiceRecord(SPP);
                try { s.connect(); } catch (Exception e) { try { s.close(); } catch (Exception e2) {} s = d.createInsecureRfcommSocketToServiceRecord(SPP); s.connect(); }
                OutputStream o = s.getOutputStream();
                for (int i = 0; i < data.length; i += 2048) { o.write(data, i, Math.min(2048, data.length - i)); o.flush(); Thread.sleep(15); }
                Thread.sleep(400);
                done(w, cb, true, "");
            } catch (Exception e) {
                prefs().edit().remove("bt").apply();
                done(w, cb, false, "پرنٹر سے رابطہ نہیں ہوا — پرنٹر آن ہے؟ (" + e.getMessage() + ")");
            } finally { try { if (s != null) s.close(); } catch (Exception e) {} }
        }).start();
    }
}
