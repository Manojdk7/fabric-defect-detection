import logging
import secrets
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config
from database import get_inspection, get_stats, init_db, list_inspections, save_inspection
from defect_detector import DefectDetector

app = Flask(__name__)
CORS(app)

Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Config.RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
init_db(Config.DATABASE_PATH)

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app.config["UPLOAD_FOLDER"] = str(Config.UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

DEFAULT_DEFECT_TYPE = "fabric"
SUPPORTED_DEFECT_TYPES = {"fabric"}
detectors = {}
detector_errors = {}
auth_tokens = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def parse_confidence(value, default=0.35):
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default

    return max(0, min(1, confidence))


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return ""


def require_auth(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        token = get_bearer_token()
        if not token or token not in auth_tokens:
            return jsonify({"error": "Authentication required"}), 401
        return route(*args, **kwargs)

    return wrapped


def current_user():
    return auth_tokens.get(get_bearer_token(), {})


def get_detector(defect_type=DEFAULT_DEFECT_TYPE):
    """Load detectors lazily so optional model failures do not break startup."""
    defect_type = defect_type.lower()

    if defect_type not in SUPPORTED_DEFECT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_DEFECT_TYPES))
        raise ValueError(f"Unsupported defect type '{defect_type}'. Supported types: {supported}")

    if defect_type in detectors:
        return detectors[defect_type]

    if defect_type in detector_errors:
        raise RuntimeError(detector_errors[defect_type])

    try:
        detectors[defect_type] = DefectDetector(defect_type=defect_type)
        logging.info("Loaded %s detector", defect_type)
        return detectors[defect_type]
    except Exception as exc:
        message = f"{defect_type} detector is unavailable: {exc}"
        detector_errors[defect_type] = message
        logging.exception(message)
        raise RuntimeError(message) from exc


def request_metadata():
    return {
        "operator_name": request.form.get("operator_name", "").strip(),
        "batch_id": request.form.get("batch_id", "").strip(),
        "fabric_type": request.form.get("fabric_type", "").strip(),
        "production_line": request.form.get("production_line", "").strip(),
        "shift": request.form.get("shift", "").strip(),
    }


@app.route("/", methods=["GET"])
def root():
    """Simple root route for quick browser checks."""
    return jsonify(
        {
            "message": f"{Config.SERVICE_NAME} API",
            "health": "/api/health",
            "login": "/api/login",
            "inspect": "/api/inspect",
            "history": "/api/inspections",
        }
    ), 200


