const rahasiaHTML = `
  <div class="navbar">
    <div class="navbar-left">
      <button class="menu-toggle" onclick="handleSidebarDisplay()">☰</button>
    </div>
    <div class="logo-box">
      <img class="logo" src="https://diverse-aqua-iq7wghij.edgeone.app/M.png" alt="Logo MMK">
      <span class="main-title">MMK | MODS</span>
    </div>
    <div class="navbar-right">
      <div id="devUndoRedoControls" style="display: none; gap: 8px; margin-right: 15px; align-items: center;">
        <button class="dev-action-badge-btn edit-btn" style="width: 32px; height: 32px; font-weight: bold;" title="Undo Data" onclick="undoDeveloperAction()">←</button>
        <button class="dev-action-badge-btn edit-btn" style="width: 32px; height: 32px; font-weight: bold;" title="Redo Data" onclick="redoDeveloperAction()">→</button>
      </div>
      <button class="search-trigger-btn" onclick="handleSearchToggle()">🔍</button>
      <div class="search-popover" id="searchPopover">
        <input type="text" id="searchInput" placeholder="Cari Mod Game..." onkeyup="executeApkSearch()">
      </div>
    </div>
  </div>

  <div class="sidebar" id="sidebarMenu">
    <span class="sidebar-close" onclick="handleSidebarDisplay()">×</span>
    <div class="sidebar-brand-area">
      <img class="sidebar-community-logo" src="https://diverse-aqua-iq7wghij.edgeone.app/M.png" alt="MMK Community">
      <div class="sidebar-brand-title">MMK | MODS</div>
      <div id="userSignBadge" class="sidebar-sign-text">Guest Mode</div>
    </div>
    <div class="cyber-auth-container" style="margin-bottom: 22px;">
      <button id="authTriggerBtn" class="cyber-auth-btn" onclick="handleAuthModalDisplay()">⚙️ Sign In</button>
    </div>
    <div class="sidebar-label">Kategori Aplikasi</div>
    <ul class="sidebar-menu-list">
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('all')">📱 All Apps</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Aplikasi Mod')">📦 Aplikasi Mod</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Games Mod')">🎮 Games Mod</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Streaming')">🎬 Streaming</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Music')">🎵 Music</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Tools')">🛠️ Tools</div></li>
      <li><div class="sidebar-item-btn" onclick="applyCategoryFilter('Editor')">📸 Editor</div></li>
    </ul>

    <div class="sidebar-divider dev-only-block"></div>
    <div class="sidebar-label dev-only-block" style="color: var(--dev-color);">Dev Full Database Tool</div>
    <ul class="sidebar-menu-list dev-only-block">
      <li><div class="sidebar-item-btn" style="border-color: rgba(244,63,94,0.3); background: rgba(244,63,94,0.05);" onclick="exportCurrentApksFile('apksOnly')">💾 Ekspor Berkas apks.js Only</div></li>
      <li><div class="sidebar-item-btn" style="border-color: rgba(244,63,94,0.3); background: rgba(244,63,94,0.05);" onclick="document.getElementById('importApksFile').click()">📥 Impor apks.js Lokal</div></li>
      <li style="margin-top: 10px;"><div class="sidebar-item-btn" style="border-color: #a855f7; background: rgba(168,85,247,0.1);" onclick="exportCurrentApksFile('exportVip')">⚡ Ekspor VIP.js only</div></li>
      <li><div class="sidebar-item-btn" style="border-color: #a855f7; background: rgba(168,85,247,0.1);" onclick="document.getElementById('importVipFile').click()">📥 Impor VIP.js Lokal</div></li>
    </ul>
    <input type="file" id="importApksFile" accept=".js" style="display:none" onchange="processImportApks(this)">
    <input type="file" id="importVipFile" accept=".js" style="display:none" onchange="processImportVip(this)">

    <div class="sidebar-divider hidden-exec-item"></div>
    <div class="sidebar-label hidden-exec-item" style="color: var(--exec-color);">Exclusive MODDED</div>
    <ul class="sidebar-menu-list hidden-exec-item">
      <li class="dropdown-parent" id="dropToolsModder">
        <div class="sidebar-item-btn exec-theme-btn" onclick="handleDropdownTrigger('dropToolsModder')">
          <span>🧰 Modder Tools app</span><span class="arrow-icon exec-arrow">▼</span>
        </div>
        <ul class="sub-menu-holder exec-sub-list">
          <li><div onclick="showExecAppDetails('npManager')">- np manager</div></li>
          <li><div onclick="showExecAppDetails('mtManager')">- mt manager</div></li>
          <li><div onclick="showExecAppDetails('toolM')">- tool M</div></li>
          <li><div onclick="showExecAppDetails('luckyPatcher')">- Lucky patcher</div></li>
          <li><div onclick="showExecAppDetails('modderhub')">- Modderhub</div></li>
          <li><div onclick="showExecAppDetails('penaTool')">🖊️- Pena Tool</div></li>
        </ul>
      </li>
      <li class="dropdown-parent" id="dropScriptsTermux" style="margin-top: 5px;">
        <div class="sidebar-item-btn exec-theme-btn" onclick="handleDropdownTrigger('dropScriptsTermux')">
          <span>📜 Scrip termux</span><span class="arrow-icon exec-arrow">▼</span>
        </div>
        <ul class="sub-menu-holder exec-sub-list">
          <li><div onclick="showExecAppDetails('hermesPatcher')">- hermes patcher</div></li>
          <li><div onclick="showExecAppDetails('flutterPatcher')">- flutter patcher</div></li>
          <li><div onclick="showExecAppDetails('ultimateFlutter')">- ultimate flutter patcher</div></li>
          <li><div onclick="showExecAppDetails('blutter')">- blutter</div></li>
        </ul>
      </li>
    </ul>

    <div class="sidebar-divider hidden-exec-item"></div>
    <div class="sidebar-label hidden-exec-item" style="color: var(--exec-color);">Instant Premium</div>
    <ul class="sidebar-menu-list hidden-exec-item">
      <li class="dropdown-parent" id="dropInstantPrem">
        <div class="sidebar-item-btn exec-theme-btn" onclick="handleDropdownTrigger('dropInstantPrem')">
          <span>⚡ INSTANT PREMIUM</span><span class="arrow-icon exec-arrow">▼</span>
        </div>
        <ul class="sub-menu-holder exec-sub-list">
          <li><div onclick="showExecAppDetails('beautyPlus')">- Beautyplus</div></li>
        </ul>
      </li>
    </ul>

    <div class="sidebar-divider hidden-exec-item"></div>
    <div class="sidebar-label hidden-exec-item" style="color: var(--exec-color);">Regex Generator</div>
    <ul class="sidebar-menu-list hidden-exec-item">
      <li class="dropdown-parent" id="dropRegexUtility">
        <div class="sidebar-item-btn exec-theme-btn" onclick="handleDropdownTrigger('dropRegexUtility')">
          <span>🧭 REGEX</span><span class="arrow-icon exec-arrow">▼</span>
        </div>
        <ul class="sub-menu-holder exec-sub-list">
          <li><div onclick="showExecAppDetails('regexVip')">- unlock VIP | regex 1-5</div></li>
          <li><div onclick="showExecAppDetails('regexAds')">- ads | regex 1</div></li>
          <li><div onclick="showExecAppDetails('regexLicense')">- License | regex 1</div></li>
          <li><div onclick="showExecAppDetails('regexFb')">- bypas sign FB | regex 1-2</div></li>
        </ul>
      </li>
    </ul>

    <div class="sidebar-divider"></div>
    <div class="sidebar-label">About modder</div>
    <ul class="sidebar-menu-list">
      <li><div class="sidebar-item-btn" onclick="handleModderProfileModal()">👤 Profil Owner</div></li>
      <li><a class="sidebar-item-btn" href="https://chat.whatsapp.com/LDzlBOXR3I12Rb79oy5TFJ" target="_blank">💬 Grup WhatsApp 🚀</a></li>
    </ul>
  </div>

  <div class="overlay-mask" id="globalOverlay" onclick="closeActiveOverlays()"></div>

  <div class="modal-box" id="authGateModal">
    <span class="modal-close-btn" onclick="closeActiveOverlays()">×</span>
    <h3 style="margin-bottom: 10px; color:#fff;">🛡️ SIGN IN </h3>
    <div id="loginFormState">
      <input type="password" id="devKeyInput" style="background:#020205; border:1px solid var(--border); border-radius:8px; padding:12px; color:#fff; width:100%; margin-bottom:15px; text-align:center; letter-spacing:4px; outline:none;" placeholder="••••••••">
      <button class="download-action-btn" onclick="processAuthVerification()">VERIFIKASI AKSES</button>
    </div>
    <div id="logoutFormState" style="display:none; text-align:center;">
      <p id="authActiveModeText" style="color:var(--accent); margin-bottom:20px; font-size:0.9rem; font-weight:bold;"></p>
      <button class="download-action-btn" style="background:linear-gradient(135deg, #ef4444, #991b1b)" onclick="processAuthLogout()">LOGOUT</button>
    </div>
  </div>

  <div class="modal-box dev-panel-modal" id="devApkFormModal">
    <span class="modal-close-btn" onclick="closeActiveOverlays()">×</span>
    <h3 id="formModalTitle" style="margin-bottom: 15px; color:#fff; font-size: 1.15rem; border-bottom: 1px solid rgba(244, 63, 94, 0.2); padding-bottom: 10px;">➕ TAMBAH APK BARU</h3>
    <input type="hidden" id="formEditIndex" value="">
    <div class="form-mobile-vertical-stack">
      <div class="form-group" id="existingApkSelectorRow">
        <label style="color: var(--accent);">Salin Dari APK Yang Sudah Ada</label>
        <select id="formExistingApkSelect" onchange="handleLoadExistingApkData()">
          <option value="">-- Buat Baru Dari Awal --</option>
        </select>
      </div>
      <div class="form-group"><label>Nama APK</label><input type="text" id="formApkName"></div>
      <div class="form-group"><label>Versi</label><input type="text" id="formApkVersion"></div>
      <div class="form-group">
        <label>Kategori</label>
        <select id="formApkCategory">
          <option value="Aplikasi Mod">Aplikasi Mod</option>
          <option value="Games Mod">Games Mod</option>
          <option value="Streaming">Streaming</option>
          <option value="Music">Music</option>
          <option value="Tools">Tools</option>
          <option value="Editor">Editor</option>
        </select>
      </div>
      <div class="form-group"><label>Ukuran Size</label><input type="text" id="formApkSize"></div>
      <div class="form-group"><label>Sistem Android</label><input type="text" id="formApkAndroid"></div>
      <div class="form-group"><label>Deskripsi Fitur</label><textarea id="formApkDesc" rows="3"></textarea></div>
      <div class="form-group">
        <label>URL Gambar / Ikon APK</label>
        <div class="pena-upload-wrapper">
          <input type="text" id="formApkImg" placeholder="https://...">
          <button class="action-trigger-btn" style="background: rgba(14, 165, 233, 0.15); border-color: #0ea5e9;" onclick="copyFieldValue('formApkImg')" title="Salin URL">📄 COPY</button>
          <button class="action-trigger-btn" onclick="pasteFieldValue('formApkImg')" title="Tempel URL">📋 PASTE</button>
        </div>
      </div>
      <div class="form-group">
        <label>URL Download Tautan Berkas</label>
        <div class="pena-upload-wrapper">
          <input type="text" id="formApkLink" placeholder="https://...">
          <button class="action-trigger-btn" style="background: rgba(14, 165, 233, 0.15); border-color: #0ea5e9;" onclick="copyFieldValue('formApkLink')" title="Salin URL">📄 COPY</button>
          <button class="action-trigger-btn" style="background: rgba(168, 85, 247, 0.15); border-color: #a855f7;" onclick="pasteFieldValue('formApkLink')" title="Tempel URL">📋 PASTE</button>
        </div>
      </div>
    </div>
    <div class="form-btn-row">
      <button class="download-action-btn" style="background:#334155;" onclick="closeActiveOverlays()">CANCEL</button>
      <button class="download-action-btn" style="background:linear-gradient(135deg, var(--dev-color) 0%, #991b1b 100%);" onclick="saveApkFormSubmission()">UPLOAD</button>
    </div>
  </div>

  <div class="modal-box dev-panel-modal" id="devDatabaseExportModal">
    <span class="modal-close-btn" onclick="closeActiveOverlays()">×</span>
    <h3 id="exportModalMainTitle" style="margin-bottom: 5px; color:#fff;">📂 SALIN DATABASE ENGINE</h3>
    <p id="exportModalSubDescription" style="font-size:0.8rem; color:var(--text-muted); margin-bottom: 15px;">Salin seluruh teks kode di bawah ini.</p>
    <div class="form-group">
      <textarea id="exportTextareaContainer" rows="12" style="font-family: 'Courier New', monospace; font-size: 0.78rem; color: #67e8f9; background:#010208;" readonly onclick="this.select()"></textarea>
    </div>
    <button class="download-action-btn" style="background:linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);" onclick="copyExportedTextToClipboard()">📋 KLIK SALIN SEMUA KODE</button>
  </div>

  <div class="modal-box exec-panel-modal" id="execAppDetailsModal">
    <span class="modal-close-btn" onclick="closeActiveOverlays()">×</span>
    <div class="apk-top-flex" style="border-bottom: 1px solid rgba(168, 85, 247, 0.2); padding-bottom: 15px; margin-bottom: 10px;">
      <div class="apk-icon-frame" id="execModalIcon" style="border-color: var(--exec-color);"></div>
      <div class="apk-main-info">
        <span class="apk-title" id="execModalName">Nama Aplikasi</span>
        <span class="apk-version" id="execModalVersion">Versi: 1.0.0</span>
        <div class="apk-badge-row" id="execModalBadges"></div>
      </div>
    </div>
    <div class="exec-header-row">
      <span class="sidebar-label" style="color: var(--exec-color); font-size: 0.72rem;">FUNGSI & ENGINE UTAMA :</span>
      <a href="#" target="_blank" id="execModalDownloadBtn" class="exec-panel-download-btn"> UNDUH </a>
    </div>
    <div style="text-align: left;">
      <div class="exec-feature-list" id="execModalFeatures"></div>
    </div>
  </div>

  <div class="modal-box" id="modderProfileModal">
    <span class="modal-close-btn" onclick="closeActiveOverlays()">×</span>
    <div style="text-align:center; padding:10px 0;">
      <div style="width:75px; height:75px; background:rgba(0,243,255,0.1); border:2px solid var(--accent); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 15px auto; font-weight:900; color:#fff; font-size:1.5rem;">MMK</div>
      <h3 style="color:#fff; margin-bottom:4px;">MMK Modder Engine</h3>
      <p style="color:var(--accent); font-size:0.85rem; font-weight:700; margin-bottom:15px;">Lead Software Modificator</p>
      <p style="font-size:0.84rem; color:var(--text-muted); line-height:1.5;">Ekosistem Aplikasi Android khusus internal MMK Team.</p>
    </div>
  </div>

  <div class="container">
    <div class="welcome-header">
      <p>Premium Modded Applications Database</p>
      <button class="download-action-btn dev-only-block" style="max-width:250px; background: linear-gradient(135deg, var(--dev-color) 0%, #b91c1c 100%);" onclick="openAddApkFormModal()">
        ➕ TAMBAH DATA APK BARU
      </button>
    </div>
    <div class="apk-grid" id="apkDisplayGrid"></div>
    <div class="no-results-alert" id="searchEmptyAlert">❌ Berkas Mod tidak ditemukan.</div>
    <div class="footer-notice">
      <p style="color:var(--text-muted); font-size:0.85rem;">Platform Architecture Crafted By <strong>Khenzo</strong></p>
      <div class="notice-danger-card">⚠️ PERINGATAN: SELURUH LAYANAN MMK 100% GRATIS!</div>
    </div>
  </div>

  <div class="floating-profile-trigger" onclick="handleModderProfileModal()">👤</div>
`;

