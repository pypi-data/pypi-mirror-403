import morsaik as kdi
import numpy as np

from numpy.testing import assert_equal

def test_MotifTrajectoryEnsemble():
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

    mts = [mt,mt]

    mte = kdi.MotifTrajectoryEnsemble(mts)

    assert_equal(mte.trajectories[0].times.val,mt.times.val)
    assert_equal(mte.trajectories[0].times.domain,mt.times.domain)
    assert_equal(mte.trajectories[1].times.val,mt.times.val)
    assert_equal(mte.trajectories[1].times.domain,mt.times.domain)
    assert_equal(mte.alphabet, mt.alphabet)
    assert_equal(mte.number_of_letters, mt.number_of_letters)
    assert(mte.motiflength==mt.motiflength)
    assert(mte.unit==mt.unit)
    for trajectory in mte.trajectories:
        for ii in range(len(trajectory.times.val)):
            assert_equal(trajectory.motifs.val,
                    mt.motifs.val
                    )


    print('mt.times')
    print(mt.times)
    assert(kdi.isinstance_motiftrajectoryensemble(mte))
    assert(kdi.are_compatible_motif_trajectory_ensembles(mte,mte))

def test_save_and_load_MotifTrajectoryEnsemble():
    alphabet = ['a','b','c']
    motiflengths = [2,3,4,5,6,10]
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    times = np.arange(3)

    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        param_file_no = 0
        archive_path = kdi.utils.create_trajectory_ensemble_path(
            strand_trajectory_id=strand_trajectory_id,
            param_file_no = param_file_no,
            motiflength=motiflength
        )

        motif_trajectory = kdi.get.strand_motifs_trajectory(motiflength, strand_trajectory_id)
        motif_trajectories = [motif_trajectory,]*2
        mte = kdi.MotifTrajectoryEnsemble(motif_trajectories)

        kdi.save_motif_trajectory_ensemble(archive_path, mte)
        actual_mte = kdi.load_motif_trajectory_ensemble(archive_path)
        assert(mte.motiflength==actual_mte.motiflength)
        assert(mte.unit==actual_mte.unit)
        assert(mte.alphabet==actual_mte.alphabet)
        for trajectory_index in range(len(actual_mte.trajectories)):
            actual = kdi._motif_trajectory_as_array(actual_mte.trajectories[trajectory_index])
            assert_equal(actual,
                    kdi._motif_trajectory_as_array(motif_trajectories[trajectory_index])
                    )
