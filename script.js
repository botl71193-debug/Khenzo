<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App Manager | MMK MODS</title>
  <link rel="stylesheet" href="style.css">
  <style>
    :root {
      --bg-main: #020205; --bg-card: #060814; --bg-sidebar: #03040b;
      --primary: #0052ff; --accent: #00f3ff; --exec-color: #a855f7;
      --dev-color: #f43f5e; --text-main: #f1f5f9; --text-muted: #64748b;
      --border: rgba(0, 82, 255, 0.25);
    }
    body { background: var(--bg-main); color: var(--text-main); padding: 20px; font-family: 'Segoe UI', Roboto, sans-serif; min-height: 100vh; }
    .am-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; flex-wrap: wrap; gap: 12px; }
    .am-header h1 { font-size: 1.4rem; font-weight: 900; background: linear-gradient(to right, #fff, var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .am-back-btn { background: rgba(0,82,255,0.15); border: 1px solid var(--primary); color: var(--accent); padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 0.85rem; }
    .am-back-btn:hover { background: var(--primary); color: #fff; }
    .am-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 20px; margin-bottom: 18px; }
    .am-card-title { font-size: 0.78rem; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px; border-bottom: 1px solid rgba(0,243,255,0.15); padding-bottom: 8px; }
    .am-form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
    .am-form-group label { font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.8px; }
    .am-form-group input, .am-form-group textarea, .am-form-group select {
      background: #020205; border: 1px solid rgba(0,82,255,0.3); border-radius: 8px;
      padding: 11px 14px; color: #fff; outline: none; font-size: 0.9rem; width: 100%;
    }
    .am-form-group input:focus, .am-form-group textarea:focus { border-color: var(--accent); box-shadow: 0 0 8px rgba(0,243,255,0.2); }
    .am-form-group textarea { min-height: 90px; resize: vertical; font-family: inherit; line-height: 1.45; }
    .am-row { display: flex; gap: 12px; flex-wrap: wrap; }
    .am-row .am-form-group { flex: 1; min-width: 140px; }
    .am-toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
    .am-toggle-row:last-child { border-bottom: none; }
    .am-toggle-label { font-size: 0.88rem; font-weight: 600; color: #e2e8f0; }
    .am-switch { position: relative; width: 48px; height: 26px; }
    .am-switch input { opacity: 0; width: 0; height: 0; }
    .am-slider { position: absolute; cursor: pointer; inset: 0; background: #334155; border-radius: 26px; transition: 0.3s; }
    .am-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
    .am-switch input:checked + .am-slider { background: linear-gradient(135deg, var(--primary), var(--accent)); }
    .am-switch input:checked + .am-slider:before { transform: translateX(22px); }
    .am-btn-row { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
    .am-btn { flex: 1; min-width: 120px; padding: 12px 16px; border: none; border-radius: 10px; font-weight: 700; font-size: 0.88rem; cursor: pointer; transition: 0.25s; }
    .am-btn-primary { background: linear-gradient(135deg, var(--primary), #002ba1); color: #fff; }
    .am-btn-primary:hover { box-shadow: 0 0 15px var(--accent); }
    .am-btn-check { background: linear-gradient(135deg, #0ea5e9, #0369a1); color: #fff; }
    .am-btn-check:hover { box-shadow: 0 0 12px #0ea5e9; }
    .am-btn-push { background: linear-gradient(135deg, var(--dev-color), #991b1b); color: #fff; }
    .am-btn-push:hover { box-shadow: 0 0 15px var(--dev-color); }
    .am-btn-secondary { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
    .pkg-check-row { display: flex; gap: 8px; align-items: flex-end; }
    .pkg-check-row .am-form-group { flex: 1; margin-bottom: 0; }
    .status-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; margin-top: 6px; }
    .status-ok { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .status-warn { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
    .status-err { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .am-preview-box { background: #010208; border: 1px dashed rgba(0,243,255,0.25); border-radius: 10px; padding: 14px; font-size: 0.82rem; color: #94a3b8; white-space: pre-wrap; max-height: 160px; overflow-y: auto; margin-top: 8px; }
    @media (max-width: 600px) {
      .am-row { flex-direction: column; }
      .pkg-check-row { flex-direction: column; align-items: stretch; }
    }
  </style>
</head>
<body>
  <div class="am-header">
    <h1>🧰 App Manager</h1>
    <a href="index.html" class="am-back-btn">← Kembali ke MMK MODS</a>
  </div>

  <!-- PKG + Version Check -->
  <div class="am-card">
    <div class="am-card-title">📦 Package & Version</div>
    <div class="pkg-check-row">
      <div class="am-form-group">
        <label>Input Pkg App</label>
        <input type="text" id="pkgInput" placeholder="com.example.game" value="">
      </div>
      <button class="am-btn am-btn-check" style="flex:0; min-width:140px; height:44px;" onclick="checkVersion()">Check Version</button>
    </div>
    <div id="versionStatus"></div>
  </div>

  <!-- UI Toggles -->
  <div class="am-card">
    <div class="am-card-title">🎛️ UI Controls</div>
    <div class="am-toggle-row">
      <span class="am-toggle-label">On/Off UI Animation</span>
      <label class="am-switch">
        <input type="checkbox" id="toggleUiAnim" checked>
        <span class="am-slider"></span>
      </label>
    </div>
    <div class="am-toggle-row">
      <span class="am-toggle-label">On/Off Theme</span>
      <label class="am-switch">
        <input type="checkbox" id="toggleTheme" checked>
        <span class="am-slider"></span>
      </label>
    </div>
  </div>

  <!-- Dates & Version -->
  <div class="am-card">
    <div class="am-card-title">📅 Schedule & Version Info</div>
    <div class="am-row">
      <div class="am-form-group">
        <label>Scheduled Date</label>
        <input type="datetime-local" id="scheduledDate">
      </div>
      <div class="am-form-group">
        <label>Release Date</label>
        <input type="datetime-local" id="releaseDate">
      </div>
    </div>
    <div class="am-form-group">
      <label>Current Version</label>
      <input type="text" id="currentVersion" placeholder="1.0.0">
    </div>
  </div>

  <!-- Dialog Content -->
  <div class="am-card">
    <div class="am-card-title">💬 Dialog Content</div>
    <div class="am-form-group">
      <label>Dialog Title</label>
      <input type="text" id="dialogTitle" placeholder="Update Available" value="Update Available">
    </div>
    <div class="am-form-group">
      <label>Update Button Link</label>
      <input type="text" id="updtBtnLink" placeholder="https://...">
    </div>
    <div class="am-form-group">
      <label>Update Button Text</label>
      <input type="text" id="updtBtnText" value="UPDATE">
    </div>
    <div class="am-form-group">
      <label>Logo URL</label>
      <input type="text" id="logoUrl" placeholder="https://...">
    </div>
  </div>

  <!-- Social Links -->
  <div class="am-card">
    <div class="am-card-title">🔗 Social Links</div>
    <div class="am-form-group">
      <label>Social Link 1</label>
      <input type="text" id="social1" placeholder="https://...">
    </div>
    <div class="am-form-group">
      <label>Social Link 2</label>
      <input type="text" id="social2" placeholder="https://...">
    </div>
    <div class="am-form-group">
      <label>Social Link 3</label>
      <input type="text" id="social3" placeholder="https://...">
    </div>
  </div>

  <!-- Messages -->
  <div class="am-card">
    <div class="am-card-title">📝 Messages</div>
    <div class="am-form-group">
      <label>Main Message</label>
      <textarea id="mainMessage">1. Anti-Ban Security Level High
2. Fastest Server Connection
3. VIP Features Unlocked
4. Mod By Zenx Modz</textarea>
    </div>
    <div class="am-form-group">
      <label>Detail Message</label>
      <textarea id="detailMessage">🚀 Pro Gaming Exp
🛡️ Safe & Verified
⚡ Instant Support
🌟 Unlimited Mods
📁 Auto Update Enabled
💎 Exclusive UI Themes
🔑 Zero Ads Experience
🔥 High FPS Optimization
🛠️ Bug Fixes V2
💎 Elite Membership</textarea>
    </div>
  </div>

  <!-- Notification -->
  <div class="am-card">
    <div class="am-card-title">🔔 Notification</div>
    <div class="am-toggle-row">
      <span class="am-toggle-label">Show Notifikasi</span>
      <label class="am-switch">
        <input type="checkbox" id="toggleNotif">
        <span class="am-slider"></span>
      </label>
    </div>
    <div class="am-form-group" style="margin-top:12px;">
      <label>Input Notif</label>
      <input type="text" id="notifText" placeholder="Pesan notifikasi...">
    </div>
  </div>

  <!-- Active Dialog + Push -->
  <div class="am-card">
    <div class="am-card-title">🚀 Push Dialog</div>
    <div class="am-toggle-row">
      <span class="am-toggle-label">Active Dialog (On/Off)</span>
      <label class="am-switch">
        <input type="checkbox" id="toggleActiveDialog" checked>
        <span class="am-slider"></span>
      </label>
    </div>
    <div class="am-btn-row" style="margin-top:16px;">
      <button class="am-btn am-btn-secondary" onclick="previewConfig()">Preview JSON</button>
      <button class="am-btn am-btn-push" onclick="pushDialog()">Push Dialog</button>
    </div>
    <div id="previewBox" class="am-preview-box" style="display:none;"></div>
    <div id="pushStatus" style="margin-top:12px;"></div>
  </div>

  <script>
    // Load saved config if any
    function loadSaved() {
      try {
        const raw = localStorage.getItem('mmk_appmanager_cfg');
        if (!raw) return;
        const cfg = JSON.parse(raw);
        if (cfg.pkg) document.getElementById('pkgInput').value = cfg.pkg;
        if (cfg.currentVersion) document.getElementById('currentVersion').value = cfg.currentVersion;
        if (cfg.dialogTitle) document.getElementById('dialogTitle').value = cfg.dialogTitle;
        if (cfg.updtBtnLink) document.getElementById('updtBtnLink').value = cfg.updtBtnLink;
        if (cfg.updtBtnText) document.getElementById('updtBtnText').value = cfg.updtBtnText;
        if (cfg.logoUrl) document.getElementById('logoUrl').value = cfg.logoUrl;
        if (cfg.social1) document.getElementById('social1').value = cfg.social1;
        if (cfg.social2) document.getElementById('social2').value = cfg.social2;
        if (cfg.social3) document.getElementById('social3').value = cfg.social3;
        if (cfg.mainMessage) document.getElementById('mainMessage').value = cfg.mainMessage;
        if (cfg.detailMessage) document.getElementById('detailMessage').value = cfg.detailMessage;
        if (cfg.notifText) document.getElementById('notifText').value = cfg.notifText;
        if (typeof cfg.uiAnim === 'boolean') document.getElementById('toggleUiAnim').checked = cfg.uiAnim;
        if (typeof cfg.theme === 'boolean') document.getElementById('toggleTheme').checked = cfg.theme;
        if (typeof cfg.showNotif === 'boolean') document.getElementById('toggleNotif').checked = cfg.showNotif;
        if (typeof cfg.activeDialog === 'boolean') document.getElementById('toggleActiveDialog').checked = cfg.activeDialog;
        if (cfg.scheduledDate) document.getElementById('scheduledDate').value = cfg.scheduledDate;
        if (cfg.releaseDate) document.getElementById('releaseDate').value = cfg.releaseDate;
      } catch(e) {}
    }

    function collectConfig() {
      return {
        pkg: document.getElementById('pkgInput').value.trim(),
        uiAnim: document.getElementById('toggleUiAnim').checked,
        theme: document.getElementById('toggleTheme').checked,
        scheduledDate: document.getElementById('scheduledDate').value,
        releaseDate: document.getElementById('releaseDate').value,
        currentVersion: document.getElementById('currentVersion').value.trim(),
        dialogTitle: document.getElementById('dialogTitle').value.trim(),
        updtBtnLink: document.getElementById('updtBtnLink').value.trim(),
        updtBtnText: document.getElementById('updtBtnText').value.trim() || 'UPDATE',
        logoUrl: document.getElementById('logoUrl').value.trim(),
        social1: document.getElementById('social1').value.trim(),
        social2: document.getElementById('social2').value.trim(),
        social3: document.getElementById('social3').value.trim(),
        mainMessage: document.getElementById('mainMessage').value,
        detailMessage: document.getElementById('detailMessage').value,
        showNotif: document.getElementById('toggleNotif').checked,
        notifText: document.getElementById('notifText').value.trim(),
        activeDialog: document.getElementById('toggleActiveDialog').checked,
        updatedAt: new Date().toISOString()
      };
    }

    function checkVersion() {
      const pkg = document.getElementById('pkgInput').value.trim();
      const statusEl = document.getElementById('versionStatus');
      if (!pkg) {
        statusEl.innerHTML = '<span class="status-badge status-err">Masukkan Package Name dulu</span>';
        return;
      }
      // Simulasi check version (bisa diganti endpoint real nanti)
      const ver = document.getElementById('currentVersion').value.trim() || '—';
      statusEl.innerHTML = `<span class="status-badge status-ok">Pkg: ${pkg} | Current Version: ${ver}</span>`;
      // Auto-fill current version field tetap di pkg yang sama
    }

    function previewConfig() {
      const cfg = collectConfig();
      const box = document.getElementById('previewBox');
      box.style.display = 'block';
      box.textContent = JSON.stringify(cfg, null, 2);
    }

    function pushDialog() {
      const cfg = collectConfig();
      if (!cfg.pkg) {
        document.getElementById('pushStatus').innerHTML = '<span class="status-badge status-err">Package Name wajib diisi!</span>';
        return;
      }
      localStorage.setItem('mmk_appmanager_cfg', JSON.stringify(cfg));
      // Simpan juga ke key per-package agar bisa multi-app
      localStorage.setItem('mmk_appmanager_' + cfg.pkg, JSON.stringify(cfg));

      document.getElementById('pushStatus').innerHTML = '<span class="status-badge status-ok">✅ Dialog config berhasil di-push & disimpan untuk pkg: ' + cfg.pkg + '</span>';
      previewConfig();
    }

    // Init
    loadSaved();
  </script>
</body>
</html>
