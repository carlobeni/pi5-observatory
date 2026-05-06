import { state } from './core/state.js';
import { elements } from './ui/dom.js';
import { debounce, showLoading, hideLoading, setBtnLoading } from './core/utils.js';
import { cameraService } from './services/cameraService.js';
import { networkService } from './services/networkService.js';
import { updateCameraVisuals, applyMaxResolution } from './ui/cameraUI.js';
import { updateConnectedUI } from './ui/networkUI.js';
import { initNavigation } from './ui/navigation.js';
import { initModals, openAuthModal } from './ui/modals.js';
import { takeSnapshot, closeSnapshot, downloadSnapshot, uploadSnapshot } from './ui/snapshotUI.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize UI Components
    initNavigation();
    initModals();

    // 2. Camera Event Listeners
    elements.btnCameraToggle.addEventListener('click', async (e) => {
        e.preventDefault();
        const newState = !state.currentCameraState.is_capturing;
        console.log(`[Toggle] Intentando cambiar estado a: ${newState ? 'ON' : 'OFF'}`);
        showLoading(newState ? 'Encendiendo sensor...' : 'Apagando sensor...');
        try {
            const data = await cameraService.toggle(newState);
            console.log('[Toggle] Respuesta API:', data);
            if (data.status === 'ok') {
                state.currentCameraState.is_capturing = data.capturing;
                if (newState) {
                    const newSrc = `/api/camera/stream?t=${Date.now()}`;
                    console.log(`[Stream] Preparando reconexión a: ${newSrc}`);
                    elements.videoStream.onload = () => console.log('[Stream] Imagen cargada exitosamente');
                    elements.videoStream.onerror = (err) => console.error('[Stream] Error cargando imagen:', err);
                    // Pequeño retardo para asegurar que el backend ha iniciado la captura
                    setTimeout(() => {
                        console.log('[Stream] Aplicando nuevo src');
                        elements.videoStream.src = newSrc;
                    }, 500);
                } else {
                    console.log('[Stream] Limpiando src');
                    elements.videoStream.src = '';
                }
                updateCameraVisuals();
            }
        } catch (e) { console.error('[Toggle] Error en la petición:', e); }
        hideLoading();
    });

    elements.btnSnapshot.addEventListener('click', takeSnapshot);
    elements.btnSnapshotClose.addEventListener('click', closeSnapshot);
    elements.btnSnapshotDownload.addEventListener('click', downloadSnapshot);
    elements.btnSnapshotUpload.addEventListener('click', uploadSnapshot);

    const debouncedExposure = debounce((val) => cameraService.sendControl('exposure', val), 150);
    elements.rangeExposure.addEventListener('input', (e) => {
        const val = e.target.value;
        elements.valExposure.textContent = val >= 1000 ? `${(val / 1000).toFixed(1)}ms` : `${val}us`;
        debouncedExposure(val);
    });

    const debouncedGain = debounce((val) => cameraService.sendControl('gain', val), 150);
    elements.rangeGain.addEventListener('input', (e) => {
        elements.valGain.textContent = e.target.value;
        debouncedGain(e.target.value);
    });

    elements.btnFullscreen.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            elements.mainVideoContainer.requestFullscreen();
            elements.btnFullscreen.classList.add('active');
        } else {
            document.exitFullscreen();
            elements.btnFullscreen.classList.remove('active');
        }
    });

    // 3. Network Event Listeners
    if (elements.toggleHsPass) {
        elements.toggleHsPass.onclick = (e) => {
            e.preventDefault();
            if (elements.hsPass.type === 'password') {
                openAuthModal('reveal', 'Introduce la contraseña de administrador para visualizar la clave actual.');
            } else {
                elements.hsPass.type = 'password';
                elements.toggleHsPass.classList.replace('fa-eye-slash', 'fa-eye');
            }
        };
    }

    elements.btnSaveHs.addEventListener('click', () => {
        openAuthModal('save', 'Introduce la contraseña de administrador para aplicar los cambios.');
    });

    elements.btnWifiConfirm.addEventListener('click', async () => {
        const wPass = elements.wifiNetPass.value;
        const originalText = elements.btnWifiConfirm.innerHTML;
        elements.wifiAuthError.classList.add('hidden');
        setBtnLoading(elements.btnWifiConfirm, true);
        try {
            const resp = await networkService.connect(state.targetSsid, wPass);
            if (resp.ok) {
                elements.wifiPassModal.classList.add('hidden');
                alert('Conexión iniciada. El dispositivo se reconectará en breve.');
                setTimeout(scanWifi, 5000);
            } else { elements.wifiAuthError.classList.remove('hidden'); }
        } catch (e) { elements.wifiAuthError.classList.remove('hidden'); }
        setBtnLoading(elements.btnWifiConfirm, false, originalText);
    });

    elements.btnAuthConfirm.addEventListener('click', async () => {
        const sudoPass = elements.adminPass.value;
        if (!sudoPass) return;
        const originalText = elements.btnAuthConfirm.innerHTML;
        setBtnLoading(elements.btnAuthConfirm, true);

        if (state.authMode === 'reveal') {
            try {
                const resp = await networkService.revealHotspotPassword(sudoPass);
                const data = await resp.json();
                if (resp.ok) {
                    elements.hsPass.value = data.password;
                    elements.hsPass.type = 'text';
                    elements.toggleHsPass.classList.replace('fa-eye', 'fa-eye-slash');
                    elements.authModal.classList.add('hidden');
                } else { elements.authError.classList.remove('hidden'); }
            } catch (e) { elements.authError.classList.remove('hidden'); }
        } else if (state.authMode === 'wifi-auth') {
            try {
                const resp = await networkService.verifyAdmin(sudoPass);
                if (resp.ok) {
                    elements.authModal.classList.add('hidden');
                    elements.wifiPassDesc.textContent = `Introduce la contraseña para: ${state.targetSsid}`;
                    elements.wifiPassModal.classList.remove('hidden');
                    elements.wifiNetPass.value = '';
                    elements.wifiNetPass.focus();
                } else { elements.authError.classList.remove('hidden'); }
            } catch (e) { elements.authError.classList.remove('hidden'); }
        } else if (state.authMode === 'wifi-disconnect') {
            try {
                const resp = await networkService.disconnect(sudoPass);
                if (resp.ok) {
                    elements.authModal.classList.add('hidden');
                    alert('Dispositivo desconectado del WiFi.');
                    setTimeout(scanWifi, 1000);
                } else { elements.authError.classList.remove('hidden'); }
            } catch (e) { elements.authError.classList.remove('hidden'); }
        } else if (state.authMode === 'save') {
            try {
                const resp = await networkService.saveHotspot({
                    ssid: elements.hsSsid.value,
                    password: elements.hsPass.value,
                    enable: true,
                    interface: 'ap0',
                    admin_password: sudoPass
                });
                if (resp.ok) {
                    alert('Configuración aplicada con éxito.');
                    elements.authModal.classList.add('hidden');
                } else { elements.authError.classList.remove('hidden'); }
            } catch (err) { alert('Conexión interrumpida. Vuelve a conectarte a la Pi.'); }
        }
        setBtnLoading(elements.btnAuthConfirm, false, originalText);
    });

    // 4. Polling & Initialization Functions
    async function pollStatus() {
        try {
            const data = await cameraService.getStatus();
            state.currentCameraState.connected = data.connected;
            state.currentCameraState.is_capturing = data.is_capturing;
            updateCameraVisuals();
            if (data.connected) {
                elements.metricTemp.textContent = `${data.temperature.toFixed(1)}°C`;
                elements.metricFps.textContent = `${data.fps.toFixed(1)} FPS`;
                elements.videoResolution.textContent = `${data.width} x ${data.height}`;
                if (data.max_width > 0 && !state.initialPropertiesLoaded) {
                    state.currentCameraState.max_width = data.max_width;
                    state.currentCameraState.max_height = data.max_height;
                    applyMaxResolution(data.max_width, data.max_height);
                }
            }
        } catch (e) { }
    }

    async function pollNetwork() {
        try {
            const data = await networkService.getStatus();
            const wlan0 = data.interfaces.find(i => i.device === 'wlan0');
            state.connectedSsid = (wlan0 && wlan0.connection !== '--') ? wlan0.connection : null;
            updateConnectedUI(state.connectedSsid, data.internet);
            elements.statusInternet.textContent = data.internet ? 'ONLINE' : 'OFFLINE';
            elements.statusInternet.className = data.internet ? 'status-pill status-on' : 'status-pill status-off';
            
            // Update Hotspot Status
            if (elements.statusHotspot) {
                elements.statusHotspot.textContent = data.hotspot_active ? 'ON' : 'OFF';
                elements.statusHotspot.className = data.hotspot_active ? 'status-pill status-on' : 'status-pill status-off';
            }
        } catch (e) { }
    }

    async function scanWifi() {
        if (!elements.wifiLoaderPanel.classList.contains('hidden')) return;
        elements.wifiLoaderPanel.classList.remove('hidden');
        try {
            await pollNetwork();
            const data = await networkService.scan();
            elements.wifiList.innerHTML = '';
            let ssids = new Set();
            if (state.connectedSsid) ssids.add(state.connectedSsid);
            const availableNetworks = data.filter(net => net.ssid && !ssids.has(net.ssid));
            availableNetworks.sort((a, b) => b.signal - a.signal);
            if (availableNetworks.length === 0) {
                elements.wifiList.innerHTML = '<li class="text-gray" style="padding:1rem;text-align:center;">No hay otras redes detectadas.</li>';
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
                elements.wifiList.appendChild(li);
            });
        } catch (e) { console.error('Scan error', e); }
        elements.wifiLoaderPanel.classList.add('hidden');
    }

    // 5. Global Window Functions (for HTML onclick)
    window.scanWifi = scanWifi;

    window.connectToWifi = (ssid) => {
        state.targetSsid = ssid;
        openAuthModal('wifi-auth', `Autorización requerida para cambiar a la red: ${ssid}`);
    };

    window.disconnectWifi = () => {
        openAuthModal('wifi-disconnect', 'Autorización requerida para desconectar del WiFi actual.', true);
    };

    // 6. Final Bootstrapping
    setInterval(pollStatus, 1500);
    setInterval(pollNetwork, 5000);
    setInterval(scanWifi, 30000);

    updateCameraVisuals();
    pollStatus();
    pollNetwork();

    networkService.getHotspotConfig().then(data => {
        elements.hsSsid.value = data.ssid;
        elements.hsPass.value = data.password;
    }).catch(() => { });

    setTimeout(scanWifi, 1000);
});
