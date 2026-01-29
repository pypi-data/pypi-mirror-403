from collections import namedtuple
import numpy as  np
from numpy.testing import assert_equal
import yaml
from os.path import exists
from .motif_trajectory import are_compatible_motif_trajectories
from .motif_trajectory import save_motif_trajectory, load_motif_trajectory
from .units import transform_dict_to_unit, transform_unit_to_dict

from ..utils.save import create_directory_path_if_not_already_existing

def MotifTrajectoryEnsemble(motif_trajectories : list):
    """
    Ensemble of motif trajectories
    """
    motif_trajectory = motif_trajectories[0]
    motif_trajectory_ensemble_properties = {
            'motiflength' : motif_trajectory.motiflength,
            'alphabet' : motif_trajectory.alphabet,
            'number_of_letters' : motif_trajectory.number_of_letters,
            'unit' : motif_trajectory.unit,
            'times' : motif_trajectory.times,
            'trajectories' : motif_trajectories}
    for motif_trajectory in motif_trajectories:
        assert_equal(motif_trajectory.motiflength, motif_trajectory_ensemble_properties['motiflength'])
        assert_equal(motif_trajectory.alphabet, motif_trajectory_ensemble_properties['alphabet'])
        assert_equal(motif_trajectory.number_of_letters, motif_trajectory_ensemble_properties['number_of_letters'])
        assert motif_trajectory.unit==motif_trajectory_ensemble_properties['unit'], "Units of motif vectors need to be the same."
        assert(are_compatible_motif_trajectories(motif_trajectory,motif_trajectories[0]),
                "Motif trajectories not compatible.")
    mt = namedtuple('MotifTrajectoryEnsemble',
                tuple(motif_trajectory_ensemble_properties.keys()))
    return mt(**motif_trajectory_ensemble_properties)

def isinstance_motiftrajectoryensemble(obj) -> bool:
    is_motif_trajectory_ensemble = True
    keys = ['motiflength', 'alphabet', 'number_of_letters', 'unit', 'trajectories', 'times']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifTrajectoryEnsemble, missing key: {}.'.format(key))
            return False
    is_motif_trajectory_ensemble *= isinstance(obj, tuple)
    is_motif_trajectory_ensemble *= hasattr(obj, '_asdict')
    is_motif_trajectory_ensemble *= hasattr(obj, '_fields')
    return bool(is_motif_trajectory_ensemble)

def are_compatible_motif_trajectory_ensembles(trjs1 : MotifTrajectoryEnsemble, trjs2 : MotifTrajectoryEnsemble) -> bool:
    if not isinstance_motiftrajectoryensemble(trjs1):
        print('Object is not a MotifTrajectoryEnsemble')
        return False
    if not isinstance_motiftrajectoryensemble(trjs2):
        print('Object is not a MotifTrajectoryEnsemble')
        return False
    if are_compatible_motif_trajectories(trjs1.trajectories[0],trjs2.trajectories[0]):
        return True
    else:
        print('MotifTrajectoryEnsembles not compatible: {} mismatch.'.format(key))

def save_motif_trajectory_ensemble(archive_path : str,
        motif_trajectory_ensemble : MotifTrajectoryEnsemble
        ) -> None:
    create_directory_path_if_not_already_existing(archive_path)
    for trajectory_index in range(len(motif_trajectory_ensemble.trajectories)):
        current_path = archive_path+'motif_trajectory_{}/'.format(trajectory_index)
        create_directory_path_if_not_already_existing(current_path)
        save_motif_trajectory(current_path,
                motif_trajectory_ensemble.trajectories[trajectory_index]
                )
    with open(archive_path+'motif_trajectory_ensemble_properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_trajectory_ensemble.motiflength,
            'alphabet':motif_trajectory_ensemble.alphabet,
            'unit':transform_unit_to_dict(motif_trajectory_ensemble.unit)},
            yaml_file,
            indent=4)

def load_motif_trajectory_ensemble(archive_path : str
        ) -> MotifTrajectoryEnsemble:
    dct_filename = archive_path+'motif_trajectory_ensemble_properties.yaml'
    motif_trajectories = []
    trajectory_index = 0
    while exists(archive_path+'motif_trajectory_{}/'.format(trajectory_index)):
        motif_trajectories = motif_trajectories + [load_motif_trajectory(archive_path+'motif_trajectory_{}/'.format(trajectory_index)),]
        trajectory_index += 1
    return MotifTrajectoryEnsemble(motif_trajectories)
