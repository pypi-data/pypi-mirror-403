import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal

def test__transform_sequence_array_to_motif_array():
    motiflengths = [4,5,6,7]
    number_of_letters = 4
    actual = np.ones((number_of_letters,)*4)
    for motiflength in motiflengths:
        desired = np.zeros((number_of_letters+1,)+(number_of_letters,)+(number_of_letters+1,)*(motiflength-2))
        if motiflength > 5:
            indices_actual = (0,slice(None),)+(slice(1,None),)*3+(0,)*(motiflength-5)
            desired[indices_actual] += actual
        elif motiflength == 5:
            desired[0,:,1:,1:,1:] += actual
        else:
            desired[1:,:,1:,1:] = actual
        assert_equal(kdi._transform_sequence_array_to_motif_array(actual,motiflength),
                desired)

def test__motif_vector_as_array():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')

    number_of_letters = len(alphabet)
    motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)

    motif_number_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)
    desired = np.zeros(
            (number_of_letters+1,)
            +(number_of_letters,)
            +(number_of_letters+1,)*(motiflength-2)
            )
    for key in motif_number_dct.keys():
        current_array = np.random.randint(1e3)*np.ones(motif_number_dct[key].shape)
        current_indices = kdi._motif_indices_in_motifs_array(
                current_array,
                motiflength,
                key not in kdi.domains._motif_categories()[-2:]
                )
        motif_number_dct[key] = current_array
        desired[current_indices] = current_array

    motif_number_vector = kdi.MotifVector(motiflength,alphabet,unit)
    motif_number_vector = motif_number_vector(motif_number_dct)

    actual = kdi._motif_vector_as_array(motif_number_vector)
    assert_equal(actual,desired)


def test_save_and_load_motif_vector():
    archive_path = "./archive/test_motif_number_vector/"
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')

    motif_number_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)

    motif_number_vector = kdi.MotifVector(motiflength,alphabet,unit)
    motif_number_vector = motif_number_vector(motif_number_dct)

    kdi.save_motif_vector(archive_path, motif_number_vector)

    actual = kdi.load_motif_vector(archive_path)
    assert_equal(actual, motif_number_vector)
    assert(kdi.isinstance_motifvector(motif_number_vector))
