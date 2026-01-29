from os.path import exists

from .alphabet import alphabet as get_alphabet
from ..read.strand_motifs_trajectory import strand_motifs_trajectory as read_strand_motifs_trajectory
from ..utils.manage_strand_reactor_files import _create_typical_strand_trajectory_section_complexes_filepath 

def strand_motifs_trajectory(
        motiflength : int,
        strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0,
        skiprows : int = 2,
        execution_time_path : str = None
        ):
    alphabet = get_alphabet(strand_trajectory_id)

    current_filepath = lambda sn : _create_typical_strand_trajectory_section_complexes_filepath(
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
    if execution_time_path is not None:
        with open(execution_time_path,'a') as f:
            f.write('\n'+str(simulations_no))
    return read_strand_motifs_trajectory(filepaths,
            alphabet,
            motiflength,
            skiprows =skiprows)
