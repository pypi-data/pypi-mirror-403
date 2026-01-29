from pathlib import Path
import shutil
import subprocess
import importlib
from datetime import datetime


def open_or_preview_certificate(program: str):
    """
    Opens final certificate if it exists.
    Otherwise generates and opens a preview certificate.

    Program-agnostic. Future-proof for InfraHack.
    """

    devopsmind_home = Path.home() / ".devopsmind"
    program_dir = devopsmind_home / "programs" / program
    cert_dir = program_dir / "certificate"

    if not program_dir.exists():
        raise RuntimeError(f"Program '{program}' not found.")

    # -------------------------------
    # Case 1: Final certificate exists
    # -------------------------------
    final_pdf = cert_dir / f"{program}-certificate.pdf"
    if final_pdf.exists():
        _open_pdf(final_pdf)
        return final_pdf, "final"

    # -------------------------------
    # Load program cert backend
    # -------------------------------
    try:
        cert_module = importlib.import_module(
            f"devopsmind.programs.{program}.cert.generator"
        )
    except ModuleNotFoundError:
        raise RuntimeError(
            f"Program '{program}' does not support certificates."
        )

    generate_certificate = getattr(cert_module, "generate_certificate", None)
    if not generate_certificate:
        raise RuntimeError(
            f"Program '{program}' certificate backend is invalid."
        )

    # -------------------------------
    # Preview path (safe)
    # -------------------------------
    identity = program_dir / "certificate_identity.json"
    if not identity.exists():
        raise RuntimeError(
            "Certificate name not found.\n"
            "Start the program once to set your certificate name."
        )

    preview_root = devopsmind_home / "tmp" / "certificate-preview"
    preview_root.mkdir(parents=True, exist_ok=True)

    temp_program_dir = preview_root / f"{program}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copytree(program_dir, temp_program_dir)

    # Program-specific preview generation
    generate_certificate(program, temp_program_dir)

    preview_pdf = temp_program_dir / "certificate" / f"{program}-certificate.pdf"
    _open_pdf(preview_pdf)

    return preview_pdf, "preview"


def _open_pdf(path: Path):
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", str(path)])
    elif shutil.which("open"):  # macOS
        subprocess.Popen(["open", str(path)])
