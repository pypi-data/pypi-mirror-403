import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal
import pytest

def test_motif_trajectory():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    times = kdi.TimesVector(np.arange(3), 'ms')

    motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)
    motif_number_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)

    motif_number_vector = kdi.MotifVector(motiflength,alphabet,unit)
    motif_number_vector = motif_number_vector(motif_number_dct)
    motif_number_vectors = [motif_number_vector,]*times.shape[0]
    mt = kdi.MotifTrajectory(motif_number_vectors,times)

    assert_equal(mt.times.val,times.val)
    assert(mt.times.domain[0].units,times.domain[0].units)
    assert(mt.alphabet==alphabet)
    assert(mt.number_of_letters==len(alphabet))
    assert(mt.motiflength==motiflength)
    assert(mt.unit==unit)
    for ii in range(times.shape[0]):
        for key in mt.motifs.keys():
            assert_equal(mt.motifs[key].val[ii],
                    motif_number_vectors[ii].motifs[key].val
                )

def test_motif_trajectory_assertion():
    """
    Tests that the concatentaiton of motif_vectors with different units raises AssertionError
    """
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    units2 = [kdi.make_unit(''),kdi.make_unit('mol')]
    for unit2 in units2:
        times = kdi.TimesVector(np.arange(3), 'ms')

        motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)
        motif_number_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)

        motif_number_vector = kdi.MotifVector(motiflength,alphabet,unit)
        motif_number_vector2 = kdi.MotifVector(motiflength,alphabet,unit2)
        motif_number_vector = motif_number_vector(motif_number_dct)
        motif_number_vector2 = motif_number_vector2(motif_number_dct)
        motif_number_vectors = [motif_number_vector,]*times.shape[0]
        motif_number_vectors[-1] = motif_number_vector2
        with pytest.raises(AssertionError):
            mt = kdi.MotifTrajectory(motif_number_vectors,times)

def test_save_and_load_motif_trajectory():
    motiflengths = [2,3,4,5,6,10]
    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        archive_path = './archive/{strand_trajectory_id}/'.format(strand_trajectory_id=strand_trajectory_id)

        motif_trajectory = kdi.get.strand_motifs_trajectory(motiflength, strand_trajectory_id)
        kdi.save_motif_trajectory(archive_path, motif_trajectory)
        actual = kdi._motif_trajectory_as_array(
                kdi.load_motif_trajectory(archive_path)
                )
        assert_equal(actual,
                kdi._motif_trajectory_as_array(motif_trajectory)
                )

def test_array_to_motif_trajectory():
    motiflengths = [2,3,4,5,6,10]
    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        archive_path = './archive/{strand_trajectory_id}/'.format(strand_trajectory_id=strand_trajectory_id)

        motif_trajectory = kdi.get.strand_motifs_trajectory(motiflength, strand_trajectory_id)
        motif_trajectory_array, times_array = kdi._motif_trajectory_as_array(motif_trajectory)
        actual = kdi._array_to_motif_trajectory(
                motif_trajectory_array,
                motif_trajectory.times,
                motiflength = motif_trajectory.motiflength,
                alphabet = motif_trajectory.alphabet,
                unit = motif_trajectory.unit
                )
        actual = kdi._motif_trajectory_as_array(
                actual
                )
        assert_equal(actual,
                kdi._motif_trajectory_as_array(motif_trajectory)
                )
