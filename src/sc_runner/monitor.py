"""."""
import logging
import os
import time
from sc_runner.signal_sender import send_update
from sc_runner.constants import REQUEST_INTERVAL

def monitor_job(output_file_path: str, project_id: int, token: str, backend_url: str):
    """
    Monitors the job status and file changes, sending updates when changes are detected.
    """
    initial_mod_time = os.path.getmtime(output_file_path) if os.path.exists(output_file_path) else 0

    while True:
        if os.path.exists(output_file_path) and os.path.getmtime(output_file_path) > initial_mod_time:
            send_update(project_id, status='ruuning', token=token, backend_url=backend_url)
            initial_mod_time = os.path.getmtime(output_file_path)
            logging.info(f"File modified for project {project_id}, update sent.")

        time.sleep(REQUEST_INTERVAL)
