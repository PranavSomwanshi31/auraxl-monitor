# AuraXL Agentic Monitor - Anywhere & Worldwide Deployment Guide

This guide explains how to access and use your **AuraXL Agentic Monitor APK** from **anywhere in the world** (on mobile phones, 4G/5G cellular data, tablets, or remote computers).

---

## 🌟 Method 1: Automatic Global HTTPS Tunnel (Ready Out-of-the-Box)

Whenever you run:
```powershell
python "D:\Auraxl\Website\run_server.py"
```
The server automatically launches a **Cloudflare Global Tunnel** that assigns you a live public HTTPS address:
```
👉 https://[random-subdomain].trycloudflare.com
```
*(The link is printed in your terminal and saved to `D:\Auraxl\Website\GLOBAL_ACCESS_URL.txt`)*

### How to use anywhere:
1. Copy the global HTTPS URL.
2. Open it in **Google Chrome** on ANY mobile phone (connected to mobile 4G/5G data or remote Wi-Fi).
3. Tap **"Install AuraXL Monitor"** / **"Add to Home Screen"** to install the APK directly!
4. Log in with **UserID**: `admin` | **Password**: `AuraXL@2026`.

---

## ☁️ Method 2: Free 24/7 Cloud Hosting (No PC Required)

If you want the monitor to run continuously 24/7 in the cloud even when your personal computer is turned off:

### Deploy to Render (Free):
1. Create a free account at [Render.com](https://render.com).
2. Click **New +** > **Web Service**.
3. Connect your repository or upload the `D:\Auraxl\Website` folder.
4. Render will automatically detect `render.yaml` or set:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python backend/app.py`
5. Click **Deploy**. Render gives you a permanent 24/7 URL like:
   ```
   https://auraxl-monitor.onrender.com
   ```

### Deploy via Docker:
Run on any VPS, AWS EC2, Google Cloud Run, or DigitalOcean droplet:
```bash
docker build -t auraxl-monitor .
docker run -d -p 5000:5000 --name auraxl auraxl-monitor
```

---

## 📱 Method 3: Local Network Access

When on the same Wi-Fi network at home or office:
- **PC Access**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Local Phone Access**: `http://192.168.30.220:5000`

---

## 🔑 Login Credentials
- **UserID**: `admin`
- **Password**: `AuraXL@2026`
- **Target Site**: `https://www.auraxl.com`
