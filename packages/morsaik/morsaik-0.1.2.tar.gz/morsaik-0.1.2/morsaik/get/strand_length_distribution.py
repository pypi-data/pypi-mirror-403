from ..read.strand_length_distribution import strand_length_distribution as read_strand_length_distribution
from ..utils.manage_strand_reactor_files import _create_typical_strand_trajectory_section_dirpath
from .alphabet import alphabet as get_alphabet
from os.path import exists

def strand_length_distribution(
        strand_trajectory_id : str,
        param_file_no : int = 0,
        ) -> dict:
    alphabet = get_alphabet(strand_trajectory_id)
    current_filepath = lambda srn, sn : _create_typical_strand_trajectory_section_dirpath(
        strand_trajectory_id,
        param_file_no=param_file_no,
        simulations_run_no=srn,
        simulations_no = sn
        ) + 'length_distribution.txt'
    simulations_run_no = 0
    simulations_no = 0
    filepath_lists = []
    while exists(current_filepath(simulations_run_no,simulations_no)):
        filepaths = []
        while exists(current_filepath(simulations_run_no, simulations_no)):
            filepaths += [current_filepath(simulations_run_no, simulations_no),]
            simulations_no += 1
        filepath_lists = filepath_lists + [filepaths,]
        simulations_run_no += 1
        simulations_no = 0
    return [read_strand_length_distribution(
        filepaths,
        alphabet
    ) for filepaths in filepath_lists]
