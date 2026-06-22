# Inspection Dashboard

This is the active React frontend for the Quality Inspection project.

## Run locally

From this folder:

```bash
npm start
```

The app runs at `http://localhost:3000` and expects the Flask backend at `http://localhost:5000/api`.

## Useful scripts

- `npm start`: start the development server
- `npm run build`: build the production bundle
- `npm test`: run tests

## Main workflow

1. Start the backend from the project root with `python app.py`
2. Start this frontend with `npm start`
3. Use the dashboard to:
   - check backend health
   - upload an image
   - run inspection
   - review the returned defect summary
