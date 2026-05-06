import threading
import time
import socket
import logging
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
try:
    from luma.oled.device import ssd1306
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class OLEDManager:
    def __init__(self, camera_manager=None, network_manager=None):
        self.camera_manager = camera_manager
        self.network_manager = network_manager
        self.device = None
        self.running = False
        self.thread = None
        
        if not LUMA_AVAILABLE:
            logger.error("[OLED] Librerías luma.oled no encontradas.")
            return

        try:
            # Intentar inicializar I2C en el bus 1, dirección 0x3C
            serial = i2c(port=1, address=0x3C)
            self.device = ssd1306(serial)
            logger.info("[OLED] Pantalla inicializada correctamente en 0x3C.")
        except Exception as e:
            logger.warning(f"[OLED] No se pudo encontrar pantalla en 0x3C: {e}. Reintentando en 0x3D...")
            try:
                serial = i2c(port=1, address=0x3D)
                self.device = ssd1306(serial)
                logger.info("[OLED] Pantalla inicializada correctamente en 0x3D.")
            except Exception as e2:
                logger.error(f"[OLED] Error final inicializando pantalla: {e2}")

    def start(self):
        if self.device and not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True, name="OLEDUpdateThread")
            self.thread.start()
            logger.info("[OLED] Hilo de actualización iniciado.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.device:
            try:
                self.device.clear()
            except:
                pass

    def _draw_icons(self, draw, x, y, icon_type):
        """Dibuja pequeños iconos de 10x10 píxeles."""
        if icon_type == "ip":
            # Icono de red/mundo
            draw.ellipse((x, y+1, x+8, y+9), outline="white")
            draw.line((x+4, y+1, x+4, y+9), fill="white")
            draw.line((x, y+5, x+8, y+5), fill="white")
        elif icon_type == "wifi":
            # Ondas de WiFi
            draw.arc((x, y, x+9, y+9), 225, 315, fill="white")
            draw.arc((x+2, y+2, x+7, y+7), 225, 315, fill="white")
            draw.point((x+4, y+6), fill="white")
        elif icon_type == "cam":
            # Cuerpo de cámara
            draw.rectangle((x, y+2, x+9, y+8), outline="white")
            draw.rectangle((x+3, y+4, x+6, y+7), outline="white") # Lente
            draw.point((x+1, y+1), fill="white") # Botón
        elif icon_type == "cpu":
            # Microchip
            draw.rectangle((x+2, y+2, x+7, y+7), fill="white")
            for i in range(3):
                draw.line((x+3+i*2, y, x+3+i*2, y+1), fill="white")
                draw.line((x+3+i*2, y+8, x+3+i*2, y+9), fill="white")
                draw.line((x, y+3+i*2, x+1, y+3+i*2), fill="white")
                draw.line((x+8, y+3+i*2, x+9, y+3+i*2), fill="white")

    def _get_ip(self):
        try:
            if self.network_manager and self.network_manager.is_hotspot_active():
                return "192.168.4.1"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Sin Red"

    def _get_temp(self):
        try:
            res = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True)
            return res.stdout.replace("temp=", "").replace("'C\n", "°C")
        except:
            return "--°C"

    def _update_loop(self):
        while self.running:
            try:
                ip = self._get_ip()
                temp = self._get_temp()
                
                cam_status = "DISC"
                if self.camera_manager:
                    if self.camera_manager.camera:
                        cam_status = "BUSY" if self.camera_manager.is_capturing else "IDLE"
                    else:
                        cam_status = "OFF"
                
                ap_status = "DOWN"
                if self.network_manager and self.network_manager.is_hotspot_active():
                    ap_status = "UP"

                with canvas(self.device) as draw:
                    # Título centrado
                    draw.text((30, 0), "ASTRO PI5", fill="white")
                    draw.line((0, 12, 128, 12), fill="white")
                    
                    # IP
                    self._draw_icons(draw, 0, 16, "ip")
                    draw.text((15, 16), f"IP: {ip}", fill="white")
                    
                    # WiFi Zone
                    self._draw_icons(draw, 0, 28, "wifi")
                    draw.text((15, 28), f"ZONE: {ap_status}", fill="white")
                    
                    # Camera
                    self._draw_icons(draw, 0, 40, "cam")
                    draw.text((15, 40), f"CAM:  {cam_status}", fill="white")
                    
                    # CPU
                    self._draw_icons(draw, 0, 52, "cpu")
                    draw.text((15, 52), f"CPU:  {temp}", fill="white")
                    
                time.sleep(3)
            except Exception as e:
                logger.error(f"[OLED] Error en loop: {e}")
                time.sleep(5)
