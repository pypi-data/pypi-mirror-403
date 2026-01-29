import numpy as np

from .effective_ligation_rates_from_parameters import separate_hybridization_and_ligation_parameters

from ..obj.motif_vector import MotifVector

def onset_of_growth(
        total_mass,
        initial_dimer_concentration,
        extension_rate_constant_1_1_2,
        extension_rate_constant_1_2_2,
        cleavage_rate_constant,
    ) -> float:
    return (np.log(total_mass**2*extension_rate_constant_1_1_2-cleavage_rate_constant)-np.log(total_mass*extension_rate_constant_1_2_2*initial_dimer_concentration))/(total_mass**2*extension_rate_constant_1_1_2-cleavage_rate_constant)

def discretized_onset_of_growth(
        total_mass,
        initial_dimer_concentration,
        extension_rate_constant_1_1_2,
        cleavage_rate_constant,
        concentration_of_a_single_particle,
    ) -> float:
    return 1./(total_mass**2*extension_rate_constant_1_1_2-cleavage_rate_constant)*np.log(1.+concentration_of_a_single_particle/initial_dimer_concentration)

def onset_of_growth_from_strand_trajectory_parameters(
        initial_motif_numbers_vector : MotifVector,
        strand_reactor_parameters : dict
    ) -> float:
    ligation_rate_constant = np.exp(strand_reactor_parameters['dG_4_2Match_mean']*strand_reactor_parameters['l_critical'])
    gamma2nc = strand_reactor_parameters['dG_4_0Match']
    gamma1nc = strand_reactor_parameters['dG_4_1Match']
    gammacom = strand_reactor_parameters['dG_4_2Match_mean']
    inverse_dissociation_constant = 1./4.*(
        np.exp(-gamma2nc)
        +2*np.exp(-gamma1nc)
        +np.exp(-gammacom)
    )
    k112 = ligation_rate_constant*inverse_dissociation_constant

    epsilon1nc = strand_reactor_parameters['dG_3_0Match']
    epsiloncom = strand_reactor_parameters['dG_3_1Match_mean']
    inverse_dissociation_constant = 1./4.*(
        np.exp(gamma2nc+epsilon1nc)
        +np.exp(gamma1nc+epsilon1nc)
        +np.exp(gamma1nc+epsiloncom)
        +np.exp(gammacom+epsiloncom)
        )
    k122 = ligation_rate_constant*inverse_dissociation_constant

    concentration_of_a_single_particle = strand_reactor_parameters['c_ref']/initial_motif_numbers_vector.motifs.val['length1strand'][0]
    total_mass = np.sum(initial_motif_numbers_vector.motifs.val['length1strand'])*concentration_of_a_single_particle
    initial_dimer_concentration = np.sum(initial_motif_numbers_vector.motifs.val['length2strand'])*concentration_of_a_single_particle
    return onset_of_growth(
        total_mass,
        initial_dimer_concentration,
        k112,
        k122,
        strand_reactor_parameters['r_delig']
    )
