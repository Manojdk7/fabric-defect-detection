# HOW TO RUN THE QUALITY INSPECTION PROJECT

## ========================================
## 1. QUICK START (FASTEST WAY)
## ========================================

### Step 1: Activate Virtual Environment
```powershell
cd c:\Users\lenovo\OneDrive\Desktop\Quality-inspection
.\venv\Scripts\Activate.ps1
```

### Step 2: Start Flask Backend (API Server)
```powershell
python app.py
```
✓ Server runs on: http://localhost:5000

### Step 3: Test with cURL (in new terminal)
```powershell
# Test health check
curl http://localhost:5000/api/health

# Upload an image for inspection
curl -X POST -F "file=@path/to/image.jpg" http://localhost:5000/api/inspect
```

---

## ========================================
## 2. FULL SETUP (WITH DASHBOARD)
## ========================================

### Backend Setup:
```powershell
# Terminal 1: Activate venv
cd c:\Users\lenovo\OneDrive\Desktop\Quality-inspection
.\venv\Scripts\Activate.ps1

# Start Flask API
python app.py
# Runs on http://localhost:5000
```

### Frontend Setup:
```powershell
# Terminal 2: Install and run React dashboard
cd c:\Users\lenovo\OneDrive\Desktop\Quality-inspection\inspection-dashboard
npm install
npm start
# Runs on http://localhost:3000
```

✓ Open http://localhost:3000 in browser
✓ Upload images through the dashboard
✓ View real-time analysis

---

## ========================================
## 3. PROJECT STRUCTURE
## ========================================

```
Quality-inspection/
├── app.py                          # Flask backend API
├── defect_detector.py              # AI model detection logic
├── models/
│   └── retrained_model_test/
│       └── weights/
│           ├── best.pt             # TRAINED MODEL (197 MB)
│           └── last.pt
├── datasets/
│   └── fabric_defects/
│       ├── images/                 # 720 training images
│       └── labels/
├── inspection-dashboard/           # React web dashboard
├── uploads/                        # User uploaded images
├── inspection_results/             # Analysis results
└── venv/                          # Python dependencies
```

---

## ========================================
## 4. KEY FILES & WHAT THEY DO
## ========================================

| File | Purpose |
|------|---------|
| `app.py` | Flask web server - Main API endpoint |
| `defect_detector.py` | AI model inference logic |
| `models/retrained_model_test/weights/best.pt` | Trained YOLOv8 model (READY) |
| `quick_inference.py` | Test model on sample images |
| `05_validate_model.py` | Full validation on test set |
| `inspection-dashboard/` | Web UI for inspection |

---

## ========================================
## 5. API ENDPOINTS
## ========================================

### Health Check
```
GET http://localhost:5000/api/health
Response: {"status": "healthy", "service": "Quality Inspection System"}
```

### Inspect Image (Main)
```
POST http://localhost:5000/api/inspect
Content-Type: multipart/form-data
Body: 
  - file: [image.jpg]
  - confidence: 0.5 (optional, 0-1)

Response: {
  "success": true,
  "inspection_id": "...",
  "summary": {
    "total_defects": 241,
    "severity": "HIGH"
  },
  "detections": [...]
}
```

---

## ========================================
## 6. PYTHON SCRIPTS FOR TESTING
## ========================================

### Test Model on Samples
```powershell
.\venv\Scripts\python.exe quick_inference.py
```
Output: 2 sample images tested, 241 objects detected

### Full Validation
```powershell
.\venv\Scripts\python.exe 05_validate_model.py
```
Output: Complete model metrics and performance

### Verify Model
```powershell
.\venv\Scripts\python.exe verify_model.py
```
Output: Model status, size, dataset info

---

## ========================================
## 7. ONLINE TEST IMAGES (WITH LINKS)
## ========================================

### Fabric Defect Images - Good for Testing:

**Option 1: Pixabay** (Free, CC0 License)
- Fabric/Textile texture with defects:
  https://pixabay.com/images/search/fabric%20texture%20defect/
  
- Individual images:
  https://pixabay.com/images/id-3524381/  (Close-up fabric)
  https://pixabay.com/images/id-3524380/  (Woven pattern)
  https://pixabay.com/images/id-3524379/  (Textile detail)

**Option 2: Pexels** (Free, no attribution needed)
- Fabrics and textiles:
  https://www.pexels.com/search/fabric%20texture/
  
