import argparse
import logging
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from .nexus.grains import read_grains

logger = logging.getLogger(__name__)


def plot_grains(
    grain_lists: List,
    color_by: str = "npks",
    size_factor: float = 0.01,
    title: str = "3DXRD Grain Map",
    cmap: str = "viridis",
    figsize: tuple = (12, 12),
):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(projection="3d", proj_type="ortho")

    xx = np.array([g.translation[0] for g in grain_lists])
    yy = np.array([g.translation[1] for g in grain_lists])
    zz = np.array([g.translation[2] for g in grain_lists])

    def get_intensity(g):
        DEFAULT_INTENSITY = 1.0
        try:
            return float(
                g.intensity_info.split("mean = ")[1].split(" , ")[0].replace("'", "")
            )
        except (IndexError, ValueError) as e:
            logger.error(
                f"Failed to parse intensity from string: '{g.intensity_info}'. "
                f"Error: {e}. Returning default {DEFAULT_INTENSITY}."
            )
            return DEFAULT_INTENSITY

    sizes = np.array([get_intensity(g) * size_factor for g in grain_lists])

    if color_by == "npks":
        colors = [float(g.npks) for g in grain_lists]
        label = "Number of Peaks"
    else:
        colors = "blue"
        label = color_by

    scatterplot = ax.scatter(xx, yy, zz, c=colors, s=sizes, cmap=cmap)

    ax.set_aspect("equal")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(title)

    plt.colorbar(scatterplot, label=label, shrink=0.5)
    return fig, ax


def visualize_grains_from_file(file_path: str, entry: str, group: str, **kwargs):
    grains = read_grains(
        grain_file_h5=file_path, entry_name=entry, process_group_name=group
    )
    return plot_grains(grains, **kwargs)


def get_parser():
    parser = argparse.ArgumentParser(
        prog="ewoks3dxrd-grain-vis",
        description="Visualize grains contained in a Ewoks3dxrd NeXus file",
    )
    parser.add_argument("filename", help="File containing the Ewoks3dxrd results")
    parser.add_argument(
        "-e",
        "--entry",
        default="1.1",
        help="Name of the scan entry (x.y). Defaults to 1.1",
    )
    parser.add_argument(
        "-g",
        "--group",
        default="make_map_grains",
        help="Name of the process group. Defaults to make_map_grains",
    )
    return parser


def main() -> None:
    parser = get_parser()
    args = parser.parse_args()

    visualize_grains_from_file(args.filename, args.entry, args.group)
    plt.show()
