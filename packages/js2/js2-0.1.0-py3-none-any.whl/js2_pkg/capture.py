"""Screen capture module using mss."""

import asyncio
import base64
import io
from typing import Callable, Optional

import mss
from PIL import Image


class ScreenCapture:
    """Captures the screen and yields JPEG frames."""

    def __init__(self, fps: int = 5, quality: int = 50):
        """Initialize screen capture.

        Args:
            fps: Target frames per second (default 5 for reliability)
            quality: JPEG quality 1-100 (default 50 for bandwidth)
        """
        self.fps = fps
        self.quality = quality
        self._running = False

    def capture_frame(self) -> Optional[bytes]:
        """Capture a single frame as JPEG bytes."""
        with mss.mss() as sct:
            # Capture primary monitor (monitor 1, monitor 0 is all monitors combined)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

            # Compress to JPEG
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality)
            return buffer.getvalue()

    async def stream(self, on_frame: Callable[[bytes], None]) -> None:
        """Stream frames continuously.

        Args:
            on_frame: Callback function called with each JPEG frame
        """
        self._running = True
        interval = 1.0 / self.fps

        while self._running:
            try:
                frame = self.capture_frame()
                if frame:
                    await on_frame(frame)
            except Exception as e:
                print(f"Capture error: {e}")

            await asyncio.sleep(interval)

    def stop(self) -> None:
        """Stop the capture stream."""
        self._running = False


def frame_to_base64(frame: bytes) -> str:
    """Convert JPEG frame to base64 data URL."""
    b64 = base64.b64encode(frame).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"
