import jax.numpy as jnp
from jax.experimental import sparse
from itertools import product as iterprod

from .motif_production_transition_kernel import _hybridization_site_categories


def motif_production_rate_constants_extension_matrix(
        number_of_letters : int = 2,
        motiflength : int = 4,
        hybridization_length_max : int = 4
        ) -> sparse.BCOO:
    """
    generates a matrix as jax.experimental.sparse.BCOO matrix
    that transforms hybridization site formated vectors into collision format.

    Parameters:
    -----------
    number_of_letters : int
        default : 2
    motiflength : int
        default : 4
    hybridization_length_max : int
        default : 4
    """
    raise NotImplementedError("motif_production_rate_constants_extension_matrix is under construction")
    hybridization_site_caterories, hybridization_configuration_indices = _hybridization_site_categories(number_of_letters, hybridization_length_max)
    motif_indices = jnp.concatenate([jnp.zeros(1),jnp.cumsum(number_of_letters**jnp.arange(1,motiflength+1)),jnp.array([jnp.sum(number_of_letters**jnp.arange(1,motiflength+1))+number_of_letters**(motiflength-1)])],dtype=int)
    template_indices = (motif_indices-motif_indices[1]).at[0].set(0)
    number_of_left_reactants = number_of_right_reactants = int(motif_indices[-3])
    number_of_templates = int(template_indices[-1])
    mprcem_shape = (number_of_left_reactants,number_of_right_reactants, number_of_templates, hybridization_configuration_indices[-1])
    motif_production_rate_constants_extension_matrx = sparse.BCOO((jnp.array([0]),jnp.array([[0]*len(mprcem_shape)])),shape=mprcem_shape)
    for a_index in range(len(hybridization_site_caterories)):
        a = hybridization_site_caterories[a_index]
        left_shift = a[-1]
        left_ligant_length = a[1]
        right_ligant_length = a[2]
        template_length = a[3]
        right_shift = left_shift + right_ligant_length + left_ligant_length - template_length
        if left_shift==-1:
            left_ligant_lengths = jnp.arange(a[1],motiflength)
            # blunt end gets extended iff hybridization_length=hybridization_length_max and the ligation spot is at the center or further apart.
            # for the other part of the complex, the same rules apply as for every hybridization_length: for a dangling end, the dangling strand/motif can be extended
            # for a blunt ent that is close to the ligation spot, the complex is supposed to end there
            # This way, we only extend blunt ends on both sides, if the ligation_spot is at the center
            # If hybridization_length_max is uneven, the right central ligation spot is treated as the center,
            # so the center is at hybridization_length_max-hybridization_length_max//2 from the left side and hybridization_lengh_max//2 from the right side apart 
        elif (a[0]==hybridization_length_max) and (left_shift==0) and (a[1]>=hybridization_length_max-hybridization_length_max//2):
            # continue left ligant
            left_ligant_lengths = jnp.arange(a[1],motiflength)
        else:
            left_ligant_lengths = [a[1]]
        if right_shift==1:
            right_ligant_lengths = jnp.arange(a[2],motiflength)
        elif (a[0]==hybridization_length_max) and (right_shift==0) and (a[2]>=hybridization_length_max//2):
            right_ligant_lengths = jnp.arange(a[2],motiflength)
        else:
            right_ligant_lengths = [a[2]]
        template_might_continue_forwards = (left_shift==1) or ((a[0]==hybridization_length_max) and (left_shift==0))
        template_might_continue_backwards = (right_shift==-1) or ((a[0]==hybridization_length_max) and (right_shift==0))
        template_might_continue_both_ways = (template_might_continue_forwards and template_might_continue_backwards)
        if template_might_continue_both_ways:
            template_overhangs = jnp.arange(motiflength-a[3])
        elif template_might_continue_forwards: #(but not backwards)
            template_overhangs = jnp.arange(motiflength-a[3])
        else:
            template_overhangs = jnp.arange(1)
        for left_ligant_length, right_ligant_length, template_overhang in iterprod(left_ligant_lengths, right_ligant_lengths, template_overhangs):
            if template_overhang+a[3] == motiflength:
                template_lengths = jnp.array([motiflength])
            elif template_might_continue_backwards or template_might_continue_forwards:
                template_lengths = jnp.arange(a[3]+template_overhang, motiflength)
            else:
                template_lengths = jnp.array([a[3]+template_overhang])
            for template_length in template_lengths:
                if (template_length == (motiflength-1)) and template_might_continue_backwards and not template_might_continue_forwards:
                    template_index_start = template_indices[-1-1]
                else:
                    template_index_start = template_indices[template_length-1]

                matrix_indices = [
                        (il*number_of_letters**(a[1])+i1+motif_indices[left_ligant_length-1],
                         i2*number_of_letters**(right_ligant_length-a[2])+ir+motif_indices[right_ligant_length-1],
                         int(itc*number_of_letters**(template_overhang+a[3])+i3*number_of_letters**(template_overhang)+io+template_index_start),
                         int(i1*number_of_letters**(a[2]+a[3])+i2*number_of_letters**a[3]+i3+hybridization_configuration_indices[a_index]))
                        for i1,i2,i3 in iterprod(
                            range(number_of_letters**a[1]),
                            range(number_of_letters**a[2]),
                            range(number_of_letters**a[3])
                            )
                        for il,ir,io,itc in iterprod(
                            range(number_of_letters**int(left_ligant_length-a[1])),
                            range(number_of_letters**int(right_ligant_length-a[2])),
                            range(number_of_letters**int(template_overhang)),
                            range(number_of_letters**int(template_length-template_overhang-a[3])))
                        ]
                motif_production_rate_constants_extension_matrx = motif_production_rate_constants_extension_matrx + sparse.BCOO((jnp.array([1]*len(matrix_indices)),matrix_indices),shape=(mprcem_shape))
    return motif_production_rate_constants_extension_matrx
