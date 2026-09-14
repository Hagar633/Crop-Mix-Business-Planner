import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from crop_mix.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
