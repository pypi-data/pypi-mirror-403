import nifty8 as ift
import numpy as np

from functools import reduce

from ..obj.units import make_unit, Unit

def TimeSpace(times : np.ndarray,
              units : Unit):
    times = np.asarray(times)
    if isinstance(times,(float,np.float64,int)) or times.shape[0]<=1:
        return UnstructuredTimeDomain(1, make_unit(units))
    if isinstance(times,list) and not isinstance(times[0],(float,int)):
        raise ValueError("times needs to be 1d-array")
    elif len(times.shape) != 1:
        raise ValueError("times needs to be 1d-array")
    distances = np.diff(times)
    if np.all(distances==distances[0]):
        time_space = TimeRGSpace(times.shape, make_unit(units), distances=distances[0])
    else:
        time_space = UnstructuredTimeDomain(times.shape, make_unit(units))
    return time_space


def isinstance_timespace(obj)->bool:
    if isinstance(obj,ift.DomainTuple):
        obj = obj[0]
    if not 'units' in dir(obj):
        print("Units not specified")
        return False
    if not (isinstance(obj, TimeRGSpace) or isinstance(obj,UnstructuredTimeDomain)):
        print('not RGSpace or UnstructuredDomain')
        return False
    return True

def are_compatible_timespaces(ts1 : object,
                              ts2 : object
                              )->bool:
    if isinstance(ts1,ift.DomainTuple):
        ts1 = ts1[0]
    if isinstance(ts2,ift.DomainTuple):
        ts2 = ts2[0]
    if not isinstance_timespace(ts1):
        print('Object is not a TimeSpace')
        return False
    if not isinstance_timespace(ts2):
        print('Object is not a TimeSpace')
        return False
    if ts1.units != ts2.units:
        print('times vectors have different units: {}'.format(ts1.units) + ' and {}'.format(ts2.units))
        return False
    if ts1!=ts2:
        print('DomainMismatch')
        return False
    return True

class TimeRGSpace(ift.RGSpace):
    """
    RGSpace for time
    """
    _needed_for_hash = ['_rdistances','_shape','_harmonic']
    def __init__(self, shape, units, distances):
        self._units = make_unit(units)
        self._harmonic = False
        if np.isscalar(shape):
            shape = (shape,)
        self._shape = tuple(int(i) for i in shape)
        if min(self._shape) < 0:
            raise ValueError('Negative number of pixels encountered')
        #
        self._rdistances = (float(distances),) * len(self._shape)
        self._hdistances = tuple(
            1. / (np.array(self.shape)*np.array(self._rdistances)))
        #
        self._dvol = float(reduce(lambda x, y: x*y, self.distances))
        self._size = int(reduce(lambda x, y: x*y, self._shape))

    @property
    def units(self):
        return self._units

class UnstructuredTimeDomain(ift.UnstructuredDomain):
    """
    UnstructuredDomain for time
    """
    _needed_for_hash = ['_shape']
    def __init__(self, shape, units):
        self._units = make_unit(units)
        try:
            self._shape = tuple([int(i) for i in shape])
        except TypeError:
            self._shape = (int(shape), )

    @property
    def units(self):
        return self._units
