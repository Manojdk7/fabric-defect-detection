from datetime import datetime
from fpdf import FPDF


OUTPUT_FILE = "Quality_Inspection_Current_Project_Report.pdf"


SECTIONS = [
    (
        "Abstract",
        [
            "This report presents the current implementation status of the Quality Inspection System developed for automated fabric defect detection.",
            "The project combines a React frontend, a Flask backend, and YOLOv8-based computer vision models to inspect uploaded images and generate inspection results.",
            "The system supports health checks, single-image inspection, batch inspection, confidence-based inference, and annotated result generation.",
            "At its current stage, the project is a working prototype suitable for demonstration, learning, and further model improvement.",
        ],
    ),
    (
        "Introduction",
        [
            "Quality inspection is a critical requirement in textile manufacturing because missed defects directly affect product quality, cost, and customer satisfaction.",
            "Manual inspection is slow, inconsistent, and dependent on operator attention.",
            "This project was designed to explore how AI-based image inspection can reduce manual effort and support faster quality decisions.",
            "The present system focuses mainly on fabric defect analysis through a web-based workflow.",
        ],
    ),
    (
        "Literature Survey",
        [
            "Recent quality inspection systems often rely on deep learning object detectors such as YOLO because they provide fast inference and support real-time applications.",
            "Computer vision frameworks like OpenCV are commonly used for image preprocessing, annotation, and visualization.",
            "Flask is a lightweight backend framework widely used for AI inference APIs, while React is popular for dashboard-style user interfaces.",
            "This project follows that modern pattern by combining YOLOv8, Flask, React, and OpenCV into one end-to-end inspection workflow.",
        ],
    ),
    (
        "Objectives",
        [
            "To build a web-based quality inspection system for defect detection.",
            "To integrate a machine learning model with a usable frontend and backend workflow.",
            "To support upload, inspection, result viewing, and confidence-based analysis.",
            "To create a practical academic project that can be extended into a stronger industrial inspection solution.",
        ],
    ),
    (
        "Project Scope and Overview",
        [
            "The current project scope includes image upload, API-based processing, model inference, result summarization, and annotated image storage.",
            "The React application provides the user interface, while the Flask API handles inspection requests.",
            "The detection pipeline currently supports fabric inspection most actively; PCB-related structure exists in code but is not yet the main validated path.",
            "The project also contains model retraining and validation scripts for future improvement work.",
        ],
    ),
    (
        "Technical Stack",
        [
            "Frontend: React 18, React Scripts, custom CSS.",
            "Backend: Python, Flask, Flask-CORS, Werkzeug.",
            "AI / CV: Ultralytics YOLOv8, PyTorch, OpenCV, NumPy.",
            "Project structure: app.py for API, defect_detector.py for inference logic, inspection-dashboard/ for UI, uploads/ and inspection_results/ for runtime files.",
        ],
    ),
    (
        "System Architecture & Methodology",
        [
            "Step 1: The user uploads an image through the React dashboard.",
            "Step 2: The frontend sends the image and confidence threshold to the Flask API endpoint /api/inspect.",
            "Step 3: The backend validates the file, stores it locally, and invokes the defect detector.",
            "Step 4: The detector loads the best available fabric model and can use a fallback defect model if the primary model misses a defect.",
            "Step 5: OpenCV draws annotations, the backend generates a structured report, and the frontend displays PASS or FAIL with details.",
        ],
    ),
    (
        "Key Implementation Features",
        [
            "Backend health check endpoint for connectivity testing.",
            "Single-image inspection and batch inspection API routes.",
            "Confidence slider in the frontend for tuning sensitivity.",
            "Annotated image generation and storage in inspection_results/.",
            "Result summary including total defects, severity breakdown, defect breakdown, recommendations, and quality score.",
            "Current debugging improvements include corrected frontend-backend integration and better model selection logic.",
        ],
    ),
    (
        "Conclusion",
        [
            "The Quality Inspection System is currently a functional prototype with successful frontend-backend integration and end-to-end inspection workflow.",
            "The system can upload images, process them through the backend, and return defect analysis results through a modern web interface.",
            "However, model accuracy still depends on the quality of the trained datasets and the chosen weights.",
            "The project is suitable for academic presentation and can be improved further through retraining, dataset expansion, and performance validation.",
        ],
    ),
    (
        "Reference",
        [
            "1. Ultralytics YOLOv8 documentation.",
            "2. Flask documentation.",
            "3. React documentation.",
            "4. OpenCV documentation.",
            "5. PyTorch documentation.",
            "6. MVTec AD dataset resources used for defect-detection experimentation.",
        ],
    ),
]


class ProjectReportPDF(FPDF):
    def header(self):
        if self.page_no() >= 2:
            self.set_font("Helvetica", "", 10)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Team Name | Swavik Internship", 0, 1, "R")
            self.set_draw_color(80, 80, 80)
            self.rect(8, 8, 194, 281)
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, str(self.page_no()), 0, 0, "R")


def add_cover_page(pdf: ProjectReportPDF):
    month_year = datetime.now().strftime("%B %Y")

    pdf.add_page()
    pdf.rect(8, 8, 194, 281)

    pdf.set_y(30)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "QUALITY INSPECTION SYSTEM", 0, 1, "C")

    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, "Project Report", 0, 1, "C")
    pdf.ln(18)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Submitted by", 0, 1, "C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 13)
    for index in range(1, 5):
        pdf.cell(0, 8, f"{index}. Name {index}", 0, 1, "C")

    pdf.ln(18)
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, "Mentor / Guide:", 0, 1, "C")
    pdf.cell(0, 8, "Your Guide name, SWAVIK Internship Program", 0, 1, "C")

    pdf.ln(18)
    pdf.cell(0, 8, "Institution:", 0, 1, "C")
    pdf.cell(0, 8, "Clg Name.......", 0, 1, "C")
    pdf.cell(0, 8, f"Month & Year: {month_year}", 0, 1, "C")


def add_index_page(pdf: ProjectReportPDF):
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 14, "INDEX", 0, 1, "L")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(25, 8, "Sl. No.", 0, 0)
    pdf.cell(110, 8, "Title", 0, 0)
    pdf.cell(35, 8, "Page No.", 0, 1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 12)
    start_page = 3
    for index, (title, _) in enumerate(SECTIONS, start=1):
        pdf.cell(25, 8, str(index), 0, 0)
        pdf.cell(110, 8, title, 0, 0)
        pdf.cell(35, 8, str(start_page), 0, 1)
        start_page += 1


def add_section_page(pdf: ProjectReportPDF, title: str, paragraphs):
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 12, title.upper(), 0, 1, "L")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(25, 25, 25)

    for paragraph in paragraphs:
        pdf.multi_cell(0, 8, paragraph)
        pdf.ln(3)


def create_pdf():
    pdf = ProjectReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_title("Quality Inspection System - Current Project Report")
    pdf.set_author("OpenAI Codex")

    add_cover_page(pdf)
    add_index_page(pdf)

    for title, paragraphs in SECTIONS:
        add_section_page(pdf, title, paragraphs)

    pdf.output(OUTPUT_FILE)
    print(f"PDF report created: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_pdf()
