import sys, os
import json, io, base64
import numpy as np

import matplotlib
matplotlib.use('Agg')
colors = ['#336699', '#aa3333', '#66aa33']
matplotlib.rcParams['axes.color_cycle'] = colors
matplotlib.rcParams['xtick.labelsize'] = 10
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial']
from matplotlib import pyplot as plt
from matplotlib import gridspec

def format_axes(ax):
    for direction in ['bottom', 'top', 'right', 'left']:
        ax.spines[direction].set_color('#aaaaaa')
    for direction in ['left', 'top', 'right']:
        ax.spines[direction].set_visible(False)
    gridlines = ax.get_xgridlines() + ax.get_ygridlines()
    for line in gridlines:
        line.set_linestyle('-')
        line.set_color('#999999')
        line.set_alpha(0.25)

def plot_hist(gs, title, data, bins, ticks, color):
    ax = plt.subplot(gs)
    plt.title(title, fontsize=12)
    plt.hist(data, bins, normed=True, histtype='step')
    plt.xticks(ticks)
    ax.axes.xaxis.set_ticklabels([])
    ax.tick_params(axis='both', which='both',length=0)
    plt.grid()
    plt.yticks([])
    format_axes(ax)
    plt.xlim([np.min(bins)-1, np.max(bins)+1])

def plot_box(gs, data, index, bins, ticks, color):
    width = 0.75
    ax = plt.subplot(gs)
    bp = plt.boxplot(data, positions=(1,), vert=False, widths=(width,),  showfliers=False)
    for prop in ['boxes', 'caps', 'medians', 'whiskers', 'fliers']:
        plt.setp(bp[prop], color=color, linewidth=1, linestyle='-')
    format_axes(ax)
    plt.xticks(ticks)
    plt.xlabel('Minutes', fontsize=9)
    plt.yticks([])
    plt.xlim([np.min(bins)-1, np.max(bins)+1])
    plt.ylim([0.25,1.75])
    plt.grid()

def get_b64_plots(data):
    plot_meta = [
        { 'data_field': 'pt_wait_ct', 'title': 'Patient waiting room time', 'bins': np.linspace(0, 65, 66), 'ticks': np.linspace(0, 60, 5)},
        { 'data_field': 'end_time', 'title': 'Last patient checked out', 'bins': np.linspace(145, 185, 41), 'ticks': np.linspace(150, 180, 4)},
        { 'data_field': 'pt_wait_atp', 'title': 'PT waiting for attending', 'bins': np.linspace(0, 35, 36), 'ticks': np.linspace(0, 30, 4)},
        { 'data_field': 'ct_wait_atp', 'title': 'CT waiting for attending', 'bins': np.linspace(0, 35, 36), 'ticks': np.linspace(0, 30, 4)}
    ]
    b64_plots = []
    for plot in plot_meta:
        fig = plt.figure(figsize=(4, 3.5))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        plot_hist(gs[0], plot['title'], data[plot['data_field']], plot['bins'], plot['ticks'], colors[0])
        plot_box(gs[1], data[plot['data_field']], 0, plot['bins'], plot['ticks'], colors[0])
        plt.subplots_adjust(hspace=0.0)
        # save b64 encoded png
        buf = io.BytesIO();
        plt.gcf().savefig(buf, format='png');
        buf.seek(0);
        b64_plots.append(base64.b64encode(buf.read()))
    return b64_plots