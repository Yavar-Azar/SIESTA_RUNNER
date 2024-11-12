"""."""

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np  # type: ignore
import plotly.graph_objects as go  # type: ignore
import plotly.io as pio  # type: ignore
from plotly.offline import plot  # type: ignore
from sc_runner.constants import (  # type: ignore
    CALC_RESULT_JSON,
    GENERAL_INFO_JSON,
    SIESTA_OUT,
)


color_pallete = [
    [
        'rgba(0, 149, 168, 0.4)',
        'rgba(17, 46, 81,0.4)',
        'rgba(255, 112, 67, 0.4)',
        'rgba(128, 64, 211, 0.4)',
        'rgba(161, 132, 151, 0.4)',
        'rgba(187, 66, 21, 0.4)',
        'rgba(174, 154, 15, 0.4)',
        'rgba(15, 121, 174, 0.4)',
    ],
    [
        'rgba(0, 149, 168, 0.8)',
        'rgba(17, 46, 81,0.8)',
        'rgba(255, 112, 67, 0.8)',
        'rgba(128, 64, 211, 0.8)',
        'rgba(161, 132, 151, 0.8)',
        'rgba(187, 66, 21, 0.8)',
        'rgba(174, 154, 15, 0.8)',
        'rgba(15, 121, 174, 0.8)',
    ],
]


def result_2_dict() -> Dict[str, Any]:
    """Convert a band.json file to a dictionary containing all needed data to plot the band structure.

    Returns:
        Dict[str, Any]: Dictionary containing necessary data for plotting the band structure.
    """
    band_dict = json.loads(Path(CALC_RESULT_JSON).read_text())['bandstructure']

    data_shape = band_dict['energies']['__ndarray__'][0]
    n_spin, n_k, n_bands = data_shape
    ef = band_dict['reference']
    temp_matrix = band_dict['energies']['__ndarray__'][2]
    temp_arr = np.array(temp_matrix) - ef
    bandmat = temp_arr.reshape(data_shape)
    path_data = band_dict['path']
    special_points = path_data['special_points']
    temp_k_matrix = path_data['kpts']['__ndarray__']
    # k_shape = temp_k_matrix[0]
    k_temp = temp_k_matrix[2]
    k_vectors_list = [k_temp[x : x + 3] for x in range(0, len(k_temp), 3)]
    k_vectors = np.array(k_vectors_list)
    ind_label = []

    for sp in list(special_points.keys()):
        for ik in range(len(k_vectors)):
            if k_vectors_list[ik] == special_points[sp]['__ndarray__'][2]:
                ind_label.append((ik, sp))

    ind_lb_sorted = sorted(ind_label, key=lambda x: x[0])
    inds = [x[0] for x in ind_lb_sorted]
    mod_inds = [inds[0]]

    for i in range(1, len(inds)):
        if (inds[i] - inds[i - 1]) > 1:
            mod_inds.append(inds[i])

    labelst = path_data['labelseq']
    _jumploc = []

    comma_count = 0

    # Loop through the string to find indices
    for i in range(1, len(labelst)):
        if labelst[i] == ',':
            # Adjust the index by the number of commas encountered so far
            _jumploc.append(i - 1 - comma_count)
            # Increment the comma count after adding the index
            comma_count += 1

    modified = [x for x in labelst if x != ',']

    for j in _jumploc:
        modified[j - 1] = modified[j - 1] + ',' + modified[j]
        modified[j] = ' '

    modified_labels = [x for x in modified if x != ' ']
    # n_mod_labels = len(labelst) - 2 * len(_jumploc)
    # index_list = [ind_lb_sorted[0][0]]
    k_diff = k_vectors[1:, :] - k_vectors[: n_k - 1, :]
    kline = np.zeros(n_k)

    for ik in range(int(n_k - 1)):
        abs_k_dif = np.linalg.norm(k_diff[ik])
        k_plus = 0.0 if abs_k_dif > 0.2 else abs_k_dif
        kline[ik + 1] = kline[ik] + k_plus

    klinev = np.reshape(kline, (n_k, 1))
    n_special_k_points = len(mod_inds)
    xticks = [kline[i] for i in mod_inds]
    xticklabels = modified_labels

    banddata = {
        'efermi': ef,
        'kpath': klinev,
        'nspin': n_spin,
        'nkpoints': n_k,
        'nbands': n_bands,
        'nspk': n_special_k_points,
        'bandmatrix': bandmat,
        'xticks': xticks,
        'xticklabels': xticklabels,
    }
    return banddata


