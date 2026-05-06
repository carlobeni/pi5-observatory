import os
import sys
import signal
import logging
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.instances import camera_manager, camera_worker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CameraWorker...")
    camera_worker.start()
    yield
    # Shutdown
    logger.info("Stopping CameraWorker...")
    camera_worker.stop()
    camera_worker.join(timeout=2)
    logger.info("Server shutdown complete.")

app = FastAPI(title="Pi5 Observatory", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
from app.api.camera_router import router as camera_router
from app.api.network_router import router as network_router
app.include_router(camera_router, prefix="/api/camera", tags=["camera"])
app.include_router(network_router, prefix="/api/network", tags=["network"])

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def listen_for_quit():
    """Listens for Ctrl+Q (ASCII 17) in the terminal."""
    if not sys.stdin.isatty():
        return
    import termios
    import tty
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            char = sys.stdin.read(1)
            if (char == '\x11'): # Ctrl+Q
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                print("\n")
                logger.info("Ctrl+Q detectado. Cerrando servidor...")
                os.kill(os.getpid(), signal.SIGINT)
                break
    except Exception as e:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Start the Ctrl+Q listener thread
    quit_thread = threading.Thread(target=listen_for_quit, daemon=True)
    quit_thread.start()
    
    port = config.get("streaming", {}).get("local_port", 8000)
    # uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    # Using a config object to allow better signal handling
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info", loop="uvloop")
    server = uvicorn.Server(config)
    server.run()