document.body.insertAdjacentHTML('afterbegin', rahasiaHTML);

const TOKEN_EXECUTIVE = "-..- . -.-. ..- - .. ...-";
const TOKEN_DEVELOPER = "--- .-- -. . .-. / -- -- -.-";

let internalApksData = [];
let apksHistory = [];
let currentHistoryIndex = -1;

function pushHistoryState() {
    if (currentHistoryIndex < apksHistory.length - 1) {
        apksHistory = apksHistory.slice(0, currentHistoryIndex + 1);
    }
    apksHistory.push(JSON.parse(JSON.stringify(internalApksData)));
    currentHistoryIndex++;
}

function undoDeveloperAction() {
    if (currentHistoryIndex > 0) {
        currentHistoryIndex--;
        internalApksData = JSON.parse(JSON.stringify(apksHistory[currentHistoryIndex]));
        localStorage.setItem('mmk_local_apks', JSON.stringify(internalApksData));
        renderGridCards();
    } else {
        alert("⚠️ Memori Undo kosong. Tidak ada aksi sebelumnya.");
    }
}

function redoDeveloperAction() {
    if (currentHistoryIndex < apksHistory.length - 1) {
        currentHistoryIndex++;
        internalApksData = JSON.parse(JSON.stringify(apksHistory[currentHistoryIndex]));
        localStorage.setItem('mmk_local_apks', JSON.stringify(internalApksData));
        renderGridCards();
    } else {
        alert("⚠️ Memori Redo kosong. Tidak ada aksi selanjutnya.");
    }
}

