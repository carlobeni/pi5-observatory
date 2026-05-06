export const cameraService = {
    async toggle(enable) {
        const resp = await fetch(`/api/camera/toggle?enable=${enable}`, { method: 'POST' });
        return await resp.json();
    },
    
    async sendControl(control, value) {
        await fetch(`/api/camera/control?control=${control}&value=${value}`, { method: 'POST' });
    },
    
    async setResolution(width, height) {
        await fetch(`/api/camera/resolution?width=${width}&height=${height}`, { method: 'POST' });
    },
    
    async getStatus() {
        const resp = await fetch('/api/camera/status');
        return await resp.json();
    }
};
