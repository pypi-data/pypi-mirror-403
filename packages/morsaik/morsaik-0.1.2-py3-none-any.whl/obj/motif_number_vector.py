from .motif_vector import MotifVector
from .units import make_unit

def MotifNumberVector(motiflength : int,
                      alphabet : str):
    unit = make_unit('particles')
    return MotifVector(motiflength, alphabet, unit)
