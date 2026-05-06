import { elements } from './dom.js';
import { showLoading, hideLoading } from '../core/utils.js';

export function takeSnapshot() {
    const { videoStream, snapshotOverlay, snapshotImg } = elements;
    
    // Create a temporary canvas to capture the image from the stream
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size to match the video stream natural size
    canvas.width = videoStream.naturalWidth || videoStream.width;
    canvas.height = videoStream.naturalHeight || videoStream.height;
    
    // Draw current frame to canvas
    ctx.drawImage(videoStream, 0, 0, canvas.width, canvas.height);
    
    // Get image as data URL
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
    
    // Show in preview
    snapshotImg.src = dataUrl;
    snapshotOverlay.classList.remove('hidden');
}



export function closeSnapshot() {
    if (confirm('¿Estás seguro de salir? Se perderá la imagen capturada si no la has guardado o descargado.')) {
        elements.snapshotOverlay.classList.add('hidden');
        elements.snapshotImg.src = '';
    }
}

export function downloadSnapshot() {
    const dataUrl = elements.snapshotImg.src;
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.download = `pi5-capture-${timestamp}.jpg`;
    link.href = dataUrl;
    link.click();
}

export async function uploadSnapshot() {
    const dataUrl = elements.snapshotImg.src;
    showLoading('Sincronizando con la nube de Supabase...', 'cloud');
    try {
        const resp = await fetch('/api/camera/snapshot/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: dataUrl })
        });
        const data = await resp.json();
        if (data.status === 'ok') {
            alert('¡Imagen guardada con éxito!');
        } else {
            alert('Error al guardar: ' + data.message);
        }
    } catch (e) {
        alert('Error de conexión al guardar la imagen.');
    }
    hideLoading();
}
