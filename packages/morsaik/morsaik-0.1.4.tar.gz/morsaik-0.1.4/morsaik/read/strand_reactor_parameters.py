from ..utils.manage_strand_reactor_files import _return_parameters_to_read_from_parameters_file
from json import loads, JSONDecodeError

def _read_strand_trajectory_ensemble_parameters(
        filepath : str,
        parameters_to_read_from_parameters_file : list
    ) -> dict:
    file1 = open(filepath, 'r')
    lines = file1.readlines()
    tagged_lines = (line for line in lines if any(line.startswith(tag) for tag in parameters_to_read_from_parameters_file))

    kwargs_parameters = {}
    for line in tagged_lines:
        line = line.split("//")[0]
        line = line.split("=")
        try:
            kwargs_parameters[line[0].strip()] = loads(line[1].strip())
        except JSONDecodeError:
            try:
                kwargs_parameters[line[0].strip()] = bool(line[1].strip())
            except TypeError:
                kwargs_parameters[line[0].strip()] = line[1].strip()
    c_ref = kwargs_parameters['c_ref']
    stalling = ['stalling_on', 'use_kinetic_bias_factor']
    if stalling in list(kwargs_parameters.keys()):
        if not np.prod([bool(kwargs_parameters[stall]) for stall in stalling]):
                kwargs_parameters['stalling_factor_first'] = 1.
                kwargs_parameters['stalling_factor_second'] = 1.
    #kwargs_parameters['V'] = self._motifs[0][0,1,0,0]/kwargs_parameters['c_ref']
    return kwargs_parameters

def strand_reactor_parameters(
        filepath : str,
        parameters_to_read_from_parameters_file : list = None,
    ) -> dict:
    """
    reads strand reactor parameters from strand reactor data

    Parameters:
    -----------
    filepath : str
        file path

    Returns:
    --------
    strand_reactor_parameters : dict
        Dictionary with strand reactor parameters
    """
    if parameters_to_read_from_parameters_file is None:
        parameters_to_read_from_parameters_file = _return_parameters_to_read_from_parameters_file()
    return _read_strand_trajectory_ensemble_parameters(filepath,
            parameters_to_read_from_parameters_file)
