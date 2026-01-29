import morsaik as kdi

def test_motif_breakage_vector():
    motiflengths = [2,3,4,5,6,9,10]
    alphabet = ['a','b']
    units = [kdi.make_unit(''),1./kdi.make_unit('s')]
    for motiflength in motiflengths:
        for unit in units:
            motif_breakage_vector_dct = kdi._create_empty_motif_breakage_dct(motiflength,
                                                alphabet
                                                )
            motif_breakage_vector = kdi.MotifBreakageVector(motiflength,alphabet,unit)
            motif_breakage_vector = motif_breakage_vector(motif_breakage_vector_dct)
            assert(kdi.isinstance_motifbreakagevector(motif_breakage_vector))
