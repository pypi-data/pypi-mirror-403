import numpy as np
import warnings
import itertools

from .dissociation_constant import ligation_rate_constant_from_strand_reactor_parameters as infer_ligation_rate_constant_from_strand_reactor_parameters
from .dissociation_constant import dissociation_constant_from_strand_reactor_parameters as infer_dissociation_constant_from_strand_reactor_parameters

# Goeppel2022Thermodynamic Eqn A6, A30, A29
'''
according to Eqn A26
K_D = e^{\beta \Delta \mathcal G_\text{tot}(C)

β∆G_tot(C)= ∑_\text{continuous blocks} γ_i +
+ ∑_\text{dangling ends} ǫ_d +
+ ∑_\text{ligation sites} γ_l

(c^0)^2/K_{\{1,1|2\}} = \sum_{C \in \mathcal{C}_{\{1,1|2\}}} e^{-\beta
\Delta \mathcal{G}_\text{tot}(C)/|\mathcal{C}_{\{1,1|2\}}|
\lambda_{lrp} = k_\text{lig}/K_D
'''

'''
Do:5-Do:24; 8-20
Fr:9-Sa:4; Fr:10-Fr:22
Sa:13-So:8; -
So:17-Mo:12; So:22-Mo:10
Mo:21-Di:16, Di:2- Di:14
Mi:01-Mi:20, Mi:6:00 -Mi:18:00
'''

def effective_ligation_rates_from_parameters(trj_parameters : dict,
                                             complements : list = [1,0,3,2],
                                             motiflength : int = 4,
                                             standard_concentration :float = 1.
                                             ) -> np.ndarray:
    # TODO:make_differentiable
    if motiflength != 4:
        # TODO:implement_for_general_motiflength
        raise NotImplementedError("function only implemented for fourmers, yet")
    warnings.warn("This function has not been properly tested yet") # FIXME:test_function
    characteristic_ligation_length = trj_parameters['l_critical']
    hybridization_parameters, ligation_parameters = separate_hybridization_and_ligation_parameters(trj_parameters)
    return calculate_effective_ligation_rate_for_tetramer_creation(
        standard_concentration,
        characteristic_ligation_length,
        complements = complements,
        ligation_parameters = ligation_parameters,
        hybridization_parameters = hybridization_parameters
        )

def calculate_effective_ligation_rate_for_tetramer_creation(
        standard_concentration,
        characteristic_ligation_length,
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
    ligation_rate_constant = infer_ligation_rate_constant_from_strand_reactor_parameters(
        hybridization_parameters,
        ligation_parameters,
        complements,
        characteristic_ligation_length
    )
    # Eqn. A29
    dissociation_constant = infer_dissociation_constant_from_strand_reactor_parameters(
        characteristic_ligation_length,
        ligation_parameters,
        complements,
        hybridization_parameters
    )
    # Eqn. A30
    effective_ligation_rate_constant = ligation_rate_constant / dissociation_constant
    return effective_ligation_rate_constant

def separate_hybridization_and_ligation_parameters(
        traj_parameters : dict
    ) -> (dict,dict):
    ligation_parameters = {'stalling_factor_first' : 1.,
            'stalling_factor_second' : 1.
            }
    hybridization_parameters = {'dG_4_2Match_mean':0.,
            'dG_4_1Match':0.,
            'dG_4_0Match':0.,
            'dG_3_1Match_mean':0.,
            'dG_3_0Match':0.,
            'ddG_4_2Match_alternating':0.,
            'ddG_3_1Match_alternating':0.
            }
    for kk in ligation_parameters.keys():
        ligation_parameters[kk] = traj_parameters[kk]
    for kk in hybridization_parameters.keys():
        hybridization_parameters[kk] = traj_parameters[kk]
    return hybridization_parameters, ligation_parameters
