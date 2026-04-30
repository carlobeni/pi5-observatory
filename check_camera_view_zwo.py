#!/usr/bin/env python3
import os
import sys

# Auto-activar el entorno virtual si no se está usando
venv_python = os.path.expanduser("~/asi_env/bin/python")
if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    os.execl(venv_python, venv_python, *sys.argv)

import zwoasi as asi
import cv2
import numpy as np
import time

# ---------- INIT SDK ----------
asi.init(os.environ.get("ZWO_ASI_LIB", "/usr/local/lib/libASICamera2.so"))

n = asi.get_num_cameras()
print("Cámaras detectadas:", n)
if n == 0:
    raise RuntimeError("No se detectaron cámaras ASI")

cam = asi.Camera(0)

# ---------- CONFIG ----------
WIDTH  = 640
HEIGHT = 480
BIN    = 1

cam.set_image_type(asi.ASI_IMG_RAW8)
cam.set_roi_format(WIDTH, HEIGHT, BIN, asi.ASI_IMG_RAW8)

EXPOSURE_US = 10000   # 10 ms
GAIN = 50

cam.set_control_value(asi.ASI_EXPOSURE, EXPOSURE_US)
cam.set_control_value(asi.ASI_GAIN, GAIN)

cam.start_video_capture()
print("Captura de video iniciada")

# Timeout recomendado por SDK
TIMEOUT_MS = int(EXPOSURE_US / 1000 * 2 + 500)

# ---------- FPS MEASUREMENT ----------
fps_window = 30               # frames por ventana
frame_count = 0
t0 = time.perf_counter()
fps = 0.0

try:
    while True:
        try:
            frame = cam.capture_video_frame(timeout=TIMEOUT_MS)
        except asi.ZWO_IOError:
            continue

        if frame is None:
            continue

        frame_count += 1

        # ---------- FPS CALC ----------
        if frame_count == fps_window:
            t1 = time.perf_counter()
            fps = fps_window / (t1 - t0)
            t0 = t1
            frame_count = 0

        # ---------- IMAGE ----------
        img = frame.reshape((HEIGHT, WIDTH))
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # ---------- OVERLAY ----------
        cv2.putText(
            img_bgr,
            f"FPS: {fps:5.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        cv2.imshow("ASI174 Live + FPS", img_bgr)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cam.stop_video_capture()
    cam.close()
    cv2.destroyAllWindows()
    print("Cámara cerrada correctamente")
