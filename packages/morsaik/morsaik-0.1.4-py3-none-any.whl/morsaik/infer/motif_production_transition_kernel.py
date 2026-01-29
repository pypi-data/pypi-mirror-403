import jax.numpy as jnp
import jax
from itertools import product as iterprod
from jax.experimental import sparse

def _hybridization_site_categories(
        number_of_letters : int = 2,
        hybridization_length_max : int = 4
        ) -> list[tuple[int]]:
    """
    returns all possible hybridization site categories for a given
    number of letters and maximum hybridization length
    in terms of the lenght of the hybridization site, the length of the left, right and template reactant and the shift (overhang) of the left strand vs the template strand.

    Parameters:
    -----------
    hybridization_length_max : int

    Returns:
    --------
    hybridization_site_categories : list[tuple[int]]
        hybridization_length, left_ligant_length, right_ligant_length, template_length, shift_length
    """
    hybridization_site_categories = []
    for hybridization_length in range(2,hybridization_length_max+1):
        for left_ligant_length in range(1, hybridization_length):
            for right_ligant_length in range(max(1,hybridization_length-left_ligant_length-(hybridization_length>2)-(hybridization_length>3)),hybridization_length-left_ligant_length+1):
                for template_length in range(max(hybridization_length-(hybridization_length>2)-(hybridization_length>3),2*hybridization_length-(hybridization_length>2)-(hybridization_length>3)-right_ligant_length-left_ligant_length),hybridization_length+1):
                    for shift_length in range(-1,2):
                        if left_ligant_length==1 and shift_length <0:
                            continue
                        if right_ligant_length==1 and shift_length+right_ligant_length+left_ligant_length-template_length>0:
                            continue
                        if (hybridization_length==(left_ligant_length+right_ligant_length+(shift_length==1)+(shift_length==template_length-right_ligant_length-left_ligant_length-1))) and (hybridization_length==template_length+(shift_length==-1)+(shift_length+right_ligant_length+left_ligant_length-template_length==1)):
                            hybridization_site_categories += [(hybridization_length,left_ligant_length,right_ligant_length,template_length,shift_length)]
    number_hybridization_configurations = [number_of_letters**(hybridization_site_category[1]+hybridization_site_category[2]+hybridization_site_category[3]) for hybridization_site_category in hybridization_site_categories]
    hybridization_configuration_indices = jnp.cumsum(jnp.array([0]+number_hybridization_configurations))
    return hybridization_site_categories, hybridization_configuration_indices

def print_hybridization_site_categories(hybridization_length_max : int = 4):
    hybridization_site_categories = _hybridization_site_categories(hybridization_length_max)
    for hybridization_site_category in hybridization_site_categories:
        print('\n'+'0'*hybridization_site_category[0]+f"{hybridization_site_category[0]}")
        print('0'*(hybridization_site_category[-1]==1)+'L'*hybridization_site_category[1]+'|'+'R'*hybridization_site_category[2])
        print('0'*(hybridization_site_category[-1]==-1)+'T'*(hybridization_site_category[1]+a[-1])+'-'+'T'*(hybridization_site_category[3]-hybridization_site_category[1]-hybridization_site_category[-1]))
        print(hybridization_site_category)

