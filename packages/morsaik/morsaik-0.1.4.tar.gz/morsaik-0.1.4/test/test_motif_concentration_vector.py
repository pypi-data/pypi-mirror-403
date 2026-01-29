import morsaik as kdi
from morsaik import make_unit
import numpy as np
from numpy.testing import assert_equal

def test_motif_concentration_vector():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = make_unit('mol')/make_unit('L')

    motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)

    motif_concentration_dct = kdi._create_empty_motif_vector_dct(motiflength,alphabet=alphabet)

    motif_concentration_vector = kdi.MotifConcentrationVector(motiflength,alphabet)
    motif_concentration_vector = motif_concentration_vector(motif_concentration_dct)

    assert(motif_concentration_vector.alphabet==alphabet)
    assert(motif_concentration_vector.number_of_letters==len(alphabet))
    assert(motif_concentration_vector.motiflength==motiflength)
    assert(motif_concentration_vector.unit/unit==1.0)
    for motif_category in motif_categories:
        assert_equal(motif_concentration_vector.motifs[motif_category].val,
                motif_concentration_dct[motif_category].val
                )
