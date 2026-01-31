import math
import os

import matplotlib.colors as col
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from unac.util.config import Config


def plot_comparison(means, stddevs, legend, ticks, title, fn):
    assert means.shape == stddevs.shape
    assert len(legend) == means.shape[0]
    assert len(ticks) == means.shape[1]

    fig, ax = plt.subplots()
    num_datasets = means.shape[0]
    colors_hsv = np.ones((num_datasets, 3))
    for i in range(0, num_datasets):
        colors_hsv[i, 0] = i / (num_datasets + 1)
    colors_rgb = col.hsv_to_rgb(colors_hsv)
    width = 0.8 / num_datasets
    pos = np.arange(means.shape[1])
    plots = []
    min_val = math.inf
    for i, val in enumerate(means):
        offset = -(-(num_datasets - 1) / 2 * width + i * width)
        errs = stddevs[i, :]
        tmp_plt = ax.bar(
            pos - offset,
            val,
            width=width,
            yerr=errs,
            color=colors_rgb[i],
            ecolor="k",
            align="center",
        )
        plots.append(tmp_plt[0])
        min_val = min(min_val, np.min(val))

    ax.set_xticks(pos)
    ax.set_xticklabels(ticks)
    if min_val > -Config.get_neg_tol():
        ax.set_ylim(ymin=0)
    else:
        ax.axhline(y=0, color="k", linestyle="dotted")
    ax.legend(plots, legend)
    ax.set_title(title)
    plt.savefig(fn)
    plt.close("all")


def plot_problematic(data, problematic, path):
    if not os.path.exists(path):
        os.makedirs(path)
    if len(data) == 0:
        return
    for prob in problematic:
        prob_data = {}
        times = None
        for cor in data:
            if prob in data[cor]:
                prob_data[cor], _ = data[cor][prob].calc_means_and_stddevs()
                # this will get overwritten for every cor, but should be identical anyhow
                masses = data[cor][prob].get_masses()
                times = data[cor][prob].get_times()
        collected_data = pd.DataFrame(columns=masses)

        for time in times:
            for cor in prob_data:
                collected_data.loc[cor] = prob_data[cor].loc[:, time]
            fig, axs = plt.subplots(2, 1, sharex=True)

            # plot the difference from mean to judge deviations (violations of tolerance.diff)
            (collected_data - collected_data.mean()).transpose().plot.bar(ax=axs[0], legend=False)
            lims = axs[0].get_ylim()
            axs[0].set_ylim(
                min(lims[0], 1.1 * -Config.get_diff_tol() / 2), max(lims[1], 1.1 * Config.get_diff_tol() / 2)
            )
            axs[0].set_title("absolute difference from mean")
            xlims = axs[0].get_xlim()
            axs[0].hlines(0, xlims[0], xlims[1], colors="k")
            axs[0].hlines(
                [-Config.get_diff_tol() / 2, Config.get_diff_tol() / 2],
                xlims[0],
                xlims[1],
                colors="red",
                linestyles="dashed",
            )
            yticks = list(axs[0].get_yticks())
            ytick_labs = axs[0].get_yticklabels()
            axs[0].set_yticks(yticks + [-Config.get_diff_tol() / 2, Config.get_diff_tol() / 2])
            axs[0].set_yticklabels(ytick_labs + ["-Diff tol/2", "Diff tol/2"])
            axs[0].get_yticklabels()[-1].set_color("red")
            axs[0].get_yticklabels()[-2].set_color("red")

            # plot the values to judge negative values (violations of tolerance.negative)
            collected_data.transpose().plot.bar(ax=axs[1])
            axs[1].set_title("absolute value [truncated]")
            min_val = min(0, 1.1 * collected_data.min().min())
            axs[1].set_ylim(min(min_val, 1.1 * -Config.get_neg_tol()), Config.get_neg_tol())
            axs[1].hlines(0, xlims[0], xlims[1], colors="k")
            axs[1].hlines(-Config.get_neg_tol(), xlims[0], xlims[1], colors="red", linestyles="dashed")
            yticks = list(axs[1].get_yticks())
            ytick_labs = axs[1].get_yticklabels()
            axs[1].set_yticks(yticks + [-Config.get_neg_tol()])
            axs[1].set_yticklabels(ytick_labs + ["-Negative tol"])
            axs[1].get_yticklabels()[-1].set_color("red")

            fig.suptitle(f"{prob} at {time}")
            handles, labels = axs[1].get_legend_handles_labels()
            axs[1].get_legend().remove()
            fig.legend(
                handles,
                labels,
                bbox_to_anchor=(0.5, 0),
                bbox_transform=fig.transFigure,
                loc="lower center",
                ncol=len(labels),
            )
            plt.tight_layout(rect=[0, 0.07, 1, 1])
            plt.savefig(f"{path}/{prob}_at_{time}.png")


def plot_data(data, path):
    if not os.path.exists(path):
        os.makedirs(path)
    if len(data) == 0:
        return

    # not all metabolites are featured in all data sets ->
    # collect all metabolites
    mets = set()
    for datum in data:
        mets.update(data[datum].keys())

    for met in mets:
        # calculate which datum include the metabolite
        active_data = []
        active_names = []
        for key in data:
            datum = data[key]
            if met in datum:
                active_data.append(datum[met])
                active_names.append(key)

        if len(active_data) <= 1:
            # nothing to compare
            continue

        means = []
        stddevs = []

        for datum in active_data:
            m, s = datum.calc_means_and_stddevs()
            means.append(m)
            stddevs.append(s)

        # if two data sets include a metabolite, they also have to include all time-points
        times = means[0].columns.tolist()
        multi_times = len(times) > 1
        for time in times:
            t_means = np.vstack(tuple([x[time] for x in means]))
            t_stddevs = np.vstack(tuple([x[time] for x in stddevs]))

            time_str = ""
            if multi_times:
                time_str = f"_at_{time}"

            plot_comparison(
                t_means,
                t_stddevs,
                active_names,
                means[0].index.tolist(),
                met,
                f"{path}/{met}{time_str}.png",
            )


def plot_timeseries(data, path):
    os.makedirs(path, exist_ok=True)

    plt.figure()
    for met in data:
        if data[met].is_inst():
            m, s = data[met].calc_means_and_stddevs()
            m.transpose().plot(yerr=s.transpose(), title=f"{data[met].build_plot_title()}")
            plt.savefig(f"{path}/{met}.png")
            plt.close()
    plt.close("all")
