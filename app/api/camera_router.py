import cv2
from fastapi import APIRouter, Response, Request
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
    from app.main import logger
    from app.core.instances import camera_manager, camera_worker
    logger.info(f"Petición de TOGGLE recibida: enable={enable}")
    if not camera_manager.camera:
        logger.warning("Intento de toggle sin cámara conectada")
        return {"status": "error", "message": "Cámara no conectada"}
    
    camera_worker.user_enabled = enable
    
    if enable:
        logger.info("Forzando reinicio de captura...")
        try:
            camera_manager.stop_capture()
            time.sleep(0.2)
            if camera_manager.start_capture():
                camera_worker._capture_started = True
                return {"status": "ok", "capturing": True}
            else:
                return {"status": "error", "message": "No se pudo iniciar la captura"}
        except Exception as e:
            logger.error(f"Error forzando captura: {e}")
            return {"status": "error", "message": str(e)}
    else:
        logger.info("Deteniendo captura...")
        camera_worker.user_enabled = False
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

@router.post("/snapshot/save")
async def save_snapshot(request: Request):
    try:
        from app.core.supabase_client import supabase, bucket_name
        from app.main import logger
        
        if not supabase:
            logger.error("Supabase client not initialized")
            return {"status": "error", "message": "Supabase no está configurado"}

        data = await request.json()
        image_data = data.get("image") # base64 string
        if not image_data:
            return {"status": "error", "message": "No image data provided"}
        
        # Clean base64 data
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        import base64
        import uuid
        from datetime import datetime
        
        try:
            img_bytes = base64.b64decode(image_data)
        except Exception as e:
            return {"status": "error", "message": f"Error decoding image: {e}"}
        
        # Generate names
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        file_name = f"obs_{timestamp}_{file_id}.jpg"
        storage_path = f"images/{file_name}"
        
        # Get current camera parameters for metadata
        from app.core.instances import camera_manager
        from app.core.frame_buffer import frame_buffer
        
        cam_config = camera_manager.config.get("camera", {})
        frame_meta = frame_buffer.get_metadata()
        
        metadata = {
            "app": "pi5-observatory",
            "version": "1.0",
            "camera_settings": {
                "exposure_us": cam_config.get("initial_exposure_us"),
                "gain": cam_config.get("initial_gain"),
                "bin": cam_config.get("initial_bin"),
                "width": cam_config.get("initial_width"),
                "height": cam_config.get("initial_height")
            },
            "sensor_data": {
                "temperature": frame_meta.get("temperature"),
                "fps": frame_meta.get("fps")
            }
        }
        
        # 1. Upload to Storage
        logger.info(f"Uploading {file_name} to Supabase Storage bucket '{bucket_name}' in 'images/' folder...")
        try:
            supabase.storage.from_(bucket_name).upload(
                path=storage_path,
                file=img_bytes,
                file_options={"content-type": "image/jpeg"}
            )
        except Exception as e:
            logger.error(f"Storage upload failed: {e}")
            return {"status": "error", "message": f"Error en Storage: {str(e)}"}
            
        # 2. Insert to Database
        logger.info(f"Inserting record for {file_name} into live_captures table...")
        try:
            supabase.table("live_captures").insert({
                "file_name": file_name,
                "storage_bucket": bucket_name,
                "storage_path": storage_path,
                "obs_datetime": now.isoformat(),
                "metadata_json": metadata
            }).execute()
        except Exception as e:
            logger.error(f"Database insert failed: {e}")
            return {"status": "error", "message": f"Error en Base de Datos: {str(e)}"}
        
        logger.info(f"Snapshot {file_name} saved successfully.")
        return {"status": "ok", "message": "Imagen guardada en Supabase con éxito"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

