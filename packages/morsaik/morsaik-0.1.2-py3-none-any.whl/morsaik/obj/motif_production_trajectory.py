from collections import namedtuple
import numpy as np
import nifty8 as ift
import itertools
from typing import Union
import yaml
from scipy.sparse import coo_matrix, save_npz, load_npz
from os import makedirs

from warnings import warn

from .times_vector import TimesVector
from .motif_vector import isinstance_motifvector
from .motif_production_vector import (isinstance_motifproductionvector,
                                      _motif_production_array_shape,
                                      _moved_axes,
                                      _reaction_indices,
                                      _array_to_motif_production_vector,
                                      )
from .units import (Unit, make_unit,
                    transform_unit_to_dict, transform_dict_to_unit)

from ..domains.motif_space import _return_motif_categories
from ..domains.trajectory_space import TrajectorySpace
from ..domains.motif_production_space import (_determine_product_and_template_categories_and_ligation_spots,
                                              _valid_production_channel,
                                              _production_channel_id,
                                              )


from ..utils.transform_vectors_to_fields import transform_dicts_to_field


def MotifProductionTrajectory(motif_production_vectors : list,
                              times : ift.Field):
    """
    A trajectory of MotifProductionVectors.
    """
    motif_production_vector = motif_production_vectors[0]
    motif_productions = [motif_production_vectors[ii].productions for ii in range(len(motif_production_vectors))]
    motif_production_trajectory_properties = {'motiflength' : motif_production_vector.motiflength,
                                              'alphabet' : motif_production_vector.alphabet,
                                              'number_of_letters' : motif_production_vector.number_of_letters,
                                              'maximum_ligation_window_length' : motif_production_vector.maximum_ligation_window_length,
                                              'unit' : motif_production_vector.unit,
                                              'times': times,
                                              'productions' : transform_dicts_to_field(motif_productions, times.domain)
                                              }
    for motif_production_vector in motif_production_vectors:
        assert(motif_production_vector.motiflength==motif_production_trajectory_properties['motiflength'])
        assert(motif_production_vector.alphabet==motif_production_trajectory_properties['alphabet'])
        assert(motif_production_vector.number_of_letters==motif_production_trajectory_properties['number_of_letters'])
        assert motif_production_vector.unit==motif_production_trajectory_properties['unit'], "Units of motif vectors need to be the same."
    mt = namedtuple('MotifProductionTrajectory',
                tuple(motif_production_trajectory_properties.keys()))
    return mt(**motif_production_trajectory_properties)

def isinstance_motifproductiontrajectory(obj) -> bool:
    is_motif_production_trajectory = True
    keys = ['motiflength', 'alphabet', 'maximum_ligation_window_length', 'number_of_letters', 'unit', 'times', 'productions']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifProductionTrajectory, missing key: {}.'.format(key))
            return False
    is_motif_production_trajectory *= isinstance(obj, tuple)
    is_motif_production_trajectory *= hasattr(obj, '_asdict')
    is_motif_production_trajectory *= hasattr(obj, '_fields')
    return bool(is_motif_production_trajectory)

def are_compatible_motif_production_trajectories(trj1 : MotifProductionTrajectory, trj2 : MotifProductionTrajectory) -> bool:
    if not isinstance_motifproductiontrajectory(trj1):
        print('Object is not a MotifProductionTrajectory')
        return False
    if not isinstance_motifproductiontrajectory(trj2):
        print('Object is not a MotifProductionTrajectory')
        return False
    keys = ['motiflength', 'alphabet', 'maximum_ligation_window_length', 'unit']
    for key in keys:
        tt1 = trj1._asdict()[key]
        tt2 = trj2._asdict()[key]
        if isinstance(tt1, ift.Field):
            tt1 = tt1.val
        if isinstance(tt2, ift.Field):
            tt2 = tt2.val
        if not np.prod(tt1==tt2):
            print('MotifProductionTrajectories not compatible: {} mismatch.'.format(key))
            return False
    try:
        if not np.prod(trj1.times.val==trj2.times.val) or not np.prod(trj1.times.domain[0]==trj2.times.domain[0]):
            key = 'times'
            warn('MotifTrajectories {} mismatch.'.format(key))
    except ValueError:
        key = 'times'
        warn('MotifTrajectories {} mismatch.'.format(key))
    return True

