#!/usr/bin/env python3
import os
import sys

# Auto-activar el entorno virtual si no se está usando
venv_python = os.path.expanduser("~/asi_env/bin/python")
if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    os.execl(venv_python, venv_python, *sys.argv)

import zwoasi as asi
import time

asi.init(os.environ.get("ZWO_ASI_LIB", "/usr/local/lib/libASICamera2.so"))

print("Detectando cámaras...")
n = asi.get_num_cameras()
print("Cámaras detectadas:", n)

if n == 0:
    exit(0)

time.sleep(0.2)
cam = asi.Camera(0)

info = cam.get_camera_property()
print("Información de la cámara:")
for k, v in info.items():
    print(f"  {k}: {v}")

cam.close()
print("Cámara cerrada correctamente")
