import os

bind = f"0.0.0.0:{os.getenv('PORT', '7860')}"
workers = 2            # Keep low — each worker loads ML models into memory
timeout = 120          # YOLO inference on CPU can take time
preload_app = False    # Let each worker load models independently
accesslog = "-"        # Log requests to stdout (visible in HF Spaces logs)
errorlog = "-"         # Log errors to stdout
