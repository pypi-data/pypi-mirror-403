import morsaik as kdi
import numpy as np

def test_motif_breakage_trajectory():
    motiflengths = [2,3,4,5,6,9,10]
    alphabet = ['a','b']
    units = [kdi.make_unit(''),1./kdi.make_unit('s')]
    times = kdi.TimesVector(np.arange(3), kdi.make_unit('s'))
    for motiflength in motiflengths:
        for unit in units:
            motif_breakage_vector_dct = kdi._create_empty_motif_breakage_dct(motiflength,
                                                alphabet
                                                )
            motif_breakage_vector = kdi.MotifBreakageVector(motiflength,alphabet,unit)
            motif_breakage_vector = motif_breakage_vector(motif_breakage_vector_dct)
            mbvs = [motif_breakage_vector]*times.shape[0]
            motif_breakage_trajectory = kdi.MotifBreakageTrajectory(mbvs, times)
            assert(kdi.isinstance_motifbreakagetrajectory(motif_breakage_trajectory))
            assert(kdi.are_compatible_motif_breakage_trajectories(
                motif_breakage_trajectory,
                motif_breakage_trajectory)
                   )
