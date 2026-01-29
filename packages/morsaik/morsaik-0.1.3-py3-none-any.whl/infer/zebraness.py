import numpy as np

from ..obj.motif_trajectory import MotifTrajectory, _motif_trajectory_as_array

def system_level_motif_zebraness(
        motif_trajectory : MotifTrajectory,
        axis=0
    ) -> np.ndarray:
    c, _ = _motif_trajectory_as_array(motif_trajectory)
    shape = c.shape
    if axis == 0:
        c = c.reshape((1,)+shape)
    if axis > 1:
        raise NotImplementedError("compute_system_level_motif_zebraness so for only defined for maximum first axis being time axis or static motif concentration vector")
    shape = c.shape
    if shape[1]>3:
        raise NotImplementedError("Zebraness only defined for binary alphabet.")
    if len(shape)!=5:
        raise NotImplementedError("Zebraness only implemented for four-letter motifs.")
    number_of_timesteps = shape[0]

    concentration_of_zebra_ligations = np.zeros(number_of_timesteps)
    concentration_of_zebra_ligations += np.sum(c[:,:,-2,-1,:].reshape((number_of_timesteps,-1)), axis =1)
    concentration_of_zebra_ligations += np.sum(c[:,:,-1,-2,:].reshape((number_of_timesteps,-1)), axis=1)

    concentration_of_ligations_in_total = np.zeros(number_of_timesteps)
    concentration_of_ligations_in_total += np.sum(
                c[:,:,-2:,-2:,:].reshape((number_of_timesteps,-1)),
                axis=1
                )

    return concentration_of_zebra_ligations/concentration_of_ligations_in_total

def individual_motif_zebraness(c):
    shape = c.shape
    if len(shape)==4:
        c = c.reshape((-1,)+shape)
    if shape[1]>3:
        raise NotImplementedError("Zebraness only defined for binary alphabet.")
    if len(shape)!=5:
        raise NotImplementedError("Zebraness only implemented for four-letter motifs.")
    # Monomers don't have zebraness
    z = np.zeros(shape)
    # Zebraness of first binary motif
    z[:,-1,-2,-2:,:]+=1
    z[:,-2,-1,-2:,:]+=1
    # Zebraness of second binary motif
    z[:,:,-1,-2,:]+=1
    z[:,:,-2,-1,:]+=1
    # Zebraness of last binary motif
    z[:,:,-2:,-1,-2]+=1
    z[:,:,-2:,-2,-1]+=1
    # multiply by length
    y = np.zeros(shape)
    y[:,0,-2:,-2:,0] = 1.
    y[:,0,-2:,-2:,-2:] = 2.
    y[:,-2:,-2:,-2:,0] = 2.
    y[:,-2:,-2:,-2:,-2:] = 3.
    return z/y