- Direct samples:
  https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg
  https://images.pexels.com/photos/3697881/pexels-photo-3697881.jpeg

**Option 3: Unsplash** (Free, creative commons)
- Textiles and fabrics:
  https://unsplash.com/s/photos/fabric-texture
  
- Specific images:
  https://images.unsplash.com/photo-1591670882546-8c4c30bdd180  (Cloth texture)
  https://images.unsplash.com/photo-1584270354949-fed02779c368  (Weave pattern)

**Option 4: MVTEC AD Dataset** (Academic, includes defects)
- Fabric defect dataset:
  https://www.mvtec.com/company/research/datasets/mvtec-ad
  (This is what the model was trained on!)

---

## ========================================
## 8. HOW TO TEST WITH ONLINE IMAGES
## ========================================

### Method 1: Download & Upload Through Dashboard
```
1. Open http://localhost:3000
2. Click "Upload Image"
3. Select downloaded image
4. View results in real-time
```

### Method 2: Test via Python Script
```powershell
# Download image first, then test
python -c "
import requests
from pathlib import Path

url = 'https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg'
response = requests.get(url)
Path('test_image.jpg').write_bytes(response.content)
print('Image downloaded: test_image.jpg')
"

# Then test with model
.\venv\Scripts\python.exe quick_inference.py
```

### Method 3: Direct API Call
```powershell
# Create a test script to download and send
$url = "https://images.pexels.com/photos/4551832/pexels-photo-4551832.jpeg"
$outputPath = "test_fabric.jpg"

# Download image
(New-Object Net.WebClient).DownloadFile($url, $outputPath)

# Send to API
$filePath = "test_fabric.jpg"
$url = "http://localhost:5000/api/inspect"

$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$boundary = [System.Guid]::NewGuid().ToString()
$body = @()

# Build multipart form-data request
$body += "--$boundary"
$body += "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $filePath -Leaf)`""
$body += "Content-Type: image/jpeg"
$body += ""
$body += [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetString($fileBytes)
$body += "--$boundary--"

$response = Invoke-WebRequest -Uri $url -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body ($body -join "`r`n")
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## ========================================
## 9. BEST ONLINE FABRIC IMAGES FOR TESTING
## ========================================

### Recommended Test Images:

1. **Close-up Weave Pattern**
   https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg
   ✓ Good for detecting thread defects

2. **Cotton Fabric Texture**
   https://images.pexels.com/photos/5866438/pexels-photo-5866438.jpeg
   ✓ Uniform texture, suitable for defect detection

3. **Woven Cloth Detail**
   https://images.pexels.com/photos/3945674/pexels-photo-3945674.jpeg
   ✓ Clear fabric structure

4. **Textile Pattern**
   https://images.unsplash.com/photo-1598394692202-bf96a3ee82c9
   ✓ High resolution, good for analysis

5. **Linen Texture**
   https://images.unsplash.com/photo-1578988185632-e2589b9f5300
   ✓ Plain weave pattern

---

## ========================================
## 10. TROUBLESHOOTING
## ========================================

### Issue: "Port 5000 already in use"
```powershell
# Kill process on port 5000
Get-Process | Where-Object {$_.Name -eq "python"} | Stop-Process
# Or specify different port:
$env:FLASK_PORT=5001
python app.py
```

### Issue: "Model not found"
```powershell
# Verify model exists
Test-Path "models/retrained_model_test/weights/best.pt"
# Should return: True
```

### Issue: Dependencies missing
```powershell
# Reinstall requirements
python -m pip install -r requirements.txt
```

### Issue: "CUDA out of memory"
```powershell
# Run on CPU instead
# Edit app.py and app.config['DEVICE'] = 'cpu'
```

---

## ========================================
## 11. PERFORMANCE TIPS
## ========================================

- Model size: 197 MB (loaded once at startup)
- CPU inference time: 2-5 seconds per image
- Max file size: 16 MB
- Supported formats: PNG, JPG, JPEG, GIF, BMP

---

## ========================================
## 12. NEXT STEPS
## ========================================

1. Start Flask: `python app.py`
2. Open Dashboard: http://localhost:3000
3. Upload a test image (see links above)
4. View AI analysis results
5. Export inspection report

✓ All ready to go! 🚀