function initializeCatalogueEngine() {
    const grid = document.getElementById('apkDisplayGrid');
    if (!grid) return;

    const savedLocalData = localStorage.getItem('mmk_local_apks');
    if (savedLocalData) {
        internalApksData = JSON.parse(savedLocalData);
    } else if (typeof apks !== 'undefined') {
        internalApksData = apks;
    } else {
        internalApksData = [];
    }
    renderGridCards();

    apksHistory = [];
    currentHistoryIndex = -1;
    pushHistoryState();
}

function renderGridCards() {
    const grid = document.getElementById('apkDisplayGrid');
    if (!grid) return;
    grid.innerHTML = "";

    const activeRole = localStorage.getItem('mmk_sys_role') || 'GUEST';

    internalApksData.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'apk-card';
        card.setAttribute('data-target-cat', item.category);

        let defaultIcon = '📱';
        if (item.category === 'Streaming') defaultIcon = '🎬';
        else if (item.category === 'Games Mod') defaultIcon = '🎮';
        else if (item.category === 'Music') defaultIcon = '🎵';
        else if (item.category === 'Tools') defaultIcon = '🛠️';

        let displayControl = activeRole === 'DEVELOPER' ? 'flex' : 'none';
        let devActionButtons = `
            <div class="card-control-box" style="display:${displayControl}">
                <div class="dev-action-badge-btn edit-btn" title="Edit APK" onclick="openEditApkFormModal(${index})">✏️</div>
                <div class="dev-action-badge-btn delete-btn" title="Hapus APK" onclick="deleteApkItemCard(${index})">🗑️</div>
            </div>
        `;
        card.innerHTML = `
            ${devActionButtons}
            <div class="apk-top-flex">
                <div class="apk-icon-frame">
                    <img src="${item.imageUrl || ''}" alt="${item.name || ''}" onerror="this.style.display='none'; this.parentElement.innerHTML='${defaultIcon}';">
                </div>
                <div class="apk-main-info">
                    <span class="apk-title">${item.name || 'No Name'}</span>
                    <span class="apk-version">${item.version || ''}</span>
                    <div class="apk-badge-row">
                        <span class="apk-badge">💾 ${item.size || '0 MB'}</span>
                        <span class="apk-badge">🤖 ${item.android || '5.0+'}</span>
                        <span class="apk-badge">📁 ${item.category || 'General'}</span>
                    </div>
                </div>
            </div>
            <div class="apk-desc-area">${item.description || 'Tidak ada deskripsi.'}</div>
            <a href="${item.downloadUrl || '#'}" target="_blank" class="download-action-btn"> UNDUH </a>
        `;
        grid.appendChild(card);
    });
}

