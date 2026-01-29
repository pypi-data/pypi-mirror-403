import jax
import jax.numpy as jnp
from typing import Callable

import nifty8.re as jft

from .collisions import collisions_from_motif_concentration_trajectory_array_and_collision_rate_constants_array

def motif_production_rates_array_from_motif_production_rate_constants_array_and_motif_concentrations_array(
        motif_production_rate_constants : jax.Array,
        motif_logconcentrations_trajectory : jax.Array,
        motif_concentration_trajectory_times_array : jax.Array = None,
        ):
    """
    calculates motif production rates from
    motif production rate constants and motif concentrations
    Parameters:
    -----------
    motif_production_rate_constants : jax.Array
    motif_concentration_trajectories : jax.Array

    Returns:
    --------
    motif_production_rates : jax.Array
    """
    motiflength = len(motif_logconcentrations_trajectory[0].shape)
    nol = motif_logconcentrations_trajectory[0].shape[0]-1
    mpr_shape = (nol+1,nol,nol,nol+1,nol+1,nol,nol,nol+1)
    if motiflength == 4:
        # \lambda_{ijk} c_i c_j c_k
        # integrate collision over time
        exposure = collisions_from_motif_concentration_trajectory_array_and_collision_rate_constants_array(
                motif_logconcentrations_trajectory,
                motif_concentration_trajectory_times_array=motif_concentration_trajectory_times_array,
                concentrations_are_logarithmised = True
                )
        motif_production_rates = motif_production_rate_constants.flatten()*exposure
        return motif_production_rates.reshape(mpr_shape)
    else:
        raise NotImplementedError("only implemented for motiflength 4")

def motif_production_rates_array_from_motif_production_counts(
        motif_production_rates_model : jft.Model,
        motif_production_rates_estimate : jft.Vector,
        motif_production_counts : list[jax.Array],
        sample_key : jax.Array,
        minimization_function : Callable
        ):
    """
    Parameters :
    ------------
    motif_production_rate : jax.Array
    motif_production_counts : list[jax.Array]
    sample_key : jax.Array
    minimization_function : Callable
        minimizes nifty8.re.likelihood_impl.Poissonian

    Returns:
    --------
    motif_production_rates_samples : list[jax.Array]
    """
    likelihood = jft.Poissonian(motif_production_counts[0]).amend(motif_production_rates_model)
    for ii in range(1,len(motif_production_counts)):
        likelihood = likelihood + jft.Poissonian(motif_production_counts[ii]).amend(motif_production_rates_model)
    return minimization_function(likelihood, motif_production_rates_estimate)
        

def left_reactant_logconcentration(
        motif_logconcentrations_array : jax.Array,
        motiflength : int,
        number_of_letters : int
    ):
    '''
    if not del_t c_l
    for motiflength = 4:
    collision_exponent[l1,l2,l3,r2,r3,r4][p1,p2,p3,p4] += c[l1,l2,l3,0]
    For jit, motiflength and number_of_letters are stated explicitly,
    the motif_logconcentrations_array must fulfill
    motiflength = len(motif_logconcentrations_array.shape)
    nol = motif_logconcentrations_array.shape[1]

    Parameters:
    -----------
    motif_logconcentrations_array : jax.Array
    motiflength : int
    number_of_letters : int


    Returns:
    --------
    collision_exponent : jax.Array
    '''
    nol = number_of_letters #motif_logconcentrations_array.shape[1]
    collision_exponent = jnp.zeros((nol+1,)*(motiflength-2)+(nol,nol)+(nol+1,)*(motiflength-2)+(nol+1,)*int(motiflength>2)+(nol,nol)+(nol+1,)*(motiflength-3))
    for strandlength in range(1,motiflength):
        shape = (0,)*(motiflength-1-strandlength)+(slice(1,None),)*(strandlength-1)+(slice(None),)
        shape2 = (nol+1,)*(motiflength>1)+(nol,)+(nol+1,)*(motiflength-2)+(1,)*(motiflength-2)#(3*motiflength-strandlength-2)
        shape3 = (slice(1,None),)*int(strandlength>1) + (slice(None),) + (slice(1,None),)*(strandlength-2)+(0,)*(motiflength-strandlength)
        mla = motif_logconcentrations_array.reshape(shape2)
        return mla.at[shape3], shape, collision_exponent
        collision_exponent = collision_exponent.at[shape].add(mla.at[shape3])
    return collision_exponent
