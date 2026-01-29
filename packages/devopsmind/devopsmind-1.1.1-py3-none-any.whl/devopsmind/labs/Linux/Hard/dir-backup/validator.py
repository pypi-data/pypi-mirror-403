#!/usr/bin/env python3
import os
import tarfile

def validate():
    data_dir = "data"
    archive = "backup.tar.gz"
    script = "backup.sh"

    # --- Required script ---
    if not os.path.exists(script):
        message = "backup.sh not found."
        return False, message

    # --- Required data directory ---
    if not os.path.isdir(data_dir):
        message = "Directory 'data' not found in working directory."
        return False, message

    # --- Required archive ---
    if not os.path.exists(archive):
        message = "backup.tar.gz not found. Run backup.sh to create it."
        return False, message

    # --- Verify archive contents ---
    try:
        with tarfile.open(archive, "r:gz") as tf:
            names = tf.getnames()
    except tarfile.TarError as e:
        message = f"Failed to read archive: {e}"
        return False, message

    has_data = any(
        name == data_dir or name.startswith(f"{data_dir}/")
        for name in names
    )

    if not has_data:
        message = "Archive does not contain the 'data' directory and its files."
        return False, message

    message = "backup.tar.gz contains the data directory. Backup is correct."
    return True, message

if __name__ == "__main__":
    ok, message = validate()
    print(message)
