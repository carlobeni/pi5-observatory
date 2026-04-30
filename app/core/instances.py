from app.modules.camera.camera_manager import CameraManager
from app.modules.camera.camera_worker import CameraWorker
from app.modules.streaming.remote_pusher import RemotePusher

# Global instances to be shared across the app
camera_manager = CameraManager()
camera_worker = CameraWorker(camera_manager)
remote_pusher = RemotePusher()
