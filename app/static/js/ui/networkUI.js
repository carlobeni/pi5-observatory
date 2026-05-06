import { state } from '../core/state.js';
import { elements } from './dom.js';

export function updateConnectedUI(ssid, hasInternet) {
    if (!ssid) {
        elements.connectedNetSection.innerHTML = '';
        elements.connectedNetSection.classList.add('hidden');
        return;
    }

    elements.connectedNetSection.classList.remove('hidden');
    elements.connectedNetSection.innerHTML = `
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
