import jax.numpy as jnp
from jax.experimental import sparse
from warnings import warn

def _realign_fourmer_concentration_vector(fourmer_c):
    if len(fourmer_c.shape)==1:
        # fourmer_c_format = 'slim'
        return fourmer_c
    elif fourmer_c.shape[1]==fourmer_c.shape[0]:
        fourmer_c_format = 'excessive'
    else:
        fourmer_c_format = 'extensive'
        new_fourmer_c = jnp.zeros((fourmer_c.shape[0],)*len(fourmer_c.shape))
        fourmer_c = new_fourmer_c.at[:,1:].set(fourmer_c)
    invalid_c = fourmer_c[0,0,1:,0]
    fourmer_c = fourmer_c.at[0,0,1:,0].set(fourmer_c[0,1:,0,0])
    fourmer_c = fourmer_c.at[0,1:,0,0].set(invalid_c)
    if fourmer_c_format == 'excessive':
        return fourmer_c
    else:
        return fourmer_c[:,:,1:]

def _set_invalid_logc_to_log0(
        fourmer_logc : jnp.ndarray,
        pseudo_count_concentration : float = 1.e-12,
        print_warning : bool = False,
        right_aligned : bool = False
        ) -> jnp.ndarray:
    """
    fourmer_logc : jnp.ndarray,
    pseudo_count_concentration : float = 1.e-12,
    print_warning : bool = False,
    right_aligned : bool = False
        whether strands are aligned to the left ([0,a_1,...a_l,0,...,0])
        or to the right  ([0,...,a_1,...a_l,0]),
        default is left aligned.
    """
    log0 = jnp.log(pseudo_count_concentration)
    if print_warning:
        if right_aligned:
            if jnp.any(fourmer_logc[:,:,0,:] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[:,:,0,:])=} > {log0=}")
            if jnp.any(fourmer_logc[1:,0,1:,:] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[1:,0,1:,:])=} > {log0=}")
            if jnp.any(fourmer_logc[0,0,1:,1:] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[0,0,1:,1:])=} > {log0=}")
            fourmer_logc = fourmer_logc.at[:,:,0,:].set(log0)
            fourmer_logc = fourmer_logc.at[1:,0,1:,:].set(log0)
            fourmer_logc = fourmer_logc.at[0,0,1:,1:].set(log0)
        else:
            if jnp.any(fourmer_logc[:,0,:,:] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[:,0,:,:])=} > {log0=}")
            if jnp.any(fourmer_logc[:,1:,0,1:] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[:,1:,0,1:])=} > {log0=}")
            if jnp.any(fourmer_logc[1:,1:,0,0] > log0):
                warn(f"Invalid Entry in {jnp.max(fourmer_logc[1:,1:,0,0])=} > {log0=}")
            fourmer_logc = fourmer_logc.at[:,0,:,:].set(log0)
            fourmer_logc = fourmer_logc.at[:,1:,0,1:].set(log0)
            fourmer_logc = fourmer_logc.at[1:,1:,0,0].set(log0)
    return fourmer_logc

def _set_invalid_logc_diff_to_zero(
        logc_diff : jnp.ndarray,
        print_warning : bool = True,
        right_aligned : bool = False
        ) -> jnp.ndarray:
    if print_warning:
        if right_aligned:
            if jnp.any(logc_diff[:,:,0,:] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[:,:,0,:])=} > 0.")
            if jnp.any(logc_diff[1:,0,1:,:] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[1:,0,1:,:])=} > 0.")
            if jnp.any(logc_diff[0,0,1:,1:] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[0,0,1:,1:])=} > 0.")
            logc_diff = logc_diff.at[:,:,0,:].set(0.)
            logc_diff = logc_diff.at[1:,0,1:,:].set(0.)
            logc_diff = logc_diff.at[0,0,1:,1:].set(0.)
        else:
            if jnp.any(logc_diff[:,0,:,:] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[:,0,:,:])=} > 0.")
            if jnp.any(logc_diff[:,1:,0,1:] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[:,1:,0,1:])=} > 0.")
            if jnp.any(logc_diff[1:,1:,0,0] != 0.):
                warn(f"Invalid Entry in logc_diff: {jnp.max(logc_diff[1:,1:,0,0])=} > 0.")
        logc_diff = logc_diff.at[:,0,:,:].set(0.)
        logc_diff = logc_diff.at[:,1:,0,1:].set(0.)
        logc_diff = logc_diff.at[1:,1:,0,0].set(0.)
    return logc_diff

def _cosinus_lowcut(
        x : jnp.ndarray,
        lowcut : float = 0.,
        slope : float = 1.
        ):
    if slope == 0.:
        return jnp.where(
                x<lowcut,
                0.,
                1.)
    x = jnp.where(x<lowcut,0.,x)
    return jnp.where(
            x<lowcut+slope,
            0.5*(1-jnp.cos(jnp.pi*(x-lowcut)/slope)),
            1.)

