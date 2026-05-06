export const elements = {
    sidebar: document.querySelector('.sidebar'),
    btnHamburger: document.getElementById('btn-hamburger'),
    navButtons: document.querySelectorAll('.nav-btn'),
    views: document.querySelectorAll('.view'),
    viewTitle: document.getElementById('view-title'),

    statusCameraCombined: document.getElementById('status-camera-combined'),
    statusInternet: document.getElementById('status-internet'),
    statusHotspot: document.getElementById('status-hotspot'),
    dotCamera: document.getElementById('dot-camera'),
    dotInternet: document.getElementById('dot-internet'),
    dotHotspot: document.getElementById('dot-hotspot'),
    iconStatusCamera: document.getElementById('icon-status-camera'),
    iconStatusInternet: document.getElementById('icon-status-internet'),
    iconStatusHotspot: document.getElementById('icon-status-hotspot'),

    metricTemp: document.getElementById('metric-temp'),
    metricFps: document.getElementById('metric-fps'),
    metricTempContainer: document.getElementById('metric-temp-container'),
    metricFpsContainer: document.getElementById('metric-fps-container'),

    videoResolution: document.getElementById('video-resolution'),
    videoStream: document.getElementById('video-stream'),
    videoLoader: document.getElementById('video-loader'),
    videoLoaderText: document.getElementById('video-loader-text'),
    iconTransmitting: document.getElementById('icon-transmitting'),

    videoOverlayTopLeft: document.querySelector('.video-overlay-top-left'),
    videoOverlayTopRight: document.querySelector('.video-overlay-top-right'),
    videoOverlayControlsLeft: document.querySelector('.video-overlay-controls-left'),
    videoOverlayBottomRight: document.querySelector('.video-overlay-bottom-right'),

    rangeExposure: document.getElementById('range-exposure'),
    valExposure: document.getElementById('val-exposure'),
    rangeGain: document.getElementById('range-gain'),
    valGain: document.getElementById('val-gain'),

    btnFullscreen: document.getElementById('btn-fullscreen'),
    btnCameraToggle: document.getElementById('btn-camera-toggle'),
    btnSnapshot: document.getElementById('btn-snapshot'),
    mainVideoContainer: document.getElementById('main-video-container'),

    snapshotOverlay: document.getElementById('snapshot-overlay'),
    snapshotImg: document.getElementById('snapshot-img'),
    btnSnapshotClose: document.getElementById('btn-snapshot-close'),
    btnSnapshotDownload: document.getElementById('btn-snapshot-download'),
    btnSnapshotUpload: document.getElementById('btn-snapshot-upload'),

    wifiList: document.getElementById('wifi-list'),
    wifiLoaderPanel: document.getElementById('wifi-loader-panel'),
    connectedNetSection: document.getElementById('connected-network-section'),

    wifiPassModal: document.getElementById('wifi-pass-modal'),
    wifiNetPass: document.getElementById('wifi-net-pass'),
    btnWifiConfirm: document.getElementById('btn-wifi-confirm'),
    btnWifiCancel: document.getElementById('btn-wifi-cancel'),
    wifiPassDesc: document.getElementById('wifi-pass-desc'),

    hsSsid: document.getElementById('hs-ssid'),
    hsPass: document.getElementById('hs-pass'),
    toggleHsPass: document.getElementById('toggle-hs-pass'),

    loadingOverlay: document.getElementById('loading-overlay'),
    loaderText: document.getElementById('loader-text'),
    btnSaveHs: document.getElementById('btn-save-hs'),

    authModal: document.getElementById('auth-modal'),
    adminPass: document.getElementById('admin-pass'),
    btnAuthCancel: document.getElementById('btn-auth-cancel'),
    btnAuthConfirm: document.getElementById('btn-auth-confirm'),
    authModalDesc: document.getElementById('auth-modal-desc'),
    networkWarning: document.getElementById('network-warning'),
    authError: document.getElementById('auth-error'),
    internetWarning: document.getElementById('internet-warning'),
    wifiAuthError: document.getElementById('wifi-auth-error')
};
