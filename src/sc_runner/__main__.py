# __main__.py
import logging
from multiprocessing import Process
from sc_runner.runner import run_calculation
from sc_runner.monitor import monitor_job
from sc_runner.constants import LOG_FILE, output_file_path, backend_url
from sc_runner.analyse.analyse_results import Analysis
from sc_runner.types import ProjectType
import os
import time

def main():
    project_id = os.getenv('PROJECT_ID')
    token = os.getenv('TOKEN')

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    job_process = Process(target=run_calculation)
    monitor_process = Process(target=monitor_job, args=(  output_file_path, project_id, token, backend_url))

    job_process.start()
    monitor_process.start()

    job_process.join()
    time.sleep(2)
    Analysis(project_type=ProjectType.SINGLE_POINT).perform_analysis()

    monitor_process.terminate()



if __name__ == "__main__":
    main()
