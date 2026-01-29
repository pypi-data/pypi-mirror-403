import morsaik as kdi
import numpy as np
import pytest

from numpy.testing import assert_equal

def test_motif_production_trajectory_ensemble():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('mol')/kdi.make_unit('L')
    times = kdi.TimesVector(np.arange(3), 'ms')
    maximum_ligation_window_length = motiflength

    motif_categories = kdi.domains._return_motif_categories(motiflength=motiflength)
    motif_production_dct = kdi._create_empty_motif_production_dict(motiflength,
                                                                     alphabet,
                                                                     maximum_ligation_window_length
                                                                     )

    motif_production_vector = kdi.MotifProductionVector(motiflength,
                                                        alphabet,
                                                        unit,
                                                        maximum_ligation_window_length
                                                        )
    motif_production_vector = motif_production_vector(motif_production_dct)
    motif_production_vectors = [motif_production_vector,]*times.shape[0]
    mt = kdi.MotifProductionTrajectory(motif_production_vectors,times)

    mts = [mt,mt]

    mte = kdi.MotifProductionTrajectoryEnsemble(mts)

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
            assert_equal(trajectory.productions.val,
                    mt.productions.val
                    )

    assert(kdi.isinstance_motifproductiontrajectoryensemble(mte))
    print('mte')
    print(mte)
    assert(kdi.are_compatible_motif_production_trajectory_ensembles(mte,mte))

def test_save_and_load_motif_production_trajectory_ensemble():
    motiflengths = [4,]#[2,3,4,5,6,10]

    for motiflength in motiflengths:
        strand_trajectory_id='9999_99_99__99_99_99'
        archive_path = kdi.utils.create_trajectory_ensemble_path(
                strand_trajectory_id=strand_trajectory_id,
                param_file_no = 0,
                motiflength=motiflength
                )

        motif_production_trajectory = kdi.get.strand_motifs_productions_trajectory(motiflength, strand_trajectory_id)
        motif_production_trajectories = [motif_production_trajectory,]*2
        mte = kdi.MotifProductionTrajectoryEnsemble(motif_production_trajectories)

        kdi.save_motif_production_trajectory_ensemble(archive_path, mte)
        actual_mte = kdi.load_motif_production_trajectory_ensemble(archive_path)
        assert(mte.motiflength==actual_mte.motiflength)
        assert(mte.alphabet==actual_mte.alphabet)
        assert(mte.maximum_ligation_window_length==actual_mte.maximum_ligation_window_length)
        assert(mte.number_of_letters==actual_mte.number_of_letters)
        assert(mte.unit==actual_mte.unit)
        for trajectory_index in range(len(actual_mte.trajectories)):
            actual = kdi._motif_production_trajectory_as_array(actual_mte.trajectories[trajectory_index])
            assert_equal(actual,
                    kdi._motif_production_trajectory_as_array(motif_production_trajectories[trajectory_index])
                    )
