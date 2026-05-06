import { state } from '../core/state.js';
import { elements } from './dom.js';
import { cameraService } from '../services/cameraService.js';

export function updateCameraVisuals() {
    const { currentCameraState } = state;
    const { 
        statusCameraCombined, videoLoaderText, videoLoader, 
        videoStream, iconTransmitting, metricTempContainer, 
        metricFpsContainer, btnCameraToggle 
    } = elements;

    if (!currentCameraState.connected) {
        if (statusCameraCombined) {
            statusCameraCombined.textContent = 'DESCONECTADA';
            statusCameraCombined.className = 'status-pill status-off';
        }
        if (elements.dotCamera) {
            elements.dotCamera.className = 'status-dot status-off';
            if (elements.iconStatusCamera) elements.iconStatusCamera.style.color = 'var(--text-gray)';
        }
        videoLoaderText.textContent = 'Cámara Desconectada';
        videoLoader.classList.remove('hidden');
        videoStream.classList.add('signal-off');
        iconTransmitting.style.color = 'var(--text-gray)';
        metricTempContainer.style.display = 'none';
        metricFpsContainer.style.display = 'none';
        if (elements.videoOverlayControlsLeft) elements.videoOverlayControlsLeft.style.opacity = '0';
        if (elements.videoOverlayControlsLeft) elements.videoOverlayControlsLeft.style.pointerEvents = 'none';
    } else {
        metricTempContainer.style.display = 'flex';
        metricFpsContainer.style.display = 'flex';
        if (elements.videoOverlayControlsLeft) elements.videoOverlayControlsLeft.style.opacity = '1';
        if (elements.videoOverlayControlsLeft) elements.videoOverlayControlsLeft.style.pointerEvents = 'auto';
        
        if (currentCameraState.is_capturing) {
            if (statusCameraCombined) {
                statusCameraCombined.textContent = 'TOMANDO IMAGEN';
                statusCameraCombined.className = 'status-pill status-on';
            }
            if (elements.dotCamera) {
                elements.dotCamera.className = 'status-dot status-on';
                if (elements.iconStatusCamera) elements.iconStatusCamera.style.color = 'var(--accent-green)';
            }
            videoLoader.classList.add('hidden');
            videoStream.classList.remove('signal-off');
            iconTransmitting.style.color = 'var(--accent-green)';
            if (elements.btnSnapshot) elements.btnSnapshot.disabled = false;
        } else {
            if (statusCameraCombined) {
                statusCameraCombined.textContent = 'EN ESPERA';
                statusCameraCombined.className = 'status-pill status-wait';
            }
            if (elements.dotCamera) {
                elements.dotCamera.className = 'status-dot status-wait';
                if (elements.iconStatusCamera) elements.iconStatusCamera.style.color = 'var(--warning-yellow)';
            }
            videoLoaderText.textContent = 'Sensor en Espera';
            videoLoader.classList.remove('hidden');
            videoStream.classList.add('signal-off');
            iconTransmitting.style.color = 'var(--text-gray)';
            if (elements.btnSnapshot) elements.btnSnapshot.disabled = true;
        }
    }

    if (currentCameraState.is_capturing) {
        btnCameraToggle.classList.add('active');
    } else {
        btnCameraToggle.classList.remove('active');
    }
}

export async function applyMaxResolution(w, h) {
    if (w === 0 || h === 0) return;
    try {
        await cameraService.setResolution(w, h);
        state.initialPropertiesLoaded = true;
        console.log(`Resolución máxima aplicada automáticamente: ${w}x${h}`);
    } catch (e) { console.error('Error aplicando resolución automática', e); }
}
