import os
import time

MAX_AGE_SECONDS = 1800  # 30 minutes retention

def purge_old_files(directories: list[str]) -> None:
    """Deletes files in the target directories older than MAX_AGE_SECONDS."""
    now = time.time()
    for directory in directories:
        if not os.path.exists(directory):
            continue
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    if now - os.path.getmtime(file_path) > MAX_AGE_SECONDS:
                        os.remove(file_path)
            except Exception as e:
                print(f"[Cleanup Error] Unable to remove {file_path}: {e}")