def plot_band_go() -> None:
    """Generates a Plotly graph of the band structure from a JSON file and saves it as a JSON file.

    Returns:
        None
    """
    band_dict = result_2_dict()

    graphs = []

    specialk = band_dict['xticks']
    specialksymb = band_dict['xticklabels']
    bandmat = band_dict['bandmatrix']
    maxbands = bandmat.max(axis=1).max(axis=0)
    # minbands = bandmat.min(axis=1).min(axis=0)
    lowlimind = len(maxbands[maxbands < 0.0])
    spin = band_dict['nspin']
    x_kpath = band_dict['kpath'].flatten()
    n_band = band_dict['nbands']
    legends_stat = [False for x in range(n_band)]
    legends_stat[lowlimind - 3: lowlimind + 3] = [True for x in range(6)]
    range_y = [-6.0, 8.0]
    range_y_4_v_lines = [range_y[0] - 1, range_y[1] + 1]

    for x in specialk:
        graphs.append(
            go.Scatter(
                x=[x, x],
                y=range_y_4_v_lines,
                showlegend=False,
                line={'color': 'rgb(180, 171, 186)', 'width': 1},
            )
        )

    graphs.append(
        go.Scatter(
            x=[-1, max(x_kpath) + 1],
            y=[range_y[0], range_y[0]],
            line={'color': 'rgb(180, 171, 186)', 'width': 1},
            showlegend=False,
        )
    )
    graphs.append(
        go.Scatter(
            x=[-1, max(x_kpath) + 1],
            y=[range_y[1], range_y[1]],
            line={'color': 'rgb(180, 171, 186)', 'width': 1},
            showlegend=False,
        )
    )

    graphs.append(
        go.Scatter(
            x=[-1, max(x_kpath) + 1],
            y=[0, 0],
            line={'color': 'rgb(180, 171, 186)', 'width': 1},
            showlegend=False,
        )
    )

    if spin == 1:
        spin_labels = ['']
    elif spin == 2:
        spin_labels = [u'\u2191', u'\u2193']

    for s in range(spin):
        for i_band in range(0, n_band):
            graphs.append(
                go.Scatter(
                    x=x_kpath,
                    y=bandmat[s, :, i_band] - 0.0001 * s,  # Small shift for visualization purposes
                    mode='lines',
                    showlegend=legends_stat[i_band],
                    line=dict(shape='linear', color=color_pallete[s][i_band % 5], width=4 - 2 * s),
                    name='band_' + str(i_band + 1) + spin_labels[s],
                    yaxis='y1',
                )
            )

    layout = go.Layout(
        title='',
        width=1000,
        height=800,
        xaxis=dict(
            range=[min(x_kpath), max(x_kpath)],
            tickmode='array',
            tickvals=specialk,
            ticktext=specialksymb,
            mirror=True,
            ticks='outside',
            tickfont=dict(family='Helvetica, san-serif', size=24, color='black'),
            title=dict(text='', font=dict(size=8, family='Helvetica, san-serif')),
        ),
        yaxis=dict(
            mirror=True,
            ticks='outside',
            tickfont=dict(family='Helvetica, san-serif', size=18, color='black'),
            range=range_y,
            title=dict(text='Energy (eV)', font=dict(size=24, family='Helvetica, san-serif')),
        ),
        legend=dict(font=dict(family="Courier", size=24, color="black")),
        plot_bgcolor='rgba(249,254,254, 0.99)',
        paper_bgcolor='rgba(249,253,253, 0.99)',
    )

    fig1 = dict(data=graphs, layout=layout)
    graphJSON = pio.to_json(fig1, pretty=True)
    # Save the JSON graph data to a file in the same directory as 'bands.json'
    with open('band_structure_plot.json', 'w') as outfile:
        outfile.write(graphJSON)

    plot(fig1, filename='band.html', auto_open=False)

    return None
