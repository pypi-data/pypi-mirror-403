from collections import namedtuple
import numpy as  np
import jax.numpy as jnp
import jax
import yaml
from typing import Union

from warnings import warn

import nifty8 as ift

from .motif_vector import _motif_vector_as_array, _array_to_motif_vector_dct, category_indices
from .motif_vector import MotifVector, isinstance_motifvector

from ..domains.trajectory_space import TrajectorySpace, TimeRGSpace, UnstructuredTimeDomain
from .times_vector import TimesVector
from .units import isunit, make_unit
from .units import transform_unit_to_dict, transform_dict_to_unit

from ..utils.save import create_directory_path_if_not_already_existing
from ..utils.transform_vectors_to_fields import transform_dicts_to_field

def MotifTrajectory(motif_vectors : list,
                    times : Union[TimeRGSpace, UnstructuredTimeDomain]):
    """
    """
    motif_vector = motif_vectors[0]
    motifs = [motif_vectors[ii].motifs for ii in range(len(motif_vectors))]
    if not isinstance(times,ift.Field):
        raise TypeError('times vector needs to be Field')
    if not (isinstance(times.domain,(TimeRGSpace,UnstructuredTimeDomain)) or isinstance(times.domain[0],(TimeRGSpace,UnstructuredTimeDomain))):
        raise TypeError('times vector domain needs to be a time domain')
    motif_trajectory_properties = {'motiflength' : motif_vector.motiflength,
        'alphabet' : motif_vector.alphabet,
        'number_of_letters' : motif_vector.number_of_letters,
        'unit' : motif_vector.unit,
        'times': times,
        'motifs' : transform_dicts_to_field(motifs, times.domain)}
    for motif_vector in motif_vectors:
        assert(motif_vector.motiflength==motif_trajectory_properties['motiflength'])
        assert(motif_vector.alphabet==motif_trajectory_properties['alphabet'])
        assert(motif_vector.number_of_letters==motif_trajectory_properties['number_of_letters'])
        if isunit(motif_vector.unit)==isunit(motif_trajectory_properties['unit']):
            assert motif_vector.unit==motif_trajectory_properties['unit'], "Units of motif vectors need to be the same:{unit1} != {unit2}".format(
                unit1 = motif_vector.unit,
                unit2 = motif_trajectory_properties['unit']
                )
        else:
            raise AssertionError("Units of motif vectors need to be the same:{unit1} != {unit2}".format(
                unit1 = motif_vector.unit,
                unit2 = motif_trajectory_properties['unit']
                )
                                 )
    mt = namedtuple('MotifTrajectory',
                tuple(motif_trajectory_properties.keys()))
    return mt(**motif_trajectory_properties)

def isinstance_motiftrajectory(obj) -> bool:
    is_motif_trajectory = True
    keys = ['motiflength', 'alphabet', 'number_of_letters', 'unit', 'times', 'motifs']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifTrajectory, missing key: {}.'.format(key))
            return False
    is_motif_trajectory *= isinstance(obj, tuple)
    is_motif_trajectory *= hasattr(obj, '_asdict')
    is_motif_trajectory *= hasattr(obj, '_fields')
    return bool(is_motif_trajectory)

def are_compatible_motif_trajectories(trj1 : MotifTrajectory, trj2 : MotifTrajectory) -> bool:
    if not isinstance_motiftrajectory(trj1):
        print('Object is not a MotifTrajectory')
        return False
    if not isinstance_motiftrajectory(trj2):
        print('Object is not a MotifTrajectory')
        return False
    keys = ['motiflength', 'alphabet', 'unit']
    for key in keys:
        if not np.prod(trj1._asdict()[key]==trj2._asdict()[key]):
            print('MotifTrajectories not compatible: {} mismatch.'.format(key))
            return False
    try:
        if not np.prod(trj1.times.val==trj2.times.val) or not np.prod(trj1.times.domain[0]==trj2.times.domain[0]):
            key = 'times'
            warn('MotifTrajectories {} mismatch.'.format(key))
    except ValueError:
        key = 'times'
        warn('MotifTrajectories {} mismatch.'.format(key))
    return True