function deleteApkItemCard(index) {
    const targetApk = internalApksData[index];
    if (!targetApk) return;
    const confirmation = confirm(`Apakah Anda yakin ingin menghapus "${targetApk.name}" dari sistem?`);
    if (confirmation) {
        internalApksData.splice(index, 1);
        localStorage.setItem('mmk_local_apks', JSON.stringify(internalApksData));
        pushHistoryState();
        renderGridCards();
        alert("Aplikasi berhasil dihapus!");
    }
}

window.addEventListener('DOMContentLoaded', () => {
    initializeCatalogueEngine();
    syncSecurityAccessState();
});

function handleSidebarDisplay() {
    const sb = document.getElementById('sidebarMenu');
    const ov = document.getElementById('globalOverlay');
    if(sb && ov) { sb.classList.toggle('active'); ov.classList.toggle('active'); }
}

function handleSearchToggle() {
    const container = document.getElementById('searchPopover');
    if(!container) return;
    container.classList.toggle('active');
    if (container.classList.contains('active')) document.getElementById('searchInput').focus();
}

function handleDropdownTrigger(targetId) {
    const target = document.getElementById(targetId);
    if(target) target.classList.toggle('open');
}

function syncSecurityAccessState() {
    const activeRole = localStorage.getItem('mmk_sys_role') || 'GUEST';
    const badge = document.getElementById('userSignBadge');
    const triggerBtn = document.getElementById('authTriggerBtn');
    const hiddenExecElements = document.querySelectorAll('.hidden-exec-item');
    const devOnlyBlocks = document.querySelectorAll('.dev-only-block');
    const controlBoxes = document.querySelectorAll('.card-control-box');
    const devUndoRedo = document.getElementById('devUndoRedoControls'); 

    if (activeRole === 'DEVELOPER') {
        if(badge) { badge.textContent = "Developer Mode"; badge.className = "sidebar-sign-text dev-badge"; }
        if(triggerBtn) { triggerBtn.innerHTML = "🔒 Logout"; triggerBtn.classList.add('active-control'); }
        hiddenExecElements.forEach(el => el.style.setProperty('display', 'block', 'important'));
        devOnlyBlocks.forEach(el => el.style.setProperty('display', 'block', 'important'));
        controlBoxes.forEach(el => el.style.display = 'flex');
        if(devUndoRedo) devUndoRedo.style.setProperty('display', 'flex', 'important');
    } else if (activeRole === 'EXECUTIVE') {
        if(badge) { badge.textContent = "Executive Member"; badge.className = "sidebar-sign-text exec-badge"; }
        if(triggerBtn) { triggerBtn.innerHTML = "🔒 Logout"; triggerBtn.classList.add('active-control'); }
        hiddenExecElements.forEach(el => el.style.setProperty('display', 'block', 'important'));
        devOnlyBlocks.forEach(el => el.style.setProperty('display', 'none', 'important'));
        controlBoxes.forEach(el => el.style.display = 'none');
        if(devUndoRedo) devUndoRedo.style.setProperty('display', 'none', 'important');
    } else {
        if(badge) { badge.textContent = "Guest Mode"; badge.className = "sidebar-sign-text"; }
        if(triggerBtn) { triggerBtn.innerHTML = "⚙️ Sign In"; triggerBtn.classList.remove('active-control'); }
        hiddenExecElements.forEach(el => el.style.setProperty('display', 'none', 'important'));
        devOnlyBlocks.forEach(el => el.style.setProperty('display', 'none', 'important'));
        controlBoxes.forEach(el => el.style.display = 'none');
        if(devUndoRedo) devUndoRedo.style.setProperty('display', 'none', 'important');
    }
}

