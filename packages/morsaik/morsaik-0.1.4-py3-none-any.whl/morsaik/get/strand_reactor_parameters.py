from ..read.strand_reactor_parameters import strand_reactor_parameters as read_strand_reactor_parameters
from ..utils.manage_strand_reactor_files import _create_typical_strand_parameters_filepath

def strand_reactor_parameters(
        strand_trajectory_id : str,
        param_file_no : int = 0
    ) -> dict:
    """
    gets strand reactor parameters for certain strand trajectory id

    Parameters:
    -----------
    strand_trajectory_id : str
        file path
    param_file_no : int

    Returns:
    --------
    strand_reactor_parameters : dict
        Dictionary with strand reactor parameters
    """
    filepath = _create_typical_strand_parameters_filepath(strand_trajectory_id,
            param_file_no=param_file_no)
    return read_strand_reactor_parameters(filepath)
