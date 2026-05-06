from fastapi import APIRouter, HTTPException
from app.modules.network.network_manager import NetworkManager
from pydantic import BaseModel

router = APIRouter()
nm = NetworkManager()

def has_internet():
    import socket
    try:
        # Try to connect to a DNS server (Google)
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except:
        return False

class ConnectRequest(BaseModel):
    ssid: str
    password: str = None
    interface: str = "wlan0"

class HotspotRequest(BaseModel):
    ssid: str
    password: str
    interface: str = "ap0"
    enable: bool = True
    admin_password: str = None

@router.get("/status")
async def get_status():
    internet = has_internet()
    public_ip = "Desconocida"
    if internet:
        try:
            import urllib.request
            # Use a short timeout to avoid blocking the API
            public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=2).read().decode('utf8')
        except:
            pass

    return {
        "interfaces": nm.get_interfaces(),
        "details": nm.get_current_connection_details(),
        "internet": internet,
        "public_ip": public_ip,
        "hotspot_active": nm.is_hotspot_active()
    }

@router.get("/scan")
async def scan_wifi(interface: str = "wlan0"):
    return nm.scan_wifi(interface)

@router.post("/connect")
async def connect_wifi(req: ConnectRequest):
    success = nm.connect_wifi(req.ssid, req.password, req.interface)
    if success:
        return {"status": "ok", "message": f"Connected to {req.ssid}"}
    raise HTTPException(status_code=400, detail="Failed to connect")

@router.post("/hotspot")
async def manage_hotspot(req: HotspotRequest):
    action = "up" if req.enable else "down"

    # MANDATORY VALIDATION
    if not nm.verify_admin_password(req.admin_password):
        raise HTTPException(status_code=401, detail="Invalid administrator password")
        
    success = nm.manage_hotspot(req.ssid, req.password, req.interface, action, req.admin_password)
    if success:
        return {"status": "ok", "message": f"Hotspot {action} successful"}
    raise HTTPException(status_code=400, detail="Failed to manage hotspot")

@router.post("/disconnect")
async def disconnect_wifi(data: dict):
    # Use 'password' to match standard admin auth field if possible, 
    # but here we check both for robustness
    admin_password = data.get("password") or data.get("admin_password")
    if not admin_password:
        raise HTTPException(status_code=400, detail="Admin password required")
    
    # VALIDATION
    if not nm.verify_admin_password(admin_password):
        raise HTTPException(status_code=401, detail="Invalid administrator password")
        
    success = nm.disconnect_wifi(admin_password=admin_password)
    if success:
        return {"status": "ok", "message": "Disconnected successfully"}
    raise HTTPException(status_code=500, detail="Failed to disconnect")

@router.get("/hotspot/config")
async def get_hotspot_config():
    # Only returns SSID (safe)
    return nm.get_hotspot_config()

@router.post("/hotspot/config")
async def get_hotspot_config_secure(data: dict):
    # Returns SSID + real password (requires sudo)
    password = data.get("admin_password")
    if not password:
        raise HTTPException(status_code=400, detail="Admin password required")
    
    # MANDATORY VALIDATION
    if not nm.verify_admin_password(password):
        raise HTTPException(status_code=401, detail="Invalid administrator password")
        
    return nm.get_hotspot_config(admin_password=password)

@router.post("/verify-admin")
async def verify_admin(data: dict):
    password = data.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="Password required")
    if nm.verify_admin_password(password):
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Invalid administrator password")