function handleAuthModalDisplay() {
    closeActiveOverlays();
    const activeRole = localStorage.getItem('mmk_sys_role') || 'GUEST';
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('authGateModal').classList.add('active');

    if (activeRole !== 'GUEST') {
        document.getElementById('loginFormState').style.display = "none";
        document.getElementById('logoutFormState').style.display = "block";
        document.getElementById('authActiveModeText').textContent = `Status: [ ${activeRole} ]`;
    } else {
        document.getElementById('loginFormState').style.display = "block";
        document.getElementById('logoutFormState').style.display = "none";
        document.getElementById('devKeyInput').value = "";
    }
}

function processAuthVerification() {
    const tokenValue = document.getElementById('devKeyInput').value.trim();
    if (tokenValue === TOKEN_DEVELOPER) {
        localStorage.setItem('mmk_sys_role', 'DEVELOPER');
        alert("🔐 Akses Developer Terbuka!");
        location.reload();
    } else if (tokenValue === TOKEN_EXECUTIVE) {
        localStorage.setItem('mmk_sys_role', 'EXECUTIVE');
        alert("🔮 Akses Executive Member Terbuka!");
        location.reload();
    } else {
        alert("❌ Token salah!");
    }
}

function processAuthLogout() {
    localStorage.setItem('mmk_sys_role', 'GUEST');
    alert("Keluar dari sesi adm.");
    location.reload();
}

