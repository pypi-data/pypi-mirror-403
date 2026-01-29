import matplotlib.pyplot as plt
from os import makedirs

from .zebraness import system_level_motif_zebraness as plot_system_level_motif_zebraness
from .entropy import motif_entropy as plot_motif_entropy

def motif_trajectory_analysis(
        motif_trajectory_ensembles : list,
        plot_instructions : dict,
        plot_parameters_list : list,
        plotting_time_windows : list = None,
        plotpath : str = './Plots/'
    ):
    """
    Meta function to plot all analysis plots as specified in the plotting constructions.
    """
    makedirs(plotpath, exist_ok=True)
    if plot_instructions['plot_system_level_motif_zebraness']:
        ii = 0
        for motif_trajectory_ensemble in  motif_trajectory_ensembles:
            plot_parameters = plot_parameters_list[ii]
            plot_system_level_motif_zebraness(
                motif_trajectory_ensemble,
                plotting_time_windows = plotting_time_windows,
                plot_parameters = plot_parameters,
                plotpath = plotpath
            )
    if plot_instructions['plot_motif_entropy']:
        ii = 0
        for motif_trajectory_ensemble in  motif_trajectory_ensembles:
            plot_parameters = plot_parameters_list[ii]
            plot_motif_entropy(
                motif_trajectory_ensemble,
                linestyle = plot_parameters['linestyle'],
                color = plot_parameters['color'],
            )
            plt.close('all')
            ii+=1
