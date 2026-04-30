import threading
import time
import logging
import numpy as np
import cv2
from app.core.frame_buffer import frame_buffer

logger = logging.getLogger(__name__)

class CameraWorker(threading.Thread):
    def __init__(self, camera_manager):
        super().__init__(daemon=True)
        self.camera_manager = camera_manager
        self.running = False
        self.user_enabled = True # New flag to track user intent
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()
        self.running = False

    def run(self):
        logger.info("CameraWorker thread started.")
        self.running = True
        self._capture_started = False
        
        # Initial connection attempt
        if not self.camera_manager.connect():
            logger.error("Initial camera connection failed. Will retry in loop.")

        frame_count = 0
        t0 = time.perf_counter()
        fps = 0.0
        fps_window = 30
        
        last_meta_poll = 0
        cached_exposure = 10000
        cached_temp = 0.0

        while not self._stop_event.is_set():
            if not self.camera_manager.camera:
                time.sleep(2)
                self.camera_manager.connect()
                continue

            try:
                # Poll exposure and temperature only every 1 second to save USB bandwidth
                now = time.time()
                if now - last_meta_poll > 1.0:
                    try:
                        cached_exposure = self.camera_manager.camera.get_control_value(0)[0] # ASI_EXPOSURE
                        cached_temp = self.camera_manager.get_temperature()
                        last_meta_poll = now
                    except:
                        pass
                
                timeout_ms = int(cached_exposure / 1000 * 2 + 500)
                
                # Start capture if not already started and user wants it
                if self.user_enabled and not self._capture_started:
                    if self.camera_manager.start_capture():
                        self._capture_started = True
                
                # If user disabled, ensure we are stopped and skip frame capture
                if not self.user_enabled:
                    if self._capture_started:
                        self.camera_manager.stop_capture()
                        self._capture_started = False
                    time.sleep(0.5)
                    continue

                frame = self.camera_manager.get_frame(timeout=timeout_ms)
                
                if frame is not None:
                    frame_count += 1
                    
                    # FPS Calculation
                    if frame_count >= fps_window:
                        t1 = time.perf_counter()
                        fps = frame_count / (t1 - t0)
                        t0 = t1
                        frame_count = 0
                    
                    # Process frame (Convert to numpy if needed)
                    props = self.camera_manager.camera.get_roi_format()
                    width, height = props[0], props[1]
                    
                    data = np.frombuffer(frame, dtype=np.uint8)
                    
                    # Handle different image types based on data size
                    if data.size == width * height:
                        img = data.reshape((height, width))
                    elif data.size == width * height * 3:
                        img = data.reshape((height, width, 3))
                    elif data.size == width * height * 2:
                        img = data.view(np.uint16).reshape((height, width))
                        img = (img >> 8).astype(np.uint8)
                    else:
                        logger.error(f"Unexpected frame size: {data.size} for {width}x{height}")
                        continue
                    
                    # Update buffer
                    # Encode JPEG once here to avoid re-encoding in API for each client
                    jpeg_quality = self.camera_manager.config["camera"].get("quality_jpeg", 80)
                    _, jpeg_buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
                    
                    frame_buffer.update_frame(img, jpeg_frame=jpeg_buffer.tobytes(), fps=fps, temperature=cached_temp)
                else:
                    # Possible disconnection
                    logger.warning("Captured frame is None. Checking camera...")
                    if self.camera_manager.get_detected_cameras() == 0:
                        logger.error("Camera lost connection.")
                        self.camera_manager.camera = None
            
            except Exception as e:
                logger.error(f"Error in CameraWorker loop: {e}")
                time.sleep(1)

        self.camera_manager.stop_capture()
        self.camera_manager.close()
        logger.info("CameraWorker thread stopped.")
