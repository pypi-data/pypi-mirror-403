import nifty8 as ift
import numpy as np

from ..obj.units import make_unit, Unit

from ..domains.time_space import TimeSpace, are_compatible_timespaces, isinstance_timespace

def TimesVector(times : np.ndarray,
                units : Unit
                ) -> ift.Field:
    return ift.Field(ift.DomainTuple.make(TimeSpace(times, units)),
                     times)

def isinstance_times_vector(obj)->bool:
    if not isinstance(obj,ift.Field):
        print("Not a NIFTy-Field")
        return False
    if not isinstance_timespace(obj.domain):
        print('Domain is not a TimeSpace.')
        return False
    return True

def are_compatible_times_vectors(timesvector1 : TimesVector,
                                 timesvector2 : TimesVector
                                 ) -> bool:
    if not isinstance_times_vector(timesvector1):
        print('Object is not a TimesVector')
        return False
    if not isinstance_times_vector(timesvector2):
        print('Object is not a TimesVector')
        return False
    if not are_compatible_timespaces(timesvector1.domain, timesvector2.domain):
        return False
    return True