def _extend_motif_production_rate_constants_array_to_collisions_format(
        motif_production_rate_constants : jax.Array,
        maximum_ligation_window_length : int = 4,
        motiflength : int = 4,
        number_of_letters : int = 4
        ) -> jax.Array:
    """
    The motif_production_rate_constants are categorized by the ligation windows.
    For the transition kernal they first need to be extended to the shape of the ligation_sites,
    which means a degeneracy, i.e. all ligation_sites with the same ligation window get the same contribution.

    In principle, there are the following different ligation windows:
    ((0,0),(0,0)); ((0,1:),(0,0)); ((1:,0),(0,0)); ((0,0),(0,1:));((0,0),(1:,0));((0,0),(1:,1:));((1:,0),(1:,0));((0,1:),(0,1:)),((1:,1:),(0,0))
    for ligation_window_length<=maximum_ligation_window_length
    Ligation windows of ligation_window_length=maximum_ligation_window_length, we additionally have
    ((1:,1:),(0,1:));((1:,1:),(1:,0));((1:,0),(1:,1:);((0,1:),(1:,1:));((1:,1:),(1:,1:))
    """
    if maximum_ligation_window_length <4:
        ligation_window_lengths = [1]
        raise NotImplementedError("Only implemented for ligation window length greater than 4 so far.")
    else:
        ligation_window_lengths = range(4,maximum_ligation_window_length+1)
    number_of_motifs = jnp.concatenate((number_of_letters**jnp.arange(1,motiflength+1),jnp.array([number_of_letters**(motiflength-1)])))
    number_of_strands = number_of_motifs[:-3]
    number_of_beginnings = number_of_motifs[-3]
    number_of_continuations = number_of_motifs[-2]
    number_of_ends = number_of_motifs[-1]

    reactant_indices = jnp.concatenate((jnp.zeros(1),jnp.cumsum(number_of_letters**jnp.arange(1,motiflength+1))), dtype=int)
    template_indices = jnp.concatenate((jnp.zeros(2),jnp.cumsum(jnp.concatenate((number_of_letters**jnp.arange(2,motiflength+1),jnp.array([number_of_letters**(motiflength-1)]))))),dtype=int)
    ligation_spot_formations = jnp.zeros((jnp.sum(number_of_strands)+number_of_ends,jnp.sum(number_of_strands)+number_of_beginnings,jnp.sum(number_of_strands[1:])+number_of_beginnings+number_of_continuations+number_of_ends))

    for ligation_window_length in ligation_window_lengths:
        for ligation_spot in range(1,ligation_window_length-2):
            for g1,g2,g3,g4 in iterprod([0,1],repeat=4):
                if ligation_window_length != maximum_ligation_window_length:
                    if (g2,g3)==(1,1) or (g1,g4)==(1,1):
                        continue
                if g1 == 0:
                    # length-{ligation_spot}-strand
                    left_strandlength = ligation_spot
                    left_ligs_slices = [(slice(reactant_indices[left_strandlength-1],reactant_indices[left_strandlength]),)]
                    left_prods_slices = [
                            (0,) + (slice(None),)*int(left_strandlength)
                            ]
                    left_prods_zeros_shapes = [
                            (number_of_letters,)*int(left_strandlength)
                            ]
                    left_prods_zeros_reshapes = [
                            (number_of_letters**left_strandlength,)
                            ]
                    """
                    number_of_strands[ligation_spot]
                    left_indices = [slice(
                            jnp.sum(number_of_strands[:ligation_spot])-1,
                            jnp.sum(number_of_strands[:ligation_spot]) + number_of_strands[ligation_spot])
                            ]
                    """
                else:
                    # [strand[ii] for ii in range(ligation_spot+1,motiflength-1)] + ['end']
                    left_strandlengths = jnp.arange(ligation_spot+1,motiflength)
                    left_ligs_slices = [
                            (slice(reactant_indices[left_strandlength-1],reactant_indices[left_strandlength]),)
                            for  left_strandlength in left_strandlengths
                            ]
                    left_prods_slices = [
                        (None,)*int(left_strandlength-ligation_spot-1)
                        + (slice(1,None),)
                        + (slice(None),)*int(ligation_spot)
                        for left_strandlength in left_strandlengths
                    ]
                    left_prods_zeros_shapes = [
                            (number_of_letters,)*int(left_strandlength)
                            for left_strandlength in left_strandlengths
                            ]
                    left_prods_zeros_reshapes = [
                        (number_of_letters**left_strandlength,)
                        for left_strandlength in left_strandlengths
                    ]
                    # left_indices_collisions = [(number_of_letters,)*(motiflength-ligation_spot-2)+(slice(number_of_letters**(ligation_spot+1)),) for strandlength in range(ligation_spot,motiflength)]
                    """
                    left_indices_collisions_shapes = [(number_of_letters,)*strandlength for strandlength in range(ligation_spot, motiflength)]
                    left_indices_collisions_indices = [slice(
                        jnp.sum(number_of_letters**jnp.arange(1,strandlength)),
                        jnp.sum(number_of_letters**jnp.arange(1,strandlength+1)),
                        ) for strandlength in range(ligation_spot, motiflength)]
                    left_indices_productions = [(None,)*strandlength+(slice(number_of_letters**(ligation_spot+1)),) for strandlength in range(ligation_spot,motiflength)]#(motiflength-ligation_spot-2)
                    ligation_spot_formations[left_indices_collisions_indices,right_indices_collisions_indices,template_indices_collisions_indices].reshape(left_indices_collisions_shapes+right_indices_collisions_shapes,template_indices_collisions_shapes) = motif_production_rate_constants[left_indices_productions]
                    left_indices = [
                            slice(jnp.sum(number_of_strands[:ligation_spot])-1),None)
                            ]
                    collisions_format[left_indices_collisions] = motif_production_rate_constants[left_indices_productions]
                    """
                if g2 == 0:
                    # [strand[ligation_window_length-ls-2]]
                    right_strandlength = int(ligation_window_length-ligation_spot-2)
                    right_ligs_slices = [
                            (slice(reactant_indices[right_strandlength-1],reactant_indices[right_strandlength]),)
                            ]
                    right_prods_zeros_shapes = [(number_of_letters,)*int(right_strandlength)]
                    right_prods_zeros_reshapes = [(number_of_letters**right_strandlength,)]
                    right_prods_slices = [
                            (slice(None),)*right_strandlength+(0,)
                            ]
                else:
                    # right_categories = [strand[ii] for ii in range(ligation_window_length-ls-1,motiflength-1)] + ['beginning']
                    right_strandlengths = jnp.arange(ligation_window_length-ligation_spot-1,motiflength-1)
                    right_ligs_slices = [
                            (slice(reactant_indices[right_strandlength-1],reactant_indices[right_strandlength]),)
                            for right_strandlength in right_strandlengths
                            ]
                    right_prods_zeros_shapes = [(number_of_letters,)*int(right_strandlength) for right_strandlength in right_strandlengths]
                    right_prods_zeros_reshapes = [(number_of_letters**int(right_strandlength),) for right_strandlength in right_strandlengths]
                    right_prods_slices = [
                            (slice(None),)*int(ligation_window_length-ligation_spot-2)
                            + (slice(1,None),)
                            +(None,)*int(right_strandlength-(ligation_window_length-ligation_spot-2)-1)
                            for right_strandlength in right_strandlengths
                            ]
                if (g3,g4) == (0,0):
                    # template_category = strand[ligation_window_length-2]
                    template_strandlength = ligation_window_length-2
                    template_ligs_slices = [
                        (slice(template_indices[template_strandlength-1],template_indices[template_strandlength]),)
                    ]
                    template_prods_zeros_shapes = [(number_of_letters,)*(template_strandlength)]
                    template_prods_zeros_reshapes = [(number_of_letters**template_strandlength,)]
                    template_prods_slices = [
                            (0,)*(1-g3)
                            + (slice(None),)*int(ligation_window_length-2)
                            + (0,)*(1-g4)
                    ]
                elif (g3,g4) == (0,1):
                    # template_category = [strand[ii] for ii in range(ligation_window_length-1,motiflength-1)] + ['beginning']
                    template_strandlengths = jnp.arange(ligation_window_length-1,motiflength)
                    template_ligs_slices = [
                            (slice(template_indices[template_strandlength-1],template_indices[template_strandlength]),)
                            for template_strandlength in template_strandlengths
                            ]
                    template_prods_zeros_shapes = [(number_of_letters,)*int(template_strandlength) for template_strandlength in template_strandlengths]
                    template_prods_zeros_reshapes = [(number_of_letters**template_strandlength,) for template_strandlength in template_strandlengths]
                    template_prods_slices = [
                            (0,)*(1-g3)
                            + (slice(None),)*int(ligation_window_length-2)
                            + (0,)*(1-g4) + (slice(1,None),)*g4
                    ]
                elif (g3,g4) == (1,0):
                    # template_category = [strand[ii] for ii in range(ligation_window_length-1,motiflength-1)] + ['end']
                    template_strandlengths = jnp.arange(ligation_window_length-1,motiflength)
                    template_ligs_slices = [
                        (slice(template_indices[template_strandlength-1],template_indices[template_strandlength]),)
                        for template_strandlength in template_strandlengths
                        ]
                    template_ligs_slices[-1] = (slice(template_indices[-2],template_indices[-1]),)
                    template_prods_zeros_shapes = [(number_of_letters,)*int(template_strandlength) for template_strandlength in template_strandlengths]
                    template_prods_zeros_reshapes = [(number_of_letters**template_strandlength,) for template_strandlength in template_strandlengths]
                    template_prods_slices = [
                            (None,)*int(template_strandlength-ligation_window_length)
                            + (slice(1,None),)
                            + (slice(None),)*int(ligation_window_length-2)
                            + (0,)
                            for template_strandlength in template_strandlengths
                            ]
                elif (g3,g4) == (1,1):
                    # template_category = [strand[ii] for ii in range(ligation_window_length,motiflength-2)] + ['continuation'] + (lw<maximum_ligation_window_length)*['beginning','end']
                    template_strandlengths = jnp.concatenate((jnp.arange(ligation_window_length,motiflength+1),)+(jnp.array([motiflength-1]),)*(ligation_window_length<motiflength))
                    template_ligs_slices = [
                            (slice(template_indices[template_length_index-1],template_indices[template_length_index]),)
                            for template_length_index in range(ligation_window_length, ligation_window_length+len(template_strandlengths))
                            for left_continuation in jnp.arange(0,template_strandlengths[template_length_index]-ligation_window_length+1)
                            ]
                    template_prods_zeros_shapes = [
                            (number_of_letters,)*int(template_strandlengths[template_length_index])
                            for template_length_index in range(ligation_window_length, ligation_window_length+len(template_strandlengths))
                            for left_continuation in jnp.arange(0,template_strandlengths[template_length_index]-ligation_window_length+1)
                            ]
                    template_prods_zeros_reshapes = [
                            (number_of_letters**int(template_strandlengths[template_length_index]),)
                            for template_length_index in range(ligation_window_length, ligation_window_length+len(template_strandlengths))
                            for left_continuation in jnp.arange(0,template_strandlengths[template_length_index]-ligation_window_length+1)
                    ]
                    template_prods_slices = [
                        (None,)*int(left_continuation)
                        + (slice(1,None),)
                        + (slice(None),)*int(ligation_window_length-2)
                        + (slice(1,None),)
                        + (None,)*int(template_strandlength-ligation_window_length-left_continuation)
                        for template_length_index in range(ligation_window_length, ligation_window_length+len(template_strandlengths))
                        for left_continuation in jnp.arange(0,template_strandlengths[template_length_index]-ligation_window_length+1)
                    ]
                left_reactant_indices = jnp.arange(len(left_ligs_slices))
                right_reactant_indices = jnp.arange(len(right_ligs_slices))
                template_catalyst_indices = jnp.arange(len(template_ligs_slices))
                for left_reactant_ii, right_reactant_ii, template_ii in iterprod(left_reactant_indices, right_reactant_indices, template_catalyst_indices):
                    ligation_spot_formations = ligation_spot_formations.at[left_ligs_slices[left_reactant_ii]+right_ligs_slices[right_reactant_ii]+template_ligs_slices[template_ii]].add(
                        (jnp.zeros(left_prods_zeros_shapes[left_reactant_ii] + right_prods_zeros_shapes[right_reactant_ii] + template_prods_zeros_shapes[template_ii])
                         + motif_production_rate_constants[left_prods_slices[left_reactant_ii]+right_prods_slices[right_reactant_ii]+template_prods_slices[template_ii]]).reshape(
                             left_prods_zeros_reshapes[left_reactant_ii] + right_prods_zeros_reshapes[right_reactant_ii] + template_prods_zeros_reshapes[template_ii]
                             )
                         )
    return ligation_spot_formations

