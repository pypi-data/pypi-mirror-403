import nifty8 as ift
from typing import Union

from .time_space import TimeSpace, TimeRGSpace, UnstructuredTimeDomain

def TrajectorySpace(motif_space : Union[ift.MultiDomain, ift.DomainTuple, ift.Domain],
                    time_space : Union[TimeRGSpace,UnstructuredTimeDomain]) -> ift.MultiField:
    while isinstance(motif_space, ift.DomainTuple):
        motif_space = motif_space[0]
    while isinstance(time_space, ift.DomainTuple):
        time_space = time_space[0]
    trajectory_space = {}
    for key in motif_space.keys():
        ms = motif_space[key]
        if isinstance(ms, ift.DomainTuple):
            ms = tuple([mm for mm in ms])
        else:
            ms = (ms,)
        trajectory_space[key] = ift.DomainTuple.make((time_space,)+ms)
    return ift.MultiDomain.make(trajectory_space)