def _cut_low_concentrations(
        logc_diff : jnp.ndarray,
        fourmer_logc : jnp.ndarray,
        soft_reactant_threshold : float = 1.e-12,
        fourmer_logc_slope : float = 0.,
        logc_diff_slope : float = 0.
        ) -> jnp.ndarray:
    if (logc_diff_slope == 0.) and (fourmer_logc_slope == 0.):
        return jnp.where((fourmer_logc<=jnp.log(soft_reactant_threshold))*(logc_diff<0.),0.,logc_diff)
    elif fourmer_logc_slope < 0.:
        raise ValueError(f"fourmer_logc_slope must be semi-positive, but\n{fourmer_logc_slope= }")
    elif logc_diff_slope< 0.:
        raise ValueError(f"logc_diff_slope must be semi-positive, but\n{logc_diff_slope = }")
    else:
        weight=1.-(1.-_cosinus_lowcut(fourmer_logc,lowcut=jnp.log(soft_reactant_threshold),slope=fourmer_logc_slope))*(1.-_cosinus_lowcut(logc_diff,lowcut=0.,slope=logc_diff_slope))
        return weight*logc_diff

def _treat_nans(
        logc_diff,
        fourmer_c,
        hard_reactant_threshold
        ) -> jnp.ndarray:
    fourmer_c[jnp.isnan(lrr)]<0.
    lrr.at[jnp.isnan(lrr)].set()
    jnp.where(jnp.isnan(log_reaction_rates))
    logc_diff = jnp.where(jnp.isnan(logc_diff)*(fourmer_c<hard_reactant_threshold),0.,logc_diff)
    if jnp.any(jnp.isnan(logc_diff)):
        warn("NaN detected detected.")
    return logc_diff

def _extract_left_reactant_c(fourmer_c):
    fourmer_c = jnp.moveaxis(fourmer_c,-1,0)
    return fourmer_c[0]

def _initizialize_left_reactant_extraction_matrix(
        numer_of_letters : int,
        motiflength : int) -> jnp.ndarray:
    # shape of left reactant
    left_reactant_shape = (jnp.sum(nol**jnp.arange(1,motiflength)),)
    # shape of full fourmer_c
    # left reactant extraction matrix
    lrem = jnp.zeros(left_reactant_shape+(numer_of_letters+1,)*motiflength)
    for strandlength in range(1,motiflength):
        if strandlength == motiflength-1:
            indcs = (slice(1,None),)*strandlength + (0,)
        else: 
            indcs = (0,) + (slice(1,None),)*strandlength + (0,)*(motiflength-strandlength-1)
        indcs_new1 = jnp.sum(nol**jnp.arange(1,strandlength))-1
        indcs_new2 = jnp.sum(nol**jnp.arange(1,strandlength+1))-1
        lrem.at[(slice(indcs_new1,indcs_new2),)+indcs].add(1)
    return lrem

def _extract_right_reactant_c(fourmer_c):
    """
    nol = fourmer_c.shape[0]-1
    motiflength = len(fourmer_c.shape)
    if fourmer_c.shape[1]+1==fourmer_c.shape[0]:
        fourmer_c = jnp.zeros((nol+1,)*motiflength).at[:,1:].set(fourmer_c)
    right_reactant_c = jnp.zeros(
            jnp.sum(nol**jnp.arange(1,motiflength))
            )
    for strandlength in range(1,motiflength):
        if strandlength == motiflength-1:
            indcs = (0,) + (slice(1,None),)*strandlength
        else: 
            indcs = (0,) + (slice(1,None),)*strandlength + (0,)*(motiflength-strandlength-1)
        indcs_new1 = jnp.sum(nol**jnp.arange(1,strandlength))-1
        indcs_new2 = jnp.sum(nol**jnp.arange(1,strandlength+1))-1
        right_reactant_c = right_reactant_c.at[indcs_new1:indcs_new2].set(fourmer_c[indcs])
    return left_reactant_c
    """
    return fourmer_c[0]

def _extract_template_c(
        fourmer_c,
        number_of_letters = None,
        ):
    """
    nol = fourmer_c.shape[0]-1
    motiflength = len(fourmer_c.shape)
    if fourmer_c.shape[1]+1==fourmer_c.shape[0]:
        fourmer_c = jnp.zeros((nol+1,)*motiflength).at[:,1:].set(fourmer_c)
    template_c = jnp.zeros(
            jnp.sum(nol**jnp.arange(2,motiflength+1)+nol**(motiflength-1))
            )
    for templatelength in range(2,motiflength+2):
        if templatelength == motiflength+1:
            indcs = (slice(1,None),)*strandlength + (0,)
        else: 
            indcs = (0,) + (slice(1,None),)*templatelength + (0,)*(motiflength-templatelength-1)
        indcs_new1 = jnp.sum(nol**jnp.arange(1,strandlength))
        indcs_new2 = jnp.sum(nol**jnp.arange(1,strandlength+1))
        right_reactant_c = right_reactant_c.at[indcs_new1:indcs_new2].set(fourmer_c[indcs])
    return template_c
    """
    if len(fourmer_c.shape)==1:
        fourmer_c_format = 'slim'
        if number_of_letters is None:
            raise ValueError("number of letters needs to be given to extract template concentration vector.")
    if len(fourmer_c.shape)!=4:
        raise NotImplementedError(f"Only implemented for motiflength 4, but {motiflength = }")
    elif fourmer_c.shape[1]==fourmer_c.shape[0]:
        fourmer_c_format = 'excessive'
        return (fourmer_c[0,1,0,1]*jnp.ones(fourmer_c.shape)).at[:,1:,1:,:].set(
                fourmer_c[:,1:,1:,:]
                )
    else:
        fourmer_c_format = 'extensive'
        return fourmer_c[:,:,1:,:]
