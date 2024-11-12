"""."""


import json
import logging
from pathlib import Path

import netCDF4 as nc  # type: ignore
import numpy as np  # type: ignore

from sc_runner.constants import GENERAL_INFO_JSON  # type: ignore


def nc_parser(grid_nc_file: str) -> None:
    """Parses a netCDF file containing grid data and write results to json.

    The function calculates dot products, cross products, average values over grid
    directions, volume, differential volumes, and checks for orthogonality. The results
    are saved in JSON format to a file depending on the input file name.

    Args:
        grid_nc_file (str): The path to the netCDF file to be parsed.

    Returns:
        None
    """
    # Check if the file exists
    if not Path(grid_nc_file).exists():
        logging.error(f"File {grid_nc_file} does not exist.")
        return

    dataset = nc.Dataset(grid_nc_file, mode='r')

    json_data = {}
    for dim_name, dim in dataset.dimensions.items():
        json_data[dim_name] = len(dim)

    for var_name in dataset.variables:
        var_data = dataset.variables[var_name][:]
        json_data[var_name] = var_data.tolist()

    cell = dataset.variables['cell']
    grid_data = dataset.variables['gridfunc']
    n_spin, n1, n2, n3 = np.shape(grid_data)

    dot_ab = np.dot(cell[0], cell[1]).tolist()
    dot_ac = np.dot(cell[0], cell[2]).tolist()
    dot_bc = np.dot(cell[1], cell[2]).tolist()
    # Check if all dot products are zero
    json_data['orthogonal'] = bool((dot_ab == 0) and (dot_ac == 0) and (dot_bc == 0))

    face_ab = np.linalg.norm(np.cross(cell[0], cell[1]))
    face_ac = np.linalg.norm(np.cross(cell[0], cell[2]))
    face_bc = np.linalg.norm(np.cross(cell[1], cell[2]))

    json_data['face_ab'] = float(face_ab)  # type: ignore
    json_data['face_ac'] = float(face_ac)  # type: ignore
    json_data['face_bc'] = float(face_bc)  # type: ignore

    diff_a = np.linalg.norm(cell[0]) / json_data['n1']
    diff_b = np.linalg.norm(cell[1]) / json_data['n1']
    diff_c = np.linalg.norm(cell[2]) / json_data['n3']

    json_data['diff_a'] = float(diff_a)  # type: ignore
    json_data['diff_b'] = float(diff_b)  # type: ignore
    json_data['diff_c'] = float(diff_c)  # type: ignore

    json_data['volume'] = float(np.dot(np.cross(cell[0], cell[1]), cell[2]))  # type: ignore

    json_data['diff_volume'] = float(
        json_data['volume'] / (json_data['n1'] * json_data['n2'] * json_data['n3'])
    )  # type: ignore

    json_data['a_grid'] = np.linspace(0, np.linalg.norm(cell[0]), n1 + 1)[:-1].tolist()
    json_data['b_grid'] = np.linspace(0, np.linalg.norm(cell[1]), n2 + 1)[:-1].tolist()
    json_data['c_grid'] = np.linspace(0, np.linalg.norm(cell[2]), n3 + 1)[:-1].tolist()
    # TODO: extend for spin
    a_average = 1.0 / (n2 * n3) * np.sum(grid_data[0], axis=(1, 2))
    b_average = 1.0 / (n1 * n3) * np.sum(grid_data[0], axis=(0, 2))
    c_average = 1.0 / (n1 * n2) * np.sum(grid_data[0], axis=(0, 1))

    json_data['a_average'] = a_average.tolist()
    json_data['b_average'] = b_average.tolist()
    json_data['c_average'] = c_average.tolist()

    general_info = json.loads(Path(GENERAL_INFO_JSON).read_text())

    json_data.update(general_info)

    if grid_nc_file == 'Rho.grid.nc':
        grid_total_charge = json_data['diff_volume'] * np.sum(grid_data)
        logging.info(f'total charge is  {grid_total_charge}')
        Path('Rho_grid.json').write_text(json.dumps(json_data))
    elif grid_nc_file == 'ElectrostaticPotential.grid.nc':
        Path('ElectrostaticPotential_grid.json').write_text(json.dumps(json_data))

    return None

