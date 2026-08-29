import sys
import os

# Ensure src directory is in python module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Launch FastAPI app directly via uvicorn — no Gradio dependency needed
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("crop_mix.app:app", host="0.0.0.0", port=port)
else:
    # When imported by the Gradio runner, expose the FastAPI app as the ASGI app
    from crop_mix.app import app
