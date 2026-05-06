import { state } from '../core/state.js';
import { elements } from './dom.js';
import { setBtnLoading } from '../core/utils.js';
import { networkService } from '../services/networkService.js';

export function initModals() {
    const { 
        wifiPassModal, btnWifiCancel, btnWifiConfirm, 
        wifiNetPass, authModal, btnAuthCancel, 
        btnAuthConfirm, adminPass, authError 
    } = elements;

    btnWifiCancel.addEventListener('click', () => {
        wifiPassModal.classList.add('hidden');
    });

    btnAuthCancel.addEventListener('click', () => {
        authModal.classList.add('hidden');
    });

    // Note: Confirm buttons are handled in main.js or separate event handlers 
    // because they often involve cross-module logic.
}

export function openAuthModal(mode, desc, showInternetWarning = false) {
    const { authModal, authModalDesc, networkWarning, internetWarning, authError, adminPass } = elements;
    state.authMode = mode;
    authModalDesc.textContent = desc;
    networkWarning.classList.toggle('hidden', mode !== 'save');
    if (internetWarning) internetWarning.classList.toggle('hidden', !showInternetWarning);
    authError.classList.add('hidden');
    authModal.classList.remove('hidden');
    adminPass.value = '';
    adminPass.focus();
}
