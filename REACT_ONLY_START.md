# RUN REACT DASHBOARD ONLY

## Quick Start (One Command)

```powershell
cd c:\Users\lenovo\OneDrive\Desktop\Quality-inspection\inspection-dashboard
npm start
```

✅ Opens automatically at: **http://localhost:3000**

---

## What This Does

- Starts React development server
- Opens web dashboard in browser
- Hot-reload enabled (changes update automatically)

---

## First Time Setup

If you get npm errors:

```powershell
cd inspection-dashboard

# Install dependencies (one time only)
npm install

# Start dashboard
npm start
```

---

## Requirements

- Node.js 14+ (check: `node --version`)
- npm (check: `npm --version`)

---

## Dashboard Features

- ✓ Image upload interface
- ✓ Real-time model predictions
- ✓ Defect visualization
- ✓ Inspection reports

---

## Connect to Backend (Optional)

If you also want the Flask API:

```powershell
# Terminal 1: React Dashboard
cd inspection-dashboard
npm start
# Opens: http://localhost:3000

# Terminal 2: Flask Backend (new PowerShell window)
cd ..
python app.py
# Runs on: http://localhost:5000
```

---

## Commands

```powershell
npm start       # Start development server (http://localhost:3000)
npm build       # Build for production
npm test        # Run tests
npm eject       # Eject from Create React App (not reversible!)
```

---

## Troubleshooting

### Port 3000 already in use
```powershell
# Kill process on port 3000
Get-Process | Where-Object {$_.Name -eq "node"} | Stop-Process

# Or use different port
set PORT=3001
npm start
```

### npm not found
```powershell
# Install Node.js from: https://nodejs.org/
# Then close and reopen PowerShell
```

### node_modules missing
```powershell
npm install
npm start
```

---

## That's it! 🚀

Just run: `npm start`
