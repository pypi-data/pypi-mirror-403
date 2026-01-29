import numpy as np

def unzero(x, shift=1.e-12, shiftmode = 'relmin'):
    """
    function that returns an array with shift for all zero values of input array x.

    Parameters
    ----------
    x : array
    shift : float, optional
    shiftmode : string, optional
        options are 'relmin', 'relmax', 'abs'
        standing for shifting the array by
        'relmin': the minimum of x time shift
        'relmax': the maximum of x time shift
        'abs': the shift absolutely
    """
    if shiftmode == 'relmin':
        if len(x[x!=0]) == 0:
            print("Unzeroed array is completely zero.")
        else:
            print("Minimum value of unzeroed array is {}".format(np.min(x[x!=0])))
            shift = np.min(x[x!=0])*shift
    elif shiftmode == 'relmax':
        if len(x[x!=0]) == 0:
            print("Unzeroed array is completely zero.")
        else:
            print("Maximum value of unzeroed array is {}".format(np.max(x[x!=0])))
            shift = np.max(x[x!=0])*shift
    elif shiftmode == 'abs':
        shift = shift
    else:
        raise NotImplementedError("shift mode = '{}' is not implemented".format(shiftmode))
    rtrn = np.zeros(x.shape)
    rtrn[x==0.] += shift
    return rtrn
