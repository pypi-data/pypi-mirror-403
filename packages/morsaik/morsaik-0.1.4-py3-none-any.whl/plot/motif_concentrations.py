from ..domains.motif_space import _return_motif_categories
from ..obj.units import transform_unit_to_str

import numpy as np
import itertools as it
import matplotlib.pyplot as plt
from os import makedirs

general_plot_parameters = {
        'plotpath' : None,
        'plotting_time_windows' : None,
        'md_linestyle' : '--',
        'md_color' : 'blue',
        'sd_linestyle' : '-.',
        'sd_alpha' : 0.8,
        'sd_color' : 'blue',
        }
def calculate_concentration_of_a_single_particle(c_ref,number_a_monomers):
    return c_ref/number_a_monomers

def compute_words(letters,zeros=(0,0,0,0)): 
    zeros = np.asarray(zeros)
    nol = len(letters)
    shape = np.asarray((nol,)*len(zeros))
    shape = tuple(shape+zeros)
    ne = np.empty(shape, dtype=object)
    if zeros[0]:
        ne[0] = '0'
    for ii in range(nol):
        ne[ii+zeros[0]] = letters[ii]
    for jj in range(1,len(shape)):
        ne = np.swapaxes(ne,jj,0)
        if zeros[jj]:
            ne[0] += '0'
        for ii in range(nol):
            ne[ii+zeros[jj]] += letters[ii]
        ne = np.swapaxes(ne,jj,0)
    return ne

def continuations_trajectories(
        motif_trajectory_ensembles : list,
        plotting_time_windows : list = None,
        c_ref : float = 1.,
        plotpath : str = './Plots/',
        plot_parameters : list = [{
            'linestyle' : '-',
            'color' : 'b',
            'alpha' : 0.3,
            'label' : 'Strand',
        }],
    ) -> None:
    motif_trajectories(
        motif_trajectory_ensembles,
        plotting_time_windows = plotting_time_windows,
        c_ref = c_ref,
        plotpath = plotpath,
        plot_parameters = plot_parameters,
        motifs_key = _return_motif_categories(motiflength)[-2]
    )

