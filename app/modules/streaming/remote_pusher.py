import threading
import time
import cv2
import asyncio
import websockets
import logging
import yaml
from app.core.frame_buffer import frame_buffer

logger = logging.getLogger(__name__)

class RemotePusher(threading.Thread):
    def __init__(self, config_path="config.yaml"):
        super().__init__(daemon=True)
        self.config = self._load_config(config_path)
        self.running = False
        self._stop_event = threading.Event()

    def _load_config(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def stop(self):
        self._stop_event.set()
        self.running = False

    async def _push_loop(self):
        conf = self.config.get("streaming", {})
        if not conf.get("remote_enabled", False):
            logger.info("Remote streaming disabled in config.")
            return

        uri = conf.get("remote_url")
        auth_key = conf.get("remote_auth_key")
        
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info(f"Connected to remote server: {uri}")
                    
                    # Authenticate if needed
                    if auth_key:
                        await websocket.send(f"AUTH:{auth_key}")
                    
                    while not self._stop_event.is_set():
                        jpeg_buffer, metadata = frame_buffer.get_jpeg_frame(timeout=1.0)
                        if jpeg_buffer is not None:
                            # Send the pre-encoded JPEG
                            await websocket.send(jpeg_buffer)
                            
                            # Limit FPS for remote to save bandwidth
                            await asyncio.sleep(1.0 / self.config["camera"].get("fps_target", 15))
                        else:
                            await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Remote pusher error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    def run(self):
        logger.info("RemotePusher thread started.")
        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._push_loop())
        logger.info("RemotePusher thread stopped.")
