from os.path import exists

from ..read.strand_motifs_productions_trajectory import strand_motifs_productions_trajectory as read_strand_motifs_productions_trajectory
from .alphabet import alphabet as get_alphabet
from ..utils.manage_strand_reactor_files import _create_typical_strand_trajectory_section_ligations_filepath 

def strand_motifs_productions_trajectory(
        motiflength : int,
        strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0,
        skiprows : int = 2,
        maximum_ligation_window_length : int = None
        ):
    if maximum_ligation_window_length is None:
        maximum_ligation_window_length = motiflength

    alphabet = get_alphabet(strand_trajectory_id)

    current_filepath = lambda sn : _create_typical_strand_trajectory_section_ligations_filepath(
            strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=simulations_run_no,
            simulations_no = sn,
            )

    simulations_no = 0
    filepaths = []
    while exists(current_filepath(simulations_no)):
        filepaths += [current_filepath(simulations_no),]
        simulations_no += 1

    return read_strand_motifs_productions_trajectory(filepaths, alphabet, motiflength,
            maximum_ligation_window_length)