@app.route("/api/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if username != Config.ADMIN_USER or password != Config.ADMIN_PASSWORD:
        logging.warning("Failed login for user=%s", username)
        return jsonify({"error": "Invalid username or password"}), 401

    token = secrets.token_urlsafe(32)
    auth_tokens[token] = {
        "username": username,
        "role": "admin",
        "issued_at": time.time(),
    }
    logging.info("Login success for user=%s", username)
    return jsonify({"token": token, "user": auth_tokens[token]}), 200


@app.route("/api/logout", methods=["POST"])
@require_auth
def logout():
    auth_tokens.pop(get_bearer_token(), None)
    return jsonify({"success": True}), 200


@app.route("/api/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": current_user()}), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint with model/database status."""
    stats = get_stats(Config.DATABASE_PATH)
    return jsonify(
        {
            "status": "healthy",
            "service": Config.SERVICE_NAME,
            "version": Config.VERSION,
            "database": str(Config.DATABASE_PATH),
            "uploads": str(Config.UPLOAD_FOLDER),
            "results": str(Config.RESULTS_FOLDER),
            "detectors": {
                defect_type: (
                    "loaded"
                    if defect_type in detectors
                    else "unavailable"
                    if defect_type in detector_errors
                    else "not_loaded"
                )
                for defect_type in sorted(SUPPORTED_DEFECT_TYPES)
            },
            "stats": stats,
        }
    ), 200


@app.route("/api/inspect", methods=["POST"])
@require_auth
def inspect_image():
    """
    Main inspection endpoint.

    Request:
        - file: Image file (multipart/form-data)
        - confidence: Optional confidence threshold (0-1)
        - defect_type: fabric
        - operator_name, batch_id, fabric_type, production_line, shift
    """
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            allowed = ", ".join(sorted(Config.ALLOWED_EXTENSIONS)).upper()
            return jsonify({"error": f"File type not allowed. Use: {allowed}"}), 400

        original_name = secure_filename(file.filename)
        timestamp = f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"
        filename = f"{timestamp}_{original_name}"
        filepath = Config.UPLOAD_FOLDER / filename
        file.save(filepath)

        confidence = parse_confidence(request.form.get("confidence", 0.35))
        defect_type = DEFAULT_DEFECT_TYPE
        metadata = request_metadata()

        try:
            detector = get_detector(defect_type)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503

        started_at = time.perf_counter()
        result = detector.detect_defects(str(filepath), confidence_threshold=confidence)
        processing_time_ms = round((time.perf_counter() - started_at) * 1000)

        if "error" in result:
            logging.warning("Inspection failed: %s", result["error"])
            return jsonify(result), 400

        annotated_path = Config.RESULTS_FOLDER / f"annotated_{Path(filename).stem}.png"
        detector.save_annotated_image(result, str(annotated_path))

        report = detector.generate_inspection_report(result)
        inspection_id = f"{report['inspection_id']}_{secrets.token_hex(3)}"
        response_data = {
            "success": True,
            "inspection_id": inspection_id,
            "timestamp": report.get("timestamp", result["timestamp"]),
            "defect_type": defect_type,
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
            "metadata": metadata,
            "upload_path": str(filepath),
            "annotated_image_path": str(annotated_path),
            "image_info": report["image_info"],
            "summary": report["summary"],
            "defect_breakdown": report["defect_breakdown"],
            "severity_breakdown": report["severity_breakdown"],
            "detections": report["detections"],
            "recommendations": report["recommendations"],
        }

        save_inspection(Config.DATABASE_PATH, response_data)
        logging.info(
            "Inspection %s complete status=%s defects=%s time_ms=%s user=%s",
            response_data["inspection_id"],
            response_data["summary"]["status"],
            response_data["summary"]["total_defects"],
            processing_time_ms,
            current_user().get("username", "unknown"),
        )

        return jsonify(response_data), 200

    except Exception as exc:
        logging.exception("Unhandled inspection error")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/inspections", methods=["GET"])
@require_auth
def inspections():
    limit = min(200, max(1, int(request.args.get("limit", 50))))
    status = request.args.get("status") or None
    search = request.args.get("search") or None
    return jsonify({"items": list_inspections(Config.DATABASE_PATH, limit, status, search)}), 200


@app.route("/api/inspections/<inspection_id>", methods=["GET"])
@require_auth
def inspection_detail(inspection_id):
    inspection = get_inspection(Config.DATABASE_PATH, inspection_id)
    if not inspection:
        return jsonify({"error": "Inspection not found"}), 404
    return jsonify(inspection), 200


@app.route("/api/defect-types", methods=["GET"])
@require_auth
def get_defect_types():
    """Get list of detectable defect types."""
    try:
        detector = get_detector(DEFAULT_DEFECT_TYPE)
        detectable_types = list(detector.defect_classes.keys())
    except RuntimeError:
        detectable_types = []

    return jsonify(
        {
            "default_defect_type": DEFAULT_DEFECT_TYPE,
            "supported_modes": ["fabric"],
            "types": detectable_types,
            "unavailable_detectors": detector_errors,
            "descriptions": {
                "crack": "Surface or structural cracks",
                "scratch": "Surface scratches or abrasions",
                "hole": "Holes or punctures",
                "stain": "Discoloration or stains",
                "misalignment": "Incorrect positioning or alignment",
                "discoloration": "Color variations or fading",
            },
        }
    ), 200


@app.route("/api/batch-inspect", methods=["POST"])
@require_auth
def batch_inspect():
    """Inspect multiple images at once."""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist("files")
        confidence = parse_confidence(request.form.get("confidence", 0.35))
        results = []

        for file in files:
            if not file or not allowed_file(file.filename):
                continue

            original_name = secure_filename(file.filename)
            timestamp = f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"
            filename = f"{timestamp}_{original_name}"
            filepath = Config.UPLOAD_FOLDER / filename
            file.save(filepath)

            detector = get_detector(DEFAULT_DEFECT_TYPE)
            started_at = time.perf_counter()
            result = detector.detect_defects(str(filepath), confidence_threshold=confidence)
            processing_time_ms = round((time.perf_counter() - started_at) * 1000)

            if "error" in result:
                continue

            annotated_path = Config.RESULTS_FOLDER / f"annotated_{Path(filename).stem}.png"
            detector.save_annotated_image(result, str(annotated_path))
            report = detector.generate_inspection_report(result)
            inspection_id = f"{report['inspection_id']}_{secrets.token_hex(3)}"

            item = {
                "success": True,
                "inspection_id": inspection_id,
                "timestamp": report.get("timestamp", result["timestamp"]),
                "defect_type": DEFAULT_DEFECT_TYPE,
                "confidence": confidence,
                "processing_time_ms": processing_time_ms,
                "metadata": request_metadata(),
                "upload_path": str(filepath),
                "annotated_image_path": str(annotated_path),
                "image_info": report["image_info"],
                "summary": report["summary"],
                "defect_breakdown": report["defect_breakdown"],
                "severity_breakdown": report["severity_breakdown"],
                "detections": report["detections"],
                "recommendations": report["recommendations"],
            }
            save_inspection(Config.DATABASE_PATH, item)
            results.append(item)

        return jsonify({"success": True, "total_images": len(files), "processed": len(results), "results": results}), 200

    except Exception as exc:
        logging.exception("Unhandled batch inspection error")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/results/<path:filename>", methods=["GET"])
def get_result_image(filename):
    """Serve annotated inspection images created by the detector."""
    safe_filename = secure_filename(Path(filename).name)
    image_path = Config.RESULTS_FOLDER / safe_filename

    if not image_path.exists():
        return jsonify({"error": "Result image not found"}), 404

    return send_file(image_path)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logging.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Quality Inspection System API")
    print("Starting server at http://localhost:5000")
    print("Default login: admin / admin123")
    app.run(debug=True, host="0.0.0.0", port=5000)
