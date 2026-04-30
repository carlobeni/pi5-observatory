document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const sidebar = document.querySelector('.sidebar');
    const btnHamburger = document.getElementById('btn-hamburger');
    const navButtons = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view');
    const viewTitle = document.getElementById('view-title');
    
    const statusCameraCombined = document.getElementById('status-camera-combined');
    const statusInternet = document.getElementById('status-internet');
    
    const metricTemp = document.getElementById('metric-temp');
    const metricFps = document.getElementById('metric-fps');
    const videoResolution = document.getElementById('video-resolution');
    const videoStream = document.getElementById('video-stream');
    const streamUrlText = document.getElementById('stream-url-text');
    
    const rangeExposure = document.getElementById('range-exposure');
    const valExposure = document.getElementById('val-exposure');
    const rangeGain = document.getElementById('range-gain');
    const valGain = document.getElementById('val-gain');
    
    const selectResolution = document.getElementById('select-resolution');
    const btnFullscreen = document.getElementById('btn-fullscreen');
    const btnCameraToggle = document.getElementById('btn-camera-toggle');
    const mainVideoContainer = document.getElementById('main-video-container');
    
    const wifiList = document.getElementById('wifi-list');
    const wifiLoaderPanel = document.getElementById('wifi-loader-panel');
    const connectedNetSection = document.getElementById('connected-network-section');
    
    const wifiPassModal = document.getElementById('wifi-pass-modal');
    const wifiNetPass = document.getElementById('wifi-net-pass');
    const btnWifiConfirm = document.getElementById('btn-wifi-confirm');
    const btnWifiCancel = document.getElementById('btn-wifi-cancel');
    const wifiPassDesc = document.getElementById('wifi-pass-desc');

    const hsSsid = document.getElementById('hs-ssid');
    const hsPass = document.getElementById('hs-pass');
    const toggleHsPass = document.getElementById('toggle-hs-pass');
    
    const loadingOverlay = document.getElementById('loading-overlay');
    const loaderText = document.getElementById('loader-text');
    const btnSaveHs = document.getElementById('btn-save-hs');
    
    const authModal = document.getElementById('auth-modal');
    const adminPass = document.getElementById('admin-pass');
    const btnAuthCancel = document.getElementById('btn-auth-cancel');
    const btnAuthConfirm = document.getElementById('btn-auth-confirm');
    const authModalDesc = document.getElementById('auth-modal-desc');
    const networkWarning = document.getElementById('network-warning');
    const authError = document.getElementById('auth-error');
    let authMode = 'save';

    let currentCameraState = {
        max_width: 0,
        max_height: 0,
        is_capturing: false,
        connected: false
    };

    let connectedSsid = null;
    let initialPropertiesLoaded = false;

    // Helpers
    function debounce(func, timeout = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }

    function showLoading(text = 'Procesando...') {
        loaderText.textContent = text;
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    function setBtnLoading(btn, isLoading, originalText) {
        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = `<i class="fas fa-circle-notch spin"></i> Procesando...`;
        } else {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // Hamburger Menu Logic
    btnHamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('open');
        btnHamburger.innerHTML = sidebar.classList.contains('open') ? '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
    });

    document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== btnHamburger) {
            sidebar.classList.remove('open');
            btnHamburger.innerHTML = '<i class="fas fa-bars"></i>';
        }
    });

    // Navigation
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            navButtons.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(target).classList.add('active');
            viewTitle.textContent = btn.innerText.trim();
            if (window.innerWidth <= 1024) {
                sidebar.classList.remove('open');
                btnHamburger.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    });

    // Camera Toggle
    btnCameraToggle.addEventListener('click', async (e) => {
        e.preventDefault();
        const newState = !currentCameraState.is_capturing;
        showLoading(newState ? 'Encendiendo sensor...' : 'Apagando sensor...');
        try {
            const resp = await fetch(`/api/camera/toggle?enable=${newState}`, { method: 'POST' });
            const data = await resp.json();
            if (data.status === 'ok') {
                currentCameraState.is_capturing = data.capturing;
                updateUIVisuals();
            }
        } catch (e) { console.error('Toggle error', e); }
        hideLoading();
    });

    function updateUIVisuals() {
        if (currentCameraState.is_capturing) {
            videoStream.classList.remove('signal-off');
            btnCameraToggle.classList.add('active');
        } else {
            videoStream.classList.add('signal-off');
            btnCameraToggle.classList.remove('active');
        }

        // Update Combined Status
        if (!currentCameraState.connected) {
            statusCameraCombined.textContent = 'DESCONECTADA';
            statusCameraCombined.className = 'status-pill status-off';
        } else if (currentCameraState.is_capturing) {
            statusCameraCombined.textContent = 'TOMANDO IMAGEN';
            statusCameraCombined.className = 'status-pill status-on';
        } else {
            statusCameraCombined.textContent = 'EN ESPERA';
            statusCameraCombined.className = 'status-pill status-wait';
        }
    }

    // Controls
    const sendControl = async (control, value) => {
        try {
            await fetch(`/api/camera/control?control=${control}&value=${value}`, { method: 'POST' });
        } catch (e) { console.error('Control error', e); }
    };

    const debouncedExposure = debounce((val) => sendControl('exposure', val), 150);
    rangeExposure.addEventListener('input', (e) => {
        const val = e.target.value;
        valExposure.textContent = val >= 1000 ? `${(val / 1000).toFixed(1)}ms` : `${val}us`;
        debouncedExposure(val);
    });

    const debouncedGain = debounce((val) => sendControl('gain', val), 150);
    rangeGain.addEventListener('input', (e) => {
        valGain.textContent = e.target.value;
        debouncedGain(e.target.value);
    });

    // Resolution
    function updateResolutionOptions(maxW, maxH) {
        if (maxW === 0 || maxH === 0) return;
        selectResolution.innerHTML = '';
        const scales = [
            { label: '100% (Nativo)', scale: 1 },
            { label: '75% (Escalado)', scale: 0.75 },
            { label: '50% (Binning)', scale: 0.5 },
            { label: '25% (Rápido)', scale: 0.25 }
        ];
        scales.forEach(s => {
            const w = Math.floor(maxW * s.scale);
            const h = Math.floor(maxH * s.scale);
            const opt = document.createElement('option');
            opt.value = `${w},${h}`;
            opt.textContent = `${s.label} - ${w}x${h}`;
            selectResolution.appendChild(opt);
        });
        initialPropertiesLoaded = true;
    }

    selectResolution.addEventListener('change', async () => {
        const [w, h] = selectResolution.value.split(',').map(Number);
        showLoading(`Ajustando resolución a ${w}x${h}...`);
        try {
            await fetch(`/api/camera/resolution?width=${w}&height=${h}`, { method: 'POST' });
            videoStream.src = `/api/camera/stream?t=${Date.now()}`;
        } catch (e) { alert('Error de resolución'); }
        hideLoading();
    });

    function updateConnectedUI(ssid, hasInternet) {
        if (!ssid) {
            connectedNetSection.innerHTML = '';
            connectedNetSection.classList.add('hidden');
            return;
        }

        connectedNetSection.classList.remove('hidden');
        connectedNetSection.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
                <div style="display:flex; gap:1rem; align-items:center;">
                    <i class="fas fa-link" style="color:var(--accent-green); font-size:1.2rem;"></i>
                    <div style="display:flex; flex-direction:column; gap:0.2rem;">
                        <span style="font-weight:600; font-size:1.1rem;">${ssid}</span>
                        <div class="wifi-badge-container">
                            <span class="wifi-badge badge-connected">Conectado</span>
                            ${hasInternet ? 
                                '<span class="wifi-badge badge-internet"><i class="fas fa-globe"></i> Internet OK</span>' : 
                                '<span class="wifi-badge badge-offline"><i class="fas fa-times-circle"></i> Sin Internet</span>'}
                        </div>
                    </div>
                </div>
                <button class="btn btn-secondary btn-sm" style="color:#ef4444; border-color:rgba(239, 68, 68, 0.3);" onclick="window.disconnectWifi()">
                    <i class="fas fa-times"></i> Desconectar
                </button>
            </div>
        `;
    }

    async function scanWifi() {
        if (!wifiLoaderPanel.classList.contains('hidden')) return;
        wifiLoaderPanel.classList.remove('hidden');
        try {
            const statusResp = await fetch('/api/network/status');
            const statusData = await statusResp.json();
            const wlan0 = statusData.interfaces.find(i => i.device === 'wlan0');
            const hasInternet = statusData.internet;
            connectedSsid = (wlan0 && wlan0.connection !== '--') ? wlan0.connection : null;
            updateConnectedUI(connectedSsid, hasInternet);

            const resp = await fetch('/api/network/scan');
            const data = await resp.json();
            wifiList.innerHTML = '';
            let ssids = new Set();
            if (connectedSsid) ssids.add(connectedSsid);
            const availableNetworks = data.filter(net => net.ssid && !ssids.has(net.ssid));
            availableNetworks.sort((a, b) => b.signal - a.signal);
            if (availableNetworks.length === 0) {
                wifiList.innerHTML = '<li class="text-gray" style="padding:1rem;text-align:center;">No hay otras redes detectadas.</li>';
            }
            availableNetworks.forEach(net => {
                const li = document.createElement('li');
                li.className = 'wifi-item';
                li.innerHTML = `
                    <div class="wifi-info">
                        <i class="fas fa-wifi" style="color:var(--text-gray);"></i>
                        <div style="display:flex; flex-direction:column; gap:0.2rem;">
                            <span style="font-weight:500;">${net.ssid}</span>
                            <span style="font-size:0.75rem; color:var(--text-gray);">${net.signal}% señal</span>
                        </div>
                    </div>
                    <button class="btn btn-primary btn-sm">Conectar</button>
                `;
                li.querySelector('button').onclick = () => window.connectToWifi(net.ssid);
                wifiList.appendChild(li);
            });
        } catch (e) { console.error('Scan error', e); }
        wifiLoaderPanel.classList.add('hidden');
    }
    
    window.scanWifi = scanWifi;

    let targetSsid = '';
    window.connectToWifi = (ssid) => {
        targetSsid = ssid;
        authMode = 'wifi-auth';
        authModalDesc.textContent = `Autorización requerida para cambiar a la red: ${ssid}`;
        networkWarning.classList.add('hidden');
        document.getElementById('internet-warning').classList.add('hidden');
        authError.classList.add('hidden');
        authModal.classList.remove('hidden');
        adminPass.value = '';
        adminPass.focus();
    };

    window.disconnectWifi = () => {
        authMode = 'wifi-disconnect';
        authModalDesc.textContent = 'Autorización requerida para desconectar del WiFi actual.';
        networkWarning.classList.add('hidden');
        document.getElementById('internet-warning').classList.remove('hidden');
        authError.classList.add('hidden');
        authModal.classList.remove('hidden');
        adminPass.value = '';
        adminPass.focus();
    };

    btnWifiCancel.addEventListener('click', () => {
        wifiPassModal.classList.add('hidden');
    });

    btnWifiConfirm.addEventListener('click', async () => {
        const wPass = wifiNetPass.value;
        const wifiError = document.getElementById('wifi-auth-error');
        const originalText = btnWifiConfirm.innerHTML;
        wifiError.classList.add('hidden');
        setBtnLoading(btnWifiConfirm, true);
        try {
            const resp = await fetch('/api/network/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid: targetSsid, password: wPass })
            });
            if (resp.ok) {
                wifiPassModal.classList.add('hidden');
                alert('Conexión iniciada. El dispositivo se reconectará en breve.');
                setTimeout(scanWifi, 5000);
            } else { wifiError.classList.remove('hidden'); }
        } catch (e) { wifiError.classList.remove('hidden'); }
        setBtnLoading(btnWifiConfirm, false, originalText);
    });

    if (toggleHsPass) {
        toggleHsPass.onclick = (e) => {
            e.preventDefault();
            if (hsPass.type === 'password') {
                authMode = 'reveal';
                authModalDesc.textContent = 'Introduce la contraseña de administrador para visualizar la clave actual.';
                networkWarning.classList.add('hidden');
                authError.classList.add('hidden');
                authModal.classList.remove('hidden');
                adminPass.value = '';
                adminPass.focus();
            } else {
                hsPass.type = 'password';
                toggleHsPass.classList.replace('fa-eye-slash', 'fa-eye');
            }
        };
    }

    btnSaveHs.addEventListener('click', () => {
        authMode = 'save';
        authModalDesc.textContent = 'Introduce la contraseña de administrador para aplicar los cambios.';
        networkWarning.classList.remove('hidden');
        authError.classList.add('hidden');
        authModal.classList.remove('hidden');
        adminPass.value = '';
        adminPass.focus();
    });

    btnAuthCancel.addEventListener('click', () => {
        authModal.classList.add('hidden');
    });

    btnAuthConfirm.addEventListener('click', async () => {
        const sudoPass = adminPass.value;
        if (!sudoPass) return;
        const originalText = btnAuthConfirm.innerHTML;
        setBtnLoading(btnAuthConfirm, true);

        if (authMode === 'reveal') {
            try {
                const resp = await fetch('/api/network/hotspot/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ admin_password: sudoPass })
                });
                const data = await resp.json();
                if (resp.ok) {
                    hsPass.value = data.password;
                    hsPass.type = 'text';
                    toggleHsPass.classList.replace('fa-eye', 'fa-eye-slash');
                    authModal.classList.add('hidden');
                    authError.classList.add('hidden');
                } else { authError.classList.remove('hidden'); }
            } catch (e) { authError.classList.remove('hidden'); }
            setBtnLoading(btnAuthConfirm, false, originalText);
            return;
        }

        if (authMode === 'wifi-auth') {
            try {
                const resp = await fetch('/api/network/verify-admin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: sudoPass })
                });
                if (resp.ok) {
                    authModal.classList.add('hidden');
                    wifiPassDesc.textContent = `Introduce la contraseña para: ${targetSsid}`;
                    wifiPassModal.classList.remove('hidden');
                    wifiNetPass.value = '';
                    wifiNetPass.focus();
                } else { authError.classList.remove('hidden'); }
            } catch (e) { authError.classList.remove('hidden'); }
            setBtnLoading(btnAuthConfirm, false, originalText);
            return;
        }

        if (authMode === 'wifi-disconnect') {
            try {
                const resp = await fetch('/api/network/disconnect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: sudoPass })
                });
                if (resp.ok) {
                    authModal.classList.add('hidden');
                    alert('Dispositivo desconectado del WiFi.');
                    setTimeout(scanWifi, 1000);
                } else { authError.classList.remove('hidden'); }
            } catch (e) { authError.classList.remove('hidden'); }
            setBtnLoading(btnAuthConfirm, false, originalText);
            return;
        }

        try {
            const resp = await fetch('/api/network/hotspot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    ssid: hsSsid.value, 
                    password: hsPass.value, 
                    enable: true,
                    interface: 'ap0',
                    admin_password: sudoPass
                })
            });
            if (resp.ok) {
                alert('Configuración aplicada con éxito.');
                authModal.classList.add('hidden');
                authError.classList.add('hidden');
            } else { authError.classList.remove('hidden'); }
        } catch (err) { alert('Conexión interrumpida. Vuelve a conectarte a la Pi.'); }
        setBtnLoading(btnAuthConfirm, false, originalText);
        hideLoading();
    });

    async function loadHotspotConfig() {
        try {
            const resp = await fetch('/api/network/hotspot/config');
            const data = await resp.json();
            hsSsid.value = data.ssid;
            hsPass.value = data.password;
        } catch (e) {}
    }

    async function pollStatus() {
        try {
            const resp = await fetch('/api/camera/status');
            const data = await resp.json();
            currentCameraState.connected = data.connected;
            currentCameraState.is_capturing = data.is_capturing;
            updateUIVisuals();
            metricTemp.textContent = `${data.temperature.toFixed(1)}°C`;
            metricFps.textContent = `${data.fps.toFixed(1)} FPS`;
            videoResolution.textContent = `${data.width} x ${data.height}`;
            if (data.max_width > 0 && !initialPropertiesLoaded) {
                currentCameraState.max_width = data.max_width;
                currentCameraState.max_height = data.max_height;
                updateResolutionOptions(data.max_width, data.max_height);
            }
        } catch (e) {}
    }

    async function pollNetwork() {
        try {
            const resp = await fetch('/api/network/status');
            const data = await resp.json();
            const wlan0 = data.interfaces.find(i => i.device === 'wlan0');
            connectedSsid = (wlan0 && wlan0.connection !== '--') ? wlan0.connection : null;
            updateConnectedUI(connectedSsid, data.internet);
            statusInternet.textContent = data.internet ? 'ONLINE' : 'OFFLINE';
            statusInternet.className = data.internet ? 'status-pill status-on' : 'status-pill status-off';
        } catch (e) {}
    }

    btnFullscreen.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            mainVideoContainer.requestFullscreen();
            btnFullscreen.classList.add('active');
        } else {
            document.exitFullscreen();
            btnFullscreen.classList.remove('active');
        }
    });

    setInterval(pollStatus, 1500);
    setInterval(pollNetwork, 5000);
    setInterval(scanWifi, 30000);
    pollStatus();
    pollNetwork();
    loadHotspotConfig();
    setTimeout(scanWifi, 1000);
});
