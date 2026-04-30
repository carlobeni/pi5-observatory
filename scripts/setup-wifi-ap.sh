#!/bin/bash

# Configuration
PHYS_INT="wlan0"
AP_INT="ap0"
IP_ADDR="192.168.4.1"
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"

# Check if physical interface exists
if ! ip link show "$PHYS_INT" > /dev/null 2>&1; then
    echo "Error: Physical interface $PHYS_INT not found."
    exit 1
fi

# 1. Detect current channel of wlan0 to avoid conflicts
CURRENT_CHAN=$(iw dev "$PHYS_INT" info | grep channel | awk '{print $2}')
if [ -z "$CURRENT_CHAN" ]; then
    echo "Warning: Could not detect wlan0 channel, defaulting to 1"
    CURRENT_CHAN=1
fi

# 2. Update hostapd.conf with the detected channel
if [ -f "$HOSTAPD_CONF" ]; then
    echo "Updating $HOSTAPD_CONF to use channel $CURRENT_CHAN..."
    sed -i "s/^channel=.*/channel=$CURRENT_CHAN/" "$HOSTAPD_CONF"
fi

# 3. Create virtual interface if it doesn't exist
if ! ip link show "$AP_INT" > /dev/null 2>&1; then
    echo "Creating virtual interface $AP_INT..."
    MAC_ADDR=$(cat /sys/class/net/$PHYS_INT/address)
    
    # Generate a locally administered MAC address (flip the 2nd bit of the first byte)
    FIRST_BYTE=$(echo $MAC_ADDR | cut -d: -f1)
    REST_BYTES=$(echo $MAC_ADDR | cut -d: -f2-6)
    # Using printf to ensure compatibility
    NEW_FIRST_BYTE=$(printf "%02x" $((0x$FIRST_BYTE | 2)))
    NEW_MAC="$NEW_FIRST_BYTE:$REST_BYTES"
    
    echo "Using MAC $NEW_MAC for $AP_INT"
    iw dev "$PHYS_INT" interface add "$AP_INT" type __ap addr "$NEW_MAC"
    sleep 2
fi

# 4. Configure IP and bring up
if ip link show "$AP_INT" > /dev/null 2>&1; then
    echo "Configuring $AP_INT with IP $IP_ADDR..."
    ip addr flush dev "$AP_INT" 2>/dev/null || true
    ip addr add "$IP_ADDR/24" dev "$AP_INT"
    ip link set "$AP_INT" up
    echo "Interface $AP_INT is ready on channel $CURRENT_CHAN."
else
    echo "Error: Failed to create $AP_INT"
    exit 1
fi
