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
from fastapi.responses import RedirectResponse, Response

# Load environment variables
load_dotenv()
from app.core.instances import camera_manager, camera_worker, network_manager, oled_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CameraWorker...")
    camera_worker.start()
    
    # Start OLED Display
    logger.info("Starting OLEDManager...")
    oled_manager.start()
    oled_manager.set_message("SISTEMA ONLINE")
    
    # Auto-activate Hotspot on run
    try:
        logger.info("[STARTUP] Activando Zona WiFi automáticamente...")
        # No password needed if running as service/root
        network_manager.manage_hotspot(action="up")
    except Exception as e:
        logger.error(f"[STARTUP] Error iniciando Hotspot: {e}")
        
    yield
    # Shutdown
    logger.info("Stopping OLEDManager...")
    oled_manager.set_message("APAGANDO...")
    oled_manager.stop()
    
    logger.info("Stopping CameraWorker...")
    camera_worker.stop()
    camera_worker.join(timeout=2)
    logger.info("Server shutdown complete.")

app = FastAPI(title="ASTRO PI5", lifespan=lifespan)

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
    # If the host is not the Pi's IP or observatory.local, and it's a browser request,
    # we could potentially redirect here, but better to handle common detection paths first.
    return templates.TemplateResponse("index.html", {"request": request})

# --- Captive Portal Detection Routes ---

@app.get("/generate_204") # Android / Chrome
@app.get("/gen_204")
@app.get("/connectivitycheck.gstatic.com/generate_204")
async def android_detection():
    return RedirectResponse(url="http://192.168.4.1/", status_code=302)

@app.get("/hotspot-detect.html") # iOS / macOS
@app.get("/library/test/success.html")
@app.get("/captive.apple.com/hotspot-detect.html")
async def apple_detection():
    return RedirectResponse(url="http://192.168.4.1/", status_code=302)

@app.get("/connecttest.txt") # Windows
@app.get("/ncsi.txt")
@app.get("/msftconnecttest.com/connecttest.txt")
async def windows_detection():
    return RedirectResponse(url="http://192.168.4.1/", status_code=302)

@app.get("/redirect")
@app.get("/kindle-wifi/wifiredirect.html") # Kindle
@app.get("/ncsi")
async def general_redirect():
    return RedirectResponse(url="http://192.168.4.1/", status_code=302)

# Catch-all for other captive portal checks or unknown domains
@app.middleware("http")
async def captive_portal_middleware(request: Request, call_next):
    host = request.headers.get("host", "")
    # If the host is an external domain (redirected by DNS), redirect to our local IP/Domain
    # Check if host is NOT our local IP or expected domain
    local_hosts = ["192.168.4.1", "observatory.local", "localhost", "127.0.0.1"]
    
    # Allow local API calls and static files
    if any(lh in host for lh in local_hosts) or host == "":
        return await call_next(request)
    
    # If it's a captive portal detection URL, let it through to its specific route
    detection_paths = [
        "/generate_204", "/gen_204", "/connectivitycheck.gstatic.com/generate_204",
        "/hotspot-detect.html", "/library/test/success.html", "/captive.apple.com/hotspot-detect.html",
        "/connecttest.txt", "/ncsi.txt", "/msftconnecttest.com/connecttest.txt",
        "/redirect", "/kindle-wifi/wifiredirect.html", "/ncsi"
    ]
    if request.url.path in detection_paths:
        return await call_next(request)
        
    # Otherwise, redirect to dashboard
    logger.info(f"[CAPTIVE] Redirecting request for {host}{request.url.path} to dashboard")
    return RedirectResponse(url="http://192.168.4.1/")

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

def print_banner(port):
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = "192.168.4.1" # Standard for our hotspot
    except:
        local_ip = "192.168.4.1"
    
    banner = f"""
    \033[94m
    #################################################
    #                                               #
    #        PI5 OBSERVATORY - DASHBOARD            #
    #                                               #
    #################################################
    \033[0m
    \033[92m[SISTEMA]\033[0m Puerto: {port}
    \033[92m[SISTEMA]\033[0m Modo: Portal Cautivo ACTIVO
    
    \033[93m[ACCESO]\033[0m Conéctate al WiFi: \033[1mASTRO PI5\033[0m
    \033[93m[ACCESO]\033[0m Link directo: \033[1mhttp://{local_ip}\033[0m
    \033[93m[ACCESO]\033[0m Link local:   \033[1mhttp://observatory.local\033[0m
    
    \033[90mPresiona Ctrl+Q para salir con seguridad\033[0m
    """
    print(banner)

if __name__ == "__main__":
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Start the Ctrl+Q listener thread
    quit_thread = threading.Thread(target=listen_for_quit, daemon=True)
    quit_thread.start()
    
    port = config.get("streaming", {}).get("local_port", 80)
    
    print_banner(port)
    
    # uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    # Using a config object to allow better signal handling
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="error", loop="uvloop")
    server = uvicorn.Server(config)
    server.run()
