# Fabric Defect Detection System

AI-powered fabric inspection system using YOLOv8 for real-time defect detection and quality control in textile manufacturing.

## Features

✅ **Real-time Defect Detection** - Live camera feed with automatic fabric inspection  
✅ **YOLOv8 AI Model** - High-accuracy defect classification  
✅ **Auto-Capture & Inspect** - Continuous automated scanning at configurable intervals  
✅ **Beautiful Dashboard** - Black & white minimalist interface for easy operation  
✅ **Detailed Analytics** - Severity breakdown, quality scores, trends  
✅ **Batch Processing** - Inspect multiple images at once  
✅ **Export Reports** - CSV and PDF inspection reports  
✅ **Defect Types** - Detects cracks, scratches, holes, stains, discoloration, misalignment  
✅ **Multi-User Support** - Operator login with role-based access  
✅ **Database Logging** - Full inspection history with metadata  

## Project Structure
fabric-defect-detection/
├── app.py # Flask backend API
├── config.py # Configuration settings
├── defect_detector.py # YOLOv8 detection engine
├── database.py # SQLite inspection database
├── requirements.txt # Python dependencies
├── inspection-dashboard/ # React frontend
│ ├── src/
│ │ ├── App.js # Main React component
│ │ ├── App.css # Black & white styling
│ │ └── index.js # React entry point
│ └── package.json # Node dependencies
├── models/ # Trained defect detection models
├── datasets/ # Training datasets (optional)
└── README.md # This file



## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Webcam (for live inspection)

### Backend Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/fabric-defect-detection.git
   cd fabric-defect-detection



   python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py

Frontend Setup
cd inspection-dashboard
npm install
npm start

Run the System
Terminal 1 - Backend API (Port 5000)
python app.py

Terminal 2 - Frontend Dashboard (Port 3000)
cd inspection-dashboard
npm start

Open Dashboard
Navigate to http://localhost:3000
Login with default credentials:
Username: admin
Password: admin123
Usage
Manual Inspection
Click "Upload" tab
Drag & drop or select fabric image
Adjust confidence threshold (0-1)
Click "Run Inspection"
View results with annotated image
Automated Live Scanning
Click "Camera" tab
Click "Start Camera"
Auto-scan starts automatically with 4-second intervals
Adjust interval slider (2-15 seconds)
Click "Stop" to end scanning
Batch Processing
Upload multiple images
System processes all images sequentially
Get summary report for entire batch


Model Information
Model: YOLOv8 (Nano/Medium)
Framework: PyTorch
Input Size: 640x640
Classes: Crack, Scratch, Hole, Stain, Misalignment, Discoloration
Performance: Real-time inference on CPU/GPU
Defect Classes
Defect	Severity	Description
Crack	High	Surface or structural cracks
Scratch	Medium	Surface scratches or abrasions
Hole	High	Holes or punctures in fabric
Stain	Medium	Discoloration or stains
Misalignment	Low	Incorrect weave or pattern alignment
Discoloration	Low	Color variations or fading
Technologies
Backend:Flask (REST API)
PyTorch / YOLOv8 (AI Model)
SQLite (Database)
OpenCV (Image Processing)
Frontend:

React.js (UI)
CSS3 (Styling)
Fetch API (Backend Communication)
Performance
Detection Speed: ~100-300ms per image (CPU)
Accuracy: 85-95% (depending on fabric type)
Max Batch Size: 200 images
Memory Usage: ~500MB
