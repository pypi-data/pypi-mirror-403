import jax.numpy as jnp
import os

def save(filename : str,
        arr : jnp.ndarray,
        allow_pickle : bool
        ):
    jnp.save(filename, arr)

def create_directory_if_not_already_existing(path):
    try:
        os.makedirs(path,mode=0o777)
        print("created directory {}".format(path))
    except(FileExistsError):
        pass

def create_directory_path_if_not_already_existing(path : str
        ) -> None:
    directories = path.split('/')
    current_path = ""
    for directory in directories:
        current_path += directory + '/'
        if directory in ('','.'):
            continue
        create_directory_if_not_already_existing(current_path)

def create_strand_trajectory_ensemble_path(
        strand_trajectory_id : str,
        param_file_no : int,
        ) -> str:
    return f'./archive/{strand_trajectory_id}/data_param_file_{param_file_no}/'

def create_trajectory_ensemble_path(
        strand_trajectory_id : str,
        param_file_no : int,
        motiflength : int,
        ) -> str:
    return create_strand_trajectory_ensemble_path(strand_trajectory_id,param_file_no)+f'{motiflength}-mer_dynamics/'


def create_motif_production_trajectory_ensemble_path(
        strand_trajectory_id : str,
        param_file_no : int,
        motiflength : int,
        maximum_ligation_window_length
        ) -> str:
    return create_trajectory_ensemble_path(strand_trajectory_id, param_file_no, motiflength) + '{}-mer_prductions/'.format(maximum_ligation_window_length)
