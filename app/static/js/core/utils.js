import { elements } from '../ui/dom.js';

export function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}

export function showLoading(text = 'Procesando...', type = 'default') {
    if (elements.loaderText) elements.loaderText.textContent = text;
    
    // Switch between default spinner and cloud animation
    const loaderContainer = document.querySelector('#loading-overlay .loader');
    const cloudContainer = document.querySelector('#loading-overlay .cloud-loader-container');
    
    if (type === 'cloud') {
        if (loaderContainer) loaderContainer.classList.add('hidden');
        if (!cloudContainer) {
            const newCloud = document.createElement('div');
            newCloud.className = 'cloud-loader-container';
            newCloud.innerHTML = `
                <div class="cloud-loader">
                    <i class="fas fa-cloud cloud-icon"></i>
                    <i class="fas fa-arrow-up cloud-arrow"></i>
                </div>
                <div class="cloud-dots">
                    <div class="cloud-dot"></div>
                    <div class="cloud-dot"></div>
                    <div class="cloud-dot"></div>
                </div>
            `;
            document.querySelector('#loading-overlay').insertBefore(newCloud, elements.loaderText);
        } else {
            cloudContainer.classList.remove('hidden');
        }
    } else {
        if (loaderContainer) loaderContainer.classList.remove('hidden');
        if (cloudContainer) cloudContainer.classList.add('hidden');
    }
    
    if (elements.loadingOverlay) elements.loadingOverlay.classList.remove('hidden');
}

export function hideLoading() {
    if (elements.loadingOverlay) elements.loadingOverlay.classList.add('hidden');
}

export function setBtnLoading(btn, isLoading, originalText) {
    if (isLoading) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fas fa-circle-notch spin"></i> Procesando...`;
    } else {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}