def motif_trajectories(
        motif_trajectory_ensembles : list,
        alphabet : list[str] = None,
        plotting_time_windows : list = None,
        c_ref : float = 1.,
        plotpath : str = './Plots/',
        plot_parameters : list = [{
            'linestyle' : '-',
            'color' : 'b',
            'alpha' : 0.3,
            'label' : 'Strand',
        }],
        plotformats : list = ['.pdf'],
        ylim : list = None,
        motifs_key : str = _return_motif_categories()[-2],
        concentration_of_a_single_particle : float = None,
        annotations : dict = {
            'X': {
                'text':'a',
                'xy':(0,1),
                'xycoords':'axes fraction',
                'xytext':(+0.5,-0.5),
                'textcoords':'offset fontsize',
                'verticalalignment':'top'
                },
            'YY':{
                'text':'b',
                'xy':(0,1),
                'xycoords':'axes fraction',
                'xytext':(+0.5,-0.5),
                'textcoords':'offset fontsize',
                'verticalalignment':'top'
                },
            'XYX':{
                'text':'c',
                'xy':(0,1),
                'xycoords':'axes fraction',
                'xytext':(+0.5,-0.5),
                'textcoords':'offset fontsize',
                'verticalalignment':'top'
                },
            'XXXX':{
                'text':'d',
                'xy':(0,1),
                'xycoords':'axes fraction',
                'xytext':(+0.5,-0.5),
                'textcoords':'offset fontsize',
                'verticalalignment':'top'
                },
            },
        **kwargs
    ) -> None:
    makedirs(plotpath, exist_ok=True)
    if not isinstance(motif_trajectory_ensembles,list):
        motif_trajectory_ensembles = [motif_trajectory_ensembles,]
    if not isinstance(plot_parameters, list):
        plot_parameters = [plot_parameters,]
    if len(plot_parameters) != len(motif_trajectory_ensembles):
        plot_parameters = plot_parameters*len(motif_trajectory_ensembles)
    motiflength = motif_trajectory_ensembles[0].motiflength
    number_of_letters = motif_trajectory_ensembles[0].number_of_letters
    if motifs_key in _return_motif_categories(motiflength)[-3:]:
        wordlength = motiflength - int(motifs_key != _return_motif_categories()[-2])
    else:
        wordlength = np.where(np.isin(_return_motif_categories(motiflength)[:-3],motifs_key))[0][0]+1
    words = compute_words(
        motif_trajectory_ensembles[0].alphabet if alphabet is None else alphabet,
        zeros=(0,)*wordlength
    )
    monomer_key = _return_motif_categories(motiflength)[0]

    motifs_list = [[motif_trajectory_ensemble.trajectories[trajectory_index] for trajectory_index in range(len(motif_trajectory_ensemble.trajectories))] for motif_trajectory_ensemble in motif_trajectory_ensembles]

    if concentration_of_a_single_particle is None:
        for ii in range(len(motif_trajectory_ensembles)):
            if isinstance(motif_trajectory_ensembles[ii].unit,(int,float)) and motif_trajectory_ensembles[ii].unit==1:
                concentration_of_a_single_particle = calculate_concentration_of_a_single_particle(c_ref, motifs_list[0][0].motifs.val[monomer_key].reshape(-1)[0])
    if concentration_of_a_single_particle is None:
        concentration_of_a_single_particle = np.min(motifs_list[0][0].motifs.val[monomer_key].reshape(-1))

    if ylim is None:
        ymax = [10**(np.ceil(np.log10(np.max(motifs[0].motifs[motifs_key].val))))*(
            1-(concentration_of_a_single_particle-1)*(isinstance(motifs[0].unit,(int,float)))
            ) for motifs in motifs_list]
        ymax = np.nanmax(list(ymax))
        if np.isnan(ymax) or np.isinf(ymax):
            ymax = None
        ylim = [concentration_of_a_single_particle/2.,ymax]

    if plotting_time_windows is None:
        plotting_time_windows = [[motif_trajectory_ensembles[0].times.val[0],motif_trajectory_ensembles[0].times.val[-1]]]

    for tptt in plotting_time_windows:
        for logt, logy in it.product(*([False,True],)*2):
            for motif_index in range(number_of_letters**wordlength):
                word = words.reshape(-1)[motif_index]
                for ii in range(len(motif_trajectory_ensembles)):
                    for motif in motifs_list[ii]:
                        if isinstance(motif_trajectory_ensembles[ii].unit,(int,float)) and motif_trajectory_ensembles[ii].unit==1:
                            mm = motif.motifs[motifs_key].val*concentration_of_a_single_particle
                        else:
                            mm = motif.motifs[motifs_key].val
                        mm = mm.reshape(len(mm),-1)
                        plt.plot(motif.times.val, mm[:,motif_index], **plot_parameters[ii])
                if word in annotations.keys():
                    plt.annotate(**annotations[word])
                plt.title(word)
                plt.xscale('linear'*(1-logt)+'log'*logt)
                plt.yscale('linear'*(1-logy)+'log'*logy)
                pth = plotpath+f'{motifs_key}_trajectories_{word}_'
                pth +=str(tptt[0])+'-'+str(tptt[1])
                pth += '_log'*logy+'_lin'*(1-logy)
                pth += '_log'*logt+'_lin'*(1-logt)
                if tptt[0] is None:
                    tptt[0] = 10**int(np.log10(motif_trajectory_ensembles[0].times.val[0]))
                if tptt[1] is None:
                    tptt[1] = np.max([motif_trajectory_ensemble.times.val[-1] for motif_trajectory_ensemble in motif_trajectory_ensembles])
                if logt and tptt[0]==0.:
                    tptt[0] = 10**int(np.log10(motif_trajectory_ensembles[0].times.val[1]))
                plt.xlim(*tptt)
                plt.ylim(ylim)
                plt.xlabel('Time ' + transform_unit_to_str(motif_trajectory_ensembles[0].times.domain[0].units))

                plt.ylabel('Concentration $[\mathrm{mol}/\mathrm{L}]$')# + transform_unit_to_str(motifs_list[0][0].unit))
                for plotformat in plotformats:
                    plt.savefig(pth+plotformat)
                print(f"Saved {pth+plotformat}.")
                plt.close('all')
