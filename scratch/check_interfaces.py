from app.modules.network.network_manager import NetworkManager
import json

nm = NetworkManager()
print(json.dumps(nm.get_interfaces(), indent=2))
