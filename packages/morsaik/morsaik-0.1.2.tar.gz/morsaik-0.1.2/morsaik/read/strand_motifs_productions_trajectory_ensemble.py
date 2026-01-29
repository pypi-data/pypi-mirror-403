import numpy as np
from typing import Union
from .strand_motifs_productions_trajectory import strand_motifs_productions_trajectory as read_strand_motifs_productions_trajectory
from ..obj.motif_production_trajectory_ensemble import MotifProductionTrajectoryEnsemble
from ..obj.motif_production_trajectory import isinstance_motifproductiontrajectory, are_compatible_motif_production_trajectories
from warnings import warn

def strand_motifs_productions_trajectory_ensemble(filepath_lists : list,
        alphabet : list,
        motiflength : int,
        maximum_ligation_window_length : int,
        skiprows : int =2) -> MotifProductionTrajectoryEnsemble:
    """
    reads from the ligation_statistics.txt of the RNAReactor simulation output and returns corresponding
    production vectors in motif space.

    PARAMETERS:
    -----------
    filepath_lists : list
        Output files (ligation_statistics.txt) of the RNAReactor simulation
        Can be list of lists of motif_production_trajectory_sections, then the inner list
        will be used for creating the motif trajectories, the outer list
        distinguishes the different motif trajectories.
    skiprow : int, optional
        Skip the first `skiprow` lines, including comments
        when reading the files;
        default : 2

    RETURN:
    -------
    strand_motifs_productions_trajectory_ensemble : MotifProductionTrajectoryEnsemble
    """
    if filepath_lists is str:
        filepath_lists = [[filepath_lists,],]
    if not isinstance(filepath_lists, list):
        raise ValueError("filepaths needs to be list.")
    motifs_productions_trajectories = []

    for filepaths in filepath_lists:
        motifs_productions_trajectories = motifs_productions_trajectories + [read_strand_motifs_productions_trajectory(
            filepaths,
            alphabet,
            motiflength,
            maximum_ligation_window_length
            ),]
        assert isinstance_motifproductiontrajectory(motifs_productions_trajectories[-1]), "Not a MotifProductionTrajectory"
        if (len(motifs_productions_trajectories)>1) and not are_compatible_motif_production_trajectories(motifs_productions_trajectories[0], motifs_productions_trajectories[-1]):
            raise ValueError("Non compatible motif production trajectories.")
    return MotifProductionTrajectoryEnsemble(motifs_productions_trajectories)
