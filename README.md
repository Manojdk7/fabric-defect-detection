# Quality-inspection
AI-powered quality inspection system for detecting defects in fabrics and PCBs using YOLOv8 computer vision.

## Active app structure

- `app.py`: Flask backend API
- `defect_detector.py`: YOLO inference and inspection report logic
- `inspection-dashboard/`: active React frontend

## Local run

1. Start the backend from the project root: `python app.py`
2. Start the frontend from `inspection-dashboard/`: `npm start`
3. Open `http://localhost:3000`

The React app talks to the Flask API at `http://localhost:5000/api`.
