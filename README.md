# Pi5 Observatory - Embedded System

Sistema robusto para el control, visualización y gestión de cámaras astronómicas ZWO en Raspberry Pi 5 con Ubuntu.

## Características
- **Panel de Control Local**: Interfaz web moderna con visualización en tiempo real (MJPEG).
- **Gestión de Red Integrada**: Control de Hotspot y Uplink WiFi directamente desde el panel.
- **Transmisión Remota**: Streaming simultáneo hacia servidores externos vía WebSocket.
- **Arquitectura Modular**: Backend basado en FastAPI con procesamiento de cámara en segundo plano.

## Instalación

### 1. Requisitos Previos
Asegúrate de tener instalado el SDK de ZWO en `/usr/local/lib/libASICamera2.so`. Si no lo tienes, sigue los pasos de la sección "SDK de ZWO" más abajo.

### 2. Configurar el Entorno
```bash
# Instalar Poetry si no lo tienes
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Instalar dependencias
poetry install
```

### 3. Configuración
Edita el archivo `config.yaml` para ajustar los parámetros de tu cámara, red y streaming remoto.

## Ejecución

### Modo Desarrollo
```bash
poetry run python -m app.main
```
El panel estará disponible en `http://localhost:8000` o la IP de tu Pi.

### Como Servicio del Sistema (Systemd)
```bash
# Copiar el archivo de servicio
sudo cp systemd/pi5-observatory.service /etc/systemd/system/
sudo systemctl daemon-reload

# Habilitar e iniciar
sudo systemctl enable pi5-observatory
sudo systemctl start pi5-observatory

# Ver logs
journalctl -u pi5-observatory -f
```

## Estructura del Proyecto
- `app/`: Código fuente principal.
  - `api/`: Endpoints de la API (Cámara, Red).
  - `modules/`: Lógica de negocio (ZWO SDK, NetworkManager).
  - `core/`: Componentes base (Frame Buffer, Config).
  - `static/`: Frontend (HTML/CSS/JS).
- `config.yaml`: Configuración centralizada.
- `systemd/`: Archivo para ejecución automática.

## SDK de ZWO (Instalación rápida)
```bash
# Descargar y extraer (ejemplo para x64/ARM)
wget -O ASI_Camera_SDK.zip "https://dl.zwoastro.com/software?app=DeveloperCameraSdk&platform=windows86&region=Overseas"
unzip ASI_Camera_SDK.zip
# Copiar librería según arquitectura
sudo cp ASI_linux_mac_SDK_V1.40/lib/armv8/libASICamera2.so /usr/local/lib/
sudo ldconfig

# Reglas udev para permisos USB
sudo tee /etc/udev/rules.d/99-zwo.rules << 'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="03c3", MODE="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```
