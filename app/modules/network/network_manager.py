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
        """Verify if the provided password is correct by comparing against system shadow file."""
        if not password:
            return False
        try:
            user = getpass.getuser()
            # We need sudo -S to read /etc/shadow using the provided password
            proc = subprocess.Popen(["sudo", "-S", "grep", f"^{user}:", "/etc/shadow"], 
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(input=password + "\n", timeout=5)
            
            if proc.returncode != 0 or not stdout:
                logger.error(f"[AUTH] No se pudo leer el archivo shadow para {user}")
                return False
            
            shadow_line = stdout.strip()
            parts = shadow_line.split(':')
            if len(parts) < 2:
                return False
                
            hashed_password = parts[1]
            
            # Compare using crypt
            is_valid = (crypt.crypt(password, hashed_password) == hashed_password)
            
            if is_valid:
                logger.info(f"[AUTH] Validación EXITOSA para usuario: {user}")
            else:
                logger.warning(f"[AUTH] Validación FALLIDA para usuario: {user}")
                
            return is_valid
        except Exception as e:
            logger.error(f"[AUTH] Error en validación criptográfica: {e}")
            return False
        
    def _run_command(self, cmd, password=None):
        try:
            if password:
                # Run with sudo and provide password via stdin
                sudo_cmd = ["sudo", "-S"] + cmd
                result = subprocess.run(sudo_cmd, input=f"{password}\n", capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}\nError: {e.stderr}")
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

    def connect_wifi(self, ssid, password, interface="wlan0"):
        cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", interface]
        if password:
            cmd.extend(["password", password])
        
        output = self._run_command(cmd)
        return output is not None

    def disconnect_wifi(self, interface="wlan0", admin_password=None):
        cmd = ["nmcli", "device", "disconnect", interface]
        # Use _run_command which handles sudo if password is provided
        output = self._run_command(cmd, admin_password)
        return output is not None

    def get_hotspot_config(self, admin_password=None):
        config = {"ssid": "Desconocido", "password": "••••••••"}
        
        # 1. Try to get SSID via 'iw' (doesn't need sudo usually)
        try:
            ssid_out = self._run_command(["iw", "dev", "ap0", "info"])
            if ssid_out:
                match = re.search(r"ssid (.*)", ssid_out)
                if match:
                    config["ssid"] = match.group(1).strip()
        except:
            pass

        # 2. If admin_password is provided, read the real password from hostapd.conf
        if admin_password:
            try:
                content = self._run_command(["cat", "/etc/hostapd/hostapd.conf"], admin_password)
                if content:
                    pass_match = re.search(r"^wpa_passphrase=(.*)$", content, re.MULTILINE)
                    if pass_match: config["password"] = pass_match.group(1).strip()
                    
                    # Also refresh SSID from file just in case
                    ssid_match = re.search(r"^ssid=(.*)$", content, re.MULTILINE)
                    if ssid_match: config["ssid"] = ssid_match.group(1).strip()
            except Exception as e:
                logger.error(f"Error reading hostapd config with sudo: {e}")
                
        return config

    def manage_hotspot(self, ssid=None, password=None, interface="ap0", action="up", admin_password=None):
        # We now use the custom hostapd + dnsmasq setup
        if action == "up":
            # If SSID or password provided, update the config file
            if ssid or password:
                try:
                    # We need sudo to write to /etc/hostapd/hostapd.conf
                    # Create a temporary file and then move it with sudo
                    temp_conf = "/tmp/hostapd_new.conf"
                    with open("/etc/hostapd/hostapd.conf", "r") as f:
                        lines = f.readlines()
                    
                    with open(temp_conf, "w") as f:
                        for line in lines:
                            if line.startswith("ssid=") and ssid:
                                f.write(f"ssid={ssid}\n")
                            elif line.startswith("wpa_passphrase=") and password:
                                f.write(f"wpa_passphrase={password}\n")
                            else:
                                f.write(line)
                    
                    # Move temp file to destination with sudo
                    self._run_command(["mv", temp_conf, "/etc/hostapd/hostapd.conf"], admin_password)
                    logger.info("Updated hostapd.conf with new credentials.")
                except Exception as e:
                    logger.error(f"Failed to update hostapd.conf: {e}")

            # Ensure the interface exists first
            self._run_command(["systemctl", "start", "wifi-ap.service"], admin_password)
            # Start/Restart services
            self._run_command(["systemctl", "restart", "hostapd"], admin_password)
            self._run_command(["systemctl", "restart", "dnsmasq"], admin_password)
            return True
        else:
            self._run_command(["systemctl", "stop", "hostapd"], admin_password)
            self._run_command(["systemctl", "stop", "dnsmasq"], admin_password)
            return True

    def get_current_connection_details(self, interface="wlan0"):
        output = self._run_command(["nmcli", "-t", "-f", "IP4.ADDRESS,IP4.GATEWAY", "device", "show", interface])
        if not output:
            return {}
        
        details = {}
        for line in output.strip().split("\n"):
            key, val = line.split(":", 1)
            details[key.lower()] = val
        return details
