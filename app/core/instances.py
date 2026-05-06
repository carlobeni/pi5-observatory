from app.modules.camera.camera_manager import CameraManager
from app.modules.camera.camera_worker import CameraWorker
from app.modules.streaming.remote_pusher import RemotePusher
from app.modules.network.network_manager import NetworkManager
from app.modules.display.oled_manager import OLEDManager

# Global instances to be shared across the app
camera_manager = CameraManager()
camera_worker = CameraWorker(camera_manager)
remote_pusher = RemotePusher()
network_manager = NetworkManager()
oled_manager = OLEDManager(camera_manager, network_manager)
