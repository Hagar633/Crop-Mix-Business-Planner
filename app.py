import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# The Hugging Face Gradio runner imports this file and looks for
# an object called `demo` (gr.Blocks) or runs it as __main__.
# We wrap our full FastAPI app inside a Gradio Blocks iframe redirect.

try:
    import gradio as gr
    from crop_mix.app import app as fastapi_app

    # Mount our FastAPI app at /api and serve a redirect page via Gradio
    with gr.Blocks(title="Crop Mix Business Planner 🌾") as demo:
        gr.HTML("""
        <style>
            body, html { margin: 0; padding: 0; height: 100%; }
            iframe { width: 100%; height: 92vh; border: none; }
        </style>
        <iframe src="/app/" allowfullscreen></iframe>
        """)

    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

except ImportError:
    # Fallback: just expose the FastAPI app directly (for non-HF environments)
    from crop_mix.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
