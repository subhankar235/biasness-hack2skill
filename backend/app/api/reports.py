from fastapi import APIRouter
from fastapi.responses import Response
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

router = APIRouter()

@router.get("/pdf")
def generate_pdf():
    buffer = BytesIO()

    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 22)
    p.drawString(50, 800, "FairLens Audit Report")

    p.setFont("Helvetica", 12)
    p.drawString(50, 770, f"Generated: {datetime.now()}")

    y = 730

    lines = [
        "Rows: 8",
        "Columns: 4",
        "Missing Values: 0",
        "Sensitive Columns: gender, age",
        "",
        "Male Approval: 1.0",
        "Female Approval: 0.25",
        "Parity Difference: 0.75",
        "Risk Level: HIGH",
        "",
        "Recommendation:",
        "Review thresholds and retrain model."
    ]

    for line in lines:
        p.drawString(50, y, line)
        y -= 25

    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            "attachment; filename=fairlens_report.pdf"
        }
    )