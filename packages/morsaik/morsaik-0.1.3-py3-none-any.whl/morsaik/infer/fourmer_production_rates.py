import jax.numpy as jnp
from warnings import warn

from jax import config
config.update("jax_enable_x64", True)

from ._rates_utils import _set_invalid_logc_to_log0
from ._rates_utils import _set_invalid_logc_diff_to_zero
from ._rates_utils import _cut_low_concentrations
from ._smooth_rate_clipping import _clip_smoothly

def _initialize_empty_fourmer_production_rates(
        number_of_letters : int = 4,
        motiflength : int = 4
        ) -> jnp.ndarray :
    if motiflength != 4:
        raise NotImplementedError("motiflength!=4")
    shape = (number_of_letters+1,)*(motiflength-1)
    shape = shape*2+(number_of_letters+1,)*motiflength
    return jnp.zeros(shape)

def _set_invalid_production_rates_to_zero(
        reaction_rates : jnp.ndarray,
        ) -> jnp.ndarray:
    rr = reaction_rates.at[:,0].set(0)
    rr = rr.at[:,:,0].set(0)
    rr = rr.at[:,:,:,:,:,0].set(0)
    return rr.at[:,:,:,:,:,:,0].set(0)

def _set_invalid_log_production_rates_to_logzero(
        log_reaction_rates : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    log0 = jnp.log(pseudo_count_concentration)
    rr = log_reaction_rates.at[:,:,0].set(log0)
    rr = rr.at[:,0].set(log0)
    rr = rr.at[:,:,0].set(log0)
    rr = rr.at[:,:,:,:,:,0].set(log0)
    return rr.at[:,:,:,:,:,:,0].set(log0)

def _set_invalid_rates_to_zero(
        reaction_rates : jnp.ndarray,
        ) -> jnp.ndarray:
    """
    set invalid rates to zeros.
    Format of the rates: [l0,l1,l2,r1,r2,r3,t0,t1,t2,t3]
    """
    rr = reaction_rates.at[:,:,0].set(0)
    rr = rr.at[1:,0].set(0)
    rr = rr.at[:,:,:,0].set(0)
    rr = rr.at[:,:,:,:,0,1:].set(0)
    rr = rr.at[:,:,:,:,:,:,:,0,:,:].set(0)
    return rr.at[:,:,:,:,:,:,:,:,0,:].set(0)

def _set_invalid_log_rates_to_logzero(
        log_reaction_rates : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    log0 = jnp.log(pseudo_count_concentration)
    lrr = log_reaction_rates.at[:,:,0].set(log0)
    lrr = lrr.at[1:,0].set(log0)
    lrr = lrr.at[:,:,:,0].set(log0)
    lrr = lrr.at[:,:,:,:,0,1:].set(log0)
    lrr = lrr.at[:,:,:,:,:,:,:,0,:,:].set(log0)
    return lrr.at[:,:,:,:,:,:,:,:,0,:].set(log0)

def _add_log_rate_constants(
        log_rate_constants : jnp.ndarray,
        log_reaction_rates : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12

        ) -> jnp.ndarray:
    return log_reaction_rates.at[:,:,1:,1:,:,:,:,1:,1:,:].add(log_rate_constants.reshape((1,)+log_rate_constants.shape[:len(log_rate_constants.shape)//2]+(1,)+log_rate_constants.shape[len(log_rate_constants.shape)//2:]))

def _multiply_rr_with_rc(rr,rc):
    return rr.at[:,:,1:,1:,:,:,:,1:,1:,:].multiply(rc[None,:,:,:,:,None])

def _add_template_logc(
        fourmer_logc : jnp.ndarray,
        log_reaction_rates : jnp.ndarray,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    motiflength = 4
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    return log_reaction_rates.at[:,:,:,:,:,:,:,1:,1:,:].add(fourmer_logc[:,1:,1:,:].reshape((1,)*(2*(motiflength-1))+(number_of_letters+1,number_of_letters,number_of_letters,number_of_letters+1)))

def _add_extended_end_logc(
        fourmer_logc : jnp.ndarray,
        log_reaction_rates : jnp.ndarray,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    motiflength = 4
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    # add monomers
    lrr = log_reaction_rates.at[0,0,1:].add(fourmer_logc[0,1:,0,0].reshape((number_of_letters,)+(1,)*(motiflength-1)+(1,)*motiflength))
    # add ending motifs
    return lrr.at[:,1:,1:].add(
            fourmer_logc[:,1:,1:,0].reshape(
                (number_of_letters+1,number_of_letters,number_of_letters)+(1,)*(motiflength-1)+(1,)*motiflength
                )
            )

def _add_extending_beginning_logc(
        fourmer_logc : jnp.ndarray,
        log_reaction_rates : jnp.ndarray,
        motiflength : int = 4,
        pseudo_count_concentration : float = 1.e-12
        ) -> jnp.ndarray:
    if motiflength != 4:
        raise NotImplementedError("motiflength!=4")
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    # monomers (0100) and dimers (0110)
    lrr = log_reaction_rates.at[:,:,:,1:,:,0].add(
            fourmer_logc[0,1:,:,0].reshape(
                (1,)*(motiflength-1)+fourmer_logc[0,1:,:,0].shape+(1,)*(motiflength)
            )
            )
    # beginnings 0111
    lrr = lrr.at[:,:,:,1:,1:,1:].add(
            fourmer_logc[0,1:,1:,1:].reshape(
                (1,)*(motiflength-1)+fourmer_logc[0,1:,1:,1:].shape+(1,)*(motiflength)
            )
            )
    return lrr

def _subtract_produced_fourmers(
        fourmer_logc : jnp.ndarray,
        log_reaction_rates : jnp.ndarray,
        product_index : int = 0,
        motiflength : int = 4,
        pseudo_count_concentration : float  = 1.e-12
        ) -> jnp.ndarray:
    if motiflength != 4:
        raise NotImplementedError("motiflength != 4")
    # only subtract product, where term is nonzero (so greater log0)
    log0 = jnp.log(pseudo_count_concentration)
    if product_index==0:
        lrr = log_reaction_rates.at[:,0,:].set(log0-1)
    elif product_index==2:
        lrr = log_reaction_rates.at[:,:,:,:,0].set(log0-1)
    else:
        lrr = log_reaction_rates
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    nonzero = lrr > log0
    produced_fourmer_logc = _set_invalid_logc_diff_to_zero(fourmer_logc, print_warning = False)
    produced_fourmer_logc = produced_fourmer_logc.reshape(
                (1,)*product_index + produced_fourmer_logc.shape + (1,)*(2*(motiflength-1)-product_index)
                )
    produced_fourmer_logc = nonzero*produced_fourmer_logc
    lrr = lrr.at[:].subtract(
            produced_fourmer_logc
            )
    return _set_invalid_log_rates_to_logzero(lrr, pseudo_count_concentration/10.)

def _exponentiate_log_reaction_rates(
        log_reaction_rates : jnp.ndarray
        ) -> jnp.ndarray:
    return jnp.exp(log_reaction_rates)

def _compute_extended_end_motif_reaction_logc_rates(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        ):
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    log_rate_constants, rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    lrr = _initialize_empty_fourmer_production_rates(number_of_letters)
    lrr = _add_log_rate_constants(log_rate_constants,lrr)
    lrr = _set_invalid_log_rates_to_logzero(lrr, pseudo_count_concentration/10.)
    lrr = _add_template_logc(fourmer_logc,lrr, number_of_letters, pseudo_count_concentration)
    lrr = _add_extending_beginning_logc(fourmer_logc,lrr)
    rr = _exponentiate_log_reaction_rates(lrr)
    # clip smoothly
    rr = _clip(fourmer_logc, rr, soft_reactant_threshold, hard_reactant_threshold)
    rr = _multiply_rr_with_rc(rr,rate_constants)
    return -_set_invalid_rates_to_zero(rr)

def _clip(fourmer_logc, rr, soft_reactant_threshold, hard_reactant_threshold):
    # check for extensive or excessive format
    if rr.shape[2]<fourmer_logc.shape[1]:
        fourmer_logc = fourmer_logc[:,1:]
    elif rr.shape[2]>fourmer_logc.shape[1]:
        fourmer_logc = (hard_reactant_threshold*jnp.ones(
                (fourmer_logc.shape[0],)*len(fourmer_logc.shape)
                )).at[:,1:].set(
                        fourmer_logc
                )
    weight = _clip_smoothly(
            jnp.exp(fourmer_logc),
            soft_reactant_threshold=soft_reactant_threshold,
            hard_reactant_threshold=hard_reactant_threshold)
    return weight*rr

def _compute_extending_beginning_motif_reaction_logc_rates(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        ) -> jnp.ndarray :
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    log_rate_constants, rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    lrr = _initialize_empty_fourmer_production_rates(number_of_letters)
    lrr = _add_log_rate_constants(log_rate_constants,lrr)
    lrr = _set_invalid_log_rates_to_logzero(lrr, pseudo_count_concentration/10.)
    lrr = _add_template_logc(fourmer_logc, lrr, number_of_letters, pseudo_count_concentration)
    lrr = _add_extended_end_logc(fourmer_logc, lrr, number_of_letters)
    rr = _exponentiate_log_reaction_rates(lrr)
    # clip smoothly
    rr = _clip(fourmer_logc, rr, soft_reactant_threshold, hard_reactant_threshold)
    rr = _multiply_rr_with_rc(rr,rate_constants)
    return -_set_invalid_rates_to_zero(rr)

def _compute_produced_motif_reaction_logc_rates(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        product_index : int = 0,
        number_of_letters : int = 4,
        motiflength : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        ) -> jnp.ndarray:
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    log_rate_constants, rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    lrr = _initialize_empty_fourmer_production_rates(number_of_letters)
    lrr = _add_log_rate_constants(log_rate_constants, lrr)
    lrr = _set_invalid_log_rates_to_logzero(lrr, pseudo_count_concentration/10.)
    lrr = _add_template_logc(fourmer_logc,lrr,number_of_letters, pseudo_count_concentration)
    lrr = _add_extended_end_logc(fourmer_logc,lrr, number_of_letters)
    lrr = _add_extending_beginning_logc(fourmer_logc,lrr)
    lrr = _subtract_produced_fourmers(
            fourmer_logc,
            lrr,
            product_index=product_index
            )
    rr = _exponentiate_log_reaction_rates(lrr)
    # clip smoothly
    rr = _clip(fourmer_logc, rr, soft_reactant_threshold, hard_reactant_threshold)
    rr = _multiply_rr_with_rc(rr, rate_constants)
    return +_set_invalid_rates_to_zero(rr)

def compute_logc_diff_extended_end_motifs(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ) -> jnp.ndarray:
    log_rate_constants, rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    if motiflength!=4:
        raise NotImplementedError("motiflength!=4")
    logc_diff = jnp.zeros((number_of_letters+1,)*motiflength)
    # monomers
    extended_end_motif_reaction_rates = _compute_extended_end_motif_reaction_logc_rates(
            fourmer_logc,
            log_rate_constants,
            rate_constants,
            motiflength,
            number_of_letters,
            pseudo_count_concentration,
            soft_reactant_threshold=soft_reactant_threshold,
            hard_reactant_threshold=hard_reactant_threshold
            )
    logc_diff = logc_diff.at[0,1:,0,0].add(
            jnp.sum(
                extended_end_motif_reaction_rates[0,0,1:],
                axis = tuple([ii for ii in range(1,len(extended_end_motif_reaction_rates[0,0,1:].shape))]
                             ),
                )
            )
    # motifs
    logc_diff = logc_diff.at[:,1:,1:,0].add(
            jnp.sum(extended_end_motif_reaction_rates[:,1:,1:],
                axis = tuple([ii for ii in range((motiflength-1),len(extended_end_motif_reaction_rates[:,1:,1:].shape))])
                    )
                )
    return _set_invalid_logc_diff_to_zero(logc_diff, print_warning = False)

def compute_logc_diff_extending_beginning_motifs(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ) -> jnp.ndarray:
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    logc_diff = jnp.zeros((number_of_letters+1,)*motiflength)
    log_rate_constants, rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    extending_beginning_motif_reaction_rates = _compute_extending_beginning_motif_reaction_logc_rates(
            fourmer_logc,
            log_rate_constants,
            rate_constants,
            motiflength,
            number_of_letters,
            pseudo_count_concentration,
            soft_reactant_threshold=soft_reactant_threshold,
            hard_reactant_threshold=hard_reactant_threshold
            )
    # monomers and dimers
    logc_diff = logc_diff.at[0,1:,:,0].add(
            jnp.sum(extending_beginning_motif_reaction_rates[:,:,:,1:,:,0],
                axis = tuple([ii for ii in range(motiflength-1)])+tuple(
                    [ii for ii in range(2*motiflength-2-1,len(extending_beginning_motif_reaction_rates.shape)-1)])
                    )
                )
    # beginnings
    logc_diff = logc_diff.at[0,1:,1:,1:].add(
            jnp.sum(extending_beginning_motif_reaction_rates[:,:,:,1:,1:,1:],
                axis = tuple([ii for ii in range(motiflength-1)])+tuple([ii for ii in range(2*motiflength-2,len(extending_beginning_motif_reaction_rates.shape))])
                    )
                )
    return  _set_invalid_logc_diff_to_zero(logc_diff, print_warning = False)

def compute_logc_diff_produced_motifs(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ) -> jnp.ndarray:
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    logc_diff = jnp.zeros((number_of_letters+1,)*motiflength)
    log_rate_constants, basic_rate_constants = _split_and_shape_fprc(
            (log_rate_constants, rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    for product_index in range(motiflength-1):
        produced_motif_reaction_rates =  _compute_produced_motif_reaction_logc_rates(
                fourmer_logc,
                log_rate_constants,
                basic_rate_constants,
                product_index,
                number_of_letters,
                motiflength=motiflength,
                pseudo_count_concentration=pseudo_count_concentration,
                soft_reactant_threshold=soft_reactant_threshold,
                hard_reactant_threshold=hard_reactant_threshold
                )
        pmrr = jnp.sum(
                produced_motif_reaction_rates,
                axis = tuple(
                    [ii for ii in range(product_index)]) + tuple(
                        [ii for ii in range(motiflength+product_index,3*motiflength-2)])
                    )
        # dimers, beginning, ends and continuations
        logc_diff = logc_diff.at[:,1:,1:,:].add(pmrr[:,1:,1:,:])
    return _set_invalid_logc_diff_to_zero(logc_diff, print_warning = False)

def compute_total_extension_rates(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        conserve_mass : bool = False,
        fourmer_logc_slope : float = 0.,
        logc_diff_slope : float = 0.
        ) -> jnp.ndarray:
    """

    Parameters:
    -----------

    conserve_mass : bool
        whether concentration of monomers shall compensate variation in the
        total mass (deprecated! Please use mass_correction_rates for this from
        now on, since this feature leads to inconsistencies in the zebraness
        and strand number)
        default False

    Returns:
    --------
    total_extension_rates : jnp.ndarray
    """
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    log_rate_constants, basic_rate_constants = _split_and_shape_fprc(
        (log_rate_constants, rate_constants),
        number_of_letters=number_of_letters,
        motiflength=motiflength,
        pseudo_count_concentration=pseudo_count_concentration
        )
    # initialize logc_diff
    logc_diff = jnp.zeros((number_of_letters+1,)*motiflength)
    # consume_left_reactant(self):
    logc_diff = jnp.add(logc_diff,
            compute_logc_diff_extended_end_motifs(
                fourmer_logc,
                log_rate_constants,
                rate_constants,
                motiflength,
                number_of_letters,
                pseudo_count_concentration,
                soft_reactant_threshold=soft_reactant_threshold,
                hard_reactant_threshold=hard_reactant_threshold
                )
            )
    # consume_right_reactant(self):
    logc_diff = jnp.add(logc_diff,
            compute_logc_diff_extending_beginning_motifs(
                fourmer_logc,
                log_rate_constants,
                rate_constants,
                motiflength,
                number_of_letters,
                pseudo_count_concentration,
                soft_reactant_threshold=soft_reactant_threshold,
                hard_reactant_threshold=hard_reactant_threshold
                )
            )
    # create_products
    logc_diff = jnp.add(logc_diff,
            compute_logc_diff_produced_motifs(
                fourmer_logc,
                log_rate_constants,
                rate_constants,
                motiflength,
                number_of_letters,
                pseudo_count_concentration,
                soft_reactant_threshold=soft_reactant_threshold,
                hard_reactant_threshold=hard_reactant_threshold
                )
            )
    if conserve_mass:
        c_diff = jnp.exp(fourmer_logc)*logc_diff
        c_diff = c_diff.at[0,1:,0,0].set(-jnp.sum(c_diff[:,1:,1:,:],axis=(0,2,3))-jnp.sum(c_diff[:,1:,1:,0],axis=(0,1)))
        logc_diff = jnp.exp(-fourmer_logc)*c_diff
    return _set_invalid_logc_diff_to_zero(logc_diff, print_warning = False)

def compute_motif_extensions(
        fourmer_logc : jnp.ndarray,
        log_rate_constants : jnp.ndarray = 0.,
        basic_rate_constants : jnp.ndarray = 1.,
        motiflength : int = 4,
        number_of_letters : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ) -> jnp.ndarray:
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if hard_reactant_threshold is None:
        hard_reactant_threshold = soft_reactant_threshold/2.
    fourmer_logc = _set_invalid_logc_to_log0(fourmer_logc, pseudo_count_concentration/10.)
    log_rate_constants, basic_rate_constants = _split_and_shape_fprc(
            (log_rate_constants, basic_rate_constants),
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            pseudo_count_concentration=pseudo_count_concentration
            )
    lrr = _initialize_empty_fourmer_production_rates(number_of_letters)
    lrr = _add_log_rate_constants(log_rate_constants, lrr)
    lrr = _set_invalid_log_rates_to_logzero(lrr, pseudo_count_concentration/10.)
    lrr = _add_extended_end_logc(fourmer_logc,lrr, number_of_letters)
    lrr = _add_extending_beginning_logc(fourmer_logc,lrr)
    lrr = _add_template_logc(fourmer_logc,lrr, number_of_letters, pseudo_count_concentration)
    rr = _exponentiate_log_reaction_rates(lrr)
    #rr = rr.at[rr<=pseudo_count_concentration].set(0.)
    rr = _clip(fourmer_logc, rr, soft_reactant_threshold, hard_reactant_threshold)
    rr = _multiply_rr_with_rc(rr,basic_rate_constants)
    return jnp.sum(rr, axis=(0,2*(motiflength-1)-1))

def _split_and_shape_fprc(
        lrc_brc,
        number_of_letters = 4,
        motiflength = 4,
        pseudo_count_concentration = 1.e-12,
        ):
    lrc, brc = lrc_brc
    lrc = _shape_fprc(
            lrc,
            number_of_letters = number_of_letters,
            motiflength = motiflength,
            pseudo_count_concentration = pseudo_count_concentration,
            fprc_are_logarithmized=True,
            shape_is_thin=True
            )
    brc = _shape_fprc(
            brc,
            number_of_letters = number_of_letters,
            motiflength = motiflength,
            pseudo_count_concentration = pseudo_count_concentration,
            fprc_are_logarithmized=False,
            shape_is_thin=True
            )
    return lrc,brc

def _shape_fprc(
        fourmer_production_rate_constants,
        number_of_letters : int = 4,
        motiflength : int = 4,
        pseudo_count_concentration : float = 1.e-12,
        fprc_are_logarithmized : bool = False,
        shape_is_thin : bool = False
        ) -> jnp.ndarray:
    motif_production_rate_constants_shape = (number_of_letters+1,)*(2*motiflength)
    if isinstance(fourmer_production_rate_constants,(float,int)):
        eerc = float(fprc_are_logarithmized)*jnp.ones(motif_production_rate_constants_shape)
        fourmer_production_rate_constants = eerc.at[:,1:,1:,:,:,1:,1:,:].set(fourmer_production_rate_constants)
    elif fourmer_production_rate_constants.size == (number_of_letters+1)**motiflength*number_of_letters**motiflength:
        eerc_new = float(fprc_are_logarithmized)*jnp.ones(motif_production_rate_constants_shape)
        fourmer_production_rate_constants = eerc_new.at[:,1:,1:,:,:,1:,1:,:].set(fourmer_production_rate_constants)
    if fourmer_production_rate_constants.shape != motif_production_rate_constants_shape:
        raise ValueError(f"{fourmer_production_rate_constants.shape=} != {motif_production_rate_constants_shape=}")
    if fprc_are_logarithmized:
        if shape_is_thin:
            #thin_shape = (number_of_letters+1,number_of_letters)
            #thin_shape += shape[::-1]
            #thin_shape += shape
            return fourmer_production_rate_constants[:,1:,1:,:,:,1:,1:,:]
        else:
            return _set_invalid_log_production_rates_to_logzero(
                    fourmer_production_rate_constants,
                    pseudo_count_concentration=pseudo_count_concentration
                    )
    else:
        if shape_is_thin:
            return fourmer_production_rate_constants[:,1:,1:,:,:,1:,1:,:]
        else:
            return _set_invalid_production_rates_to_zero(
                    fourmer_production_rate_constants,
                    )
