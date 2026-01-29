import numpy as np
from ..obj.motif_trajectory import MotifTrajectory
from ..domains.motif_space import _motif_categories

def mean_length(
        motif_trajectory : MotifTrajectory
    ):
    motif_groups = _motif_categories()
    mean_length = np.zeros(motif_trajectory.times.shape)
    total_number_of_strands = np.zeros(motif_trajectory.times.shape)
    for length in range(1,motif_trajectory.motiflength-1):
        strand_category = motif_groups[0].format(length)
        number_of_strands = np.sum(
            motif_trajectory.motifs.val[strand_category].reshape(motif_trajectory.times.shape+(-1,)),
            axis=-1
        )
        mean_length += length*number_of_strands
        total_number_of_strands += number_of_strands
    # beginnings_concentration
    number_of_strands = np.sum(
        motif_trajectory.motifs[motif_groups[-3]].val.reshape(motif_trajectory.times.shape+(-1,)),
        axis=-1
    )
    mean_length += number_of_strands
    total_number_of_strands += number_of_strands
    # continuations
    mean_length += np.sum(
        motif_trajectory.motifs[motif_groups[-2]].val.reshape(motif_trajectory.times.shape+(-1,)),
        axis=-1
    )
    # ends_concentration
    mean_length += (motif_trajectory.motiflength-2)*np.sum(
        motif_trajectory.motifs[motif_groups[-1]].val.reshape(motif_trajectory.times.shape+(-1,)),
        axis=-1
    )
    return mean_length/total_number_of_strands
