from typing import Union
import numpy as np
import warnings
import itertools

def hybridization_bond_category(
        upper_nucleotide : int,
        hybridized_nucleotide : int,
        complements : list
    ) -> (int, bool):
    number_of_mismatches = 0
    hybridization_is_dangling_end = False
    complements_0 = [0,] + [complement+1 for complement in complements]
    if upper_nucleotide * hybridized_nucleotide == 0: # if any empty letter:
        if upper_nucleotide + hybridized_nucleotide == 0: # if all empty letters:
            raise ValueError("Empty Block")
        else:
            hybridization_is_dangling_end = True
    elif upper_nucleotide != complements_0[hybridized_nucleotide]:
        number_of_mismatches += 1
    return number_of_mismatches, hybridization_is_dangling_end

def segment_category(upper_nucleotide1 : int,
                     hybridized_nucleotide1 : int,
                     upper_nucleotide2 : int,
                     hybridized_nucleotide2 : int,
                     complements : list
                     ) -> (int, bool, int, bool):
    left_mismatch, dangling_end1 = hybridization_bond_category(upper_nucleotide1, hybridized_nucleotide1, complements)
    right_mismatch, dangling_end2 = hybridization_bond_category(upper_nucleotide2, hybridized_nucleotide2, complements)
    return left_mismatch, right_mismatch, dangling_end1, dangling_end2

def analyze_segment(ii,jj,kk,ll,complements):
    number_of_mismatches, number_of_mismatches2, dangling_end1, dangling_end2 = segment_category(ii,jj,kk,ll, complements)
    number_of_mismatches += number_of_mismatches2
    return number_of_mismatches, dangling_end1, dangling_end2

def dissociation_constant_from_strand_reactor_parameters(
        #strand_reactor_parameters : dict,
        characteristic_ligation_length : int,
        ligation_parameters : dict,
        complements : list,
        hybridization_parameters : dict,
        standard_concentration : float = 1.,
        temperature = 1.#k_B K,
    ) -> np.ndarray:
    number_of_letters = len(complements)
    motif_shape = (number_of_letters+1,number_of_letters)
    motif_shape += motif_shape[::-1]
    total_free_energy = _total_free_energy(motif_shape, complements, hybridization_parameters, temperature, number_of_letters)
    # Nochmal checken mit der Standard-Konzentration
    return standard_concentration**2*np.exp(total_free_energy/temperature)

def ligation_rate_constant_from_strand_reactor_parameters(
        hybridization_parameters : dict,
        ligation_parameters : dict,
        complements : list,
        characteristic_ligation_length : int
    ):
    number_of_letters = len(complements)
    motif_shape = give_shape(number_of_letters)
    average_energy_value_of_complementary_blocks = hybridization_parameters['dG_4_2Match_mean']
    stalling_factor = _calculate_stalling(motif_shape, number_of_letters, ligation_parameters, complements)
    return np.exp(average_energy_value_of_complementary_blocks * characteristic_ligation_length) * stalling_factor 

def template_averaged_dissociation_constant_from_strand_reactor_parameters(
        characteristic_ligation_length,
        ligation_parameters,
        complements,
        hybridization_parameters,
        standard_concentration,
        temperature = 1.#k_B K,
    ):
    discon = dissociation_constant_from_strand_reactor_parameters(
        characteristic_ligation_length,
        ligation_parameters,
        complements,
        hybridization_parameters,
        standard_concentration,
        temperature
    )
    return 1./np.sum(1./discon, axis=(-4,-3,-2,-1))


def energy_continuous_block(ii,jj,kk,ll, complements, parameters):
    # check that block is actually a block and not a blunt end
    if ii+jj==0 or kk+ll==0:
        return 0.
    number_of_mismatches, dangling_end, dangling_end2 = analyze_segment(ii,jj,kk,ll, complements)
    # check that block is actually continuous, not dangling on both sides
    if bool(dangling_end*dangling_end2):
        gamma_current = 0.
    else:
        # check if any dangling end
        dangling_end = bool(dangling_end + dangling_end2)
        if number_of_mismatches == 0:
            alternating = bool(ii*kk*(ii!=kk)+jj*ll*(jj!=ll))
            if dangling_end:
                gamma_current = parameters['dG_3_1Match_mean']+0.5*(-1)**(1+alternating)*parameters['ddG_3_1Match_alternating']
            else:
                gamma_current = parameters['dG_4_2Match_mean']+0.5*(-1)**(1+alternating)*parameters['ddG_4_2Match_alternating']
        if number_of_mismatches == 1:
            if dangling_end:
                gamma_current = parameters['dG_3_0Match']
            else:
                gamma_current = parameters['dG_4_1Match']
        if number_of_mismatches == 2:
            gamma_current = parameters['dG_4_0Match']
    return gamma_current

