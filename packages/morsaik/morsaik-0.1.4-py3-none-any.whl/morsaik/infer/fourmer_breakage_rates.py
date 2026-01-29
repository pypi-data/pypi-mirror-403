import jax.numpy as jnp
from warnings import warn

from jax import config
config.update("jax_enable_x64", True)

from ._rates_utils import _set_invalid_logc_to_log0
from ._rates_utils import _set_invalid_logc_diff_to_zero
from ._rates_utils import _cut_low_concentrations
from ._smooth_rate_clipping import _clip_concentration_vector_smoothly

def _cut_small_rates(rates, rates_cut):
    # logc_diff = jnp.where((fourmer_logc<=jnp.log(pseudo_count_concentration))*(logc_diff<0.),0.,logc_diff)
    return jnp.where(
            rates<rates_cut,
            0.,
            jnp.sqrt(rates**2-rates_cut**2)
            )

def _left_continuation_frequency(
        fourmer_logc : jnp.ndarray,
        ) -> jnp.ndarray:
    return jnp.exp(fourmer_logc)/(jnp.sum(jnp.exp(fourmer_logc),axis=0)[None])

def _right_continuation_frequency(
        fourmer_logc : jnp.ndarray,
        ) -> jnp.ndarray:
    return jnp.exp(fourmer_logc)/(jnp.sum(jnp.exp(fourmer_logc),axis=-1)[:,:,:,None])

def _effective_left_breakage_frequency(
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        ) -> jnp.ndarray:
    left_continuation_frequency = _left_continuation_frequency(fourmer_logc)
    return jnp.sum(left_continuation_frequency*effective_breakage_rate_constants,axis=0)[:,:,:,None]

def _effective_central_breakage_frequency(
        effective_breakage_rate_constants : jnp.ndarray,
        ) -> jnp.ndarray:
    return effective_breakage_rate_constants

def _effective_right_breakage_frequency(
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray
        ) -> jnp.ndarray:
    right_continuation_frequency = _right_continuation_frequency(fourmer_logc)
    return jnp.sum(right_continuation_frequency*effective_breakage_rate_constants,axis=-1)[None]

