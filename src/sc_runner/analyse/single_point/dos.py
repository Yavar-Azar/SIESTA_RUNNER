"""."""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np  # type: ignore
from sc_runner.constants import CALC_RESULT_JSON


def process_dos_file(
    dos_filename: str, output_json_filename: str = 'DOS.json', spin_polarized: bool = False
) -> None:
    """Reads a DOS file from SIESTA and creates a JSON file suitable for Plotly visualization.

    The function processes the DOS data to calculate the total DOS, spin-up
    and spin-down DOS (if spin-polarized), the difference between spin-up and
    spin-down DOS, and their respective integrals using the trapezoidal rule.

    Args:
        dos_filename (str): Path to the DOS file.
        output_json_filename (str): Path where the output JSON will be saved. Defaults to 'DOS.json'.
        spin_polarized (bool): True if the DOS data is spin-polarized, False otherwise. Defaults to False.
    """
    results = json.loads(Path(CALC_RESULT_JSON).read_text())
    fermi_energy = results['fermi_energy']
    # Load data from the DOS file
    data = np.loadtxt(dos_filename)
    # Extract energy column
    energy: List[float] = data[:, 0].tolist()
    delta_E: float = data[1, 0] - data[0, 0]  # Assume uniform energy spacing

    if spin_polarized:
        # Extract spin-up and spin-down columns
        spin_up: np.ndarray = data[:, 1]
        spin_down: np.ndarray = data[:, 2]
        # Calculate total DOS as the sum of spin-up and spin-down
        total_dos: np.ndarray = spin_up + spin_down
        # Calculate difference between spin-up and spin-down
        difference: np.ndarray = spin_up - spin_down
        # Calculate integrals using trapezoidal rule for more accuracy
        cumulative_spin_up: List[float] = np.trapz(spin_up, dx=delta_E).tolist()
        cumulative_spin_down: List[float] = np.trapz(spin_down, dx=delta_E).tolist()
        cumulative_total_dos = np.trapz(total_dos, dx=delta_E).tolist()
        cumulative_difference: List[float] = np.trapz(difference, dx=delta_E).tolist()
        # Convert arrays to lists for JSON serialization
        spin_up = spin_up.tolist()
        spin_down = spin_down.tolist()
        total_dos = total_dos.tolist()
        difference = difference.tolist()

    else:
        # Non-spin-polarized case: only total DOS is present
        total_dos = data[:, 1]
        # Calculate the integral for the non-polarized total DOS
        cumulative_total_dos = np.trapz(total_dos, dx=delta_E).tolist()
        # Set spin-up and spin-down related variables to empty lists
        spin_up, spin_down, difference = [], [], []
        cumulative_spin_up, cumulative_spin_down, cumulative_difference = [], [], []
        # Convert total DOS to list for JSON serialization
        total_dos = total_dos.tolist()
    # Construct the JSON object
    json_data: Dict = {
        "fermi_energy": fermi_energy,
        "energy": energy,
        "total_dos": total_dos,
        "spin_up": spin_up,
        "spin_down": spin_down,
        "difference": difference,
        "cumulative_spin_up": cumulative_spin_up,
        "cumulative_spin_down": cumulative_spin_down,
        "cumulative_total_dos": cumulative_total_dos,
        "cumulative_difference": cumulative_difference,
        "metadata": {
            "units": {"energy": "eV", "dos": "states/eV"},
            "spin_polarized": spin_polarized,
        },
    }
    # Save JSON to file
    with open(output_json_filename, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
