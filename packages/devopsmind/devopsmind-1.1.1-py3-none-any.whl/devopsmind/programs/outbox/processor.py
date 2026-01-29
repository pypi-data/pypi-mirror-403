import json
import base64
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

DEVOPSMIND_RELAY = (
    "https://devopsmind-relay.infraforgelabs.workers.dev/cert/publish"
)


# --------------------------------------------------
# Payload builder
# --------------------------------------------------

def _load_certificate_payload(program_dir: Path) -> dict:
    cert_dir = program_dir / "certificate"

    metadata = json.loads((cert_dir / "metadata.json").read_text())
    checksum = (cert_dir / "checksum.sha256").read_text().split()[0]

    pdf_path = cert_dir / f"{metadata['program']}-certificate.pdf"
    pdf_bytes = pdf_path.read_bytes()
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    # Canonical local state (OFFLINE-FIRST)
    state = json.loads(
        (Path.home() / ".devopsmind/state.json").read_text()
    )
    profile = state.get("profile", {})

    if not profile.get("user_public_id"):
        raise RuntimeError("Missing user_public_id in profile state")

    payload = {
        # ---------------- IDENTITY ----------------
        "user_public_id": profile["user_public_id"],
        "username": profile.get("username"),

        # 🔑 delivery (hash preferred, email fallback)
        "email_hash": profile.get("email_hash"),
        "email": profile.get("email"),

        # ---------------- CERT DATA ----------------
        "program": metadata["program"],
        "certificate_id": metadata["certificate_id"],
        "issued_to": metadata["full_name"],
        "issued_at": metadata["issued_at"],
        "checksum_sha256": checksum,
        "version": metadata.get("version", "1.0"),

        # ---------------- SECURITY ----------------
        "nonce": datetime.now(timezone.utc).isoformat(),

        # ---------------- ATTACHMENT ----------------
        "pdf_base64": pdf_base64,
    }

    return payload


# --------------------------------------------------
# Publisher
# --------------------------------------------------

def publish_certificate(program_dir: Path):
    payload = _load_certificate_payload(program_dir)

    response = requests.post(
        DEVOPSMIND_RELAY,
        json=payload,
        timeout=15,
    )

    # 409 = already published (idempotent)
    if response.status_code not in (200, 201, 409):
        raise RuntimeError(
            f"Certificate publish failed: "
            f"{response.status_code} {response.text}"
        )


# --------------------------------------------------
# Outbox processor
# --------------------------------------------------

def _atomic_write(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def process_outbox(program_dir: Path):
    outbox_dir = program_dir / "outbox"
    if not outbox_dir.exists():
        return

    for entry_file in sorted(outbox_dir.glob("*.json")):
        entry = {}

        try:
            entry = json.loads(entry_file.read_text())

            if entry.get("status") == "sent":
                continue

            publish_certificate(program_dir)

            entry["status"] = "sent"
            entry["sent_at"] = datetime.now(timezone.utc).isoformat()
            entry.pop("last_error", None)

        except Exception as e:
            entry["status"] = entry.get("status", "pending")
            entry["last_error"] = str(e)
            entry["last_attempt_at"] = datetime.now(timezone.utc).isoformat()

        _atomic_write(entry_file, entry)


# --------------------------------------------------
# CLI entrypoint (internal)
# --------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: devopsmind-outbox <program_dir>", file=sys.stderr)
        sys.exit(1)

    program_dir = Path(sys.argv[1]).expanduser().resolve()
    if not program_dir.exists():
        print(f"Program dir not found: {program_dir}", file=sys.stderr)
        sys.exit(1)

    process_outbox(program_dir)


if __name__ == "__main__":
    main()
