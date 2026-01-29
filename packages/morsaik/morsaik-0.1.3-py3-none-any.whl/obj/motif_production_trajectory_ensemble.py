from collections import namedtuple
import numpy as  np
import yaml
from os.path import exists
from scipy.sparse import coo_matrix, save_npz, load_npz

from .motif_production_trajectory import save_motif_production_trajectory
from .motif_production_trajectory import are_compatible_motif_production_trajectories
from .motif_production_trajectory import load_motif_production_trajectory

from ..utils.save import create_directory_path_if_not_already_existing

def MotifProductionTrajectoryEnsemble(motif_production_trajectories : list):
    """
    Ensemble of motif production trajectories
    """
    motif_production_trajectory = motif_production_trajectories[0]
    motif_production_trajectory_ensemble_properties = {
            'motiflength' : motif_production_trajectory.motiflength,
            'alphabet' : motif_production_trajectory.alphabet,
            'maximum_ligation_window_length' : motif_production_trajectory.maximum_ligation_window_length,
            'number_of_letters' : motif_production_trajectory.number_of_letters,
            'unit' : motif_production_trajectory.unit,
            'trajectories' : motif_production_trajectories
            }
    for motif_production_trajectory in motif_production_trajectories[1:]:
        assert(motif_production_trajectory.motiflength==motif_production_trajectory_ensemble_properties['motiflength'])
        assert(motif_production_trajectory.alphabet==motif_production_trajectory_ensemble_properties['alphabet'])
        assert(motif_production_trajectory.number_of_letters==motif_production_trajectory_ensemble_properties['number_of_letters'])
        assert motif_production_trajectory.unit==motif_production_trajectory_ensemble_properties['unit'], "Units of motif vectors need to be the same."
        assert(are_compatible_motif_production_trajectories(motif_production_trajectory,motif_production_trajectories[0]),
                "Motif trajectories not compatible.")
    mt = namedtuple('MotifProductionTrajectoryEnsemble',
                tuple(motif_production_trajectory_ensemble_properties.keys()))
    return mt(**motif_production_trajectory_ensemble_properties)

def isinstance_motifproductiontrajectoryensemble(obj) -> bool:
    is_motif_production_trajectory_ensemble = True
    keys = ['motiflength', 'alphabet', 'maximum_ligation_window_length', 'number_of_letters', 'unit', 'trajectories']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifProductionTrajectoryEnsemble, missing key: {}.'.format(key))
            return False
    is_motif_production_trajectory_ensemble *= isinstance(obj, tuple)
    is_motif_production_trajectory_ensemble *= hasattr(obj, '_asdict')
    is_motif_production_trajectory_ensemble *= hasattr(obj, '_fields')
    return bool(is_motif_production_trajectory_ensemble)

def are_compatible_motif_production_trajectory_ensembles(
        trjs1 : MotifProductionTrajectoryEnsemble,
        trjs2 : MotifProductionTrajectoryEnsemble
) -> bool:
    if not isinstance_motifproductiontrajectoryensemble(trjs1):
        print('Object is not a MotifProductionTrajectoryEnsemble')
        return False
    if not isinstance_motifproductiontrajectoryensemble(trjs2):
        print('Object is not a MotifProductionTrajectoryEnsemble')
        return False
    return np.prod([are_compatible_motif_production_trajectories(
        trj1,
        trj2
    ) for trj1 in trjs1.trajectories for trj2 in trjs2.trajectories])

def save_motif_production_trajectory_ensemble(
        archive_path : str,
        motif_production_trajectory_ensemble : MotifProductionTrajectoryEnsemble,
        file_space : bool = True
    ) -> None:
    create_directory_path_if_not_already_existing(archive_path)
    for trajectory_index in range(len(motif_production_trajectory_ensemble.trajectories)):
        current_path = archive_path+'motif_production_trajectory_{}/'.format(trajectory_index)
        create_directory_path_if_not_already_existing(current_path)
        save_motif_production_trajectory(current_path,
                motif_production_trajectory_ensemble.trajectories[trajectory_index]
                )
    with open(archive_path+'motif_production_trajectory_ensemble_properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_production_trajectory_ensemble.motiflength,
            'alphabet':motif_production_trajectory_ensemble.alphabet,
            'maximum_ligation_window_length' : motif_production_trajectory_ensemble.maximum_ligation_window_length,
            'unit':motif_production_trajectory_ensemble.unit
                   },
            yaml_file,
            indent=4)

def load_motif_production_trajectory_ensemble(
        archive_path : str,
        file_sparse : bool = True
    ) -> MotifProductionTrajectoryEnsemble:
    dct_filename = archive_path+'motif_production_trajectory_ensemble_properties.yaml'
    motif_production_trajectories = []
    trajectory_index = 0
    while exists(archive_path+'motif_production_trajectory_{}/'.format(trajectory_index)):
        motif_production_trajectories = motif_production_trajectories + [load_motif_production_trajectory(
            archive_path+'motif_production_trajectory_{}/'.format(trajectory_index),
            file_sparse=file_sparse
        ),]
        trajectory_index += 1
    return MotifProductionTrajectoryEnsemble(motif_production_trajectories)
