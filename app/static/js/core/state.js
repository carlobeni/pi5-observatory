export const state = {
    currentCameraState: {
        max_width: 0,
        max_height: 0,
        is_capturing: false,
        connected: false
    },
    connectedSsid: null,
    initialPropertiesLoaded: false,
    authMode: 'save',
    targetSsid: '',
    adminPassword: null
};
