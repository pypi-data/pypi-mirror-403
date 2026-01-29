from ..obj.motif_vector import MotifVector
from ..obj.motif_trajectory import MotifTrajectory

from ..domains.motif_space import _motif_categories

import jax.numpy as jnp

def total_mass(
        motif_vector : MotifVector
        ) -> jnp.ndarray:
    """
    Parameters:
    -----------
    motif_vector : MotifVector

    Returns:
    --------
    total_mass : jnp.ndarray
    """
    motif_categories = _motif_categories()
    total_mass = 0
    for strandlength in range(1,motif_vector.motiflength-1):
        total_mass += strandlength*jnp.sum(motif_vector.motifs.val[motif_categories[0].format(strandlength)])
    total_mass += jnp.sum(motif_vector.motifs.val[motif_categories[-3]].flatten())
    total_mass += jnp.sum(motif_vector.motifs.val[motif_categories[-1]].flatten())*(motif_vector.motiflength-2)
    total_mass += jnp.sum(motif_vector.motifs.val[motif_categories[-2]].flatten())
    return total_mass

def total_mass_of_motif_concentration_trajectory_array(
        motif_concentration_trajectory_array : jnp.ndarray,
        number_of_letters : int = 4,
        motiflength : int = 4
        ) -> jnp.ndarray:
    strandmasses = jnp.concatenate([jnp.array([strandlength,]*(number_of_letters**strandlength)) for strandlength in range(1,motiflength-1)] + [jnp.array([1,]*(number_of_letters**(motiflength-1)))] + [jnp.array([1,]*(number_of_letters**(motiflength)))] + [jnp.array([motiflength-2,]*(number_of_letters**(motiflength-1)))])
    return jnp.vecdot(strandmasses[None], motif_concentration_trajectory_array, axis=1)

def total_mass_trajectory(
        motif_trajectory : MotifTrajectory
        ) -> jnp.ndarray:
    motif_categories = _motif_categories()
    total_mass_trajectory = jnp.zeros(motif_trajectory.times.size)
    for strandlength in range(1,motif_trajectory.motiflength-1):
        strand_mass_trajectory = strandlength*jnp.sum(
                motif_trajectory.motifs.val[motif_categories[0].format(strandlength)].reshape(motif_trajectory.times.size,-1),
                axis=-1)
        total_mass_trajectory = total_mass_trajectory.at[:].add(strand_mass_trajectory)
    # beginnings
    strand_mass_trajectory = jnp.sum(
            motif_trajectory.motifs.val[motif_categories[-3]].reshape(motif_trajectory.times.size,-1),
            axis=-1
            )
    total_mass_trajectory = total_mass_trajectory.at[:].add(strand_mass_trajectory)
    # continuations
    strand_mass_trajectory = jnp.sum(
            motif_trajectory.motifs.val[motif_categories[-2]].reshape(motif_trajectory.times.size,-1),
            axis=-1
            )
    total_mass_trajectory = total_mass_trajectory.at[:].add(strand_mass_trajectory)
    # endings
    strand_mass_trajectory = jnp.sum(
            motif_trajectory.motifs.val[motif_categories[-1]].reshape(motif_trajectory.times.size,-1),
            axis=-1
            )
    total_mass_trajectory = total_mass_trajectory.at[:].add((motif_trajectory.motiflength-2)*strand_mass_trajectory)
    return total_mass_trajectory
