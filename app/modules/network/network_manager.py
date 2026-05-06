import subprocess
import logging
import re
import crypt
import getpass
import os

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self):
        pass

    def verify_admin_password(self, password):
        """Verify if the provided password matches the ADMIN_PASSWORD in .env."""
        if not password:
            return False
        
        env_pass = os.getenv("ADMIN_PASSWORD")
        if not env_pass:
            logger.warning("[AUTH] ADMIN_PASSWORD no está configurado en .env. Usando verificación de sistema fallback...")
            # Fallback to a simple check if you want, or just return False
            return False
            
        is_valid = (password == env_pass)
        
        if is_valid:
            logger.info(f"[AUTH] Validación EXITOSA mediante .env")
        else:
            logger.warning(f"[AUTH] Validación FALLIDA")
            
        return is_valid
        
    def _run_command(self, cmd, password=None):
        try:
            # Check if we are running as root
            is_root = os.getuid() == 0
            
            # Use provided password or environment variable
            admin_pass = password or os.getenv("ADMIN_PASSWORD")
            
            if is_root:
                # No need for sudo if already root
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            elif admin_pass:
                # Run with sudo and provide password via stdin
                sudo_cmd = ["sudo", "-S"] + cmd
                result = subprocess.run(sudo_cmd, input=f"{admin_pass}\n", capture_output=True, text=True, check=True)
            else:
                # Try running without sudo (might fail if permission needed)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return None

    def get_interfaces(self):
        output = self._run_command(["nmcli", "device", "status"])
        if not output:
            return []
        
        interfaces = []
        lines = output.strip().split("\n")[1:]
        for line in lines:
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 3:
                interfaces.append({
                    "device": parts[0],
                    "type": parts[1],
                    "state": parts[2],
                    "connection": parts[3] if len(parts) > 3 else "--"
                })
        
        # Manually check for ap0 if not in nmcli (since it's unmanaged)
        ap0_check = self._run_command(["ip", "link", "show", "ap0"])
        if ap0_check:
            state = "up" if "UP" in ap0_check else "down"
            interfaces.append({
                "device": "ap0",
                "type": "wifi (AP)",
                "state": state,
                "connection": "Hostapd AP"
            })
        return interfaces

    def scan_wifi(self, interface="wlan0"):
        # We might need to rescan first
        self._run_command(["nmcli", "device", "wifi", "rescan"])
        output = self._run_command(["nmcli", "-t", "-f", "SSID,BARS,SECURITY,SIGNAL", "device", "wifi", "list", "ifname", interface])
        if not output:
            return []
        
        networks = []
        for line in output.strip().split("\n"):
            parts = line.split(":")
            if len(parts) >= 4 and parts[0]:
                networks.append({
                    "ssid": parts[0],
                    "bars": parts[1],
                    "security": parts[2],
                    "signal": parts[3]
                })
        return networks

    def connect_wifi(self, ssid, password, interface="wlan0", admin_password=None):
        cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", interface]
        if password:
            cmd.extend(["password", password])
        
        output = self._run_command(cmd)
        
        # ALWAYS try to sync/restart hotspot after a connection attempt to ensure availability
        if admin_password:
            if output is not None:
                logger.info(f"[NETWORK] OK: Conectado a {ssid}. Sincronizando Hotspot...")
            else:
                logger.warning(f"[NETWORK] ERR: Falló conexión a {ssid}. Reestableciendo Hotspot en modo seguro...")
            
            import time
            time.sleep(2)
            # Re-establish hotspot regardless of WiFi success
            self.manage_hotspot(action="up", admin_password=admin_password)
            
        return output is not None

    def disconnect_wifi(self, interface="wlan0", admin_password=None):
        cmd = ["nmcli", "device", "disconnect", interface]
        # Use _run_command which handles sudo if password is provided
        output = self._run_command(cmd, admin_password)
        return output is not None

    def get_hotspot_config(self, admin_password=None):
        # Default from environment
        config = {
            "ssid": os.getenv("HOTSPOT_SSID", "ASTRO PI5"), 
            "password": "••••••••"
        }
        
        # 1. Try to get real SSID via 'iw'
        try:
            ssid_out = self._run_command(["iw", "dev", "ap0", "info"])
            if ssid_out:
                match = re.search(r"ssid (.*)", ssid_out)
                if match:
                    config["ssid"] = match.group(1).strip()
        except:
            pass

        # 2. If admin_password is provided or we are root, read the real password
        is_root = os.getuid() == 0
        if admin_password or is_root:
            try:
                content = self._run_command(["cat", "/etc/hostapd/hostapd.conf"], admin_password)
                if content:
                    pass_match = re.search(r"^wpa_passphrase=(.*)$", content, re.MULTILINE)
                    if pass_match:
                        val = pass_match.group(1).strip()
                        # Only use if it's not the masked string
                        if val and "•" not in val:
                            config["password"] = val
                        else:
                            # Fallback to .env if file is masked
                            config["password"] = os.getenv("HOTSPOT_PASS", "••••••••")
                    
                    # Also refresh SSID from file
                    ssid_match = re.search(r"^ssid=(.*)$", content, re.MULTILINE)
                    if ssid_match: config["ssid"] = ssid_match.group(1).strip()
            except Exception as e:
                logger.error(f"Error reading hostapd config: {e}")
                
        return config

    def manage_hotspot(self, ssid=None, password=None, interface="ap0", action="up", admin_password=None):
        # We now use the custom hostapd + dnsmasq setup
        is_root = os.getuid() == 0
        
        if action == "up":
            # If SSID or password provided, update the config file
            if ssid or (password and "•" not in password): # Don't write masked password
                try:
                    # We need permission to read and write to /etc/hostapd/hostapd.conf
                    content = self._run_command(["cat", "/etc/hostapd/hostapd.conf"], admin_password)
                    if not content:
                        logger.error("Could not read hostapd.conf")
                        return False
                        
                    lines = content.splitlines()
                    
                    temp_conf = "/tmp/hostapd_new.conf"
                    with open(temp_conf, "w") as f:
                        for line in lines:
                            if line.startswith("ssid=") and ssid:
                                f.write(f"ssid={ssid}\n")
                            elif line.startswith("wpa_passphrase=") and password and "•" not in password:
                                f.write(f"wpa_passphrase={password}\n")
                            else:
                                f.write(line + "\n")
                    
                    # Move temp file to destination
                    self._run_command(["mv", temp_conf, "/etc/hostapd/hostapd.conf"], admin_password)
                    logger.info("Updated hostapd.conf with new credentials.")
                except Exception as e:
                    logger.error(f"Failed to update hostapd.conf: {e}")

            logger.info("[HOTSPOT] INFO: Reiniciando servicios para aplicar cambios...")
            self._run_command(["systemctl", "restart", "wifi-ap.service"], admin_password)
            
            import time
            time.sleep(2)
            
            self._run_command(["systemctl", "restart", "hostapd"], admin_password)
            self._run_command(["systemctl", "restart", "dnsmasq"], admin_password)
            
            is_active = self.is_hotspot_active()
            if is_active:
                logger.info(f"[HOTSPOT] OK: Zona WiFi Activa (SSID: {ssid if ssid else 'Actual'})")
            else:
                logger.error("[HOTSPOT] ERR: No se pudo iniciar el servicio")
            return is_active
        else:
            self._run_command(["systemctl", "stop", "hostapd"], admin_password)
            self._run_command(["systemctl", "stop", "dnsmasq"], admin_password)
            logger.info("[HOTSPOT] OFF: Zona WiFi desactivada")
            return False

    def is_hotspot_active(self):
        # Check if hostapd service is active
        try:
            # We don't use self._run_command because it logs errors on non-zero exit codes
            result = subprocess.run(["systemctl", "is-active", "hostapd"], capture_output=True, text=True)
            return result.stdout.strip() == "active"
        except Exception:
            return False

    def get_current_connection_details(self, interface="wlan0"):
        output = self._run_command(["nmcli", "-t", "-f", "IP4.ADDRESS,IP4.GATEWAY", "device", "show", interface])
        if not output:
            return {}
        
        details = {}
        for line in output.strip().split("\n"):
            key, val = line.split(":", 1)
            details[key.lower()] = val
        return details
