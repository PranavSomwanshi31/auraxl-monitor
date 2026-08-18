import os
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

BASE_DIR = r"D:\Auraxl\Website"
ANDROID_DIR = os.path.join(BASE_DIR, "android")
os.makedirs(os.path.join(ANDROID_DIR, "app", "src", "main", "java", "com", "auraxl", "monitor"), exist_ok=True)
os.makedirs(os.path.join(ANDROID_DIR, "app", "src", "main", "res", "values"), exist_ok=True)

local_ip = get_local_ip()

# 1. AndroidManifest.xml
manifest_content = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.auraxl.monitor">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="AuraXL Monitor"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.AuraXLMonitor">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:theme="@style/Theme.AuraXLMonitor.NoActionBar">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

with open(os.path.join(ANDROID_DIR, "app", "src", "main", "AndroidManifest.xml"), "w", encoding="utf-8") as f:
    f.write(manifest_content)

# 2. MainActivity.java
main_activity_content = f"""package com.auraxl.monitor;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {{
    private WebView webView;
    // Replace with your server IP or domain
    private static final String APP_URL = "http://{local_ip}:5000";

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webview);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setDatabaseEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient() {{
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {{
                Toast.makeText(MainActivity.this, "Connecting to AuraXL Server...", Toast.LENGTH_SHORT).show();
            }}
        }});
        webView.setWebChromeClient(new WebChromeClient());

        webView.loadUrl(APP_URL);
    }}

    @Override
    public void onBackPressed() {{
        if (webView.canGoBack()) {{
            webView.goBack();
        }} else {{
            super.onBackPressed();
        }}
    }}
}}
"""

with open(os.path.join(ANDROID_DIR, "app", "src", "main", "java", "com", "auraxl", "monitor", "MainActivity.java"), "w", encoding="utf-8") as f:
    f.write(main_activity_content)

# 3. Android build guide & 2-method APK installation doc
guide_content = f"""# AuraXL Agentic Monitor - Android APK Installation Guide

This project supports **Two Instant Methods** to install and run the Android APK:

---

## Method 1: Instant Direct APK / PWA Install (No Android Studio Required) ⚡
1. Start the server on your computer:
   ```bash
   python D:\\Auraxl\\Website\\run_server.py
   ```
2. Make sure your Android Phone is connected to the same Wi-Fi network as your PC.
3. Open **Google Chrome** on your Android Phone.
4. Navigate to:
   ```
   http://{local_ip}:5000
   ```
5. Chrome will display the prompt: **"Add AuraXL Monitor to Home screen"** or tap the 3-dots menu > **"Install App"**.
6. The standalone **AuraXL Agentic Monitor APK** will be installed directly on your Android phone with its app icon, push notifications, and full-screen view!

---

## Method 2: Compile Native Android APK with Android Studio 📱
1. Open **Android Studio**.
2. Select **Open Project** -> Choose `D:\\Auraxl\\Website\\android`.
3. Click **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
4. Android Studio will generate the debug APK at `android/app/build/outputs/apk/debug/app-debug.apk`.
5. Transfer and install `app-debug.apk` onto your phone.

---

## Default Login Credentials
- **UserID**: `admin`
- **Password**: `AuraXL@2026`
- **Monitored Website**: `https://www.auraxl.com`
"""

with open(os.path.join(BASE_DIR, "APK_INSTALLATION_GUIDE.md"), "w", encoding="utf-8") as f:
    f.write(guide_content)

print(f"Android wrapper created. Local IP for mobile: http://{local_ip}:5000")
