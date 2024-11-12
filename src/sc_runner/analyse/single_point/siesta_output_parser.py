"""."""


import json
import logging
import math
from pathlib import Path
from typing import Dict, Optional

from sc_runner.constants import (  # type: ignore
    CALC_RESULT_JSON,
    GENERAL_INFO_JSON,
    SIESTA_OUT,
)


def setup_logging(log_file: str = "runner.log", level: int = logging.INFO) -> None:
    """Sets up the logging configuration.

    Args:
        log_file (str): The file to which logs will be written.
        level (int): The logging level.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def extract_siesta_data(file_path: str) -> Dict[str, Optional[float]]:
    """Extracts relevant data from a Siesta output file.

    Args:
        file_path (str): The path to the Siesta output file.

    Returns:
        Dict[str, Optional[float]]: A dictionary containing the number of electrons and the norm of the force,
        or None if not found.
    """
    results = {'number_of_electrons': None, 'norm_of_force': None}
    last_tot_line = None

    try:
        # Read the entire file content as a single string
        content = Path(file_path).read_text()
        # Iterate over each line in the file
        for line in content.splitlines():
            if 'Total number of electrons:' in line:
                results['number_of_electrons'] = float(line.split()[-1])  # type: ignore
            elif line.startswith('   Tot   '):
                last_tot_line = line
        # If a 'Tot' line was found, compute the norm of the force
        if last_tot_line:
            try:
                _, x_str, y_str, z_str = last_tot_line.split()
                x, y, z = float(x_str), float(y_str), float(z_str)
                tot_force = math.sqrt(x**2 + y**2 + z**2)
                results['Total_force'] = round(tot_force, 6)  # type: ignore
            except ValueError:
                logging.error("Couldn't convert extracted force components to float.")

    except FileNotFoundError:
        logging.error(f"The file {file_path} was not found.")
    except IOError:
        logging.error(f"An IO error occurred while reading the file {file_path}.")

    return results  # type: ignore


def extract_selected_results(
    results_json_path: str, siesta_out_path: str, output_json_path: str
) -> None:
    """Extracts selected results from JSON and Siesta output files and writes to an output JSON file.

    Args:
        results_json_path (str): Path to the JSON file with results.
        siesta_out_path (str): Path to the Siesta output file.
        output_json_path (str): Path to the output JSON file.
    """
    selected_results = {}
    try:
        data = json.loads(Path(results_json_path).read_text())
        n_spin, n_k, n_eig = data['eigenvalues']['__ndarray__'][0]
        # Add spin, k-points, and eigenvalues to results
        selected_results.update(
            {
                'n_spin': n_spin,
                'n_k': n_k,
                'n_eig': n_eig,
                'fermi_energy': data['fermi_energy'],
                'energy': data['energy'],
            }
        )
        # Extract relevant data from Siesta output in one go
        siesta_data = extract_siesta_data(file_path=siesta_out_path)
        selected_results.update(siesta_data)
        # Calculate n_occupied if all necessary data is available
        if all([n_spin, n_k, n_eig, selected_results['number_of_electrons']]):
            selected_results['n_occupied'] = n_spin * (selected_results['number_of_electrons'] / 2)

    except FileNotFoundError:
        logging.error(f"The file {results_json_path} was not found.")
    except IOError:
        logging.error(f"An IO error occurred while reading the file {results_json_path}.")
    # Write results to the output JSON file
    Path(output_json_path).write_text(json.dumps(selected_results))


# Example usage
if __name__ == "__main__":
    setup_logging()
    extract_selected_results(
        results_json_path=CALC_RESULT_JSON,
        siesta_out_path=SIESTA_OUT,
        output_json_path=GENERAL_INFO_JSON,
    )
