import jax
import jax.numpy as jnp
import numpy as np

from .fourmer_production_rates import compute_motif_extensions, _set_invalid_logc_to_log0

def collisions_from_motif_concentration_trajectory_and_collision_rate_constants(
    motif_concentration_trajectory,
    collision_rate_constants = 1,
    flatten : bool = True
    ):
    '''
    The collisions give how often a certain ligation (channel)
    can be observed.
    It measures, how often the reactants (end motif of the rear strand,
    beginning motif of the fore strand and template motif)
    that perform the reaction, meet (are exposed to each other).

    Technically, it integrates over time the three
    concentrations reaction wise,
    according to effective ligation dynamics.

    Parameters:
    -----------
    motif_concentration_trajectory  :   concentration
    collision_rate_constants:   array, optional (default: None)
        weights of the integral. If None, they are set to one.
    flatten :   boolean, optional (default: True)
        if True, output is flat

    Returns:
    --------
    field : NIFTy-field
        field with each entry being the integral over the corresponding
        concentrations of the reactants that are needed for the templated
        ligation.
    '''
    #'length{}strand','beginning','continuation','end'
    endings_trajectory = motif_concentration_trajectory.motifs['ending']
    beginnings_trajectory = motif_concentration_trajectory.motifs['beginning']
    templates_trajectory = motif_concentration_trajectory.motifs

    return collisions

def motifs_collisions_array_from_motifs_array(
        motifs_array : jax.Array,
        collision_order : int = 3
        ) -> jax.Array:
    """
    takes motifs_array and calculates motifs_collisions_array, i.e.
    the $m$th outer product of the motifs array with itself,
    where $m$ is the collision_order.

    Parameters
    ----------
    motifs_array : jax.Array
    collision_order : int, optional
        number of collisions, by default 3

    Returns
    -------
    jax.Array
        motifs_collisions_array
    """
    motifs_collisions_array = motifs_array
    for ii in range(1,collision_order):
        motifs_collisions_array = motifs_collisions_array.reshape(-1,1)*motifs_array.reshape(-1,1).T
    return motifs_collisions_array.flatten()

def ligation_spot_formations_from_motifs_array(
        motifs_array : jax.Array,
        number_of_letters : int = 4,
        motiflength : int = 4
        ) -> jax.Array:
    """
    calculates the collisions that actually enable ligation,
    i.e. the $m$th outer product of the motifs array with itself,
    using infer.motifs_collisions_array_from_motifs_array
    but with only ending motifs (and strands) as fore motifs,
    beginning motifs (and strands) as rear motifs
    and only strands of at least lenth 2 as template motifs.

    Parameters
    ----------
    motifs_array : jax.Array
    number_of_letters : int, optional
        number of letters, by default 4
    motiflength : int, optional
        length of motif, by default 4

    Returns
    -------
    jax.Array
        ligation_spot_array
    """
    ligation_spot_array = motifs_collisions_array_from_motifs_array(motifs_array, collision_order = 3)
    number_of_motifs = jnp.sum(number_of_letters**jnp.arange(1,motiflength+1))+number_of_letters**(motiflength-1)
    ligation_spot_array = ligation_spot_array.reshape((number_of_motifs,)*3)
    # not all collisions enable adjacent hybridization
    number_of_continuations = number_of_letters**motiflength
    number_of_beginnings = number_of_endings = number_of_letters**(motiflength-1)
    # fore motif must end
    ligation_spot_array = jnp.concatenate(
            [ligation_spot_array[:-(number_of_beginnings + number_of_endings + number_of_continuations),:,:],
             ligation_spot_array[-number_of_endings:,:,:]
             ],
            axis = 0)
    # rear motif must begin
    ligation_spot_array = ligation_spot_array[:,:-(number_of_continuations+number_of_endings),:]
    # template must have at least one covalent bond
    return ligation_spot_array[:,:,number_of_letters:]

def collisions_from_motif_concentration_trajectory_array_and_collision_rate_constants_array(
    motif_concentration_trajectory_array : jax.Array,
    motif_concentration_trajectory_times_array : jax.Array = None,
    collision_rate_constants_array : jax.Array = 1.,
    motiflength : int = 4,
    alphabet : list = ['A', 'T'],
    complements : list = [1,0],
    concentrations_are_logarithmised : bool = True,
    pseudo_count_concentration : float = 1.e-12
    ):
    """
    Jax version of collions_from_motif_concentration_trajectory_and_collision_rate_constants
    """
    if motiflength != 4:
        raise NotImplementedError("Function only implemented for motiflength 4.")
    nol = len(alphabet)
    # for arbitrary motiflength:
    # left_reactants = motif_concentration_trajectory_array.at[(slice(None),)+(slice(None),)*(motiflength-1)+(0,)]
    # right_reactants = motif_concentration_trajectory_array.at[(slice(None),)+(0,)]
    # templates = motif_concentration_trajectory_array.at[(slice(None),)+(slice(None),)*(motiflength//2-2)+(slice(None),slice(1,None))]
    # collisions = jnp.zeros((nol+1,)*(motiflength-2)+(nol,nol)+(nol+1,)*(motiflength-2)+(nol+1,)+(nol))
    # for strandlength in range(1,motiflength-1):
    # ...
    logc = jnp.zeros((len(jnp.asarray(motif_concentration_trajectory_times_array)),)+(nol+1,)*motiflength)
    if not concentrations_are_logarithmised:
        motif_concentration_trajectory_array = motif_concentration_trajectory_array.at[motif_concentration_trajectory_array<pseudo_count_concentration].set(pseudo_count_concentration)
        logc = logc.at[:,:,1:,:,:].set(jnp.log(motif_concentration_trajectory_array))
        concentrations_are_logarithmised = True
    else:
        logc = logc.at[:,:,1:,:,:].set(motif_concentration_trajectory_array)
    if not isinstance(collision_rate_constants_array,(jax.Array,list)):
        collision_rate_constants_array = collision_rate_constants_array*jnp.ones((nol+1,)*(2*motiflength))

    collisions = jnp.array([[
        compute_motif_extensions(
            jnp.asarray(logc)[ii],#logc or c
            basic_rate_constants = jnp.asarray(collision_rate_constants_array),
            motiflength = motiflength,
            number_of_letters = len(alphabet)
            )[:,1:,1:,:,:,1:,1:,:].reshape(-1)
         ] for ii in range(len(motif_concentration_trajectory_times_array))])

    collisions = collisions.reshape(collisions.shape[0],-1)
    collisions = jnp.trapezoid(
        collisions,
        x=motif_concentration_trajectory_times_array,
        axis=0
        )
    # collisions_= collisions.reshape()
    return collisions
