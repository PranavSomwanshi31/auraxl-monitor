// AuraXL Agentic Monitor Frontend Logic - Seamless Firebase & Cloud Edition
const DEFAULT_GLOBAL_BACKEND = "https://learners-beverly-outer-recorder.trycloudflare.com";

let authToken = localStorage.getItem("auraxl_token") || "";
let currentUser = null;
let activeTab = "dashboard";
let pollingTimer = null;
let currentIssues = [];
let deferredPrompt = null;

// Backend API configuration
let API_BASE = localStorage.getItem("auraxl_api_base") || "";

function getApiBase() {
  if (API_BASE && API_BASE.trim() !== "") {
    return API_BASE.replace(/\/$/, "");
  }
  // If running on Firebase Hosting (web.app / firebaseapp.com), use the global tunnel default
  if (window.location.hostname.includes("web.app") || window.location.hostname.includes("firebaseapp.com")) {
    return DEFAULT_GLOBAL_BACKEND;
  }
  return "";
}

// Sound Alert
function playAlertSound(type = "warning") {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    if (type === "critical") {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
      osc.start(); osc.stop(audioCtx.currentTime + 0.5);
    } else {
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
      osc.start(); osc.stop(audioCtx.currentTime + 0.3);
    }
  } catch (e) {}
}

