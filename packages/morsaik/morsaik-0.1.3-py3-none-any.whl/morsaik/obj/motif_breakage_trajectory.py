from collections import namedtuple
import nifty8 as ift
import numpy as np

from ..utils.transform_vectors_to_fields import transform_dicts_to_field

def MotifBreakageTrajectory(motif_breakage_vectors : list,
                            times : ift.Field):
    motif_breakage_vector = motif_breakage_vectors[0]
    motif_breakages = [motif_breakage_vectors[ii].breakages for ii in range(len(motif_breakage_vectors))]
    motif_breakage_trajectory_properties = {'motiflength' : motif_breakage_vector.motiflength,
                                              'alphabet' : motif_breakage_vector.alphabet,
                                              'number_of_letters' : motif_breakage_vector.number_of_letters,
                                              'unit' : motif_breakage_vector.unit,
                                              'times': times,
                                              'breakages' : transform_dicts_to_field(motif_breakages, times.domain)
                                              }
    for motif_breakage_vector in motif_breakage_vectors:
        assert(motif_breakage_vector.motiflength==motif_breakage_trajectory_properties['motiflength'])
        assert(motif_breakage_vector.alphabet==motif_breakage_trajectory_properties['alphabet'])
        assert(motif_breakage_vector.number_of_letters==motif_breakage_trajectory_properties['number_of_letters'])
        assert motif_breakage_vector.unit==motif_breakage_trajectory_properties['unit'], "Units of motif breakage vectors need to be the same."
    mt = namedtuple('MotifBreakageTrajectory',
                tuple(motif_breakage_trajectory_properties.keys()))
    return mt(**motif_breakage_trajectory_properties)

def isinstance_motifbreakagetrajectory(obj) -> bool:
    is_motif_breakage_trajectory = True
    keys = ['motiflength', 'alphabet', 'number_of_letters', 'unit', 'times', 'breakages']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifBreakageTrajectory, missing key: {}.'.format(key))
            return False
    is_motif_breakage_trajectory *= isinstance(obj, tuple)
    is_motif_breakage_trajectory *= hasattr(obj, '_asdict')
    is_motif_breakage_trajectory *= hasattr(obj, '_fields')
    return bool(is_motif_breakage_trajectory)

def are_compatible_motif_breakage_trajectories(
        trj1 : MotifBreakageTrajectory,
        trj2 : MotifBreakageTrajectory
    ) -> bool:
    if not isinstance_motifbreakagetrajectory(trj1):
        print('Object is not a MotifBreakageTrajectory')
        return False
    if not isinstance_motifbreakagetrajectory(trj2):
        print('Object is not a MotifBreakageTrajectory')
        return False
    keys = ['motiflength', 'alphabet', 'unit', 'times']
    for key in keys:
        tt1 = trj1._asdict()[key]
        tt2 = trj2._asdict()[key]
        if isinstance(tt1, ift.Field):
            tt1 = tt1.val
        if isinstance(tt2, ift.Field):
            tt2 = tt2.val
        if not np.prod(tt1==tt2):
            print('MotifBreakageTrajectories not compatible: {} mismatch.'.format(key))
            return False
    return True