def save_motif_production_trajectory(
        archive_path : str,
        motif_production_trajectory : MotifProductionTrajectory,
        file_sparse : bool = True
        ) -> None:
    makedirs(archive_path, exist_ok = True)
    productions, times = _motif_production_trajectory_as_array(motif_production_trajectory)
    if file_sparse:
        save_npz(archive_path+'motif_production_trajectory_productions',
                coo_matrix(productions.reshape(1,-1))
        )
    else:
        np.save(archive_path+'motif_production_trajectory_productions',
                productions
                )
    np.save(archive_path+'motif_production_trajectory_times',
            times
            )

    with open(archive_path+'motif_production_trajectory_properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_production_trajectory.motiflength,
            'alphabet':motif_production_trajectory.alphabet,
                   'unit':transform_unit_to_dict(motif_production_trajectory.unit),
                   'times_unit' : transform_unit_to_dict(motif_production_trajectory.times.domain[0].units),
                   'maximum_ligation_window_length' : motif_production_trajectory.maximum_ligation_window_length,
                   },
            yaml_file,
            indent=4)

def load_motif_production_trajectory(
        archive_path : str,
        file_sparse : bool = True
        ) -> MotifProductionTrajectory:
    dct_filename = archive_path+'motif_production_trajectory_properties.yaml'
    productions_filename = archive_path+'motif_production_trajectory_productions'
    productions_filename += '.np'+'z'*file_sparse+'y'*(1-file_sparse)
    times_filename = archive_path+'motif_production_trajectory_times.npy'
    with open(dct_filename, 'r') as yaml_file:
        properties = yaml.safe_load(yaml_file)
    times_unit = properties['times_unit']
    del properties['times_unit']
    times_vector = TimesVector(np.load(times_filename), times_unit)
    if file_sparse:
        motif_production_trajectory_array = np.asarray(coo_matrix.todense(load_npz(productions_filename)))
        motif_production_trajectory_array = motif_production_trajectory_array.reshape(
                times_vector.domain.shape + _motif_production_array_shape(
                    len(properties["alphabet"]),
                    properties["maximum_ligation_window_length"]
                )
        )
    else:
        motif_production_trajectory_array = np.load(productions_filename)
    properties['unit'] = transform_dict_to_unit(properties['unit'])
    motif_production_trajectory = _array_to_motif_production_trajectory(times_vector, motif_production_trajectory_array,
            **properties
            )
    return motif_production_trajectory

def _array_to_motif_production_trajectory(
        times : TimesVector,
        motif_production_trajectory_array: np.ndarray,
        motiflength : int,
        alphabet : list,
        unit : Unit,
        maximum_ligation_window_length : int
        ) -> MotifProductionTrajectory:
    unit = make_unit(unit)
    motif_production_vectors = [_array_to_motif_production_vector(
        motif_production_trajectory_array[ii],
        motiflength,
        alphabet,
        unit,
        maximum_ligation_window_length
    ) for ii in range(motif_production_trajectory_array.shape[0])]
    return MotifProductionTrajectory(motif_production_vectors, times)

def _motif_production_trajectory_as_array(motif_production_trajectory : MotifProductionTrajectory
    ) -> Union[np.ndarray,np.ndarray]:
    """
    returns motifs and times of MotifTrajectory object into numpy arrays.

    Parameters:
    -----------
    motif_trajectory : MotifProducitonTrajectory

    Returns:
    --------
    motifs : np.ndarray
    times : np.ndarray
    """
    times = np.asarray(motif_production_trajectory.times.val)
    number_of_letters = motif_production_trajectory.number_of_letters
    motiflength = motif_production_trajectory.motiflength
    maximum_ligation_window_length = motif_production_trajectory.maximum_ligation_window_length

    motif_categories = _return_motif_categories(motiflength)

    motif_production_trajectory_array = np.zeros(times.shape+_motif_production_array_shape(number_of_letters,maximum_ligation_window_length))

    if maximum_ligation_window_length < 4:
        ligation_window_lengths = np.array([maximum_ligation_window_length])
    else:
        ligation_window_lengths = np.arange(4,maximum_ligation_window_length+1)

    for ligation_window_length in ligation_window_lengths:
        product_categories, template_categories, ligation_spots = _determine_product_and_template_categories_and_ligation_spots(motiflength,
                maximum_ligation_window_length,
                ligation_window_length
                )

        for product_category, template_category, ligation_spot in itertools.product(product_categories, template_categories, ligation_spots):
            if not _valid_production_channel(product_category,
                template_category,
                ligation_window_length, ligation_spot,
                maximum_ligation_window_length):
                continue
            reaction_key = _production_channel_id(product_category, template_category,
                    ligation_window_length, ligation_spot)

            destination_axes, source_axes = _moved_axes(ligation_window_length,ligation_spot, maximum_ligation_window_length)
            mpa_indices = _reaction_indices(product_category, template_category,
                    ligation_window_length, ligation_spot,
                    maximum_ligation_window_length, axes_moved=False)
            np.moveaxis(motif_production_trajectory_array,np.array(source_axes)+1,np.array(destination_axes)+1)[(slice(None),)+mpa_indices] = motif_production_trajectory.productions[reaction_key].val
    return motif_production_trajectory_array, times
