import morsaik as kdi
import numpy as np
from numpy.testing import assert_equal
import pytest

from copy import deepcopy

def _return_motif_production_category_shape_dct(motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int):
    mpcs = {}
    mpd = kdi.domains.make_motif_production_dct(alphabet,
            motiflength,
            maximum_ligation_window_length)
    for key in mpd.keys():
        mpcs[key] = mpd[key].shape
    return mpcs

def test__create_empty_motif_production_dict():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('')
    maximum_ligation_window_length = motiflength

    empv = kdi._create_empty_motif_production_dict(motiflength,
            alphabet,
            maximum_ligation_window_length
            )

    mpcsd = _return_motif_production_category_shape_dct(motiflength,
            alphabet,
            maximum_ligation_window_length
            )

    for key in mpcsd.keys():
        assert_equal(empv[key],np.zeros(mpcsd[key]))

def test_motif_production_vector():
    alphabet = ['a','b','c']
    motiflength = 5
    unit = kdi.make_unit('')
    maximum_ligation_window_length = motiflength

    motif_production_categories = kdi.domains._return_motif_production_categories(motiflength,
            alphabet,
            maximum_ligation_window_length
            )

    empv = kdi._create_empty_motif_production_dict(motiflength,
            alphabet,
            maximum_ligation_window_length
            )

    motif_production_vector = kdi.MotifProductionVector(motiflength,alphabet,unit, maximum_ligation_window_length)
    motif_production_vector = motif_production_vector(empv)

    assert(motif_production_vector.alphabet==alphabet)
    assert(motif_production_vector.number_of_letters==len(alphabet))
    assert(motif_production_vector.motiflength==motiflength)
    assert(motif_production_vector.unit==unit)
    for motif_production_category in motif_production_categories:
        assert_equal(motif_production_vector.productions[motif_production_category].val,
                empv[motif_production_category]
                )

def test_save_and_load_motif_production_vector():
    strand_trajectory_id='9999_99_99__99_99_99'
    param_file_no=0
    simulations_run_no=0
    motiflengths = [2,3,4,5]

    filepaths = kdi.utils._create_ligations_filepath_lists(strand_trajectory_id,param_file_no)[0]

    for motiflength in motiflengths:
        maximum_ligation_window_length = motiflength
        archive_path = kdi.utils.create_motif_production_trajectory_ensemble_path(
            strand_trajectory_id,
            param_file_no,
            motiflength,
            maximum_ligation_window_length
        )
        smpt = kdi.get.strand_motifs_productions_trajectory(
                motiflength,
                strand_trajectory_id,
                param_file_no=0,
                simulations_run_no=0)

        mpvd = kdi._create_empty_motif_production_dict(
            motiflength,
            smpt.alphabet,
            maximum_ligation_window_length
        )
        for key in smpt.productions.keys():
            mpvd[key] = smpt.productions[key].val[0]
        mpv = kdi.MotifProductionVector(motiflength, smpt.alphabet, kdi.make_unit('counts'), maximum_ligation_window_length)
        mpv = mpv(mpvd)
        kdi.save_motif_production_vector(archive_path, mpv)
        for key in mpv._asdict().keys():
            assert_equal(
                    mpv._asdict()[key],
                    kdi.load_motif_production_vector(archive_path)._asdict()[key]
                    )

    smpt = kdi.get.strand_motifs_productions_trajectory(6,'9999_99_99__99_99_99',0,0)
    maximum_ligation_window_length = smpt.motiflength
    actual = {}
    for key in smpt.productions.keys():
        actual[key] = deepcopy(smpt.productions[key].val[11])
    actual['length4strand_6_1_beginning'][0,1,1,0,1,0,1,0,1]=1e12
    mpv = kdi.MotifProductionVector(smpt.motiflength, smpt.alphabet, kdi.make_unit('counts'), maximum_ligation_window_length)
    actual = mpv(actual)
    # reaction:
    #a|tta-tat|at
    # in array:
    #0a|tta0-0tat|at
    #with periodic boundary conditions such that ligation spot is in the center
    # 0;0a|tta-tat|at;0
    # in indices:
    # 0;0,0|1,2,1-2,1,1|0,2;0
    assert_equal(kdi._motif_production_vector_as_array(actual)[0,0,0,1,2,1,2,1,1,0,2,0],
            1e12)