// Toast
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  const bg = type === "error" ? "bg-rose-500 text-white" :
             type === "success" ? "bg-emerald-600 text-white" :
             type === "warning" ? "bg-[#F26727] text-white" : "bg-[#0DB2A7] text-white";
  toast.className = `flex items-center gap-3 px-4 py-3 rounded-2xl shadow-xl ${bg} transition-all transform duration-300 translate-y-2 opacity-0 text-xs font-bold pointer-events-auto`;
  toast.innerHTML = `<i class="fas ${type==="error"?"fa-triangle-exclamation":type==="success"?"fa-check-circle":"fa-info-circle"} text-sm"></i><span class="flex-1 leading-snug">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.classList.remove("translate-y-2","opacity-0"), 10);
  setTimeout(() => { toast.classList.add("opacity-0","translate-y-2"); setTimeout(()=>toast.remove(),300); }, 4500);
}

// API Helper
async function api(endpoint, options = {}) {
  const base = getApiBase();
  const headers = options.headers || {};
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  if (!headers["Content-Type"] && options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  try {
    const res = await fetch(`${base}/api${endpoint}`, { ...options, headers });
    if (res.status === 401) { handleUnauthorized(); throw new Error("Unauthorized"); }
    return await res.json();
  } catch (err) {
    if (err.message === "Unauthorized") throw err;
    throw err;
  }
}

function handleUnauthorized() {
  authToken = "";
  localStorage.removeItem("auraxl_token");
  document.getElementById("auth-modal").classList.remove("hidden");
  document.getElementById("main-app").classList.add("hidden");
  if (pollingTimer) clearInterval(pollingTimer);
}

// App Init
document.addEventListener("DOMContentLoaded", async () => {
  setupPWA();
  setupEventListeners();

  if (authToken) {
    try {
      const res = await api("/auth/verify");
      if (res.authenticated) { currentUser = res.user; showApp(); return; }
    } catch (e) {}
  }
  handleUnauthorized();
});

function setupPWA() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(e => console.log("SW:", e));
  }
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const b = document.getElementById("pwa-install-banner");
    if (b) b.classList.remove("hidden");
  });
}

function showApp() {
  document.getElementById("auth-modal").classList.add("hidden");
  document.getElementById("main-app").classList.remove("hidden");
  document.getElementById("user-display-name").textContent = currentUser?.display_name || "Admin";
  switchTab(activeTab);
  loadDashboard();
  loadNotifications();
  if (pollingTimer) clearInterval(pollingTimer);
  pollingTimer = setInterval(() => {
    if (activeTab === "dashboard") loadDashboard(false);
    loadNotifications(false);
  }, 8000);
}

function switchTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.style.color = "#94a3b8";
    btn.style.backgroundColor = "transparent";
    btn.style.borderColor = "transparent";
  });
  const t = document.getElementById(`tab-${tabName}`);
  if (t) t.classList.remove("hidden");
  const b = document.getElementById(`nav-${tabName}`);
  if (b) { b.style.color="#0DB2A7"; b.style.backgroundColor="#f0fdfa"; b.style.borderColor="#99f6e4"; b.classList.add("font-bold"); }
  if (tabName === "dashboard") loadDashboard();
  if (tabName === "pages") loadPages();
  if (tabName === "diagnostics") loadDiagnostics();
  if (tabName === "notifications") loadNotifications(true);
  if (tabName === "settings") loadSettings();
}

function setupEventListeners() {
  document.getElementById("login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userId = document.getElementById("login-userid").value.trim();
    const pass = document.getElementById("login-password").value;
    const errorEl = document.getElementById("login-error");
    const btn = document.getElementById("login-btn");
    errorEl.classList.add("hidden");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-circle-notch fa-spin"></i> Authenticating...`;
    try {
      const res = await api("/auth/login", { method:"POST", body: JSON.stringify({user_id:userId, password:pass}) });
      if (res.success) {
        authToken = res.data.token;
        localStorage.setItem("auraxl_token", authToken);
        currentUser = res.data;
        showToast("Welcome to AuraXL Monitor!", "success");
        showApp();
      } else {
        errorEl.textContent = res.error || "Invalid UserID or Password.";
        errorEl.classList.remove("hidden");
      }
    } catch (err) {
      errorEl.textContent = "Connecting to backend... check that backend server is running.";
      errorEl.classList.remove("hidden");
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>Sign In to Monitor</span> <i class="fas fa-arrow-right text-xs"></i>`;
    }
  });

  document.getElementById("logout-btn")?.addEventListener("click", async () => {
    try { await api("/auth/logout", {method:"POST"}); } catch(e){}
    handleUnauthorized();
    showToast("Logged out.", "info");
  });

  document.getElementById("dash-quick-scan-btn")?.addEventListener("click", runManualScan);

  document.getElementById("settings-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const targetUrl = document.getElementById("setting-target-url").value.trim();
    const interval = document.getElementById("setting-interval").value;
    const autoEnabled = document.getElementById("setting-auto-enabled").checked;
    const soundEnabled = document.getElementById("setting-sound-enabled").checked;
    try {
      const res = await api("/settings", { method:"POST", body: JSON.stringify({ target_url: targetUrl, monitor_interval_minutes: interval, auto_monitor_enabled: autoEnabled.toString(), sound_alerts: soundEnabled.toString() }) });
      if (res.success) { showToast("Settings saved!", "success"); loadDashboard(); }
    } catch(e) { showToast("Failed to save settings.", "error"); }
  });

  document.getElementById("password-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const oldPass = document.getElementById("old-pass").value;
    const newPass = document.getElementById("new-pass").value;
    try {
      const res = await api("/auth/update-password", { method:"POST", body: JSON.stringify({old_password:oldPass, new_password:newPass}) });
      if (res.success) { showToast("Password updated!", "success"); document.getElementById("old-pass").value=""; document.getElementById("new-pass").value=""; }
      else showToast(res.error||"Update failed.", "error");
    } catch(e) { showToast("Error updating password.", "error"); }
  });

  document.getElementById("chat-form")?.addEventListener("submit", handleChatSubmit);

  document.getElementById("pwa-install-btn")?.addEventListener("click", async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const {outcome} = await deferredPrompt.userChoice;
      if (outcome === "accepted") showToast("AuraXL Monitor installed!", "success");
      deferredPrompt = null;
      document.getElementById("pwa-install-banner")?.classList.add("hidden");
    }
  });
}

async function runManualScan() {
  const scanBtn = document.getElementById("dash-quick-scan-btn");
  const origHtml = scanBtn?.innerHTML;
  if (scanBtn) { scanBtn.disabled=true; scanBtn.innerHTML=`<i class="fas fa-satellite-dish fa-spin"></i> Running Deep Audit...`; }
  showToast("Deep audit initiated on www.auraxl.com...", "info");
  try {
    const res = await api("/monitor/scan", {method:"POST"});
    if (res.success) {
      if (res.data.health_score < 50) playAlertSound("critical"); else playAlertSound("info");
      showToast(`Audit done! Health: ${res.data.health_score}/100`, res.data.health_score>70?"success":"warning");
      loadDashboard(); loadPages(); loadDiagnostics(); loadNotifications();
    }
  } catch(e) { showToast("Audit error. Check server connection.", "error"); }
  finally { if(scanBtn){scanBtn.disabled=false; scanBtn.innerHTML=origHtml;} }
}

async function loadDashboard(showLoader=true) {
  try {
    const res = await api("/monitor/status");
    if (!res.success || !res.data) return;
    const data = res.data;
    const score = data.health_score || 0;
    const scoreEl = document.getElementById("health-score-val");
    if (scoreEl) scoreEl.textContent = score;
    const badgeEl = document.getElementById("status-badge");
    const pulseEl = document.getElementById("status-pulse");
    const ipEl = document.getElementById("dash-resolved-ip");
    if (document.getElementById("dash-target-url")) document.getElementById("dash-target-url").textContent = data.target_url || "www.auraxl.com";
    let ip = "34.120.137.41";
    if (data.summary?.dns?.ips?.length) ip = data.summary.dns.ips[0];
    if (ipEl) ipEl.textContent = `DNS IP: ${ip}`;
    if (badgeEl && pulseEl) {
      if (score>=80) { badgeEl.className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-600 border border-emerald-200"; badgeEl.textContent="Healthy & Online"; pulseEl.className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"; }
      else if (score>=40) { badgeEl.className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-50 text-amber-600 border border-amber-200"; badgeEl.textContent="Degraded / Warnings"; pulseEl.className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping"; }
      else { badgeEl.className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-orange-50 text-[#F26727] border border-orange-200"; badgeEl.textContent="Critical Outage"; pulseEl.className="w-2.5 h-2.5 rounded-full bg-[#F26727] animate-ping"; }
    }
    const ringEl = document.getElementById("health-ring");
    if (ringEl) {
      const circ = 2*Math.PI*42;
      ringEl.style.strokeDasharray=`${circ} ${circ}`;
      ringEl.style.strokeDashoffset=circ-(score/100)*circ;
      ringEl.style.stroke=score>=80?"#10b981":score>=40?"#f59e0b":"#F26727";
    }
    document.getElementById("metric-issues").textContent = data.issues_count??0;
    document.getElementById("metric-pages").textContent = data.total_pages_scanned??0;
    document.getElementById("metric-latency").textContent = `${Math.round(data.response_time_ms||0)}ms`;
    const sslEl = document.getElementById("metric-ssl");
    if (sslEl) { sslEl.textContent = data.ssl_status==="VALID"?"Valid (TLS Active)":"SSL EOF Drop"; sslEl.className=data.ssl_status==="VALID"?"text-emerald-600 font-bold text-xs":"text-[#F26727] font-bold text-xs"; }
    loadRecentIssuesPreview();
  } catch(e) { console.error("Dashboard error:", e); }
}

async function loadRecentIssuesPreview() {
  try {
    const res = await api("/monitor/issues");
    if (!res.success) return;
    const issues = res.data || [];
    currentIssues = issues;
    const container = document.getElementById("dash-issues-preview");
    if (!container) return;
    if (issues.length===0) { container.innerHTML=`<div class="p-6 text-center text-slate-400 aura-card rounded-2xl"><i class="fas fa-shield-check text-emerald-500 text-3xl mb-2"></i><p class="font-bold text-slate-700">No Active Issues</p></div>`; return; }
    container.innerHTML = issues.slice(0,3).map(issue=>`
      <div class="p-4 aura-card rounded-2xl border ${issue.severity==="CRITICAL"?"border-orange-200 bg-orange-50/20":"border-teal-100"} flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${issue.severity==="CRITICAL"?"bg-orange-100 text-[#F26727] border border-orange-200":"bg-teal-50 text-[#0DB2A7] border border-teal-200"}">${issue.severity}</span>
          <span class="text-xs text-slate-400 font-mono">${new Date(issue.created_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</span>
        </div>
        <h4 class="font-bold text-slate-800 text-sm">${issue.title}</h4>
        <p class="text-xs text-slate-600 line-clamp-2">${issue.description}</p>
        <button onclick="openSolutionModal(${issue.id})" class="mt-1 text-xs font-bold text-[#0DB2A7] flex items-center gap-1.5 self-start">
          <i class="fas fa-wrench"></i> View Fix & Support Ticket <i class="fas fa-arrow-right text-[10px]"></i>
        </button>
      </div>
    `).join("");
  } catch(e) { console.error(e); }
}

async function loadPages() {
  const container = document.getElementById("pages-list");
  if (!container) return;
  container.innerHTML=`<div class="p-8 text-center text-slate-400"><i class="fas fa-spinner fa-spin text-2xl mb-2 text-[#2BC0D4]"></i><p>Loading scanned routes...</p></div>`;
  try {
    const res = await api("/monitor/pages");
    if (!res.success) return;
    const pages = res.data||[];
    if (pages.length===0) { container.innerHTML=`<div class="p-8 text-center text-slate-400">No pages recorded. Tap Re-Scan.</div>`; return; }
    container.innerHTML=pages.map(p=>{
      const isOk=p.status_code>=200&&p.status_code<400;
      const badge=isOk?`<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">${p.status_code} OK</span>`:`<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-orange-50 text-[#F26727] border border-orange-200">${p.status_code||"DROP"}</span>`;
      return `<div class="p-4 aura-card hover:border-teal-200 rounded-2xl flex flex-col gap-2 transition-all">
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0"><div class="flex items-center gap-2 flex-wrap">${badge}<span class="font-mono text-sm text-slate-800 truncate font-bold">${p.path||"/"}</span></div><p class="text-xs text-slate-500 mt-1 truncate">${p.url}</p></div>
          <span class="text-xs font-mono text-slate-500">${Math.round(p.response_time_ms||0)}ms</span>
        </div>
        <div class="flex items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
          <span><i class="fas fa-link text-[#2BC0D4] mr-1"></i>${p.links_found} links</span>
          <span><i class="fas fa-image text-[#0DB2A7] mr-1"></i>${p.assets_found} assets</span>
          ${p.issues&&p.issues.length>0?`<span class="text-[#F26727] font-semibold"><i class="fas fa-triangle-exclamation mr-1"></i>${p.issues.length} issue(s)</span>`:`<span class="text-emerald-600 font-semibold"><i class="fas fa-check mr-1"></i>Clean</span>`}
        </div>
      </div>`;
    }).join("");
  } catch(e) { container.innerHTML=`<div class="p-8 text-center text-rose-500">Failed to load pages. Check server connection.</div>`; }
}

async function loadDiagnostics() {
  const container=document.getElementById("diagnostics-list");
  if (!container) return;
  container.innerHTML=`<div class="p-8 text-center text-slate-400"><i class="fas fa-spinner fa-spin text-2xl mb-2 text-[#2BC0D4]"></i><p>Loading AI Diagnostics...</p></div>`;
  try {
    const res=await api("/monitor/issues");
    if (!res.success) return;
    const issues=res.data||[];
    currentIssues=issues;
    if (issues.length===0) { container.innerHTML=`<div class="p-12 text-center aura-card rounded-3xl"><i class="fas fa-check-double text-emerald-500 text-4xl mb-3"></i><h3 class="text-lg font-bold text-slate-800">Zero Issues Detected</h3></div>`; return; }
    container.innerHTML=issues.map(issue=>`
      <div class="p-5 aura-card rounded-3xl border ${issue.severity==="CRITICAL"?"border-orange-200":"border-teal-100"} flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <span class="px-3 py-1 rounded-full text-xs font-bold tracking-wider ${issue.severity==="CRITICAL"?"bg-orange-50 text-[#F26727] border border-orange-200":"bg-teal-50 text-[#0DB2A7] border border-teal-200"}">${issue.severity}</span>
          <span class="text-xs text-slate-500 font-mono">${issue.error_type}</span>
        </div>
        <div><h3 class="text-base font-bold text-slate-800">${issue.title}</h3><p class="text-xs text-slate-500 font-mono mt-0.5 truncate">${issue.page_url}</p></div>
        <div class="p-3.5 bg-slate-50 rounded-2xl border border-teal-100 text-xs text-slate-700"><span class="font-bold text-[#0DB2A7] block mb-1">AI Explanation:</span>${issue.description}</div>
        <div class="p-3.5 bg-orange-50/40 rounded-2xl border border-orange-100 text-xs text-slate-700"><span class="font-bold text-[#F26727] block mb-1">Root Cause:</span>${issue.root_cause}</div>
        <button onclick="openSolutionModal(${issue.id})" class="w-full py-3 aura-gradient-btn rounded-2xl font-bold text-xs shadow flex items-center justify-center gap-2">
          <i class="fas fa-tools"></i> View Steps & Copy Support Ticket
        </button>
      </div>
    `).join("");
  } catch(e) { container.innerHTML=`<div class="p-8 text-center text-rose-500">Failed to load diagnostics.</div>`; }
}

async function openSolutionModal(issueId) {
  try {
    const res=await api(`/monitor/issue/${issueId}`);
    if (!res.success||!res.data) return;
    const issue=res.data;
    document.getElementById("modal-issue-title").textContent=issue.title;
    document.getElementById("modal-issue-url").textContent=issue.page_url;
    document.getElementById("modal-issue-desc").textContent=issue.description;
    document.getElementById("modal-issue-root").textContent=issue.root_cause;
    const stepsContainer=document.getElementById("modal-steps-container");
    let steps=issue.user_fix_steps;
    if (typeof steps==="string") { try{steps=JSON.parse(steps);}catch(e){} }
    if (Array.isArray(steps)&&steps.length>0) {
      stepsContainer.innerHTML=steps.map(s=>`<div class="p-4 bg-slate-50 rounded-2xl border border-teal-100 flex gap-3"><div class="w-6 h-6 rounded-full bg-[#0DB2A7] text-white flex items-center justify-center font-bold text-xs flex-shrink-0">${s.step||"✓"}</div><div class="flex-1"><h5 class="font-bold text-slate-800 text-xs">${s.title}</h5><p class="text-xs text-slate-600 mt-1 leading-relaxed">${s.action}</p></div></div>`).join("");
    } else { stepsContainer.innerHTML=`<p class="text-xs text-slate-400">Follow hosting instructions below.</p>`; }
    const ticketBox=document.getElementById("modal-ticket-text");
    ticketBox.value=issue.support_ticket_template||"No template available.";
    const copyBtn=document.getElementById("modal-copy-ticket-btn");
    copyBtn.onclick=()=>{
      navigator.clipboard.writeText(ticketBox.value).then(()=>{
        showToast("Support ticket copied! Paste it to your hosting portal.", "success");
        copyBtn.innerHTML=`<i class="fas fa-check text-white"></i> Copied!`;
        setTimeout(()=>{copyBtn.innerHTML=`<i class="fas fa-copy"></i> Copy Support Ticket Template`;},2500);
      });
    };
    document.getElementById("solution-modal").classList.remove("hidden");
  } catch(e) { showToast("Failed to load solution.", "error"); }
}

function closeSolutionModal() { document.getElementById("solution-modal").classList.add("hidden"); }

async function loadNotifications(fullRender=false) {
  try {
    const res=await api("/notifications");
    if (!res.success) return;
    const notifs=res.data||[];
    const unread=res.unread_count||0;
    const badge=document.getElementById("notif-badge");
    const navBadge=document.getElementById("nav-notif-badge");
    if (badge){badge.textContent=unread;badge.classList.toggle("hidden",unread===0);}
    if (navBadge){navBadge.classList.toggle("hidden",unread===0);}
    if (!fullRender&&activeTab!=="notifications") return;
    const container=document.getElementById("notifications-list");
    if (!container) return;
    if (notifs.length===0){container.innerHTML=`<div class="p-12 text-center aura-card rounded-3xl"><i class="fas fa-bell-slash text-slate-400 text-3xl mb-2"></i><p class="font-bold text-slate-700">No Notifications</p></div>`;return;}
    container.innerHTML=notifs.map(n=>{
      const isCrit=n.severity==="CRITICAL",isSucc=n.severity==="SUCCESS";
      const icon=isCrit?"fa-circle-exclamation text-[#F26727]":isSucc?"fa-circle-check text-emerald-500":"fa-info-circle text-[#2BC0D4]";
      return `<div class="p-4 aura-card rounded-2xl border ${!n.is_read?"border-teal-300 bg-teal-50/30":"border-slate-100"} flex gap-3 transition-all">
        <i class="fas ${icon} text-lg mt-0.5"></i>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2"><h4 class="font-bold text-slate-800 text-xs truncate">${n.title}</h4><span class="text-[10px] text-slate-400 font-mono">${new Date(n.timestamp).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</span></div>
          <p class="text-xs text-slate-600 mt-1 leading-relaxed">${n.message}</p>
        </div>
      </div>`;
    }).join("");
  } catch(e) {}
}

async function markAllNotificationsRead() {
  try{await api("/notifications/read-all",{method:"POST"});showToast("Marked all read.","info");loadNotifications(true);}catch(e){}
}
async function clearNotifications() {
  try{await api("/notifications/clear",{method:"POST"});showToast("Cleared.","info");loadNotifications(true);}catch(e){}
}

async function handleChatSubmit(e) {
  e.preventDefault();
  const input=document.getElementById("chat-input");
  const msg=input.value.trim();
  if (!msg) return;
  const messagesContainer=document.getElementById("chat-messages");
  input.value="";
  messagesContainer.innerHTML+=`<div class="flex justify-end mb-3"><div class="max-w-[85%] p-3.5 bg-[#0DB2A7] text-white rounded-2xl rounded-tr-sm text-xs shadow-sm font-medium">${escapeHtml(msg)}</div></div>`;
  messagesContainer.scrollTop=messagesContainer.scrollHeight;
  const typingId=`typing-${Date.now()}`;
  messagesContainer.innerHTML+=`<div id="${typingId}" class="flex justify-start mb-3"><div class="max-w-[85%] p-3.5 bg-white text-slate-500 rounded-2xl rounded-tl-sm text-xs border border-teal-100 flex items-center gap-2"><i class="fas fa-robot text-[#2BC0D4]"></i><span>AuraXL AI is thinking...</span></div></div>`;
  messagesContainer.scrollTop=messagesContainer.scrollHeight;
  try {
    const res=await api("/agent/chat",{method:"POST",body:JSON.stringify({message:msg})});
    document.getElementById(typingId)?.remove();
    if (res.success) {
      messagesContainer.innerHTML+=`<div class="flex justify-start mb-3"><div class="max-w-[85%] p-3.5 bg-white text-slate-700 rounded-2xl rounded-tl-sm text-xs border border-teal-100 shadow-sm leading-relaxed"><div class="flex items-center gap-1.5 font-bold mb-1.5" style="color:#0DB2A7;"><i class="fas fa-brain"></i> AuraXL AI</div>${formatChatReply(res.reply)}</div></div>`;
    }
  } catch(e) { document.getElementById(typingId)?.remove(); }
  messagesContainer.scrollTop=messagesContainer.scrollHeight;
}

function sendPresetChat(text){const i=document.getElementById("chat-input");if(i){i.value=text;document.getElementById("chat-form")?.dispatchEvent(new Event("submit"));}}
function formatChatReply(t){let s=escapeHtml(t);s=s.replace(/\*\*(.*?)\*\*/g,"<strong class='text-slate-800'>$1</strong>");s=s.replace(/`([^`]+)`/g,"<code class='bg-teal-50 px-1 py-0.5 rounded text-[#0DB2A7] font-mono text-[11px] border border-teal-100'>$1</code>");s=s.replace(/\n/g,"<br>");return s;}
function escapeHtml(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}

async function loadSettings() {
  try {
    const res=await api("/settings");
    if (!res.success) return;
    const d=res.data;
    document.getElementById("setting-target-url").value=d.target_url||"https://www.auraxl.com";
    document.getElementById("setting-interval").value=d.monitor_interval_minutes||"5";
    document.getElementById("setting-auto-enabled").checked=d.auto_monitor_enabled==="true";
    document.getElementById("setting-sound-enabled").checked=d.sound_alerts==="true";
  } catch(e){}
}

