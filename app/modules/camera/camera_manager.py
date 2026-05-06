import os
import zwoasi as asi
import yaml
import logging

logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self, config_path="config.yaml"):
        self.camera = None
        self.is_capturing = False
        self.properties = {}
        self.config = self._load_config(config_path)
        self._init_sdk()

    def _load_config(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _init_sdk(self):
        try:
            # Try common paths for the SDK library
            lib_path = os.environ.get("ZWO_ASI_LIB", "/usr/local/lib/libASICamera2.so")
            asi.init(lib_path)
            logger.info("[CAMERA] OK: SDK ZWO ASI inicializado.")
        except Exception as e:
            logger.error(f"[CAMERA] ERR: Falló inicialización del SDK: {e}")
            raise

    def get_detected_cameras(self):
        return asi.get_num_cameras()

    def connect(self):
        try:
            num_cameras = self.get_detected_cameras()
            if num_cameras == 0:
                logger.warning("[CAMERA] ERR: No se detectaron cámaras ZWO.")
                return False

            idx = self.config["camera"]["device_index"]
            self.camera = asi.Camera(idx)
            self.properties = self.camera.get_camera_property()
            logger.info(f"[CAMERA] OK: Conectado a {self.properties.get('Name')}")
            
            # Apply initial settings
            self.apply_settings(self.config["camera"])
            return True
        except Exception as e:
            logger.error(f"[CAMERA] ERR: Error al conectar: {e}")
            return False

    def apply_settings(self, settings):
        if not self.camera:
            logger.warning("No camera object to apply settings to.")
            return False

        try:
            # ROI and format
            width = settings.get("initial_width", 640)
            height = settings.get("initial_height", 480)
            img_bin = settings.get("initial_bin", 1)
            img_type = settings.get("image_type", asi.ASI_IMG_RAW8)
            
            # Stop capture if running
            try: self.camera.stop_video_capture()
            except: pass
            
            self.camera.set_image_type(img_type)
            self.camera.set_roi_format(width, height, img_bin, img_type)

            # Controls
            self.camera.set_control_value(asi.ASI_EXPOSURE, settings.get("initial_exposure_us", 10000))
            self.camera.set_control_value(asi.ASI_GAIN, settings.get("initial_gain", 50))
            
            logger.info(f"Camera settings applied: {width}x{height}, Type: {img_type}")
            return True
        except Exception as e:
            logger.error(f"Error applying camera settings: {e}")
            return False

    def start_capture(self):
        if self.camera:
            try:
                self.camera.start_video_capture()
                self.is_capturing = True
                logger.info("[CAMERA] OK: Captura de video iniciada.")
                return True
            except Exception as e:
                if "video mode has been started" in str(e).lower():
                    self.is_capturing = True
                    return True
                logger.error(f"[CAMERA] ERR: Falló inicio de captura: {e}")
                return False
        return False

    def stop_capture(self):
        if self.camera:
            try:
                self.camera.stop_video_capture()
                self.is_capturing = False
                logger.info("Video capture stopped.")
            except:
                pass

    def get_properties(self):
        return self.properties

    def get_frame(self, timeout):
        if self.camera:
            try:
                return self.camera.capture_video_frame(timeout=timeout)
            except asi.ZWO_IOError:
                return None
        return None

    def get_controls(self):
        if not self.camera:
            return {}
        return self.camera.get_controls()

    def set_control(self, control_type, value):
        if self.camera:
            try:
                self.camera.set_control_value(control_type, value)
                # Update config to keep in sync
                if control_type == asi.ASI_EXPOSURE:
                    self.config["camera"]["initial_exposure_us"] = value
                elif control_type == asi.ASI_GAIN:
                    self.config["camera"]["initial_gain"] = value
            except Exception as e:
                logger.error(f"Error setting control {control_type}: {e}")

    def get_temperature(self):
        if self.camera:
            try:
                return self.camera.get_control_value(asi.ASI_TEMPERATURE)[0] / 10.0
            except:
                return 0.0
        return 0.0

    def close(self):
        if self.camera:
            self.camera.close()
            self.camera = None
            logger.info("Camera closed.")
