import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import qrcode
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, HexColor


# --------------------------------------------------
# THEME COLORS
# --------------------------------------------------

GOLD = HexColor("#C9A227")
SOFT_GOLD = HexColor("#E6D28A")
ACCENT_BLUE = HexColor("#3B6CFF")
WATERMARK_ALPHA = 0.06


# --------------------------------------------------
# IDENTITY HELPERS
# --------------------------------------------------

def _load_full_name(program_dir: Path) -> str:
    """
    Priority:
    1. state.json -> profile.username (UI-enforced full name)
    2. certificate_identity.json -> full_name (legacy / fallback)
    """

    # 1️⃣ Try state.json
    state_path = Path.home() / ".devopsmind" / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            username = state.get("profile", {}).get("username")
            if username and username.strip():
                return username.strip()
        except Exception:
            pass

    # 2️⃣ Fallback: certificate_identity.json
    identity_path = program_dir / "certificate_identity.json"
    if identity_path.exists():
        try:
            identity = json.loads(identity_path.read_text())
            full_name = identity.get("full_name")
            if full_name and full_name.strip():
                return full_name.strip()
        except Exception:
            pass

    # 3️⃣ Hard failure (no silent misuse)
    raise RuntimeError(
        "Full name not found. Please enter your full name in the DevOpsMind UI."
    )


# --------------------------------------------------
# DECOR HELPERS
# --------------------------------------------------

def _draw_background(c, w, h):
    c.setFillColorRGB(0.99, 0.99, 0.995)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(black)


def _rounded_border(c, x, y, w, h, r, lw, color):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, stroke=1, fill=0)
    c.setStrokeColor(black)


def _corner_flourish(c, x, y, flip_x=1, flip_y=1):
    c.saveState()
    c.translate(x, y)
    c.scale(flip_x, flip_y)
    c.setLineWidth(1)
    c.setStrokeColor(SOFT_GOLD)

    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(22, 6, 44, 22, 48, 48)
    p.curveTo(22, 44, 6, 22, 0, 0)
    c.drawPath(p)

    c.restoreState()


def _watermark_logo(c, w, h):
    logo = (
        Path(__file__).resolve().parents[4]
        / "docs"
        / "logo.png"
    )

    if not logo.exists():
        return

    c.saveState()
    c.setFillAlpha(WATERMARK_ALPHA)

    img = ImageReader(str(logo))
    iw, ih = img.getSize()

    wm_width = 12 * cm
    wm_height = wm_width * (ih / iw)

    c.drawImage(
        img,
        (w - wm_width) / 2,
        (h - wm_height) / 2,
        wm_width,
        wm_height,
        mask="auto",
    )

    c.restoreState()


# --------------------------------------------------
# CERTIFICATE GENERATOR
# --------------------------------------------------

def generate_certificate(program: str, program_dir: Path):

    cert_dir = program_dir / "certificate"
    cert_dir.mkdir(parents=True, exist_ok=True)

    # ✅ Full name resolution (state.json preferred)
    full_name = _load_full_name(program_dir)

    issued_at = datetime.now(timezone.utc)

    cert_id = f"DM-{program.upper()}-{issued_at.year}-{uuid.uuid4().hex[:8].upper()}"

    pdf_path = cert_dir / f"{program}-certificate.pdf"
    metadata_path = cert_dir / "metadata.json"
    checksum_path = cert_dir / "checksum.sha256"

    c = canvas.Canvas(str(pdf_path), pagesize=landscape(A4))
    width, height = landscape(A4)

    _draw_background(c, width, height)
    _watermark_logo(c, width, height)

    margin = 1.5 * cm

    # Gold Borders
    _rounded_border(
        c,
        margin,
        margin,
        width - 2 * margin,
        height - 2 * margin,
        r=26,
        lw=2.4,
        color=GOLD
    )

    _rounded_border(
        c,
        margin + 0.6 * cm,
        margin + 0.6 * cm,
        width - 3.2 * cm,
        height - 3.2 * cm,
        r=18,
        lw=1,
        color=SOFT_GOLD
    )

    # Corner flourishes
    fx = margin + 0.9 * cm
    fy = margin + 0.9 * cm
    fw = width - margin - 0.9 * cm
    fh = height - margin - 0.9 * cm

    _corner_flourish(c, fx, fy, 1, 1)
    _corner_flourish(c, fw, fy, -1, 1)
    _corner_flourish(c, fx, fh, 1, -1)
    _corner_flourish(c, fw, fh, -1, -1)

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(ACCENT_BLUE)
    c.drawCentredString(width / 2, height - 4.2 * cm, "DevOpsMind")

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(
        width / 2,
        height - 6.4 * cm,
        "Certificate of Completion"
    )

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.4)
    c.line(width * 0.3, height - 7.1 * cm, width * 0.7, height - 7.1 * cm)
    c.setStrokeColor(black)

    # --------------------------------------------------
    # BODY
    # --------------------------------------------------

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 9.3 * cm, "This certifies that")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(ACCENT_BLUE)
    c.drawCentredString(width / 2, height - 11.8 * cm, full_name)

    c.setFillColor(black)
    name_w = c.stringWidth(full_name, "Helvetica-Bold", 26)
    c.line(
        (width - name_w) / 2,
        height - 12.3 * cm,
        (width + name_w) / 2,
        height - 12.3 * cm
    )

    c.setFont("Helvetica", 14)
    c.drawCentredString(
        width / 2,
        height - 14.8 * cm,
        f"has successfully completed the {program.title()} Program"
    )

    # --------------------------------------------------
    # QR (LEFT)
    # --------------------------------------------------

    verify_url = f"https://devopsmind-relay.infraforgelabs.workers.dev/verify/{cert_id}"
    qr = qrcode.make(verify_url)
    qr_path = cert_dir / "verify_qr.png"
    qr.save(qr_path)

    qr_size = 3.2 * cm
    qr_x = margin + 1.4 * cm
    qr_y = margin + 2.8 * cm

    c.drawImage(
        ImageReader(str(qr_path)),
        qr_x,
        qr_y,
        qr_size,
        qr_size,
        mask="auto"
    )

    c.setFont("Helvetica", 9)
    c.drawString(qr_x, qr_y - 0.5 * cm, "Verify certificate")

    # --------------------------------------------------
    # FOOTER (RIGHT)
    # --------------------------------------------------

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(
        width - margin - 1.3 * cm,
        margin + 3.2 * cm,
        "Issued by InfraForgeLabs"
    )

    c.setFont("Helvetica", 10)
    c.drawRightString(
        width - margin - 1.3 * cm,
        margin + 2.4 * cm,
        f"Issued on {issued_at.strftime('%d %B %Y')}"
    )

    c.setFont("Helvetica", 9)
    c.drawString(
        margin + 1.4 * cm,
        margin + 1.2 * cm,
        f"Certificate ID: {cert_id}"
    )

    c.showPage()
    c.save()

    # --------------------------------------------------
    # CHECKSUM
    # --------------------------------------------------

    sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{sha256}  {pdf_path.name}\n")

    # --------------------------------------------------
    # METADATA
    # --------------------------------------------------

    metadata = {
        "program": program,
        "full_name": full_name,
        "certificate_id": cert_id,
        "issued_at": issued_at.isoformat(),
        "issued_by": "InfraForgeLabs",
        "verification_url": verify_url,
        "checksum_sha256": sha256,
        "theme": "gold-accent",
        "version": "3.0"
    }

    metadata_path.write_text(json.dumps(metadata, indent=2))
