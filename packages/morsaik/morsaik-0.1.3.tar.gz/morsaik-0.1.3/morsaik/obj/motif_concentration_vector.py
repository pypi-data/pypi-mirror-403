from .motif_vector import MotifVector
from .units import make_unit

def MotifConcentrationVector(motiflength : int,
                      alphabet : str):
    unit = make_unit('mol')/make_unit('L')
    return MotifVector(motiflength, alphabet, unit)
