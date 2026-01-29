import jax.numpy as jnp
from warnings import warn

from jax import config
config.update("jax_enable_x64", True)

def _nucleotide_mass(fourmer_log_concentration_vector):
    return jnp.sum(jnp.exp(fourmer_log_concentration_vector[:,1:]),axis=(0,2,3))+jnp.sum(jnp.exp(fourmer_log_concentration_vector[:,1:,1:,0]),axis=(0,1))

def _nucl_mass_counter(number_of_letters : int, motiflength : int):
    nucl_mass_counter = jnp.zeros((number_of_letters,)+(number_of_letters+1,)*motiflength)
    for ii in range(number_of_letters):
        nucl_mass_counter = nucl_mass_counter.at[ii,:,ii+1,:,:].add(1)
        nucl_mass_counter = nucl_mass_counter.at[ii,:,1:,ii+1,0].add(1)
    return nucl_mass_counter

def _nucleotide_mass_correction_rate(
        initial_log_concentration_array,
        current_log_concentration_array
        ):
    number_of_letters = initial_log_concentration_array.shape[0]-1
    motiflength = len(initial_log_concentration_array.shape)

    jnp.zeros((number_of_letters,)+initial_log_concentration_array.shape)
    nucl_mass_correction_rate = _nucleotide_mass(initial_log_concentration_array)-_nucleotide_mass(current_log_concentration_array)
    nucl_mass_correction_rate = nucl_mass_correction_rate.reshape((-1,)+(1,)*motiflength)

    nucl_mass_counter = _nucl_mass_counter(number_of_letters, motiflength)
    nucl_mass_correction_rate = nucl_mass_correction_rate * nucl_mass_counter * jnp.exp(current_log_concentration_array)[None]
    #return jnp.matmul(nucl_mass_counter,jnp.exp(fourmer_log_concentration_vector))

    return jnp.sum(nucl_mass_correction_rate, axis=0)

def _nonending_strand_concentration(fourmer_log_concentration_vector):
    beginning_concentration = jnp.sum(jnp.exp(fourmer_log_concentration_vector[0,1:,1:,1:]))
    ending_concentration = jnp.sum(jnp.exp(fourmer_log_concentration_vector[1:,1:,1:,0]))
    return beginning_concentration-ending_concentration

def _nonending_strand_correction_rate(
        fourmer_log_concentration_vector
        ):
    number_of_letters = fourmer_log_concentration_vector.shape[0]-1
    motiflength = len(fourmer_log_concentration_vector.shape)
    nonending_strand_concentration = jnp.zeros((number_of_letters+1,)*motiflength)
    nonending_strand_concentration = nonending_strand_concentration.at[0,1:,1:,1:].subtract(1)
    nonending_strand_concentration = nonending_strand_concentration.at[1:,1:,1:,0].add(1)
    nonending_strand_concentration = nonending_strand_concentration*jnp.exp(fourmer_log_concentration_vector)
    return _nonending_strand_concentration(fourmer_log_concentration_vector)*nonending_strand_concentration

def mass_correction_rates(
        initial_log_concentration_array : jnp.array,
        current_log_concentration_array : jnp.array,
        weight : float = 1.,
        ) -> jnp.array:
    return weight * _nonending_strand_correction_rate(current_log_concentration_array) + weight * _nucleotide_mass_correction_rate(initial_log_concentration_array, current_log_concentration_array)
