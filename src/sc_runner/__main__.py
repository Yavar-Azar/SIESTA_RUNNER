# __main__.py
import logging
import random
import string
import argparse
from multiprocessing import Process
from sc_runner.runner import run_calculation
from sc_runner.monitor import monitor_job
from sc_runner.constants import LOG_FILE, output_file_path, backend_url
from sc_runner.analyse.analyse_results import Analysis
from sc_runner.types import ProjectType
import os
import time
from sc_runner.types import ProjectType


def generate_random_token(length=12):
    """
    Generate a random token of the given length.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def main():
    # Read token and project ID from environment variables
    project_id = os.getenv('PROJECT_ID')
    token = os.getenv('TOKEN')

    if not project_id:
        logging.warning("PROJECT_ID is not set. Using default value 'default_project_id'.")
        project_id = 1001

    if not token:
        logging.warning("TOKEN is not set. Generating a random token.")
        token = generate_random_token()

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run SIESTA calculations with optional geometry optimization.")
    parser.add_argument(
        '--project-type',
        type=str,
        choices=['single_point', 'geometry_optimization', 'md'],
        default='single_point',
        help="Specify the project type. Default is single_point."
    )
    args = parser.parse_args()

    # Map project type argument to ProjectType enum
    project_type = ProjectType[args.project_type.upper()]

    # Set up logging
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Set up processes for calculation and monitoring
    job_process = Process(target=run_calculation, args=(project_type,))
    monitor_process = Process(target=monitor_job, args=(output_file_path, project_id, token, backend_url))

    # Start processes
    job_process.start()
    monitor_process.start()

    # Wait for job completion
    job_process.join()
    time.sleep(2)

    # Perform analysis after calculation
    Analysis(project_type=project_type).perform_analysis()

    # Stop the monitor process
    monitor_process.terminate()


if __name__ == "__main__":
    main()