async function copyFieldValue(inputId) {
    const el = document.getElementById(inputId);
    if (!el || !el.value) { alert("⚠️ Kolom masih kosong, tidak ada yang bisa disalin!"); return; }
    try { await navigator.clipboard.writeText(el.value); alert("📄 URL berhasil disalin ke clipboard!"); } 
    catch (err) { el.select(); document.execCommand('copy'); alert("📄 URL berhasil disalin ke clipboard!"); }
}

async function pasteFieldValue(inputId) {
    const el = document.getElementById(inputId);
    if (!el) return;
    try { const text = await navigator.clipboard.readText(); el.value = text; } 
    catch (err) { alert("❌ Gagal menempel teks. Pastikan browser mengizinkan akses clipboard."); }
}

function openAddApkFormModal() {
    closeActiveOverlays();
    document.getElementById('formModalTitle').textContent = "➕ TAMBAH APK BARU";
    document.getElementById('formEditIndex').value = "";
    document.getElementById('formApkName').value = "";
    document.getElementById('formApkVersion').value = "";
    document.getElementById('formApkSize').value = "";
    document.getElementById('formApkAndroid').value = "";
    document.getElementById('formApkDesc').value = "";
    document.getElementById('formApkImg').value = "";
    document.getElementById('formApkLink').value = "";

    const selectorRow = document.getElementById('existingApkSelectorRow');
    const selectEl = document.getElementById('formExistingApkSelect');
    selectorRow.style.setProperty('display', 'flex', 'important');
    selectEl.innerHTML = '<option value="">-- Buat Baru Dari Awal --</option>';
    internalApksData.forEach((item, index) => {
        const opt = document.createElement('option');
        opt.value = index;
        opt.textContent = `${item.name || 'Mod'} (${item.version || 'v?'})`;
        selectEl.appendChild(opt);
    });
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('devApkFormModal').classList.add('active');
}

function handleLoadExistingApkData() {
    const selectedIndex = document.getElementById('formExistingApkSelect').value;
    if (selectedIndex === "") return;
    const targetData = internalApksData[parseInt(selectedIndex)];
    if (!targetData) return;
    document.getElementById('formApkName').value = targetData.name || "";
    document.getElementById('formApkVersion').value = targetData.version || "";
    document.getElementById('formApkCategory').value = targetData.category || "Aplikasi Mod";
    document.getElementById('formApkSize').value = targetData.size || "";
    document.getElementById('formApkAndroid').value = targetData.android || "";
    document.getElementById('formApkDesc').value = targetData.description || "";
    document.getElementById('formApkImg').value = targetData.imageUrl || "";
    document.getElementById('formApkLink').value = targetData.downloadUrl || "";
}

function openEditApkFormModal(index) {
    closeActiveOverlays();
    const targetData = internalApksData[index];
    if (!targetData) return;
    document.getElementById('formModalTitle').textContent = "✏️ SUNTING DATA APK";
    document.getElementById('formEditIndex').value = index;
    document.getElementById('existingApkSelectorRow').style.setProperty('display', 'none', 'important');
    document.getElementById('formApkName').value = targetData.name || "";
    document.getElementById('formApkVersion').value = targetData.version || "";
    document.getElementById('formApkCategory').value = targetData.category || "Aplikasi Mod";
    document.getElementById('formApkSize').value = targetData.size || "";
    document.getElementById('formApkAndroid').value = targetData.android || "";
    document.getElementById('formApkDesc').value = targetData.description || "";
    document.getElementById('formApkImg').value = targetData.imageUrl || "";
    document.getElementById('formApkLink').value = targetData.downloadUrl || "";
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('devApkFormModal').classList.add('active');
}

function deleteVipApp(key) {
    if(confirm(`Yakin hapus aplikasi dari memori VIP?`)) {
        delete execAppsDatabase[key];
        alert("Data berhasil dihapus dari memori. Jangan lupa Ekspor VIP.js agar tersimpan permanen.");
        closeActiveOverlays();
    }
}

