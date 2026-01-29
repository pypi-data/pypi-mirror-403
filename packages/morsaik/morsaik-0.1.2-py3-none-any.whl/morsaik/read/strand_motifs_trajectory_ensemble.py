import numpy as np
from typing import Union
from .strand_motifs_trajectory import strand_motifs_trajectory as read_strand_motifs_trajectory
from ..obj.motif_trajectory_ensemble import MotifTrajectoryEnsemble
from ..obj.motif_trajectory import isinstance_motiftrajectory, are_compatible_motif_trajectories
from warnings import warn

def strand_motifs_trajectory_ensemble(filepath_lists : list,
        alphabet : list,
        motiflength : int = 4,
        skiprows : int =2) -> MotifTrajectoryEnsemble:
    """
    reads from the complexes.txt of the RNAReactor simulation output and returns corresponding
    concentration vectors in motif space.

    PARAMETERS:
    -----------
    filepath_lists : list
        Output files (complexes.txt) of the RNAReactor simulation
        Can be list of lists of motif_trajectory_sections, then the inner list
        will be used for creating the motif trajectories, the outer list
        distinguishes the different motif trajectories.
    skiprow : int, optional
        Skip the first `skiprow` lines, including comments
        when reading the file;
        default : 2

    RETURN:
    -------
    strand_motifs_trajectory_ensemble : MotifTrajectoryEnsemble
    """
    if filepath_lists is str:
        filepath_lists = [[filepath_lists,],]
    if not isinstance(filepath_lists, list):
        raise ValueError("filepaths needs to be list.")
    motif_trajectories = []

    for filepaths in filepath_lists:
        motif_trajectories = motif_trajectories + [read_strand_motifs_trajectory(filepaths,alphabet,motiflength=motiflength),]
        assert isinstance_motiftrajectory(motif_trajectories[-1]), "Not a MotifTrajectory"
        if (len(motif_trajectories)>1) and not are_compatible_motif_trajectories(motif_trajectories[0], motif_trajectories[-1]):
            raise ValueError("Non compatible motif trajectories.")
    return MotifTrajectoryEnsemble(motif_trajectories)