def motif_production_transition_kernel_from_motif_production_rate_constants_array(
        motif_production_rate_constants : jax.Array,
        number_of_letters : int = 4,
        motiflength : int = 4,
        maximum_ligation_window_length : int = 4
        ) -> jax.Array:
    raise NotImplementedError("motif production transition kernel under construction")
    extended_motif_production_rate_constants = _extend_motif_production_rate_constants_array_to_collisions_format(motif_production_rate_constants, 
        maximum_ligation_window_length = maximum_ligation_window_length,
        motiflength = motiflength,
        number_of_letters = number_of_letters,)
    transition_matrix = motif_production_transition_kernel_matrix(
            number_of_letters,
            motiflength,
            maximum_ligation_window_length
            )
    return transition_matrix.reshape((transition_matrix.shape[0],-1)) @ extended_motif_production_rate_constants.flatten()

def motif_production_transition_kernel_matrix(
        number_of_letters : int = 4,
        motiflength : int = 4,
        maximum_ligation_window_length : int = 4
        ) -> jax.Array:
    """
    Motif productions are in the
    Third order Motif Collisions include all combinations of three motifs independent of their category.
    Ligation sites are a subclass third order motif collisions,
    where the first motif (the left or fore motif) is a strand or an ending,
    the second motif (right or rear motif) is a strand or a beginning
    and the third motif (the template) is a strand of at least length 2 or beginning, continuation or beginning.

    Motif Productions sights only need to consider the hybridization sight and eventual dangling ends.
    They are thus a subclass of ligation sites.
    Ligation Windows categorize the motif production sites.
    The ligation windows have the length of the hybridization sight plus 2 more nucleotides to cover dangling ends.
    The 'maximum_ligation_window_length' is maximally equal to the motiflength,
    as longer motifs, and thus longer hybridization sights are not tracked.
    The biggest ligation window has thus the 'maximum_ligation_window_length'.
    The biggest ligation window is the only one that can contain hybridization sights of length equal to the ligation window or one nucleotide less.
    In addition to the hybridization site, each ligation window also stores a number between 1 and the length of the hybridization site minus one that indicates the 'ligation_spot'.

    The motif_production_rate_constants are categorized by the ligation windows.
    For the transition kernal they first need to be extended to the shape of the ligation_sites,
    which means a degeneracy, i.e. all ligation_sites with the same ligation window get the same contribution.

    To set up the transition kernel,
    all reactants in the corresponding ligation_site get a negative contribution of the corresponding rate,
    all products get a positive contribution.

    Parameters:
    -----------
    motif_production_rate_constants : jax.Array
        The rate constants for the motif production
    number_of_letters : int
        The number of letters in the alphabet
    motiflength : int
        The length of the motif
    maximum_ligation_window_length : int
        Maximum ligaion window length, default is 4

    Returns:
    --------
    jax.Array
        The motif production transition kernel
    """
    raise NotImplementedError("infer.motif_production_transition_kernel_matrix currently under construction")
    number_of_strands = int(jnp.sum(number_of_letters**jnp.arange(1,motiflength-1)))
    number_of_endings = number_of_beginnings = int(number_of_letters**(motiflength-1))
    number_of_continuations = int(number_of_letters**motiflength)
    number_of_reactants = int(jnp.sum(number_of_letters**jnp.arange(1,motiflength)))
    number_of_templates = int(jnp.sum(number_of_letters**jnp.arange(1,motiflength+1))+number_of_letters**(motiflength-1)-number_of_letters)

    extended_motif_production_rate_constants_shape = (number_of_reactants,)*2+(number_of_templates,)
    motif_production_transition_kernel = jnp.zeros((jnp.sum(motiflength**jnp.arange(1,motiflength+1))+number_of_letters**(motiflength-1),)+extended_motif_production_rate_constants_shape)

    left_reactant_entries = -jnp.outer(jnp.fill_diagonal(jnp.zeros((number_of_reactants,)*2),1,inplace=False),jnp.ones((number_of_reactants,number_of_templates))).reshape((jnp.sum(number_of_letters**jnp.arange(1,motiflength)),)*2+(number_of_reactants,number_of_templates))
    right_reactant_entries = jnp.moveaxis(left_reactant_entries,source=1,destination=2)

    left_reactant_slices = [
            (slice(number_of_strands,),slice(number_of_strands,),slice(None),slice(None)),
            (slice(number_of_strands+number_of_beginnings+number_of_continuations,None),slice(number_of_strands,number_of_reactants),slice(None),slice(None))
            ]
    left_reactants_entries_slices = [(slice(number_of_strands),)*2, (slice(number_of_strands,number_of_reactants),)*2]
    for ii in range(len(left_reactant_slices)):
        motif_production_transition_kernel = motif_production_transition_kernel.at[left_reactant_slices[ii]].add(
                left_reactant_entries[left_reactants_entries_slices[ii]]
                )

    right_reactant_slices = (slice(number_of_reactants,),slice(None),slice(number_of_reactants,),slice(None))
    motif_production_transition_kernel = motif_production_transition_kernel.at[right_reactant_slices].add(
            right_reactant_entries
            )

    motif_indices = jnp.concatenate([jnp.zeros(1),jnp.cumsum(number_of_letters**jnp.arange(1,motiflength+1)),jnp.array([jnp.sum(number_of_letters**jnp.arange(1,motiflength+1))+number_of_letters**(motiflength-1)])],)
    for strandlength in range(2,motiflength+1):
        if strandlength == motiflength-1:
            for ligation_spot in range(1,motiflength-2):
                # case1: beginning product
                for left_reactant_length in range(ligation_spot,motiflength-1):
                    for right_reactant_length in range(strandlength-left_reactant_length,motiflength):
                        product_slices = (
                                slice(int(motif_indices[-3-1]),int(motif_indices[-3])),
                                slice(int(motif_indices[left_reactant_length-1]),int(motif_indices[left_reactant_length])),
                                slice(int(motif_indices[right_reactant_length-1]),int(motif_indices[right_reactant_length])),
                                slice(None)
                                )
                        product_entries = jnp.outer(
                                jnp.fill_diagonal(jnp.zeros((number_of_letters**strandlength,)*2),1,inplace=False),
                                jnp.ones((int(number_of_letters**(right_reactant_length-(strandlength-left_reactant_length))),number_of_templates,))
                                ).reshape(
                                        (number_of_letters**strandlength,number_of_letters**left_reactant_length,number_of_letters**right_reactant_length,number_of_templates,)
                                        )
                        motif_production_transition_kernel = motif_production_transition_kernel.at[product_slices].add(
                                product_entries 
                                )
                # case2: ending product
                for left_reactant_length in range(ligation_spot,motiflength):
                    for right_reactant_length in range(max(strandlength-left_reactant_length,1), strandlength):
                        product_slices = (
                                slice(int(motif_indices[-1-1]),int(motif_indices[-1])),
                                slice(int(motif_indices[left_reactant_length-1]),int(motif_indices[left_reactant_length])),
                                slice(int(motif_indices[right_reactant_length-1]),int(motif_indices[right_reactant_length])),
                                slice(None)
                                )
                        zeros_shape = (number_of_letters**strandlength,)*2
                        ones_shape = (number_of_templates,int(number_of_letters**max(left_reactant_length+right_reactant_length-strandlength,0))) #Fixme: max(left_reactant_length-ligation_spot-k,0)???, k=1? oder k=l-3 oder so?
                        print(f'{strandlength=}')
                        print(f'{left_reactant_length=}, {right_reactant_length=}')
                        print(f'{zeros_shape=}')
                        print(f'{ones_shape=}')
                        print(f'{product_slices=}')
                        product_entries = jnp.moveaxis(
                                jnp.outer(
                                    jnp.fill_diagonal(jnp.zeros(zeros_shape),1,inplace=False),
                                    jnp.ones(ones_shape)
                                    ).reshape(zeros_shape+ones_shape),
                                source=-1,
                                destination=1,
                                ).reshape(
                                        (number_of_letters**strandlength,number_of_letters**left_reactant_length,number_of_letters**right_reactant_length,number_of_templates,)
                                        )
                        motif_production_transition_kernel = motif_production_transition_kernel.at[product_slices].add(
                                product_entries
                                )
        elif strandlength == motiflength:
            for ligation_spot in range(1,motiflength-2):
                for left_reactant_length in range(ligation_spot,motiflength):
                    for right_reactant_length in range(strandlength-left_reactant_length,motiflength):
                        product_slices = (
                                slice(int(motif_indices[-2-1]),int(motif_indices[-2])),
                                slice(int(motif_indices[left_reactant_length-1]),int(motif_indices[left_reactant_length])),
                                slice(int(motif_indices[right_reactant_length-1]),int(motif_indices[right_reactant_length])),
                                slice(None)
                                )
                        for product_index in range(0,left_reactant_length+right_reactant_length-motiflength+1):
                            # product entries have to be for all products from left to right
                            source_axes = jnp.arange(1, 1+product_index)[::-1]
                            destination_axes = jnp.arange(0,product_index)
                            zeros_shape = (number_of_letters**strandlength,)*2
                            ones_shape = (int(number_of_letters**(left_reactant_length+right_reactant_length-strandlength-product_index)), number_of_templates, int(number_of_letters**product_index))
                            product_entries = jnp.moveaxis(
                                    jnp.outer(
                                        jnp.fill_diagonal(jnp.zeros(zeros_shape),1,inplace=False),
                                        jnp.ones(ones_shape)
                                        ).reshape(zeros_shape+ones_shape),
                                    source=-1,
                                    destination=1,
                                    ).reshape(
                                            (number_of_letters**strandlength,number_of_letters**left_reactant_length,number_of_letters**right_reactant_length,number_of_templates,)
                                            )
                            motif_production_transition_kernel = motif_production_transition_kernel.at[product_slices].add(
                                    product_entries 
                                    )
        else:
            for ligation_spot in range(1,strandlength):
                left_reactant_length = ligation_spot
                right_reactant_length = strandlength - ligation_spot
                product_slices = (
                    slice(int(motif_indices[strandlength-1]),int(motif_indices[strandlength])),
                    slice(int(motif_indices[left_reactant_length-1]),int(motif_indices[left_reactant_length])),
                    slice(int(motif_indices[right_reactant_length-1]),int(motif_indices[right_reactant_length])),
                    slice(None))
                product_entries = jnp.outer(jnp.fill_diagonal(jnp.zeros((number_of_letters**strandlength,)*2),1,inplace=False),jnp.ones((number_of_templates,))).reshape((number_of_letters**strandlength,number_of_letters**ligation_spot,number_of_letters**(strandlength-ligation_spot),number_of_templates,))
                motif_production_transition_kernel = motif_production_transition_kernel.at[product_slices].add(
                        product_entries 
                        )
    return sparse.BCOO.fromdense(motif_production_transition_kernel)
