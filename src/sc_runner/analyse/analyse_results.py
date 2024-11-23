import logging
import os
from sc_runner.constants import (
    CALC_RESULT_JSON,
    GENERAL_INFO_JSON,
    POTENTIAL_GRID,
    RHO_GRID,
    SIESTA_OUT,
)
from sc_runner.analyse.single_point.dos import process_dos_file
from sc_runner.analyse.single_point.netcdf_to_json import nc_parser
from sc_runner.analyse.single_point.band_plotly_json import plot_band_go
from sc_runner.analyse.single_point.siesta_output_parser import extract_selected_results
from sc_runner.types import ProjectType
from sc_runner.analyse.analyse_trajectory import TrajectoryAnalysis
from sc_runner.analyse.single_point.pdos import PdosAnalyse


def setup_logging(log_file: str = "task_log.log", level: int = logging.INFO) -> None:
    """Sets up the logging configuration.

    Args:
        log_file (str): The file to which logs will be written.
        level (int): The logging level.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


class Analysis:
    """Class for performing different types of analysis with both shared and specific logic."""

    def __init__(self, project_type: ProjectType) -> None:
        """Initializes the analysis class with the specified project type.

        Args:
            project_type (ProjectType): The type of analysis to perform.

        Raises:
            ValueError: If the project_type is unknown.
        """
        self.project_type = project_type
        if self.project_type not in ProjectType:
            raise ValueError(f"Unknown project type: {self.project_type}")
        logging.info(f"Initialized Analysis with project type: {self.project_type.value}")

    def perform_analysis(self) -> None:
        """Performs the analysis based on the project type."""
        logging.info(f"Starting analysis for project type: {self.project_type.value}")
        self._prepare()

        try:
            if self.project_type == ProjectType.SINGLE_POINT:
                self._analyze_single_point()
            elif self.project_type == ProjectType.MD:
                self._analyze_md()
            elif self.project_type == ProjectType.RELAX:
                self._analyze_relax()
        except Exception as e:
            logging.error(f"Error during {self.project_type.value} analysis: {e}")
        finally:
            self._cleanup()

    def _prepare(self) -> None:
        """Common preparation steps before analysis."""
        logging.info("Preparing for analysis...")

    def _cleanup(self) -> None:
        """Common cleanup steps after analysis."""
        logging.info("Cleaning up after analysis...")

    def _analyze_single_point(self) -> None:
        """Performs SinglePoint-specific analysis."""
        logging.info("Performing SinglePoint analysis...")
        analyse_tasks = [
            (
                extract_selected_results,
                {
                    "results_json_path": CALC_RESULT_JSON,
                    "siesta_out_path": SIESTA_OUT,
                    "output_json_path": GENERAL_INFO_JSON,
                },
            ),
            (plot_band_go, {}),
            (process_dos_file, {"dos_filename": "siesta.DOS"}),
            (nc_parser, {"grid_nc_file": RHO_GRID}),
            (nc_parser, {"grid_nc_file": POTENTIAL_GRID}),
        ]
        for func, kwargs in analyse_tasks:
            try:
                func(**kwargs)  # type: ignore
                logging.info(f"Task {func.__name__} completed successfully.")
            except Exception as e:
                logging.error(f"Error in SinglePoint analysis task {func.__name__}: {e}")

        # Add PDOS analysis
        try:
            pdos_file = "./siesta.PDOS.xml"  # Path to the PDOS file
            pdos_output = "./pdos_data.json"  # Output path for PDOS JSON
            if os.path.exists(pdos_file):
                pdos_analyser = PdosAnalyse(pdos_file)
                pdos_analyser.write_json(pdos_output)
                logging.info(f"PDOS analysis completed and data written to {pdos_output}.")
            else:
                logging.warning(f"PDOS file {pdos_file} not found. Skipping PDOS analysis.")
        except Exception as e:
            logging.error(f"Error during PDOS analysis: {e}")

    def _analyze_md(self) -> None:
        """Performs MD-specific analysis."""
        logging.info("Performing MD analysis...")
        try:
            # Add MD-specific analysis code here
            pass
        except Exception as e:
            logging.error(f"Error in MD analysis: {e}")
            raise

    def _analyze_relax(self) -> None:
        """Performs Relax-specific (geometry optimization) analysis."""
        logging.info("Performing Relax (geometry optimization) analysis...")
        try:
            trajectory_file = "geometry_optimization.traj"
            output_json_file = "trajectory_analysis.json"

            if not os.path.exists(trajectory_file):
                raise FileNotFoundError(f"Trajectory file '{trajectory_file}' not found.")

            analysis = TrajectoryAnalysis(trajectory_file)
            analysis.save_to_json(output_json_file)
            logging.info(f"Trajectory analysis data saved to {output_json_file}.")
        except Exception as e:
            logging.error(f"Error during Relax analysis: {e}")
            raise


if __name__ == "__main__":
    setup_logging()
    try:
        analysis = Analysis(ProjectType.SINGLE_POINT)
        analysis.perform_analysis()
    except ValueError as ve:
        logging.error(f"Initialization error: {ve}")
