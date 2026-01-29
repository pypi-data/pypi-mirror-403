from collections import namedtuple
import numpy as  np
from .motif_breakage_trajectory import are_compatible_motif_breakage_trajectories

def MotifBreakageTrajectoryEnsemble(motif_breakage_trajectories : list):
    """
    Ensemble of motif breakage trajectories
    """
    motif_breakage_trajectory = motif_breakage_trajectories[0]
    motif_breakage_trajectory_ensemble_properties = {
            'motiflength' : motif_breakage_trajectory.motiflength,
            'alphabet' : motif_breakage_trajectory.alphabet,
            'number_of_letters' : motif_breakage_trajectory.number_of_letters,
            'unit' : motif_breakage_trajectory.unit,
            'trajectories' : motif_breakage_trajectories
            }
    for motif_breakage_trajectory in motif_breakage_trajectories[1:]:
        assert(motif_breakage_trajectory.motiflength==motif_breakage_trajectory_ensemble_properties['motiflength'])
        assert(motif_breakage_trajectory.alphabet==motif_breakage_trajectory_ensemble_properties['alphabet'])
        assert(motif_breakage_trajectory.number_of_letters==motif_breakage_trajectory_ensemble_properties['number_of_letters'])
        assert motif_breakage_trajectory.unit==motif_breakage_trajectory_ensemble_properties['unit'], "Units of motif vectors need to be the same."
        assert(are_compatible_motif_breakage_trajectories(motif_breakage_trajectory,motif_breakage_trajectories[0]),
                "Motif trajectories not compatible.")
    mt = namedtuple('MotifBreakageTrajectoryEnsemble',
                tuple(motif_breakage_trajectory_ensemble_properties.keys()))
    return mt(**motif_breakage_trajectory_ensemble_properties)

def isinstance_motifbreakagetrajectoryensemble(obj) -> bool:
    is_motif_breakage_trajectory_ensemble = True
    keys = ['motiflength', 'alphabet', 'number_of_letters', 'unit', 'trajectories']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifProductionTrajectoryEnsemble, missing key: {}.'.format(key))
            return False
    is_motif_breakage_trajectory_ensemble *= isinstance(obj, tuple)
    is_motif_breakage_trajectory_ensemble *= hasattr(obj, '_asdict')
    is_motif_breakage_trajectory_ensemble *= hasattr(obj, '_fields')
    return bool(is_motif_breakage_trajectory_ensemble)

def are_compatible_motif_breakage_trajectory_ensembles(
        trjs1 : MotifBreakageTrajectoryEnsemble,
        trjs2 : MotifBreakageTrajectoryEnsemble
) -> bool:
    if not isinstance_motifbreakagetrajectoryensemble(trjs1):
        print('Object is not a MotifBreakageTrajectoryEnsemble')
        return False
    if not isinstance_motifbreakagetrajectoryensemble(trjs2):
        print('Object is not a MotifBreakageTrajectoryEnsemble')
        return False
    return np.prod([are_compatible_motif_breakage_trajectories(
        trj1,
        trj2
    ) for trj1 in trjs1.trajectories for trj2 in trjs2.trajectories])
