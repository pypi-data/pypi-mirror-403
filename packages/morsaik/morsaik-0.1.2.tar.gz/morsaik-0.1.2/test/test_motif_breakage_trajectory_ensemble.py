import pytest
import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal

def test_motif_breakage_trajectory_ensemble():
    motiflengths = [2,3,4,5,6,9,10]
    for motiflength in motiflengths:
        alphabet = ['a','b','c']
        unit = kdi.make_unit('')
        times = kdi.TimesVector(np.arange(3), 'ms')

        motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)
        motif_breakage_dct = kdi._create_empty_motif_breakage_dct(motiflength,
                                                                        alphabet,
                                                                        )

        motif_breakage_vector = kdi.MotifBreakageVector(motiflength,
                                                            alphabet,
                                                            unit,
                                                            )
        motif_breakage_vector = motif_breakage_vector(motif_breakage_dct)
        motif_breakage_vectors = [motif_breakage_vector,]*times.shape[0]
        mbt = kdi.MotifBreakageTrajectory(motif_breakage_vectors,times)

        mbts = [mbt,mbt]

        mbte = kdi.MotifBreakageTrajectoryEnsemble(mbts)

        assert_equal(mbte.trajectories[0].times.val,mbt.times.val)
        assert_equal(mbte.trajectories[0].times.domain,mbt.times.domain)
        assert_equal(mbte.trajectories[1].times.val,mbt.times.val)
        assert_equal(mbte.trajectories[1].times.domain,mbt.times.domain)
        assert_equal(mbte.alphabet, mbt.alphabet)
        assert_equal(mbte.number_of_letters, mbt.number_of_letters)
        assert(mbte.motiflength==mbt.motiflength)
        assert(mbte.unit==mbt.unit)
        for trajectory in mbte.trajectories:
            for ii in range(len(trajectory.times.val)):
                assert_equal(trajectory.breakages.val,
                        mbt.breakages.val
                        )

        assert(kdi.isinstance_motifbreakagetrajectoryensemble(mbte))
        print('mbte')
        print(mbte)
        assert(kdi.are_compatible_motif_breakage_trajectory_ensembles(mbte,mbte))

@pytest.mark.skip
def test_save_and_load_motif_breakage_trajectory_ensemble():
    alphabet = ['A','T']
    motiflengths = [4,]#[2,3,4,5,6,10]
    complements = [1,0]
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    times = kdi.TimesVector(np.arange(3), kdi.read.symbol_config('time', unitformat=True))

    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        archive_path = kdi.utils.create_trajectory_ensemble_path(
                strand_trajectory_id=strand_trajectory_id,
                param_file_no = 0,
                motiflength=motiflength
                )

        motif_breakage_vector = kdi.get.motif_breakage_rate_constants_from_strand_reactor_parameters(strand_trajectory_id, motiflength, complements)
        motif_breakage_vectors = [motif_breakage_vector,]*times.shape[0]
        motif_breakage_trajectory = kdi.MotifBreakageTrajectory(motif_breakage_vectors,times)
        motif_breakage_trajectories = [motif_breakage_trajectory,]*2
        mbte = kdi.MotifBreakageTrajectoryEnsemble(motif_breakage_trajectories)

        kdi.save_motif_breakage_trajectory_ensemble(archive_path, mbte)
        actual_mbte = kdi.load_motif_breakage_trajectory_ensemble(archive_path)
        assert(mbte.motiflength==actual_mbte.motiflength)
        assert(mbte.alphabet==actual_mbte.alphabet)
        assert(mbte.number_of_letters==actual_mbte.number_of_letters)
        assert(mbte.unit==actual_mbte.unit)
        '''
        for trajectory_index in range(len(actual_mbte.trajectories)):
            actual = kdi._motif_breakage_trajectory_as_array(actual_mbte.trajectories[trajectory_index])
            assert_equal(actual,
                    kdi._motif_breakage_trajectory_as_array(motif_breakage_trajectories[trajectory_index])
                    )
        '''
