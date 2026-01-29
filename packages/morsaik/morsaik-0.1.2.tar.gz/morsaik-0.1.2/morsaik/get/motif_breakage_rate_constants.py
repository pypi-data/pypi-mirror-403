from .strand_reactor_parameters import strand_reactor_parameters as get_strand_reactor_parameters
from .alphabet import alphabet as get_alphabet
from ..infer.motif_breakage_rate_constants_from_strand_reactor_parameters import motif_breakage_rate_constants_from_strand_reactor_parameters as infer_motif_breakage_rate_constants_from_strand_reactor_parameters 
from ..obj.motif_breakage_vector import MotifBreakageVector

def motif_breakage_rate_constants_from_strand_reactor_parameters(
        strand_trajectory_id : str,
        motiflength : int,
        complements : list,
        param_file_no : int = 0,
        standard_concentration : float = 1.
        ) -> MotifBreakageVector:
    return infer_motif_breakage_rate_constants_from_strand_reactor_parameters(
            get_strand_reactor_parameters(strand_trajectory_id, param_file_no),
            motiflength,
            get_alphabet(strand_trajectory_id),
            complements,
            standard_concentration
            )
