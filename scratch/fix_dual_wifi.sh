#!/bin/bash
echo "=== REPARACIÓN DE MODO DUAL WIFI + HOTSPOT ==="

# 1. Configurar NetworkManager para ignorar ap0
echo "[1/4] Configurando NetworkManager para ignorar ap0..."
NM_CONF="/etc/NetworkManager/NetworkManager.conf"
if ! grep -q "unmanaged-devices=interface-name:ap0" "$NM_CONF"; then
    # Asegurar que existe la sección [keyfile]
    if ! grep -q "\[keyfile\]" "$NM_CONF"; then
        echo -e "\n[keyfile]\nunmanaged-devices=interface-name:ap0" >> "$NM_CONF"
    else
        sed -i '/\[keyfile\]/a unmanaged-devices=interface-name:ap0' "$NM_CONF"
    fi
    systemctl reload NetworkManager
    echo "   OK: NetworkManager configurado."
else
    echo "   OK: Ya estaba configurado."
fi

# 2. Forzar creación de interfaz ap0
echo "[2/4] Creando interfaz virtual ap0..."
if [ -f "/usr/local/bin/setup-wifi-ap.sh" ]; then
    bash /usr/local/bin/setup-wifi-ap.sh
    echo "   OK: Script de configuración ejecutado."
else
    echo "   ERROR: No se encontró /usr/local/bin/setup-wifi-ap.sh"
fi

# 3. Reiniciar y Habilitar servicios de red (Permanencia)
echo "[3/4] Reiniciando y Habilitando servicios de Hotspot..."
systemctl enable hostapd
systemctl enable dnsmasq
systemctl enable wifi-ap
systemctl restart hostapd
systemctl restart dnsmasq
echo "   OK: Servicios habilitados y reiniciados."

# 4. Verificar resultado final
echo "[4/4] Verificando interfaz ap0..."
if ip link show ap0 > /dev/null 2>&1; then
    echo "   SUCCESS: Interfaz ap0 creada y lista."
else
    echo "   FAILED: No se pudo crear la interfaz ap0."
fi

echo "=== REPARACIÓN COMPLETADA ==="
