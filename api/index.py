import sys
import os

# Add the project root and 'src' directory to Python path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, "src"))

# Import the FastAPI app instance
from crop_mix.app import app
