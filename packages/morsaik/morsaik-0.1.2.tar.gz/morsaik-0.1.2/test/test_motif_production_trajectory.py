import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal
import pytest

def test_motif_production_trajectory():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    times = kdi.TimesVector(np.arange(3),'ms')
    maximum_ligation_window_length = motiflength

    motif_production_vector_dct = kdi._create_empty_motif_production_dict(
            motiflength,
            alphabet,
            maximum_ligation_window_length
            )
    motif_production_vector = kdi.MotifProductionVector(motiflength,alphabet,unit,
            maximum_ligation_window_length)
    motif_production_vector = motif_production_vector(motif_production_vector_dct)
    motif_production_vectors = [motif_production_vector,]*times.shape[0]
    print('askdfjghasdf')
    print(motif_production_vectors)
    print(times)
    mpt = kdi.MotifProductionTrajectory(motif_production_vectors, times)

    assert_equal(mpt.times.val,times.val)
    assert_equal(mpt.times.domain[0].units,times.domain[0].units)
    assert(mpt.alphabet==alphabet)
    assert(mpt.number_of_letters==len(alphabet))
    assert(mpt.motiflength==motiflength)
    assert(mpt.unit==unit)
    for key in mpt.productions.val.keys():
        assert_equal(mpt.productions[key].val,
                np.asarray([motif_production_vectors[ii].productions[key].val for ii in range(times.shape[0])])
                )

def test_motif_producion_trajectory():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = 'mol/L'
    times = kdi.TimesVector(np.arange(3),'ms')
    maximum_ligation_window_length = motiflength

    motif_production_vector_dct = kdi._create_empty_motif_production_dict(
            motiflength,
            alphabet,
            maximum_ligation_window_length)

    motif_production_vector = kdi.MotifProductionVector(motiflength,alphabet,unit,
            maximum_ligation_window_length)
    motif_production_vector2 = kdi.MotifProductionVector(motiflength,alphabet,'a',
            maximum_ligation_window_length)
    motif_production_vector = motif_production_vector(motif_production_vector_dct)
    motif_production_vector2 = motif_production_vector2(motif_production_vector_dct)
    motif_production_vectors = [motif_production_vector,]*(times.shape[0]-1)
    motif_production_vectors += [motif_production_vector2,]
    with pytest.raises(AssertionError):
        mpt = kdi.MotifProductionTrajectory(motif_production_vectors, times)

def test_save_and_load_motif_production_trajectory():
    motiflengths = [4,] # TODO: [2,3,4,5,6,10]
    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        archive_path = './archive/{strand_trajectory_id}/'.format(strand_trajectory_id=strand_trajectory_id)
        motif_production_trajectory = kdi.get.strand_motifs_productions_trajectory(
            motiflength,
            strand_trajectory_id,
        )
        kdi.save_motif_production_trajectory(archive_path, motif_production_trajectory)
        actual = kdi._motif_production_trajectory_as_array(
            kdi.load_motif_production_trajectory(archive_path)
        )
        assert_equal(actual,
                     kdi._motif_production_trajectory_as_array(motif_production_trajectory)
                     )
