from .effective_ligation_rates_from_parameters import effective_ligation_rates_from_parameters
from ..obj.motif_production_vector import (MotifProductionVector, _array_to_motif_production_vector)

from ..obj.units import make_unit

def motif_production_rate_constants_from_strand_reactor_parameters(
        strand_reactor_parameters : dict,
        motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int,
        complements : list,
    ) -> MotifProductionVector:
    """
    calculates (estimates for) motif_production_rate_constants
    from strand reactor parameters 
    """
    if motiflength != 4:
        raise NotImplementedError("function only implemented for fourmers (i.e. motiflength=4, given motiflength: {})".format(motiflength))
    if maximum_ligation_window_length != 4:
        raise NotImplementedError("function only implemented for maximum_ligation_window_length 4 (given maximum_ligation_window_length: {})".format(maximum_ligation_window_length))
    unit = make_unit('mol')**2/make_unit('L')**2
    motif_production_rate_constants = effective_ligation_rates_from_parameters(
        strand_reactor_parameters,
        complements = complements,
        motiflength = motiflength
    )
    return _array_to_motif_production_vector(motif_production_rate_constants, motiflength, alphabet, unit, maximum_ligation_window_length)
