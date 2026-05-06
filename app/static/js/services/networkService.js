export const networkService = {
    async getStatus() {
        const resp = await fetch('/api/network/status');
        return await resp.json();
    },
    
    async scan() {
        const resp = await fetch('/api/network/scan');
        return await resp.json();
    },
    
    async connect(ssid, password, admin_password = null) {
        return await fetch('/api/network/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ssid, password, admin_password })
        });
    },
    
    async disconnect(sudoPass) {
        return await fetch('/api/network/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: sudoPass })
        });
    },
    
    async verifyAdmin(password) {
        return await fetch('/api/network/verify-admin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
    },
    
    async getHotspotConfig() {
        const resp = await fetch('/api/network/hotspot/config');
        return await resp.json();
    },
    
    async revealHotspotPassword(sudoPass) {
        return await fetch('/api/network/hotspot/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ admin_password: sudoPass })
        });
    },
    
    async saveHotspot(config) {
        return await fetch('/api/network/hotspot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
    }
};