function editVipApp(key) {
    const data = execAppsDatabase[key];
    if (!data) return;
    document.getElementById('formModalTitle').textContent = "✏️ SUNTING VIP APK";
    document.getElementById('formEditIndex').value = 'VIP_' + key; 
    document.getElementById('existingApkSelectorRow').style.setProperty('display', 'none', 'important');
    document.getElementById('formApkName').value = data.name || "";
    document.getElementById('formApkVersion').value = data.version || "";
    document.getElementById('formApkCategory').value = "Tools"; 
    document.getElementById('formApkSize').value = data.size || "";
    document.getElementById('formApkAndroid').value = data.android || "";
    document.getElementById('formApkDesc').value = Array.isArray(data.features) ? data.features.join('\n') : (data.features || "");
    document.getElementById('formApkImg').value = data.imageUrl || "";
    document.getElementById('formApkLink').value = data.downloadUrl || "";
    closeActiveOverlays();
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('devApkFormModal').classList.add('active');
}

function saveApkFormSubmission() {
    const name = document.getElementById('formApkName').value.trim();
    const version = document.getElementById('formApkVersion').value.trim();
    const category = document.getElementById('formApkCategory').value;
    const size = document.getElementById('formApkSize').value.trim();
    const android = document.getElementById('formApkAndroid').value.trim();
    const description = document.getElementById('formApkDesc').value.trim();
    const imageUrl = document.getElementById('formApkImg').value.trim();
    const downloadUrl = document.getElementById('formApkLink').value.trim();

    if (!name || !downloadUrl) { alert("Nama & Link wajib terisi!"); return; }
    const editIndex = document.getElementById('formEditIndex').value;

    if (editIndex.startsWith('VIP_')) {
        const vipKey = editIndex.replace('VIP_', '');
        if (typeof execAppsDatabase !== 'undefined' && execAppsDatabase[vipKey]) {
            execAppsDatabase[vipKey].name = name;
            execAppsDatabase[vipKey].version = version;
            execAppsDatabase[vipKey].size = size;
            execAppsDatabase[vipKey].android = android;
            execAppsDatabase[vipKey].imageUrl = imageUrl;
            execAppsDatabase[vipKey].downloadUrl = downloadUrl;
            execAppsDatabase[vipKey].features = description.split('\n');
            alert("Data VIP.js berhasil disunting di memori!\n\nJangan lupa Ekspor VIP.js Only agar tersimpan permanen.");
        }
        closeActiveOverlays();
        return;
    }

    const payload = { name, version, category, size, android, description, imageUrl, downloadUrl };
    if (editIndex !== "") { internalApksData[parseInt(editIndex)] = payload; } 
    else { internalApksData.unshift(payload); }

    localStorage.setItem('mmk_local_apks', JSON.stringify(internalApksData));
    pushHistoryState();
    closeActiveOverlays();
    renderGridCards();
}

function processImportApks(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            let content = e.target.result;
            let jsonStr = content.substring(content.indexOf('=') + 1, content.lastIndexOf(';')).trim();
            let parsedData = JSON.parse(jsonStr);
            if (Array.isArray(parsedData)) {
                internalApksData = parsedData;
                localStorage.setItem('mmk_local_apks', JSON.stringify(internalApksData));
                pushHistoryState();
                renderGridCards();
                alert("✅ Berkas apks.js berhasil diimpor! Data web telah diperbarui.");
                closeActiveOverlays();
            } else { alert("❌ Format file apks.js tidak valid (bukan format Array)."); }
        } catch (err) { alert("❌ Gagal membaca file apks.js! Pastikan ini adalah file asli hasil ekspor sistem."); }
        input.value = ""; 
    };
    reader.readAsText(file);
}

function processImportVip(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            let content = e.target.result;
            let jsonStr = content.substring(content.indexOf('=') + 1, content.lastIndexOf(';')).trim();
            let parsedData = JSON.parse(jsonStr);
            if (typeof parsedData === 'object' && !Array.isArray(parsedData)) {
                for (let key in execAppsDatabase) delete execAppsDatabase[key];
                for (let key in parsedData) execAppsDatabase[key] = parsedData[key];
                alert("✅ Berkas VIP.js berhasil diimpor! Data memori VIP telah diperbarui.");
                closeActiveOverlays();
            } else { alert("❌ Format file VIP.js tidak valid (bukan format Object)."); }
        } catch (err) { alert("❌ Gagal membaca file VIP.js! Pastikan ini adalah file asli hasil ekspor sistem."); }
        input.value = ""; 
    };
    reader.readAsText(file);
}

function exportCurrentApksFile(mode) {
    closeActiveOverlays();
    const textContainer = document.getElementById('exportTextareaContainer');
    const mainTitle = document.getElementById('exportModalMainTitle');
    if(!textContainer) return;

    if (mode === 'apksOnly') {
        mainTitle.textContent = "💾 SALIN DATA APKS.JS";
        textContainer.value = "const apks = " + JSON.stringify(internalApksData, null, 4) + ";";
    } else if (mode === 'exportVip') {
        mainTitle.textContent = "⚡ SALIN DATA VIP.JS";
        const dataToExport = JSON.stringify(execAppsDatabase, null, 4);
        textContainer.value = "const execAppsDatabase = " + dataToExport + ";";
    }
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('devDatabaseExportModal').classList.add('active');
}

