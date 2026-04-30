import threading
import time

class FrameBuffer:
    def __init__(self):
        self._frame = None
        self._jpeg_frame = None
        self._metadata = {
            "fps": 0.0,
            "temperature": 0.0,
            "timestamp": 0.0
        }
        self._lock = threading.Lock()
        self._new_frame_event = threading.Event()

    def update_frame(self, frame, jpeg_frame=None, fps=None, temperature=None):
        with self._lock:
            self._frame = frame
            self._jpeg_frame = jpeg_frame
            if fps is not None:
                self._metadata["fps"] = fps
            if temperature is not None:
                self._metadata["temperature"] = temperature
            self._metadata["timestamp"] = time.time()
            
            self._new_frame_event.set()
            self._new_frame_event.clear()

    def get_jpeg_frame(self, timeout=None):
        if timeout:
            self._new_frame_event.wait(timeout)
        
        with self._lock:
            return self._jpeg_frame, self._metadata.copy()

    def get_frame(self, timeout=None):
        """Returns the latest frame and metadata. If timeout is provided, waits for a new frame."""
        if timeout:
            self._new_frame_event.wait(timeout)
            # We don't clear here because multiple clients might be waiting.
            # Instead, we rely on the next update_frame to clear and set.
        
        with self._lock:
            return self._frame, self._metadata.copy()

    def get_metadata(self):
        with self._lock:
            return self._metadata.copy()

# Global singleton
frame_buffer = FrameBuffer()