def _break_central_bonds(
        logc_diff : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_central_breakage_frequency = _effective_central_breakage_frequency(effective_breakage_rate_constants)
    logc_diff = logc_diff.at[:,1:,1:,:].subtract(effective_central_breakage_frequency[:,1:,1:,:])
    return _set_invalid_logc_to_log0(logc_diff, pseudo_count_concentration=pseudo_count_concentration)

def _break_left_bonds(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_left_breakage_frequency = _effective_left_breakage_frequency(
            fourmer_logc,
            effective_breakage_rate_constants
            )
    logc_diff = logc_diff.at[1:,1:,1:,:].subtract(effective_left_breakage_frequency[1:,1:,1:,:])
    return _set_invalid_logc_to_log0(logc_diff, pseudo_count_concentration=pseudo_count_concentration)

def _break_right_bonds(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_right_breakage_frequency = _effective_right_breakage_frequency(
            fourmer_logc,
            effective_breakage_rate_constants)
    logc_diff = logc_diff.at[:,1:,1:,1:].subtract(effective_right_breakage_frequency[:,1:,1:,1:])
    return _set_invalid_logc_to_log0(logc_diff, pseudo_count_concentration=pseudo_count_concentration)

def _produce_monomers(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_central_breakage_frequency = _effective_central_breakage_frequency(effective_breakage_rate_constants)
    logc_diff = logc_diff.at[0,1:,0,0].add(jnp.sum(
            effective_central_breakage_frequency[0,1:,1:,:]*jnp.exp(fourmer_logc[0,1:,1:,:]-fourmer_logc[0,1:,0,0][:,None,None]),
            axis=(-1,-2)
            ))
    logc_diff = _set_invalid_logc_to_log0(logc_diff)
    logc_diff = logc_diff.at[0,1:,0,0].add(jnp.sum(
            effective_central_breakage_frequency[:,1:,1:,0]*jnp.exp(fourmer_logc[:,1:,1:,0]-fourmer_logc[0,1:,0,0][None,None,:]),
            axis=(0,1)
            ))
    return _set_invalid_logc_to_log0(logc_diff)

def _produce_ends(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_right_breakage_frequency = _effective_right_breakage_frequency(
            fourmer_logc,
            effective_breakage_rate_constants
            )
    logc_diff = logc_diff.at[:,1:,1:,0].add(jnp.sum(
            effective_right_breakage_frequency[:,1:,1:,1:]*jnp.exp(fourmer_logc[:,1:,1:,1:]-fourmer_logc[:,1:,1:,0][:,:,:,None]),
            axis=-1
            ))
    return _set_invalid_logc_to_log0(logc_diff)

def _produce_beginnings(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    effective_left_breakage_frequency = _effective_left_breakage_frequency(
            fourmer_logc,
            effective_breakage_rate_constants
            )
    logc_diff = logc_diff.at[0,1:,1:,:].add(
            jnp.sum(
                effective_left_breakage_frequency[1:,1:,1:,:]*jnp.exp(fourmer_logc[1:,1:,1:,:]-fourmer_logc[0,1:,1:,:][None]),
                axis=0
                )
            )
    return _set_invalid_logc_to_log0(logc_diff)

def fourmer_breakage_rates(
        fourmer_logc : jnp.ndarray,
        effective_breakage_rate_constants : jnp.ndarray = 0.,
        pseudo_count_concentration : float = 1.e-12,
        fourmer_logc_slope : float = 0.,
        logc_diff_slope : float = 0.,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        ) -> jnp.ndarray:
    """
    Performs the breakage of the left breaking motif at the breaking point
    (1,2,3,4) three breaking points
    (1,2,3,0) two breaking points
    (0,2,3,4) two breaking points
    (0,2,3,0) one breaking point
    (0,2,0,0) no breaking point
    """
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    if isinstance(effective_breakage_rate_constants, (float,int)):
        if effective_breakage_rate_constants == 0.:
            return 0.
        effective_breakage_rate_constants = effective_breakage_rate_constants*jnp.ones(fourmer_logc.shape)
        effective_breakage_rate_constants = _set_invalid_logc_diff_to_zero(
                effective_breakage_rate_constants,
                print_warning = False
                )
    cut_off_weight = _clip_concentration_vector_smoothly(jnp.exp(fourmer_logc), soft_reactant_threshold, hard_reactant_threshold)
    effective_breakage_rate_constants = cut_off_weight*effective_breakage_rate_constants
    logc_diff = jnp.zeros(fourmer_logc.shape)
    logc_diff = _break_central_bonds(
            logc_diff,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    logc_diff = _break_left_bonds(
            logc_diff,
            fourmer_logc,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    logc_diff = _break_right_bonds(
            logc_diff,
            fourmer_logc,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    logc_diff = _produce_ends(
            logc_diff,
            fourmer_logc,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    logc_diff = _produce_beginnings(
            logc_diff,
            fourmer_logc,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    logc_diff = _produce_monomers(
            logc_diff,
            fourmer_logc,
            effective_breakage_rate_constants,
            pseudo_count_concentration=pseudo_count_concentration
            )
    return _set_invalid_logc_diff_to_zero(logc_diff, print_warning = False)

def _shape_brc(
        breakage_rate_constants : jnp.ndarray,
        number_of_letters : int = 4,
        motiflength : int = 4 
        ) -> jnp.ndarray:
    # breakage_rate_constants_shape = # # (number_of_letters+1,)*(motiflength//2-1)+(number_of_letters,number_of_letters,)+(number_of_letters+1,)*(motiflength//2-1)
    breakage_rate_constants_shape = (number_of_letters+1,)*motiflength
    if isinstance(breakage_rate_constants,float):
        brc = jnp.zeros(breakage_rate_constants_shape)
        breakage_rate_constants = brc.at[:,1:,1:,:].add(breakage_rate_constants)
    elif (jnp.prod(jnp.asarray(breakage_rate_constants.shape))==(number_of_letters+1)**2*number_of_letters**2):
        brc = jnp.zeros(breakage_rate_constants_shape)
        breakage_rate_constants = brc.at[:,1:,1:,:].add(breakage_rate_constants)
    elif breakage_rate_constants.shape != breakage_rate_constants_shape:
        raise ValueError(f"{breakage_rate_constants.shape=} != {breakage_rate_constants_shape=}")
    return breakage_rate_constants
