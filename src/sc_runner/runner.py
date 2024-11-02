import os
import logging
from ase import Atoms
from ase.calculators.siesta import Siesta
from ase.io import jsonio

# Environment configuration
#os.environ['ASE_SIESTA_COMMAND'] = 'srun siesta < PREFIX.fdf > PREFIX.out'
logging.basicConfig(filename='runner.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ATOMS_JSON = 'atomic_struct.json'
CALC_JSON = 'calculator.json'
PARAMETERS_JSON = 'parameters.json'
RESULTS_FILE = 'results.json'


def load_json_data(file_path):
    """
    Loads JSON data from the given file path.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Loaded JSON data if successful, None otherwise.
    """
    try:
        return jsonio.read_json(file_path)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Failed to load JSON from {file_path}: {e}")
    return None


def configure_calculator():
    """
    Configures and returns an ASE Atoms object with an attached Siesta calculator.

    Returns:
        Atoms: Configured ASE Atoms object with Siesta calculator attached, or None on failure.
    """
    atom_object = jsonio.read_json(ATOMS_JSON)
    if not atom_object:
        logging.error("Error loading atomic structure from JSON.")
        return None

    try:
        if atom_object.pbc.any:
            logging.info('System is periodic.')
        else:
            atom_object.center(vacuum=8.0)
            atom_object.pbc = True
    except AttributeError as e:
        logging.error(f"Error with atomic structure configuration: {e}")
        return None

    calc_dict = load_json_data(CALC_JSON)
    parameters_dict = load_json_data(PARAMETERS_JSON)
    if not calc_dict or not parameters_dict:
        logging.error("Error loading calculator or parameters JSON.")
        return None

    try:
        # Initialize Siesta calculator
        calc = Siesta()
        calc.parameters['pseudo_path'] = calc_dict.get('pseudo_path', '.')
        calc.parameters['xc'] = (calc_dict.get('xc'), calc_dict.get('xcAuth'))
        calc.parameters['spin'] = calc_dict.get('spin', 'none')
        calc.parameters['energy_shift'] = calc_dict.get('energy_shift', 0.1)
        calc.parameters['basis_set'] = calc_dict.get('basisSet', 'DZP')
        calc.parameters['mesh_cutoff'] = calc_dict.get('meshCutoff', 300)
        calc.parameters['kpts'] = [int(calc_dict.get(key, 1)) for key in ['nkx', 'nky', 'nkz']]

        # Configure FDF arguments
        fdf_arguments = {
            'DM.MixingWeight': calc_dict.get('MixingCoeff', 0.3),
            'MaxSCFIterations': calc_dict.get('maxIter', 50),
            'DM.UseSaveDM': True,
        }

        if parameters_dict.get('bandWanted'):
            nk = int(parameters_dict['bandInputs']['nkforband'])
            lattice = atom_object.get_cell()
            band_path = lattice.bandpath(npoints=nk)
            calc.parameters['bandpath'] = band_path

        if parameters_dict.get('dosWanted'):
            dos_inputs = parameters_dict['dosInputs']
            pdosblock = f"\n%block ProjectedDensityOfStates\n" \
                        f"{float(dos_inputs['enemin']):8.4f} {float(dos_inputs['enemax']):8.4f} " \
                        f"{float(dos_inputs['fwhm']):8.4f} 3220 {dos_inputs['selectedunit']}\n" \
                        "%endblock ProjectedDensityOfStates"
            fdf_arguments['PDOSBLOCK'] = pdosblock

        if parameters_dict.get('chargeWanted'):
            charge_inputs = parameters_dict['chargeInputs']
            charges_args = {
                'WriteMullikenPop': int(charge_inputs.get('mullikenWanted', 0)),
                'WriteHirshfeldPop': charge_inputs.get('hirshfeldWanted', False),
                'WriteVoronoiPop': charge_inputs.get('voronoiWanted', False),
                'saverho': True,
            }
            fdf_arguments.update(charges_args)

        calc.parameters['fdf_arguments'] = fdf_arguments
        atom_object.calc = calc
        logging.info("Calculator configured successfully.")
        return atom_object

    except Exception as e:
        logging.error(f"Error configuring calculator: {e}")
        return None


def run_calculation():
    """
    Runs the Siesta calculation and saves the results to JSON files.
    """
    atoms = configure_calculator()
    if atoms:
        logging.info("Starting calculation.")
        try:
            energy = atoms.get_potential_energy()
            full_results = atoms.calc.results
            save_results_to_json(full_results, RESULTS_FILE)
            logging.info("Calculation completed successfully.")
        except Exception as e:
            logging.error(f"Calculation failed: {e}")
    else:
        logging.error("Calculation could not start due to an error in configuration.")


def save_results_to_json(results, output_file):
    """Filters and saves selected results to JSON using ASE's jsonio.

    Args:
        results (dict): Results dictionary from the Siesta calculation.
        output_file (str): Path to the output JSON file.
    """
    selected_keys = [
        'n_grid_point', 'energy', 'free_energy', 'stress', 'forces',
        'fermi_energy', 'eigenvalues', 'kpoints', 'kweights', 'dipole'
    ]
    filtered_results = {key: results.get(key) for key in selected_keys}
    jsonio.write_json(output_file, filtered_results)
    logging.info(f"Results saved to {output_file}")


if __name__ == "__main__":
    run_calculation()
