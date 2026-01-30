"""FastAPI server with WebSocket for screen sharing."""

import asyncio
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .capture import ScreenCapture, frame_to_base64

app = FastAPI(title="Screenshare MVP")

# Connected browser viewers
viewers: Set[WebSocket] = set()

# Screen capture instance
capture = ScreenCapture(fps=5, quality=50)


@app.get("/", response_class=HTMLResponse)
async def get_viewer():
    """Serve the viewer HTML page."""
    viewer_path = Path(__file__).parent / "static" / "viewer.html"
    return viewer_path.read_text()


@app.websocket("/ws/viewer")
async def viewer_websocket(websocket: WebSocket):
    """WebSocket endpoint for browser viewers."""
    await websocket.accept()
    viewers.add(websocket)
    print(f"Viewer connected. Total viewers: {len(viewers)}")

    try:
        # Keep connection alive, receive any messages (ping/pong handled automatically)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        viewers.discard(websocket)
        print(f"Viewer disconnected. Total viewers: {len(viewers)}")


async def broadcast_frame(frame: bytes) -> None:
    """Broadcast a frame to all connected viewers."""
    if not viewers:
        return

    # Convert to base64 data URL
    data_url = frame_to_base64(frame)

    # Broadcast to all viewers
    disconnected = set()
    for viewer in viewers:
        try:
            await viewer.send_text(data_url)
        except Exception:
            disconnected.add(viewer)

    # Remove disconnected viewers
    for viewer in disconnected:
        viewers.discard(viewer)


async def start_capture():
    """Start the screen capture and broadcast loop."""
    print("Starting screen capture...")
    await capture.stream(broadcast_frame)


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the FastAPI server with screen capture.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn

    # Create custom event loop to run capture alongside server
    async def main():
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        # Start capture as a background task when the server starts
        capture_task = None

        @app.on_event("startup")
        async def on_startup():
            nonlocal capture_task
            capture_task = asyncio.create_task(start_capture())

        try:
            await server.serve()
        finally:
            capture.stop()
            if capture_task:
                capture_task.cancel()
                try:
                    await capture_task
                except asyncio.CancelledError:
                    pass

    asyncio.run(main())
