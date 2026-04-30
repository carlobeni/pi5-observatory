import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.core.instances import camera_manager, camera_worker, remote_pusher
from app.api.camera_router import router as camera_router
from app.api.network_router import router as network_router

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CameraWorker...")
    camera_worker.start()
    # remote_pusher.start() # Momentarily disabled by user request
    yield
    # Shutdown
    logger.info("Stopping CameraWorker...")
    camera_worker.stop()
    # remote_pusher.stop() # Momentarily disabled by user request
    camera_worker.join()
    # remote_pusher.join() # Momentarily disabled by user request

app = FastAPI(title="Pi5 Observatory", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(camera_router, prefix="/api/camera", tags=["camera"])
app.include_router(network_router, prefix="/api/network", tags=["network"])

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    port = config.get("streaming", {}).get("local_port", 8000)
    uvicorn.run(app, host="0.0.0.0", port=port)
