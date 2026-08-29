import sys
import os

# Ensure src directory is in python module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import gradio as gr
from crop_mix.app import app as fastapi_app

# Mount our full FastAPI Crop Mix Business Planner inside Gradio for 100% Free HF Space deployment
app = gr.mount_gradio_app(app=fastapi_app, blocks=gr.Blocks(), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
