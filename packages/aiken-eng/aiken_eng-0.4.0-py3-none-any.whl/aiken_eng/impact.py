"""
These calculations are based on the Aiken impact model.  If you know... you know...
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def import_plate_fea(
    path: Path,
    thickness_list: list[int],
    diameter_list: list[int],
    material_list: list[str] = ["a572"],
) -> pd.DataFrame:
    """
    Import plate fea from the csv file repository.  Returns Pandas Dataframe
    """

    new_run = True

    for diam in diameter_list:
        for thick in thickness_list:
            for matl in material_list:
                name_string: str = str(diam) + "-" + str(thick) + "-" + matl + "-"

                filename: Path = path / (name_string + "d.txt")
                case_data: pd.DataFrame = pd.read_table(filename, sep="\t")
                case_data.drop(case_data.columns[[0, 2, 5]], axis=1, inplace=True)
                case_data.columns = [
                    "time",
                    "maximum_deformation",
                    "average_deformation",
                ]
                new_row: list[float] = [0.0, 0.0, 0.0]
                case_data.loc[1:] = case_data.loc[:]
                case_data.loc[0] = new_row

                filename: Path = path / (name_string + "e.txt")
                energy_data: pd.DataFrame = pd.read_table(filename, sep="\t")
                energy_data.drop(
                    energy_data.columns[[0, 2, 3, 5]], axis=1, inplace=True
                )
                energy_data.columns = ["time", "energy"]
                new_row: list[float] = [0.0, 0.0]
                energy_data.loc[1:] = energy_data.loc[:]
                energy_data.loc[0] = new_row

                filename: Path = path / (name_string + "s.txt")
                stress_data: pd.DataFrame = pd.read_table(filename, sep="\t")
                stress_data.drop(
                    stress_data.columns[[0, 2, 4, 5]], axis=1, inplace=True
                )
                stress_data.columns = ["time", "edge_stress"]
                new_row: list[float] = [0.0, 0.0]
                stress_data.loc[1:] = stress_data.loc[:]
                stress_data.loc[0] = new_row

                filename: Path = path / (name_string + "f1.txt")
                force1_data: pd.DataFrame = pd.read_table(filename, sep="\t")
                if len(force1_data.columns) == 7:
                    force1_data.drop(force1_data.columns[[0, 6]], axis=1, inplace=True)
                elif len(force1_data.columns) == 6:
                    force1_data.drop(force1_data.columns[[0]], axis=1, inplace=True)
                force1_data.columns = [
                    "time",
                    "perimeter_fx",
                    "perimeter_fy",
                    "perimeter_fz",
                    "perimeter_f_total",
                ]
                new_row: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0]
                force1_data.loc[1:] = force1_data.loc[:]
                force1_data.loc[0] = new_row

                filename: Path = path / (name_string + "f2.txt")
                force2_data: pd.DataFrame = pd.read_table(filename, sep="\t")
                if len(force2_data.columns) == 7:
                    force2_data.drop(force2_data.columns[[0, 6]], axis=1, inplace=True)
                if len(force2_data.columns) == 6:
                    force2_data.drop(force2_data.columns[[0]], axis=1, inplace=True)
                force2_data.columns = [
                    "time",
                    "edge_fx",
                    "edge_fy",
                    "edge_fz",
                    "edge_f_total",
                ]
                new_row: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0]
                force2_data.loc[1:] = force2_data.loc[:]
                force2_data.loc[0] = new_row

                total_force: pd.Series = (
                    force1_data.perimeter_f_total + force2_data.edge_f_total
                )
                edge_stress: pd.Series = (
                    np.abs(force2_data.edge_fx) / (3 * diam / 1000) / (thick / 1000)
                )

                case_data = pd.merge(case_data, energy_data)
                case_data = pd.merge(case_data, stress_data)
                case_data = pd.merge(case_data, force1_data)
                case_data = pd.merge(case_data, force2_data)

                diameter: list[float] = [diam / 1000 for _ in range(case_data.shape[0])]
                case_data.insert(1, "diameter", diameter)
                thickness: list[float] = [
                    thick / 1000 for _ in range(case_data.shape[0])
                ]
                case_data.insert(2, "thickness", thickness)
                material: list[str] = [matl for _ in range(case_data.shape[0])]
                case_data.insert(3, "material", material)
                # drops the last row for each case which probably includes some NaN
                case_data.drop(index=case_data.index[-1], axis=0, inplace=True)
                case_data.insert(7, "total_force", total_force)
                case_data.insert(8, "avg_edge_stress", edge_stress)
                if new_run == True:
                    fea_data = case_data
                    new_run = False
                else:
                    fea_data = pd.concat([fea_data, case_data])

    return fea_data


def plot_plate_fea(fea_data: pd.DataFrame, thickness: int):
    diameter_list: list[float] = fea_data.diameter.unique()

    colors = sns.color_palette("mako_r", len(diameter_list))

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for di, diameter in enumerate(diameter_list):
        filt = (fea_data["diameter"] == diameter) & (
            fea_data["thickness"] == thickness / 1000
        )
        ax = axes[0]
        ax.plot(
            fea_data.loc[filt, "energy"] / 1000,
            fea_data.loc[filt, "edge_f_total"] / 1000,
            "o--",
            markersize=2,
            linewidth=1,
            label=str(diameter * 1000) + "mm",
            color=colors[di],
        )

        ax = axes[1]
        ax.plot(
            fea_data.loc[filt, "energy"] / 1000,
            fea_data.loc[filt, "avg_edge_stress"] / 1e6,
            "o--",
            markersize=2,
            linewidth=1,
            color=colors[di],
        )

        ax = axes[2]
        ax.plot(
            fea_data.loc[filt, "energy"] / 1000,
            fea_data.loc[filt, "maximum_deformation"] * 1000,
            "o--",
            markersize=2,
            linewidth=1,
            color=colors[di],
        )

    ax = axes[0]
    ax.set_ylabel("Impact Force (kN)", fontsize=14)
    ax.legend(fontsize="small", title="Projectile Diameter")

    ax = axes[1]
    ax.set_ylabel("Edge Stress (MPa)", fontsize=14)
    ax.set_xlabel("Energy (kJ)", fontsize=14)
    ax.set_title(str(thickness) + " mm Plate", loc="center", fontsize=14)

    ax = axes[2]
    ax.set_ylabel("Max Displacement (mm)", fontsize=14)

    title_string = "FEA Impact Results for Single Layer " + str(thickness) + "mm Plate"
    fig.suptitle(title_string, fontsize=16)
    fig.tight_layout()

    plt.show()
