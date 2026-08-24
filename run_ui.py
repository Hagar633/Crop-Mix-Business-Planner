"""Standalone runner script for Crop Mix Business Planner Web UI."""

import sys
import webbrowser
from pathlib import Path
import uvicorn

# Add src to sys.path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"
    
    print("=" * 70)
    print("      CROP MIX BUSINESS PLANNER - FARMER TESTING WEB UI")
    print("=" * 70)
    print(f"Starting server at: {url}")
    print("Opening web browser...")
    print("Press Ctrl+C to stop the server.")
    print("=" * 70)

    # Open browser automatically after a short delay
    webbrowser.open(url)

    # Launch Uvicorn server
    uvicorn.run("crop_mix.app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