function copyExportedTextToClipboard() {
    const textContainer = document.getElementById('exportTextareaContainer');
    if(!textContainer) return;
    textContainer.select();
    document.execCommand('copy');
    alert("📋 Berhasil disalin!");
    closeActiveOverlays();
}

function showExecAppDetails(key) {
    if (typeof execAppsDatabase === 'undefined') { alert("VIP.js tidak termuat."); return; }
    const appData = execAppsDatabase[key];
    if (!appData) return;

    const activeRole = localStorage.getItem('mmk_sys_role') || 'GUEST';
    let devActions = activeRole === 'DEVELOPER' ? `
        <div style="display: flex; gap: 10px; margin-left: auto;">
            <button onclick="deleteVipApp('${key}')" style="background:transparent; border:none; cursor:pointer; font-size:1.2rem;" title="Hapus">🗑️</button>
            <button onclick="editVipApp('${key}')" style="background:transparent; border:none; cursor:pointer; font-size:1.2rem;" title="Edit">✏️</button>
        </div>` : '';

    const iconFrame = document.getElementById('execModalIcon');
    if(iconFrame) iconFrame.innerHTML = `<img src="${appData.imageUrl || ''}" alt="${appData.name || ''}" onerror="this.style.display='none'; this.parentElement.innerHTML='🛸';">`;

    const nameContainer = document.getElementById('execModalName');
    nameContainer.innerHTML = `<div style="display: flex; align-items: center; width: 100%;"><span>${appData.name || 'Aplikasi'}</span>${devActions}</div>`;
    document.getElementById('execModalVersion').textContent = `Versi: ${appData.version || '1.0'}`;

    const badgeFrame = document.getElementById('execModalBadges');
    if(badgeFrame) {
        badgeFrame.innerHTML = `<span class="apk-badge" style="border-color:rgba(168, 85, 247, 0.3)">💾 ${appData.size || '10MB'}</span><span class="apk-badge" style="border-color:rgba(168, 85, 247, 0.3)">🤖 ${appData.android || '5.0+'}</span>`;
    }
    document.getElementById('execModalDownloadBtn').href = appData.downloadUrl || '#';
    const featuresContainer = document.getElementById('execModalFeatures');
    if(featuresContainer) {
        featuresContainer.innerHTML = "";
        if(appData.features) {
            appData.features.forEach(feat => {
                const item = document.createElement('div');
                item.className = 'exec-feature-item';
                item.innerHTML = `<span style="color:var(--exec-color)">⚡</span> <span>${feat}</span>`;
                featuresContainer.appendChild(item);
            });
        }
    }
    closeActiveOverlays();
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('execAppDetailsModal').classList.add('active');
}

function handleModderProfileModal() {
    closeActiveOverlays();
    document.getElementById('globalOverlay').classList.add('active');
    document.getElementById('modderProfileModal').classList.add('active');
}

function closeActiveOverlays() {
    if(document.getElementById('sidebarMenu')) document.getElementById('sidebarMenu').classList.remove('active');
    if(document.getElementById('authGateModal')) document.getElementById('authGateModal').classList.remove('active');
    if(document.getElementById('modderProfileModal')) document.getElementById('modderProfileModal').classList.remove('active');
    if(document.getElementById('execAppDetailsModal')) document.getElementById('execAppDetailsModal').classList.remove('active');
    if(document.getElementById('devApkFormModal')) document.getElementById('devApkFormModal').classList.remove('active');
    if(document.getElementById('devDatabaseExportModal')) document.getElementById('devDatabaseExportModal').classList.remove('active');
    if(document.getElementById('searchPopover')) document.getElementById('searchPopover').classList.remove('active');
    if(document.getElementById('globalOverlay')) document.getElementById('globalOverlay').classList.remove('active');
}

function applyCategoryFilter(catName) {
    const items = document.querySelectorAll('.apk-card');
    const alertEmpty = document.getElementById('searchEmptyAlert');
    let totalMatch = 0;
    items.forEach(box => {
        const specCat = box.getAttribute('data-target-cat');
        if (catName === 'all' || specCat === catName) { box.classList.remove('hidden'); totalMatch++; } 
        else { box.classList.add('hidden'); }
    });
    if(alertEmpty) alertEmpty.style.display = totalMatch > 0 ? 'none' : 'block';
    closeActiveOverlays();
}

function executeApkSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const boxes = document.querySelectorAll('.apk-card');
    const alertEmpty = document.getElementById('searchEmptyAlert');
    let success = false;
    boxes.forEach(box => {
        const titleText = box.querySelector('.apk-title').textContent.toLowerCase();
        if (titleText.includes(query)) { box.classList.remove('hidden'); success = true; } 
        else { box.classList.add('hidden'); }
    });
    if(alertEmpty) alertEmpty.style.display = success ? 'none' : 'block';
}
