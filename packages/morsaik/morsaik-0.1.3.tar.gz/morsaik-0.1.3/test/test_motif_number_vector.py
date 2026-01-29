import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal

from morsaik import make_unit

def test_motif_number_vector():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = make_unit('particles')

    motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)

    motif_number_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)

    motif_number_vector = kdi.MotifNumberVector(motiflength,alphabet)
    motif_number_vector = motif_number_vector(motif_number_dct)

    assert(motif_number_vector.alphabet==alphabet)
    assert(motif_number_vector.number_of_letters==len(alphabet))
    assert(motif_number_vector.motiflength==motiflength)
    assert(motif_number_vector.unit==unit)
    for motif_category in motif_categories:
        assert_equal(motif_number_vector.motifs[motif_category].val,
                motif_number_dct[motif_category].val
                )