def _energy_continuous_blocks(motif_shape, complements, hybridization_parameters):
    """
    ii,kk
    jj-ll
    alternating:
    X,Y Y,X
    Y-X,X-Y
    homogeneous
    X,X Y,Y
    Y-Y,X-X
    gamma_alternating <= gamma_homogeneous < gamma_one_mismatch < gamma_two_mismatches
    """
    rtrn = np.zeros(motif_shape*2)
    number_of_letters = len(complements)
    for ii,jj,kk,ll in itertools.product(range(number_of_letters+1),repeat=4):
        gamma_current = energy_continuous_block(ii,jj,kk,ll, complements, hybridization_parameters)
        #building blocks:
        #r2,r3,t4,t3
        if kk!=0 and ll !=0:
            rtrn[ii,kk-1,:,:,:,:,ll-1,jj] += gamma_current
        #r3,l2,t3,t2
        if ii*jj*kk*ll!=0:
            rtrn[:,ii-1,kk-1,:,:,ll-1,jj-1,:] += gamma_current
        #l2,l3,t2,t1
        if ii*jj!=0:
            rtrn[:,:,ii-1,kk,ll,jj-1,:,:] += gamma_current
    def make_invalid_terms_zero(rates, status_shall_be_printed=True):
        if rates.shape[1]==rates.shape[0]-1:
            rates[:,0] = 0.
            if status_shall_be_printed:
                print('Put 2nd letter to zero')
        if rates.shape[2]==rates.shape[3]-1:
            rates[:,:,0,1:]=0.
            if status_shall_be_printed:
                print('Put 3rd letter to zero, if 4th is empty')
        if rates.shape[2]==rates.shape[0]-1:
            rates[1:,:,0]=0.
            if status_shall_be_printed:
                print('Put 3rd letter to zero, if 1st is empty')
        if rates.shape[5]==rates.shape[0]-1:
            rates[:,:,:,:,:,0] = 0.
            if status_shall_be_printed:
                print('Put 6th letter to zero')
        if rates.shape[6]==rates.shape[7]-1:
            rates[:,:,:,:,:,:,0,1:] = 0.
            if status_shall_be_printed:
                print('Put 6th letter to zero, if 7th is empty')
        if rates.shape[6]==rates.shape[4]-1:
            rates[:,:,:,:,1:,:,0] = 0.
            if status_shall_be_printed:
                print('Put 7th letter to zero, if 5th is empty')
        return rates
    return rtrn

def _ligation_sites_term():
    warnings.warn('calculate_ligation_sites_term not yet implemented.')
    return 0.

def _total_hybridization_energy(motif_shape, complements, hybridization_parameters):
    the = _energy_continuous_blocks(motif_shape, complements, hybridization_parameters)
    the += _ligation_sites_term()
    return the

def _check_rotational_symmetry(number_of_letters, motif_shape):
    '''
    r2,r3,l2,l3,t1,t2,t3,t4
    r2-r3|l2-l3
    t4-t3-t2-t1
    rotational sym: (r2,r3,l2,l3)=(t1,t2,t3,t4)
    '''
    shape = motif_shape*2
    rho = np.zeros(shape)
    for r2 in range(number_of_letters+1):
        for r3 in range(number_of_letters):
            for l2 in range(number_of_letters):
                for l3 in range(number_of_letters+1):
                    rho[r2,r3,l2,l3,r2,r3,l2,l3] = 1.
    return 0.

def _calculate_entropic_term(number_of_letters, motif_shape):
    '''
    \rho \ln(2)
    \rho = 1 if strand is rotationally symmetric,
    0 else
    '''
    return _check_rotational_symmetry(number_of_letters, motif_shape) * np.log(2.)

def _total_free_energy(motif_shape,complements, hybridization_parameters, temperature, number_of_letters):
    return _total_hybridization_energy(motif_shape, complements, hybridization_parameters) + temperature*_calculate_entropic_term(number_of_letters,motif_shape)

def _calculate_stalling_factor(ii,jj,kk,ll, segment_is_to_the_left, ligation_parameters, complements):
    """
    ii,kk
    jj-ll
    alternating:
    X,Y Y,X
    Y-X,X-Y
    homogeneous
    X,X Y,Y
    Y-Y,X-X
    gamma_alternating <= gamma_homogeneous < gamma_one_mismatch < gamma_two_mismatches
    """
    sigma1 = ligation_parameters['stalling_factor_first']
    sigma2 = ligation_parameters['stalling_factor_second']
    left_mismatch = False if not ii*jj else hybridization_bond_category(ii,jj, complements)[0]
    right_mismatch = False if not kk*ll else hybridization_bond_category(kk,ll, complements)[0]
    rtrn = 1.
    if segment_is_to_the_left:
        if right_mismatch:
            rtrn *= sigma1
            if left_mismatch:
                rtrn *= sigma2
    else:
        if left_mismatch:
            rtrn *= sigma1
            if right_mismatch:
                rtrn *= sigma2
    return rtrn

def _calculate_stalling(motif_shape, number_of_letters, ligation_parameters, complements):
    stalling = np.ones(motif_shape*2)
    for ii in range(0,number_of_letters+1):
        for jj in range(0, number_of_letters+1):
            for kk in range(0, number_of_letters+1):
                for ll in range(0, number_of_letters+1):
                    segment_is_to_the_left=True
                    stalling_factor = _calculate_stalling_factor(ii,jj,kk,ll,segment_is_to_the_left, ligation_parameters, complements)
                    if kk!=0 and ll !=0:
                        stalling[ii,kk-1,:,:,:,:,ll-1,jj] *= stalling_factor
                    segment_is_to_the_left=False
                    stalling_factor = _calculate_stalling_factor(ii,jj,kk,ll,segment_is_to_the_left, ligation_parameters, complements)
                    if ii*jj!=0:
                        stalling[:,:,ii-1,kk,ll,jj-1,:,:] *= stalling_factor
    # TODO: Check, das invalid terms zero
    return stalling

def give_shape(number_of_letters):
    shape = (number_of_letters+1,number_of_letters)
    shape += shape[::-1]
    return shape
