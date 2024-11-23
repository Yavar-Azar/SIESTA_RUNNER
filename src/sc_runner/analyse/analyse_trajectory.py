import os
import json
import numpy as np
from ase.io.trajectory import Trajectory
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TrajectoryAnalysis:
    def __init__(self, trajectory_file: str = 'geometry_optimization.traj'):
        """
        Initialize the trajectory analysis module.

        Parameters:
            trajectory_file (str): Path to the ASE trajectory file.
        """
        self.trajectory_file = trajectory_file
        if not os.path.exists(self.trajectory_file):
            raise FileNotFoundError(f"Trajectory file '{self.trajectory_file}' not found.")
        self.traj = Trajectory(self.trajectory_file)

    def extract_energies(self):
        """
        Extract potential energies for each step in the trajectory.

        Returns:
            list: List of potential energies.
        """
        logging.info("Extracting potential energies from trajectory.")
        return [atoms.get_potential_energy() for atoms in self.traj]

    def extract_forces(self):
        """
        Extract total forces (magnitude) at each step in the trajectory.

        Returns:
            list: List of force magnitudes.
        """
        logging.info("Extracting forces from trajectory.")
        return [np.linalg.norm(np.sum(atoms.get_forces(), axis=0)) for atoms in self.traj]

    def extract_positions(self):
        """
        Extract atomic positions for each step in the trajectory.

        Returns:
            list: List of atomic positions as 2D arrays for each step.
        """
        logging.info("Extracting atomic positions from trajectory.")
        return [atoms.get_positions().tolist() for atoms in self.traj]

    def extract_step_data(self):
        """
        Extract a summary of trajectory data including energies, forces, and positions.

        Returns:
            dict: Structured data containing step-wise energies, forces, and positions.
        """
        energies = self.extract_energies()
        forces = self.extract_forces()
        positions = self.extract_positions()

        step_data = {
            "steps": [
                {
                    "step": i + 1,
                    "energy": energies[i],
                    "force_magnitude": forces[i],
                    "positions": positions[i],
                }
                for i in range(len(self.traj))
            ]
        }

        return step_data

    def save_to_json(self, output_file: str):
        """
        Save trajectory analysis data to a JSON file.

        Parameters:
            output_file (str): Path to save the JSON file.
        """
        logging.info("Saving trajectory analysis data to JSON.")
        data = self.extract_step_data()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {output_file}")


# Example usage
if __name__ == "__main__":
    trajectory_file = "geometry_optimization.traj"  # Update this to your trajectory file path
    output_json_file = "trajectory_analysis.json"  # JSON output path

    try:
        analysis = TrajectoryAnalysis(trajectory_file)
        analysis.save_to_json(output_json_file)
        logging.info("Trajectory analysis completed successfully.")
    except Exception as e:
        logging.error(f"Error during trajectory analysis: {e}")
