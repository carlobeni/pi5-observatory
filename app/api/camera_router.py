import cv2
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from app.core.frame_buffer import frame_buffer
import time

router = APIRouter()

def gen_frames():
    """Generator for MJPEG stream."""
    while True:
        # Use pre-encoded JPEG from buffer to save CPU
        jpeg_buffer, metadata = frame_buffer.get_jpeg_frame(timeout=1.0)
        if jpeg_buffer is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_buffer + b'\r\n')
        else:
            time.sleep(0.1)

@router.get("/stream")
async def video_feed():
    return StreamingResponse(gen_frames(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/status")
async def get_status():
    from app.core.instances import camera_manager
    metadata = frame_buffer.get_metadata()
    
    # Get current resolution and properties
    width, height = 0, 0
    max_width, max_height = 0, 0
    if camera_manager.camera:
        try:
            roi = camera_manager.camera.get_roi_format()
            width, height = roi[0], roi[1]
            props = camera_manager.get_properties()
            max_width = props.get("MaxWidth", 0)
            max_height = props.get("MaxHeight", 0)
        except Exception as e:
            from app.modules.camera.camera_manager import logger as cam_logger
            cam_logger.error(f"Error fetching camera ROI/Properties: {e}")
            pass

    return {
        "connected": camera_manager.camera is not None,
        "is_capturing": camera_manager.is_capturing,
        "fps": metadata["fps"],
        "temperature": metadata["temperature"],
        "timestamp": metadata["timestamp"],
        "width": width,
        "height": height,
        "max_width": max_width,
        "max_height": max_height
    }

@router.get("/remote_status")
async def get_remote_status():
    from app.core.instances import camera_manager
    config = camera_manager.config.get("streaming", {})
    return {
        "enabled": config.get("remote_enabled", False),
        "url": config.get("remote_url", "")
    }

@router.post("/toggle")
async def toggle_capture(enable: bool):
    from app.core.instances import camera_manager, camera_worker
    if not camera_manager.camera:
        return {"status": "error", "message": "Cámara no conectada"}
    
    camera_worker.user_enabled = enable
    
    if enable:
        # Worker will see user_enabled=True and start capture
        return {"status": "ok", "capturing": True}
    else:
        # Worker will see user_enabled=False and stop capture
        camera_manager.stop_capture()
        camera_worker._capture_started = False
        return {"status": "ok", "capturing": False}

@router.post("/resolution")
async def set_resolution(width: int, height: int, bin: int = 1):
    from app.core.instances import camera_manager
    if not camera_manager.camera:
        return {"status": "error", "message": "Camera not connected"}
    
    # Stop capture before changing ROI
    from app.core.instances import camera_worker
    camera_worker._capture_started = False
    camera_manager.stop_capture()
    
    camera_manager.config["camera"]["initial_width"] = width
    camera_manager.config["camera"]["initial_height"] = height
    camera_manager.config["camera"]["initial_bin"] = bin
    
    camera_manager.apply_settings(camera_manager.config["camera"])
    
    # Worker will restart capture automatically
    return {"status": "ok", "width": width, "height": height}

@router.post("/control")
async def set_control(control: str, value: int):
    from app.core.instances import camera_manager
    # Map control strings to ASI constants
    import zwoasi as asi
    mapping = {
        "exposure": asi.ASI_EXPOSURE,
        "gain": asi.ASI_GAIN,
        "bandwidth": asi.ASI_BANDWIDTHOVERLOAD
    }
    
    if control in mapping:
        if not camera_manager.camera:
            return {"status": "error", "message": "Camera not connected"}
        camera_manager.set_control(mapping[control], value)
        return {"status": "ok", "control": control, "value": value}
    return {"status": "error", "message": "Unknown control"}
