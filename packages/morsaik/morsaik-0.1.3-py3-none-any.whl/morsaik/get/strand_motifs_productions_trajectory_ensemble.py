from os.path import exists

from .alphabet import alphabet as get_alphabet
from ..read.strand_motifs_productions_trajectory_ensemble import strand_motifs_productions_trajectory_ensemble as read_strand_motifs_productions_trajectory_ensemble
from ..utils.manage_strand_reactor_files import _create_typical_strand_trajectory_section_ligations_filepath 

def strand_motifs_productions_trajectory_ensemble(
        motiflength : int,
        strand_trajectory_id : str,
        param_file_no : int = 0,
        skiprows : int = 2,
        maximum_ligation_window_length : int = None,
        ):
    if maximum_ligation_window_length is None:
        maximum_ligation_window_length = motiflength

    alphabet = get_alphabet(strand_trajectory_id)

    current_filepath = lambda srn, sn : _create_typical_strand_trajectory_section_ligations_filepath(
            strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=srn,
            simulations_no = sn,
            )

    simulations_run_no = 0
    simulations_no = 0
    filepath_lists = []
    while exists(current_filepath(simulations_run_no, simulations_no)):
        filepaths = []
        while exists(current_filepath(simulations_run_no, simulations_no)):
            filepaths += [current_filepath(simulations_run_no, simulations_no),]
            simulations_no += 1
        filepath_lists = filepath_lists + [filepaths,]
        simulations_run_no += 1
    return read_strand_motifs_productions_trajectory_ensemble(filepath_lists,
            alphabet,
            motiflength,
            maximum_ligation_window_length,
            skiprows =skiprows)
