import matplotlib.pyplot as plt
import numpy as np
from itertools import product as iterprod

from ..obj.motif_trajectory_ensemble import MotifTrajectoryEnsemble
from ..obj.units import transform_unit_to_str
from .colors import _choose_color

from ..infer.zebraness import system_level_motif_zebraness as infer_system_level_motif_zebraness
from ..infer.zebraness import individual_motif_zebraness as infer_individual_motif_zebraness

def zebraness(
        motif_trajectory_ensemble : MotifTrajectoryEnsemble,
        linestyle = '-',
        color = 'b',
        axis = None
    ):
    if axis is None:
        axis = plt.gca()
    ii = 0
    for motif_trajectory in motif_trajectory_ensemble.trajectories:
        colr = _choose_color(color, ii/np.max([1,len(motif_trajectory_ensemble.trajectories)-1]))
        print("Plotting zebraness...")
        times = motif_trajectory.times
        motifs = motif_trajectory.motifs.val

        zebras = motif_trajectory.motifs['length2strand'].val[:,0,1]+motif_trajectory.motifs['length2strand'].val[:,1,0]
        c0 = np.sum(motif_trajectory.motifs['length2strand'].val.reshape((times.shape[0],-1)), axis = 1)
        zebraness = zebras/c0

        axis.plot(times.val, zebraness, linestyle = linestyle, color = colr)
        axis.set_xlabel('Time ' + transform_unit_to_str(times.domain[0].units))
        axis.set_ylabel('Zebraness []')
        axis.set_ylim([0.,1.])
        ii += 1

def nest_mean(rough_list : list) -> np.ndarray:
    """
    arranges list of arrays such that all start at zeroth position and gives back mean of the occupied values.
    """
    # even list
    nested_mean_length = np.max([len(rl) for rl in rough_list])
    nested_mean = []
    for rl in rough_list:
        rl = np.array(list(rl) + [np.nan]*(nested_mean_length-len(rl)))
        nested_mean += [rl]
    return np.nanmean(nested_mean, axis = 0)

def system_level_motif_zebraness(
        motif_trajectory_ensembles : list,
        plotting_time_windows : list = None,
        plot_mean : list = [False],
        plot_parameters : list = [{
            'linestyle' : '-',
            'color' : 'b',
            'alpha' : 0.3,
            'label' : 'Strand',
        }],
        plotpath : str = None,
        plotformats : list = ['.pdf'],
        annotation : dict = {
            'text':'',
            'xy':(0,1),
            'xycoords':'axes fraction',
            'xytext':(+0.5,-0.5),
            'textcoords':'offset fontsize',
            'verticalalignment':'top',
            'bbox':{
                'facecolor':'white',
                'edgecolor':'none',
                'alpha':'0.7'
            },
            },
    ):
    """
    plots system level motif zebraness, i.e. the fraction of alternating 2-mers
    in the whole motif reactor.

    Parameters:
    -----------
    motif_trajectory_ensemble : list of MotifTrajectoryEnsemble
    plotting_time_windows : list = None,
    plot_mean : list
        default: [False]
    plot_parameters : list
        of dicts of format {
            'linestyle' : '-',
            'color' : 'b',
            'alpha' : 0.3,
            'label' : 'Strand',
        }
    plotpath : str
        default: None,
    plotformats : list
        default: ['.pdf'],
    annotation : dict
        default: {
        'text':'',
        'xy':(0,1),
        'xycoords':'axes fraction',
        'xytext':(+0.5,-0.5),
        'textcoords':'offset fontsize',
        'verticalalignment':'top',
        'bbox':{
            'facecolor':'white',
            'edgecolor':'none',
            'alpha':'0.7'
        },
        },

    Returns:
    --------
    None

    """
    if not isinstance(motif_trajectory_ensembles,list):
        motif_trajectory_ensembles = [motif_trajectory_ensembles,]
    if not isinstance(plot_parameters, list):
        plot_parameters = [plot_parameters,]
    times_list = [
            motif_trajectory_ensemble.trajectories[
                np.argmax([motif_trajectory_ensemble.trajectories[ti].times.size
                           for ti in range(len(motif_trajectory_ensemble.trajectories))])].times
                for motif_trajectory_ensemble in motif_trajectory_ensembles
                ]
    motif_trajectories_list = [
            motif_trajectory_ensemble.trajectories
            for motif_trajectory_ensemble in motif_trajectory_ensembles
                          ]

    if plotting_time_windows is None:
        plotting_time_windows = [[times_list[0].val[0],times_list[0].val[-1]]]

    for tptt in plotting_time_windows:
        for yscale, xscale in iterprod(['linear','log'],repeat=2):
            plt.close('all')
            for ii in range(len(motif_trajectories_list)):
                motif_trajectories = motif_trajectories_list[ii]
                colrs = plot_parameters[ii]['color']
                trj_times_val = motif_trajectories[0].times.val
                if plot_mean[ii]:
                    zebraness_mean = []
                for jj in range(len(motif_trajectories)):
                    colr = _choose_color(colrs, jj/np.max([1,len(motif_trajectories)-1]))
                    trj = motif_trajectories[jj]
                    if len(trj.times.val)>len(trj_times_val):
                        trj_times_val = trj.times.val
                    zebraness = infer_system_level_motif_zebraness(trj, axis=1)
                    if plot_mean[ii]:
                        zebraness_mean += [zebraness]
                    plt.plot(trj.times.val,
                            zebraness,
                            plot_parameters[ii]['linestyle'],
                            color = colr,
                            label= plot_parameters[ii]['label'],
                            alpha  = plot_parameters[ii]['alpha'])
                if plot_mean[ii]:
                    zebraness_mean = nest_mean(zebraness_mean)
                    colr = _choose_color(color, color_parameter = len(colrs//2))
                    plt.plot(trj_times_val,
                            zebraness_mean,
                            '-',
                            color = colr,
                            label= plot_parameters[ii]['label'],
                            alpha  = np.min((1.,plot_parameters[ii]['alpha']*2.))
                            )
            plt.annotate(**annotation)
            plt.xscale(xscale)
            plt.yscale(yscale)
            plt.xlabel('Time ' + transform_unit_to_str(times_list[0].domain[0].units))
            plt.ylabel('Zebraness []')
            if tptt[0] is None:
                tptt[0] = 10**int(np.log10(times_list[0].val[1]))
            if tptt[1] is None:
                tptt[1] = np.max([tl.val[-1] for tl in times_list])
            if xscale=='log' and tptt[0]==0.:
                tptt[0] = 10**int(np.log10(times_list[0].val[1]))
            plt.xlim(*tptt)
            plt.ylim([0.,1.])
            if plotpath is not None:
                pp = plotpath+'{title}_{tptt0}-{tptt1}_{yscale}-{xscale}'
                figname = pp.format(
                    title='motif_zebraness',
                    tptt0=str(tptt[0]),
                    tptt1=str(tptt[1]),
                    xscale=xscale,
                    yscale=yscale,
                )
                for plotformat in plotformats:
                    plt.savefig(figname + plotformat)
                print('plotted {}'.format(figname))
                plt.close()
