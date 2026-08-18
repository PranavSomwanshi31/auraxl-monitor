# AuraXL Agentic Monitor - Android APK Installation Guide

This project supports **Two Instant Methods** to install and run the Android APK:

---

## Method 1: Instant Direct APK / PWA Install (No Android Studio Required) ⚡
1. Start the server on your computer:
   ```bash
   python D:\Auraxl\Website\run_server.py
   ```
2. Make sure your Android Phone is connected to the same Wi-Fi network as your PC.
3. Open **Google Chrome** on your Android Phone.
4. Navigate to:
   ```
   http://192.168.30.220:5000
   ```
5. Chrome will display the prompt: **"Add AuraXL Monitor to Home screen"** or tap the 3-dots menu > **"Install App"**.
6. The standalone **AuraXL Agentic Monitor APK** will be installed directly on your Android phone with its app icon, push notifications, and full-screen view!

---

## Method 2: Compile Native Android APK with Android Studio 📱
1. Open **Android Studio**.
2. Select **Open Project** -> Choose `D:\Auraxl\Website\android`.
3. Click **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**.
4. Android Studio will generate the debug APK at `android/app/build/outputs/apk/debug/app-debug.apk`.
5. Transfer and install `app-debug.apk` onto your phone.

---

## Default Login Credentials
- **UserID**: `admin`
- **Password**: `AuraXL@2026`
- **Monitored Website**: `https://www.auraxl.com`
