#!/bin/bash

# Script to apply system-level changes for Pi5 Observatory
# Run this with: sudo ./scripts/apply_system_config.sh

echo "Applying DNS redirection for Captive Portal..."
if [ -d "/etc/dnsmasq.d" ]; then
    echo "address=/#/192.168.4.1" | tee -a /etc/dnsmasq.d/ap0.conf
    systemctl restart dnsmasq
    echo "OK: DNS redirection configured."
else
    echo "ERR: /etc/dnsmasq.d not found."
fi

echo "Installing systemd service..."
cp systemd/pi5-observatory.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pi5-observatory.service

echo "------------------------------------------------"
echo "¡Todo listo! El observatorio ahora es autónomo."
echo "Puedes iniciarlo ahora con:"
echo "sudo systemctl start pi5-observatory"
echo "------------------------------------------------"
echo "Logs disponibles en: tail -f logs/systemd.log"
