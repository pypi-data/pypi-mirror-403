from os.path import exists

def transform_execution_time_txt_to_list(
        path : str = "archive/9999_99_99__99_99_99/data_param_file_0/4-mer_dynamics/execution_time.txt"
        ) -> list:
    with open(path,'r') as f:
        a=f.readlines()
    return [int(aa.replace('\n','').split(':')[-1]) for aa in a[1:]]

def _return_parameters_to_read_from_parameters_file() -> list:
    return ['c_ref',
            'l_critical',
            'r_delig',
            'dG_4_2Match_mean',
            'dG_4_1Match',
            'dG_4_0Match',
            'dG_3_1Match_mean',
            'dG_3_0Match',
            'ddG_4_2Match_alternating',
            'ddG_3_1Match_alternating',
            'stalling_on',
            'use_kinetic_bias_factor',
            'stalling_factor_first',
            'stalling_factor_second' 
            ]

def _create_typical_strand_reactor_dirpath(strand_trajectory_id : str) -> str:
    dirpath = './data/'
    dirpath += strand_trajectory_id + '/'
    return dirpath

def _create_typical_strand_trajectory_ensemble_dirpath(strand_trajectory_id : str,
        param_file_no : int = 0) -> str:
    dirpath = _create_typical_strand_reactor_dirpath(strand_trajectory_id)
    dirpath += 'data_exp/data_param_file_{}/'.format(param_file_no)
    return dirpath

def _create_typical_strand_trajectory_dirpath(strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0) -> str:
    dirpath = _create_typical_strand_trajectory_ensemble_dirpath(
            strand_trajectory_id,
            param_file_no)
    dirpath += 'data_simulations_run_{}/'.format(simulations_run_no)
    return dirpath

def _create_typical_strand_trajectory_section_dirpath(strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0,
        simulations_no : int = 0
        ) -> str:
    dirpath = _create_typical_strand_trajectory_dirpath(strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=simulations_run_no)
    dirpath += 'data_simulations_{}/'.format(simulations_no)
    return dirpath

def _create_typical_strand_trajectory_section_complexes_filepath(strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0,
        simulations_no : int = 0,
        filename : str = 'complexes.txt'
        ) -> str:
    dirpath = _create_typical_strand_trajectory_section_dirpath(strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=simulations_run_no,
            simulations_no = simulations_no
            )
    return dirpath+filename

def _create_complexes_filepath_lists(strand_trajectory_id : str,
        param_file_no :int,
        ):
    current_filepath = lambda srn, sn : _create_typical_strand_trajectory_section_complexes_filepath(
            strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=srn,
            simulations_no = sn,
            )
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
    return filepath_lists

def _create_ligations_filepath_lists(strand_trajectory_id : str,
        param_file_no :int,
        ):
    current_filepath = lambda srn, sn : _create_typical_strand_trajectory_section_ligations_filepath(
            strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=srn,
            simulations_no = sn,
            )
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
    return filepath_lists

def _create_typical_strand_trajectory_section_ligations_filepath(strand_trajectory_id : str,
        param_file_no : int = 0,
        simulations_run_no : int = 0,
        simulations_no : int = 0,
        filename : str = 'ligation_statistics.txt'
        ) -> str:
    dirpath = _create_typical_strand_trajectory_section_dirpath(strand_trajectory_id,
            param_file_no=param_file_no,
            simulations_run_no=simulations_run_no,
            simulations_no = simulations_no
            )
    return dirpath+filename

def _create_typical_strand_parameters_filepath(
        strand_trajectory_id : str,
        param_file_no : int = 0
    ) -> str:
    filepath = _create_typical_strand_reactor_dirpath(strand_trajectory_id)
    filepath += 'all_parameter_files/parameters_{}.txt'.format(param_file_no)
    return filepath

def _create_typical_alphabet_filepath(strand_trajectory_id : str) -> str:
    filepath = _create_typical_strand_reactor_dirpath(strand_trajectory_id)
    filepath += 'bin/initial_configurations/nucleotides.txt'
    return filepath

def read_txt(title_path, replace=[["\n", ""],["\r", ""]]):  
    """
    reads a file and returns its content as string
    """
    with open(title_path, "r", encoding ="utf8") as current_file:
        text = current_file.read()
        for rpl in replace:
            text = text.replace(rpl[0],rpl[1])
    return text
