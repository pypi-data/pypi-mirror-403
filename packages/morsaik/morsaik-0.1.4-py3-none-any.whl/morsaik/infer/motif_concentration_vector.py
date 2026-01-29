from ..obj.motif_concentration_vector import MotifConcentrationVector
from ..obj.motif_number_vector import MotifNumberVector
from ..obj.motif_vector import _motif_vector_as_array, _array_to_motif_vector_dct

def motif_concentration_vector_from_motif_number_vector(
        motif_number_vector : MotifNumberVector,
        c_ref : float
        ) -> MotifConcentrationVector:
    """
    transform a motif number vector intro motif concentration vector

    Parameters:
    -----------
    motif_number_vector : MotifNumberVector
    c_ref : float
        reference concentration of monomers with the first letter

    Returns:
    --------
    moif_concentration_vector : MotifConcentrationVector
    """
    motif_concentration_vector = MotifConcentrationVector(motif_number_vector.motiflength,motif_number_vector.alphabet)
    single_particle_concentration = c_ref/motif_number_vector.motifs['length1strand'][0]
    motif_concentration_array = single_particle_concentration*_motif_vector_as_array(motif_number_vector)
    return motif_concentration_vector(_array_to_motif_vector_dct(motif_concentration_array))
