import morsaik as kdi
import numpy as np
import nifty8 as ift

def test_times_vector():
    times = np.arange(128)
    times_vector = kdi.TimesVector(times, 's')
    assert(times_vector.domain==ift.DomainTuple.make(kdi.domains.TimeSpace(times,'s')))
    assert(times_vector.domain[0].units==kdi.make_unit('s'))
    times = np.copy(times)
    times[-64:]*=10
    times_vector1 = kdi.TimesVector(times,'s')
    assert(times_vector1.domain==ift.DomainTuple.make(kdi.domains.TimeSpace(times, 's')))
    assert(times_vector1.domain[0].units==kdi.make_unit('s'))
    assert(kdi.are_compatible_times_vectors(times_vector1,times_vector1))
    times_vector2 = kdi.TimesVector(times,kdi.make_unit('ms'))
    assert(not kdi.are_compatible_times_vectors(times_vector,times_vector1))
    assert(not kdi.are_compatible_times_vectors(times_vector,times_vector2))

