import jax.numpy as jnp

from ._rates_utils import _realign_fourmer_concentration_vector
from ._rates_utils import _extract_left_reactant_c, _extract_right_reactant_c, _extract_template_c

def _clip_single_concentration_smoothly(
    concentration,
    soft_reactant_threshold,
    hard_reactant_threshold):
    rtrn = jnp.pi*(concentration-soft_reactant_threshold)/(soft_reactant_threshold-hard_reactant_threshold)
    return (jnp.cos(rtrn) + 1.)/2.

def _clip_concentration_vector_smoothly(
    concentration_vector,
    soft_reactant_threshold,
    hard_reactant_threshold):
    if soft_reactant_threshold==0.:
        return 1.
    weight = jnp.where(
            concentration_vector <= hard_reactant_threshold,
            0.,
            1.)
    return jnp.where(
            weight*(concentration_vector < soft_reactant_threshold),
            _clip_single_concentration_smoothly(concentration_vector,soft_reactant_threshold,hard_reactant_threshold),
            weight).reshape(concentration_vector.shape)

def _transform_rr_to_reactant_format(rr):
    nol = rr.shape[0]-1
    motiflength = (len(rr.shape)+2)/3
    left_reactant_number = right_reactant_number = jnp.sum(nol**jnp.arange(1,motiflength-1))
    template_reactant_number = jnp.sum(nol**jnp.arange(2,motiflength+1))*nol**(motiflength-1)
    # init rr in reactant format (rr_rf)
    rr_rf = jnp.zeros((left_reactant_number,right_reactant_number,template_reactant_number))
    # transform left reactant axes
    for left_strandlength in range(1,motiflength):
        rr_indcs1 = jnp.sum(nol**jnp.arange(1,left_strandlength))
        rr_indcs1 = (slice(rr_indcs1,rr_indcs1+nol**left_strandlength),)
        rr_rf_indcs1 = (0,)*(motiflength-left_strandlength-1) + (slice(None),)*left_strandlength
        for right_strandlength in range(1,motiflength):
            rr_indcs2 = jnp.sum(nol**jnp.arange(1,right_strandlength))
            rr_indcs2 = (slice(rr_indcs2,rr_indcs2+nol**left_strandlength),)
            rr_rf_indcs2 = (slice(None),)*right_strandlength + (0,)*(motiflength-right_strandlength-1)
            for templatelength in  range(2,motiflength+2):
                rr_indcs3 = jnp.sum(nol**jnp.arange(1,templatelength))
                if templatelength == motiflength+1:
                    rr_rf_indcs3 = (slice(1,None),)*strandlength + (0,)
                    rr_indcs3 = (slice(rr_indcs3,rr_indcs3+nol**(templatelength)),)
                else: 
                    rr_rf_indcs3 = (0,) + (slice(1,None),)*templatelength + (0,)*(motiflength-templatelength-1)
                    rr_indcs3 = (slice(rr_indcs3,rr_indcs3+nol**(templatelength+1)),)
                rr_rf_indcs = rr_rf_indcs1 + rr_rf_indcs2 + rr_rf_indcs3
                rr_indcs = rr_indcs1 + rr_indcs2 + rr_indcs3
                rr_rf = rr_rf.at[rr_rf_indcs].set(rr[rr_indcs])
    return rr_rf

def _transform_fourmer_rr_to_reactant_format(rr):
    nol = rr.shape[0]-1
    motiflength = (len(rr.shape)+2)/3
    if motiflength != 4:
        raise NotImplementedError(f"motiflength must be 4, but is {motiflength = }")
    raise NotImplementedError("function not yet implemented.")
    """
    left_reactant_species_number = right_reactant_species_number = nol**jnp.arange(motiflength)
    total_left_reactant_species_number = total_right_reactant_species_number = jnp.sum(left_reactant_species_number)
    template_species_number = jnp.append(nol**jnp.arange(motiflength+1) + nol**(motiflength-1))
    total_template_species_number = jnp.sum(template_species_number)
    rr_rf_shape = (left_reactant_species_number,right_reactant_species_number,template_species_number)
    rr_rf = jnp.zeros(rr_rf_shape)
    # left reactant
    rr_rf[] = rr[0,0,:]
    rr[0,1:,:]
    rr[1:,1:,:]
    # right reactant
    rr[0,1:,0,0]
    rr[0,1:,1:]
    rr[0,1:,1:,1:]
    # template
    rr[0,1:,1:,0]
    rr[0,1:,1:,1:]
    rr[1:,1:,1:,1:]
    rr[1:,1:,1:,0]
    """

def _clip_smoothly(
        reactant_concentration,
        soft_reactant_threshold : float,
        hard_reactant_threshold : float = None
        ) -> jnp.ndarray:
    if soft_reactant_threshold == 0.:
        return 1.
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    """
    weight = jnp.where(
            reactant_concentration <= hard_reactant_threshold,
            0.,
            1.)
    weight = jnp.where(
            weight*(reactant_concentration < soft_reactant_threshold),
            _clip_single_concentration_smoothly(reactant_concentration,soft_reactant_threshold,hard_reactant_threshold),
            weight)
    """
    left_reactant_c = _extract_left_reactant_c(
            _realign_fourmer_concentration_vector(reactant_concentration)
            )
    right_reactant_c = _extract_right_reactant_c(reactant_concentration)
    template_c = _extract_template_c(reactant_concentration)
    # left weight
    left_weight = _clip_concentration_vector_smoothly(left_reactant_c, soft_reactant_threshold, hard_reactant_threshold)
    # right_weight
    right_weight = _clip_concentration_vector_smoothly( right_reactant_c, soft_reactant_threshold,hard_reactant_threshold)
    # template_weight
    template_weight = _clip_concentration_vector_smoothly(template_c, soft_reactant_threshold,hard_reactant_threshold)
    return jnp.outer(
            jnp.outer(left_weight,right_weight),
            template_weight
            ).reshape(
                    left_weight.shape+right_weight.shape+template_weight.shape
                    )
