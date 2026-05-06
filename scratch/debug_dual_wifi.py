import subprocess
import os
import re
import socket

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def print_header(text):
    print(f"\n\033[1;34m=== {text} ===\033[0m")

def print_success(text):
    print(f"\033[1;32m[OK] {text}\033[0m")

def print_warning(text):
    print(f"\033[1;33m[WARN] {text}\033[0m")

def print_error(text):
    print(f"\033[1;31m[ERROR] {text}\033[0m")

def debug_dual_mode():
    print_header("DEBUG DE CONECTIVIDAD DUAL (WIFI + HOTSPOT)")
    
    # 1. Check Hardware Capabilities
    print("\n1. Verificando capacidades de hardware...")
    out, _, _ = run_cmd("iw list")
    if "valid interface combinations" in out:
        if "#{ AP } <= 1" in out and "#{ managed } <= 1" in out:
            print_success("El hardware soporta modo dual (Managed + AP).")
            if "#channels <= 1" in out:
                print_warning("Requiere que ambos operen en el MISMO CANAL.")
        else:
            print_error("El hardware podría NO soportar modo dual simultáneo.")
    else:
        print_warning("No se pudo determinar las combinaciones de interfaz (falta 'iw').")

    # 2. Check Interfaces
    print("\n2. Verificando interfaces de red...")
    out, _, _ = run_cmd("ip link show")
    has_wlan0 = "wlan0" in out
    has_ap0 = "ap0" in out
    
    if has_wlan0:
        print_success("wlan0 existe.")
        out_w, _, _ = run_cmd("iw dev wlan0 info")
        chan_match = re.search(r"channel (\d+)", out_w)
        wlan0_chan = chan_match.group(1) if chan_match else "Desconocido"
        print(f"   Canal actual wlan0: {wlan0_chan}")
    else:
        print_error("wlan0 NO existe.")

    if has_ap0:
        print_success("ap0 existe.")
    else:
        print_error("ap0 NO existe (Este es el problema principal).")

    # 3. Check Services
    print("\n3. Verificando servicios systemd...")
    services = {
        "hostapd": "Punto de Acceso",
        "dnsmasq": "Servidor DHCP/DNS",
        "wifi-ap": "Script de creación ap0"
    }
    for svc, desc in services.items():
        out, _, _ = run_cmd(f"systemctl is-active {svc}")
        if out == "active":
            print_success(f"{svc} ({desc}) está ACTIVO.")
        elif out == "activating":
            print_warning(f"{svc} ({desc}) está REINICIÁNDOSE constantemente.")
        else:
            print_error(f"{svc} ({desc}) está INACTIVO.")

    # 4. Check for Conflicts
    print("\n4. Verificando conflictos con NetworkManager...")
    out, _, _ = run_cmd("cat /etc/NetworkManager/NetworkManager.conf")
    if "unmanaged-devices=interface-name:ap0" in out:
        print_success("NetworkManager está configurado para ignorar ap0.")
    else:
        print_error("NetworkManager NO ignora ap0. Esto causará conflictos.")

    # 5. Diagnostic Summary & Recommended Fixes
    print_header("RESUMEN DE DIAGNÓSTICO")
    
    fixes = []
    if not has_ap0:
        fixes.append("Ejecutar manualmente: sudo /usr/local/bin/setup-wifi-ap.sh")
        fixes.append("Verificar logs de creación: journalctl -u wifi-ap")
    
    out, _, _ = run_cmd("systemctl is-active hostapd")
    if out != "active":
        fixes.append("Verificar configuración de hostapd: /etc/hostapd/hostapd.conf")
        fixes.append("Verificar logs de hostapd: journalctl -u hostapd -n 50")

    if "unmanaged-devices=interface-name:ap0" not in out:
        fixes.append("Agregar 'unmanaged-devices=interface-name:ap0' a /etc/NetworkManager/NetworkManager.conf")

    if fixes:
        print("Se detectaron problemas. Pasos recomendados:")
        for i, fix in enumerate(fixes, 1):
            print(f" {i}. {fix}")
    else:
        print_success("No se detectaron problemas evidentes en la configuración de bajo nivel.")

if __name__ == "__main__":
    debug_dual_mode()