def save_motif_trajectory(archive_path : str,
        motif_trajectory : MotifTrajectory
        ) -> None:
    create_directory_path_if_not_already_existing(archive_path)
    motifs, times = _motif_trajectory_as_array(motif_trajectory)
    jnp.save(archive_path+'motif_trajectory_motifs',
            motifs
            )
    jnp.save(archive_path+'motif_trajectory_times',
            times
            )

    with open(archive_path+'motif_trajectory_properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_trajectory.motiflength,
            'alphabet':motif_trajectory.alphabet,
                   'unit':transform_unit_to_dict(motif_trajectory.unit),
                   'times_unit' : transform_unit_to_dict(motif_trajectory.times.domain[0].units)},
            yaml_file,
            indent=4)

def load_motif_trajectory(archive_path : str
        ) -> MotifTrajectory:
    dct_filename = archive_path+'motif_trajectory_properties.yaml'
    motifs_filename = archive_path+'motif_trajectory_motifs'+'.npy'
    times_filename = archive_path+'motif_trajectory_times.npy'
    with open(dct_filename, 'r') as yaml_file:
        motif_trajectory_properties = yaml.safe_load(yaml_file)
    times_unit = motif_trajectory_properties['times_unit']
    del motif_trajectory_properties['times_unit']
    motif_trajectory_properties['unit'] = transform_dict_to_unit(motif_trajectory_properties['unit'])
    makeMotifVector = MotifVector(**motif_trajectory_properties)
    motif_vector_list = [makeMotifVector(
        _array_to_motif_vector_dct(motif_vec,motif_trajectory_properties['motiflength'],motif_trajectory_properties['alphabet'])
        ) for motif_vec in jnp.load(motifs_filename)]
    times_vector = TimesVector(jnp.load(times_filename),times_unit)
    return MotifTrajectory(
            motif_vector_list,
            times=times_vector
            )

def _array_to_motif_trajectory(
        motif_trajectory_array : np.ndarray,
        times : TimesVector,
        **motif_trajectory_properties
        ) -> MotifTrajectory:
    motif_vectors = [MotifVector(
            motif_trajectory_properties['motiflength'],
            motif_trajectory_properties['alphabet'],
            motif_trajectory_properties['unit']
            )(_array_to_motif_vector_dct(
                motif_trajectory_array[ii],
                motif_trajectory_properties['motiflength'],
                motif_trajectory_properties['alphabet'],
                ))
                     for ii in range(len(motif_trajectory_array))] 
    return MotifTrajectory(motif_vectors, times)

def _motif_trajectory_as_array(motif_trajectory : MotifTrajectory
        ) -> Union[np.ndarray,np.ndarray]:
    """
    returns motifs and times of MotifTrajectory object into numpy arrays.

    Parameters:
    -----------
    motif_trajectory : MotifTrajectory

    Returns:
    --------
    motifs : np.ndarray
    times : np.ndarray
    """
    times = np.asarray(motif_trajectory.times.val)
    number_of_letters = motif_trajectory.number_of_letters
    motiflength = motif_trajectory.motiflength

    motif_array_shape = (number_of_letters+1,)
    motif_array_shape += (number_of_letters,)*int(motiflength>2)
    motif_array_shape += (number_of_letters+1,)*(motiflength-1-int(motiflength>2))
    motif_array = np.zeros((len(times),) + motif_array_shape)
    for motif_category in motif_trajectory.motifs.keys():
        # get indices
        indices = (slice(None),) + category_indices(motif_category, motiflength, motif_trajectory.alphabet)
        motif_array[indices] += motif_trajectory.motifs[motif_category].val
    return motif_array, times

def extract_initial_motif_vector_from_motif_trajectory(
        motif_trajectory : MotifTrajectory,
        c_ref : float = None
    ) -> MotifVector:
    motif_array, _ = _motif_trajectory_as_array(motif_trajectory)
    if c_ref is not None:
        n_ref = motif_array[0,0,0,0,0]
        motif_array = c_ref*motif_array/n_ref
        unit = make_unit('c_0')
    else:
        unit = motif_trajectory.unit
    mvd = _array_to_motif_vector_dct(
        motif_array[0],
        motif_trajectory.motiflength,
        motif_trajectory.alphabet
    )
    motif_vector = MotifVector(
        motif_trajectory.motiflength,
        motif_trajectory.alphabet,
        unit
    )
    return motif_vector(mvd)
