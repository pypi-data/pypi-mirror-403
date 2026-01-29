from os.path import exists

from .alphabet import alphabet as get_alphabet
from ..obj.motif_trajectory_ensemble import load_motif_trajectory_ensemble, MotifTrajectoryEnsemble
from ..read.strand_motifs_trajectory_ensemble import strand_motifs_trajectory_ensemble as read_strand_motifs_trajectory_ensemble
from ..utils.manage_strand_reactor_files import _create_typical_strand_trajectory_section_complexes_filepath 
from ..utils.save import create_trajectory_ensemble_path

def strand_motifs_trajectory_ensemble(
        motiflength : int,
        strand_trajectory_id : str,
        param_file_no : int = 0,
        skiprows : int = 2,
        execution_time_path : str = None,
        **kwargs
    ) -> MotifTrajectoryEnsemble:
    alphabet = get_alphabet(strand_trajectory_id)

    #check if already in archive
    archive_path = create_trajectory_ensemble_path(
        strand_trajectory_id=strand_trajectory_id,
        param_file_no=param_file_no,
        motiflength=motiflength
    ) + 'sd/'
    if exists(archive_path):
        return load_motif_trajectory_ensemble(archive_path)
    print('Reading MotifsTrajectoryEnsemble from strand reactor data...')
    current_filepath = lambda srn, sn : _create_typical_strand_trajectory_section_complexes_filepath(
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
        if execution_time_path is not None:
            with open(execution_time_path + 'execution_time.txt','a') as f:
                f.write(f'\nsimulations_run_no {simulations_run_no}: '+str(simulations_no))
        filepath_lists = filepath_lists + [filepaths,]
        simulations_run_no += 1
        simulations_no = 0
    return read_strand_motifs_trajectory_ensemble(filepath_lists,
            alphabet,
            motiflength,
            skiprows =skiprows)
