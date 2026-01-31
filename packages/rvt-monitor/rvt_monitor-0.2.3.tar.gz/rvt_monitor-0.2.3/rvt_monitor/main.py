"""RVT-Monitor - BLE Device Monitor Application"""

import logging
import threading
import time
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORT = 8000


def setup_logging():
    """Setup logging for debugging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    # Enable DEBUG for BLE scanner
    logging.getLogger("rvt_monitor.ble.scanner").setLevel(logging.DEBUG)


def open_browser():
    """Open browser after server starts."""
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    """Main entry point."""
    setup_logging()

    from rvt_monitor.server.app import app

    # Open browser in separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start server
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
