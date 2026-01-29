from .dissociation_constant import template_averaged_dissociation_constant_from_strand_reactor_parameters

from ..obj.motif_breakage_vector import MotifBreakageVector, _array_to_motif_breakage_vector
from ..obj.units import make_unit

def motif_breakage_rate_constants_from_strand_reactor_parameters(
        strand_reactor_parameters : dict,
        motiflength : int,
        alphabet : list,
        complements : list,
        standard_concentration : float = 1.
    ) -> MotifBreakageVector:
    """
    calculates (estimates for) motif_breakage_rate_constants
    from strand reactor parameters 
    """
    if motiflength != 4:
        raise NotImplementedError("function only implemented for fourmers (i.e. motiflength=4, given motiflength: {})".format(motiflength))
    breakage_rates_unit = make_unit('')

    cleavage_rate_constant = strand_reactor_parameters['r_delig']

    ligation_parameters = {}
    ligation_keys = [
        'stalling_factor_first',
        'stalling_factor_second'
    ]
    for ligation_key in ligation_keys:
        ligation_parameters[ligation_key] = strand_reactor_parameters[ligation_key]

    hybridization_parameters = {}
    hybridization_keys = [
        'dG_4_2Match_mean',
        'dG_4_1Match',
        'dG_4_0Match',
        'dG_3_1Match_mean',
        'dG_3_0Match',
        'ddG_4_2Match_alternating',
        'ddG_3_1Match_alternating'
    ]
    for hybridization_key in hybridization_keys:
        hybridization_parameters[hybridization_key] = strand_reactor_parameters[hybridization_key]

    breakage_rates = _calculate_effective_cleavage_rate_constant_for_central_breaking_tetramer(
        cleavage_rate_constant,
        standard_concentration,
        complements,
        ligation_parameters,
        hybridization_parameters
    )
    breakage_rates = _array_to_motif_breakage_vector(breakage_rates, motiflength, alphabet, breakage_rates_unit)

    breakage_rates = MotifBreakageVector(motiflength, alphabet, unit=make_unit(''))(breakage_rates)
    return breakage_rates

def _calculate_effective_cleavage_rate_constant_for_central_breaking_tetramer(
        cleavage_rate_constant,
        standard_concentration,
        complements = [1,0,3,2],
        ligation_parameters = {'stalling_factor_first' : 1.,
            'stalling_factor_second' : 1.,
            },
        hybridization_parameters = {'dG_4_2Match_mean':0.,
                    'dG_4_1Match':0.,
                    'dG_4_0Match':0.,
                    'dG_3_1Match_mean':0.,
                    'dG_3_0Match':0.,
                    'ddG_4_2Match_alternating':0.,
                    'ddG_3_1Match_alternating':0.
                    }
        ):
    template_averaged_dissociation_constant = template_averaged_dissociation_constant_from_strand_reactor_parameters(
            None,
            ligation_parameters,
            complements,
            hybridization_parameters,
            standard_concentration,
            )
    return cleavage_rate_constant * template_averaged_dissociation_constant
