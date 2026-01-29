import nifty8 as ift
import numpy as np

from ..obj.motif_vector import isinstance_motifvector
from ..obj.motif_production_vector import isinstance_motifproductionvector

from ..domains.trajectory_space import TrajectorySpace

def transform_dicts_to_field(motifs : list,
                             time_space : ift.DomainTuple
                             ) -> ift.MultiField:
    trajectory_domain = TrajectorySpace(motifs[0].domain, time_space)
    field = {}
    for key in motifs[0].keys():
        #np.zeros(time_space.shape+motif_list[0].motifs[key].shape)
        field[key] = np.asarray([motifs[ii][key].val for ii in range(len(motifs))])
        field[key] = ift.Field(
            trajectory_domain[key],
            field[key]
            )
    return ift.MultiField.from_dict(field, domain=trajectory_domain)

def transform_vectors_to_field(motif_list : list,
                                  time_space : ift.DomainTuple) -> ift.MultiField:
    if isinstance_motifvector(motif_list[0], print_statements = False):
        motifs = [motif_list[ii].motifs for ii in range(len(motif_list))]
    elif isinstance_motifproductionvector(motif_list[0]):
        motifs = [motif_list[ii].productions for ii in range(len(motif_list))]
    #elif isinstance_motifbreakagevector(motif_list[0]):
    #    motifs = [motif_list[ii].breakages for ii in range(len(motif_list))]
    else:
        raise TypeError("motif_list needs to be MotifTrajectory or MotifProductionTrajectory")
    return transform_dicts_to_field(motifs, time_space)
