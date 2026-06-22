import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inspections (
                inspection_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                upload_path TEXT NOT NULL,
                annotated_image_path TEXT NOT NULL,
                status TEXT NOT NULL,
                quality_score REAL NOT NULL,
                total_defects INTEGER NOT NULL,
                critical_defects INTEGER NOT NULL,
                medium_defects INTEGER NOT NULL,
                minor_defects INTEGER NOT NULL,
                confidence REAL NOT NULL,
                defect_type TEXT NOT NULL,
                operator_name TEXT,
                batch_id TEXT,
                fabric_type TEXT,
                production_line TEXT,
                shift TEXT,
                processing_time_ms INTEGER,
                image_info_json TEXT NOT NULL,
                defect_breakdown_json TEXT NOT NULL,
                detections_json TEXT NOT NULL,
                recommendations_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _loads(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value) if value else fallback
    except json.JSONDecodeError:
        return fallback


def row_to_inspection(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "inspection_id": row["inspection_id"],
        "timestamp": row["timestamp"],
        "filename": row["filename"],
        "upload_path": row["upload_path"],
        "annotated_image_path": row["annotated_image_path"],
        "summary": {
            "status": row["status"],
            "quality_score": row["quality_score"],
            "total_defects": row["total_defects"],
        },
        "severity_breakdown": {
            "critical": row["critical_defects"],
            "medium": row["medium_defects"],
            "minor": row["minor_defects"],
        },
        "confidence": row["confidence"],
        "defect_type": row["defect_type"],
        "metadata": {
            "operator_name": row["operator_name"] or "",
            "batch_id": row["batch_id"] or "",
            "fabric_type": row["fabric_type"] or "",
            "production_line": row["production_line"] or "",
            "shift": row["shift"] or "",
        },
        "processing_time_ms": row["processing_time_ms"],
        "image_info": _loads(row["image_info_json"], {}),
        "defect_breakdown": _loads(row["defect_breakdown_json"], {}),
        "detections": _loads(row["detections_json"], []),
        "recommendations": _loads(row["recommendations_json"], []),
        "created_at": row["created_at"],
    }


def save_inspection(db_path: Path, inspection: Dict[str, Any]) -> None:
    summary = inspection["summary"]
    severity = inspection["severity_breakdown"]
    metadata = inspection.get("metadata", {})

    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO inspections (
                inspection_id,
                timestamp,
                filename,
                upload_path,
                annotated_image_path,
                status,
                quality_score,
                total_defects,
                critical_defects,
                medium_defects,
                minor_defects,
                confidence,
                defect_type,
                operator_name,
                batch_id,
                fabric_type,
                production_line,
                shift,
                processing_time_ms,
                image_info_json,
                defect_breakdown_json,
                detections_json,
                recommendations_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inspection["inspection_id"],
                inspection["timestamp"],
                inspection["image_info"]["filename"],
                inspection["upload_path"],
                inspection["annotated_image_path"],
                summary["status"],
                summary["quality_score"],
                summary["total_defects"],
                severity["critical"],
                severity["medium"],
                severity["minor"],
                inspection["confidence"],
                inspection["defect_type"],
                metadata.get("operator_name", ""),
                metadata.get("batch_id", ""),
                metadata.get("fabric_type", ""),
                metadata.get("production_line", ""),
                metadata.get("shift", ""),
                inspection.get("processing_time_ms"),
                json.dumps(inspection["image_info"]),
                json.dumps(inspection["defect_breakdown"]),
                json.dumps(inspection["detections"]),
                json.dumps(inspection["recommendations"]),
            ),
        )
        conn.commit()


def list_inspections(
    db_path: Path,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM inspections"
    clauses = []
    params: List[Any] = []

    if status:
        clauses.append("status = ?")
        params.append(status.upper())

    if search:
        clauses.append("(filename LIKE ? OR batch_id LIKE ? OR operator_name LIKE ?)")
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [row_to_inspection(row) for row in rows]


def get_inspection(db_path: Path, inspection_id: str) -> Optional[Dict[str, Any]]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,)).fetchone()
        return row_to_inspection(row) if row else None


def get_stats(db_path: Path) -> Dict[str, Any]:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS passed,
                SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS failed,
                AVG(quality_score) AS avg_quality_score,
                AVG(processing_time_ms) AS avg_processing_time_ms
            FROM inspections
            """
        ).fetchone()

    total = row["total"] or 0
    return {
        "total_inspections": total,
        "passed": row["passed"] or 0,
        "failed": row["failed"] or 0,
        "avg_quality_score": round(row["avg_quality_score"] or 0, 2),
        "avg_processing_time_ms": round(row["avg_processing_time_ms"] or 0, 2),
    }
