import sys
import os

# Vercel / AWS Lambda environment doesn't support POSIX semaphores (since /dev/shm is missing).
# This causes Python's multiprocessing locks (used by Pyomo on import) to raise FileNotFoundError.
# We monkeypatch the SemLock class here to bypass this restriction before importing Pyomo.
try:
    import multiprocessing.synchronize
    class MockSemLock:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def acquire(self, *args, **kwargs):
            return True
        def release(self):
            pass
    multiprocessing.synchronize.SemLock = MockSemLock
except (ImportError, AttributeError):
    pass

# Add the project root and 'src' directory to Python path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, "src"))

# Import the FastAPI app instance
from crop_mix.app import app
