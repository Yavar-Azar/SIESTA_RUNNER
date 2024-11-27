import json
import logging
import random
import string
import os
import time
from multiprocessing import Process
from sc_runner.runner import run_calculation
from sc_runner.monitor import monitor_job
from sc_runner.constants import LOG_FILE, output_file_path, backend_url
from sc_runner.analyse.analyse_results import Analysis
from sc_runner.types import ProjectType


PARAMETERS_JSON = 'parameters.json'

def generate_random_token(length=12):
    """
    Generate a random token of the given length.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def check_siesta_completion(output_):
    """
    Check if 'Job completed' is present in the last non-empty line of siesta.out.
    """
    try:
        with open(output_, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            if lines and lines[-1] == "Job completed":
                return True
            else:
                logging.warning(
                    "SIESTA job did not complete successfully. No 'Job completed' message found in the last meaningful line.")
                return False
    except FileNotFoundError:
        logging.error(f"Output file {output_} not found.")
        return False
    except Exception as e:
        logging.error(f"Error reading output file {output_}: {e}")
        return False

def load_parameters(file_path):
    """
    Load parameters from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed parameters dictionary.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Parameters file {file_path} not found.")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {file_path}: {e}")
        raise

def main():
    """
    Main function to coordinate calculation, monitoring, and analysis.
    """
    # Read token and project ID from environment variables
    project_id = os.getenv('PROJECT_ID')
    token = os.getenv('TOKEN')

    if not project_id:
        logging.warning("PROJECT_ID is not set. Using default value 'default_project_id'.")
        project_id = 1001

    if not token:
        logging.warning("TOKEN is not set. Generating a random token.")
        token = generate_random_token()

    # Load parameters from JSON file
    try:
        parameters = load_parameters(PARAMETERS_JSON)
        project_type_str = parameters.get("projectType", "single_point").lower()  # Default to 'single_point'
        project_type = ProjectType[project_type_str.upper()]
    except KeyError:
        logging.error("Invalid project_type in parameters.json. Defaulting to 'single_point'.")
        project_type = ProjectType.SINGLE_POINT
    except Exception as e:
        logging.error(f"Error loading or parsing parameters.json: {e}. Defaulting to 'single_point'.")
        project_type = ProjectType.SINGLE_POINT

    # Set up logging
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Set up processes for calculation and monitoring
    job_process = Process(target=run_calculation, args=(project_type,))
    monitor_process = Process(target=monitor_job, args=(output_file_path, project_id, token, backend_url))

    try:
        # Start processes
        logging.info(f"Starting job process with project type: {project_type}.")
        job_process.start()
        logging.info("Starting monitor process.")
        monitor_process.start()

        # Wait for job completion
        job_process.join()
        time.sleep(2)

        # Check if the job completed successfully
        if check_siesta_completion(output_file_path):
            logging.info("Job completed successfully. Starting analysis.")
            Analysis(project_type=project_type).perform_analysis()
        else:
            logging.error("Analysis skipped due to incomplete job.")
    except Exception as e:
        logging.error(f"Error during job or monitoring processes: {e}")
    finally:
        # Ensure monitor process is terminated
        logging.info("Terminating monitor process.")
        monitor_process.terminate()

if __name__ == "__main__":
    main()
