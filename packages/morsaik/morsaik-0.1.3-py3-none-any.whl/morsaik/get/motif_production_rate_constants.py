from ..read.strand_reactor_parameters import strand_reactor_parameters as read_strand_reactor_parameters
from ..utils.manage_strand_reactor_files import _create_typical_strand_parameters_filepath
from ..infer.motif_production_rate_constants_from_strand_reactor_parameters import motif_production_rate_constants_from_strand_reactor_parameters as infer_motif_production_rate_constants_from_strand_reactor_parameters
from .alphabet import alphabet as get_alphabet

from ..obj.motif_production_vector import MotifProductionVector


def motif_production_rate_constants_from_strand_reactor_parameters(
        strand_trajectory_id,
        motiflength : int,
        complements : list,
        param_file_no : int = 0,
        maximum_ligation_window_length : int = None
    ) -> MotifProductionVector:
    if motiflength != 4:
        raise NotImplementedError("")
    if maximum_ligation_window_length is None:
        maximum_ligation_window_length = motiflength
    filepath = _create_typical_strand_parameters_filepath(strand_trajectory_id, param_file_no = param_file_no)
    strand_reactor_parameters = read_strand_reactor_parameters(filepath)
    alphabet = get_alphabet(strand_trajectory_id)
    return infer_motif_production_rate_constants_from_strand_reactor_parameters(
        strand_reactor_parameters,
        motiflength,
        alphabet,
        maximum_ligation_window_length,
        complements
    )
