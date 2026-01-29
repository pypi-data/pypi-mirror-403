import numpy as np
import jax.numpy as jnp
import yaml
from ..domains.motif_space import _return_motif_categories
from collections import namedtuple
import nifty8 as ift

from .units import make_unit
from .units import transform_unit_to_dict, transform_dict_to_unit

from ..domains.motif_space import MotifSpace
from ..domains.hamming_space import HammingSpace

from ..utils.save import create_directory_path_if_not_already_existing

def MotifVector(motiflength : int,
        alphabet : list,
        unit : str):
    motif_categories = _return_motif_categories(motiflength=motiflength)
    motif_vector_properties = {'motiflength' : motiflength,
        'alphabet' : alphabet,
        'number_of_letters' : len(alphabet),
        'unit' : make_unit(unit)}
    def makeMotifVector(motif_vector_dct : dict):
        motif_vector = namedtuple('MotifVector',
                ('motifs',) + tuple(motif_vector_properties.keys()))
        motifs = ift.MultiField.from_dict(
            _motif_vector_dct_with_fields(motif_vector_dct, alphabet),
            MotifSpace.make(alphabet, motiflength, units=make_unit('bits')),
        )
        return motif_vector(**{**{'motifs': motifs}, **motif_vector_properties})
    return makeMotifVector

def add_zebra_fluctuation_to_motif_vector(motif_vector : MotifVector,
                                          zebra_fluctuation : float = 0.,
                                          braze_fluctuation : float = 0.,
                                          aa_fluctuation : float = 0.,
                                          bb_fluctuation : float = 0.,
                                          fourmer_fluctuation : float = 0.
    ) -> MotifVector:
    motif_array = _motif_vector_as_array(motif_vector)
    ic = motif_array[0,0,2,0]
    motif_array[0,0,2,0] += zebra_fluctuation*motif_array[0,0,2,0]
    motif_array[0,1,1,0] += braze_fluctuation*motif_array[0,1,1,0]

    motif_array[0,0,1,0] += aa_fluctuation*motif_array[0,0,1,0]
    motif_array[0,1,2,0] += bb_fluctuation*motif_array[0,1,2,0]

    motif_array[0,0,2,1] += fourmer_fluctuation*ic
    motif_array[1,1,1,2] += fourmer_fluctuation*ic
    motif_array[2,0,2,0] += fourmer_fluctuation*ic
    return MotifVector(motif_vector.motiflength, motif_vector.alphabet, motif_vector.unit)(_array_to_motif_vector_dct(motif_array, motif_vector.motiflength, motif_vector.alphabet))

def convert_homogeneous_dimers_to_zebra_dimers(
        motif_vector : MotifVector,
        zebra_dimer_concentration : float
    ) -> MotifVector:
    """
    Note: if zebra_dimer_concentration is negative, homogeneous dimers are added and zebra_dimers are reduced.
    """
    motif_array = _motif_vector_as_array(motif_vector)
    motif_array[0,0,2,0] += zebra_dimer_concentration
    motif_array[0,1,1,0] += zebra_dimer_concentration
    motif_array[0,1,2,0] -= zebra_dimer_concentration
    motif_array[0,0,1,0] -= zebra_dimer_concentration
    return MotifVector(motif_vector.motiflength, motif_vector.alphabet, motif_vector.unit)(_array_to_motif_vector_dct(motif_array, motif_vector.motiflength, motif_vector.alphabet))

def convert_dimers_to_tetramers(
        motif_vector : MotifVector,
        zebra_tetramer_concentration : float
    ) -> MotifVector:
    """
    Note: if zebra_tetramer_concentration is negative, homogeneous dimers are converted to tetramers instead.
    """
    motif_array = _motif_vector_as_array(motif_vector)

    if zebra_tetramer_concentration >= 0.:
        motif_array[0,0,2,1] += .5*zebra_tetramer_concentration
        motif_array[1,1,1,2] += .5*zebra_tetramer_concentration
        motif_array[2,0,2,0] += .5*zebra_tetramer_concentration

        motif_array[0,1,1,2] += .5*zebra_tetramer_concentration
        motif_array[2,0,2,1] += .5*zebra_tetramer_concentration
        motif_array[1,1,1,0] += .5*zebra_tetramer_concentration

        motif_array[0,0,2,0] -= zebra_tetramer_concentration
        motif_array[0,1,1,0] -= zebra_tetramer_concentration

    else:
        motif_array[0,0,1,1] += .5*zebra_tetramer_concentration
        motif_array[1,0,1,1] += .5*zebra_tetramer_concentration
        motif_array[1,0,1,0] += .5*zebra_tetramer_concentration

        motif_array[0,1,2,2] += .5*zebra_tetramer_concentration
        motif_array[2,1,2,2] += .5*zebra_tetramer_concentration
        motif_array[2,1,2,0] += .5*zebra_tetramer_concentration

        motif_array[0,1,2,0] -= zebra_tetramer_concentration
        motif_array[0,0,1,0] -= zebra_tetramer_concentration

    return MotifVector(motif_vector.motiflength, motif_vector.alphabet, motif_vector.unit)(_array_to_motif_vector_dct(motif_array, motif_vector.motiflength, motif_vector.alphabet))

def _motif_vector_dct_with_fields(motif_vector_dct,
                                  alphabet : list) -> dict:
    for key in motif_vector_dct.keys():
        if not isinstance(motif_vector_dct[key],ift.Field):
            motif_vector_dct[key] = ift.Field(
                ift.DomainTuple.make(HammingSpace(alphabet,len(motif_vector_dct[key].shape))),
                np.asarray(motif_vector_dct[key]))
    return motif_vector_dct

def _create_empty_motif_vector_dct(motiflength : int,
        alphabet : list = ['a','b']) -> dict:
    number_of_letters = len(alphabet)

    empty_motif_vector = {}
    for strandlength in range(1,motiflength-1):
        category = _return_motif_categories()[0].format(strandlength)
        shape = (number_of_letters,)*strandlength
        empty_motif_vector[category] = np.zeros(shape)
    motif_categories = _return_motif_categories(motiflength=motiflength)
    for category in motif_categories[-3:]:
        category_length = motiflength-1 + (category==motif_categories[-2])
        shape = (number_of_letters,)*category_length
        empty_motif_vector[category] = np.zeros(shape)
    return empty_motif_vector

def isinstance_motifvector(obj : object,
                           print_statements : bool = True
                           ) -> bool:
    is_motif_vector = True
    keys = ['motifs','motiflength', 'alphabet', 'number_of_letters', 'unit']
    for key in obj._asdict().keys():
        if key not in keys:
            if print_statements:
                print('Not a MotifVector, missing key: {}.'.format(key))
            return False
    keys = list(_return_motif_categories(motiflength=obj.motiflength))
    for key in obj.motifs.keys():
        if key not in keys:
            if print_statements:
                print('Not a MotifVector, missing key in motifs field: {}.'.format(key))
            return False
    is_motif_vector *= isinstance(obj, tuple)
    is_motif_vector *= hasattr(obj, '_asdict')
    is_motif_vector *= hasattr(obj, '_fields')
    return bool(is_motif_vector)

def are_compatible_motif_vectors(mv1 : MotifVector, mv2 : MotifVector) -> bool:
    if not isinstance_motifvector(mv1):
        print('Object is not a MotifVector')
        return False
    if not isinstance_motifvector(mv2):
        print('Object is not a MotifVector')
        return False
    keys = ['motiflength', 'alphabet', 'unit']
    for key in keys:
        if not np.prod(mv1._asdict()[key]==mv2._asdict()[key]):
            print('MotifVectors not compatible: {} mismatch.'.format(key))
            return False
    return True

def _motif_indices_in_motifs_array(motif_vector_array : np.ndarray,
        motiflength : int,
        is_beginning : bool
        ) -> tuple:
    """
    returns an index-tuple for the array in which the motif_sequence_array fits.

    Parameters:
    -----------
    motif_vector_array : np.ndarray,
    motiflength : int,
    is_beginning : bool

    Returns:
    --------
    motif_indices : tuple
    """
    if len(motif_vector_array.shape)==motiflength:
        is_beginning = False
    strandlength = len(motif_vector_array.shape)
    number_of_letters = motif_vector_array.shape[0]
    current_indices = (0,)*int(is_beginning)
    current_indices += (slice(1,number_of_letters+1),)*int(not is_beginning)
    current_indices += (slice(0,number_of_letters),)
    current_indices += (slice(1,number_of_letters+1),)*int(
            strandlength
            -1
            -int(not is_beginning)
            )
    current_indices += (0,)*(motiflength-len(current_indices))
    return current_indices

def categories_indices(motiflength : int,
                       alphabet : list
                       ) -> dict:
    """
    returns a dictionary with motif categories as keys and index-tuples as their values.

    Parameters:
    -----------
    motiflenth : int
    alphabet : list

    Returns:
    --------
    categories_indices : dict
    """
    keys = _return_motif_categories(motiflength)

    number_of_letters = len(alphabet)
    categories_indices = {}
    for strandlength in range(1,motiflength-1):
        is_beginning = True
        key = keys[strandlength-1]

        current_indices = (0,)*int(is_beginning)
        current_indices += (slice(1,number_of_letters+1),)*int(not is_beginning)
        current_indices += (slice(0,number_of_letters),)
        current_indices += (slice(1,number_of_letters+1),)*int(
                strandlength
                -1
                -int(not is_beginning)
                )
        current_indices += (0,)*(motiflength-len(current_indices))

        categories_indices[key] = current_indices

    for key in keys[-3:]:
        is_beginning = (key==keys[-3])
        strandlength = motiflength-int(key!=keys[-2])

        current_indices = (0,)*int(is_beginning)
        current_indices += (slice(1,number_of_letters+1),)*int(not is_beginning)
        current_indices += (slice(0,number_of_letters),)*(motiflength>2)
        current_indices += (slice(1,number_of_letters+1),)*int(
                strandlength
                -int(motiflength>2)
                -int(not is_beginning)
                )
        current_indices += (0,)*(motiflength-len(current_indices))

        categories_indices[key] = current_indices
    return categories_indices

def category_indices(motif_category : str,
                     motiflength : int,
                     alphabet : list
                     ) -> tuple:
    """
    returns the array-indix-tuple for a certain motif_category.
    """
    return categories_indices(motiflength, alphabet)[motif_category]

def _transform_sequence_array_to_motif_array(
        sequence_array,
        motiflength : int,
        sequence_is_beginning : bool = True
        ) -> np.ndarray:
    """
    transforms an array that only tracks letters (occupied nucleotides)
    into an array that explicitely tracks empty spots with zeros.
    Note that the second spot is always a letter, though.

    Parameters:
    -----------
    sequence_array : nd-array
    motiflength : int
    sequence_is_beginning : boolean (optional)
        whether the sequence is beginning, i.e. the first spot is zero,
        else it will be considered as end or continuation if all spots are
        letters
        default : True

    Returns:
    --------
    motif_array : nd-array
    """
    if len(sequence_array.shape)==motiflength:
        sequence_is_beginning = False
    number_of_letters = sequence_array.shape[0]
    strandlength = len(sequence_array.shape)

    motif_array_shape = (number_of_letters+1,)
    motif_array_shape += (number_of_letters,)*int(motiflength>2)
    motif_array_shape += (number_of_letters+1,)*(motiflength-1-int(motiflength>2))
    motif_array = np.zeros(motif_array_shape)

    indices_sequence_arrays = (0,)*int(sequence_is_beginning)
    indices_sequence_arrays += (slice(1,None),)*(1-int(sequence_is_beginning))
    indices_sequence_arrays += (slice(None),)*int(motiflength>2)
    indices_sequence_arrays += (slice(1,None),)*(strandlength-1-int(motiflength>2)+int(sequence_is_beginning))
    indices_sequence_arrays += (0,)*(motiflength-len(indices_sequence_arrays))

    motif_array[indices_sequence_arrays] = sequence_array
    return motif_array

def _motif_vector_as_array(motif_vector : MotifVector
        ) -> np.ndarray:
    """
    transforms a motif vector into an numpy-array

    Parameters:
    -----------
    motif_vector : MotifVector

    Returns:
    --------
    motif_array : np.ndarray
    """
    motiflength = motif_vector.motiflength
    number_of_letters = motif_vector.number_of_letters

    motif_categories = _return_motif_categories(motiflength)

    motif_array_shape = (number_of_letters+1,)
    motif_array_shape += (number_of_letters,)*int(motiflength>2)
    motif_array_shape += (number_of_letters+1,)*(motiflength-1-int(motiflength>2))
    motif_array = np.zeros(motif_array_shape)
    for motif_category in motif_categories[:-2]:
        motif_array += _transform_sequence_array_to_motif_array(
                motif_vector.motifs[motif_category].val,
                motiflength,
                sequence_is_beginning = True
                )
    for motif_category in motif_categories[-2:]:
        motif_array += _transform_sequence_array_to_motif_array(
                motif_vector.motifs[motif_category].val,
                motiflength,
                sequence_is_beginning = False
                )
    return motif_array

def _array_to_motif_vector_dct(motif_vector_array : np.ndarray,
        motiflength : int,
        alphabet : list,
        ) -> dict:
    if motiflength != len(motif_vector_array.shape):
        raise ValueError("motiflength inconsistent with array shape")
    number_of_letters = len(alphabet)
    if number_of_letters != motif_vector_array.shape[0]-1:
        raise ValueError("alphabet shape ({alphabet_shape}) inconsistent with motif_vector_array shape ({motif_vector_array_shape})".format(
            alphabet_shape = len(alphabet),
            motif_vector_array_shape = motif_vector_array.shape
                    ))

    motif_vector_dct = {}
    for strandlength in range(1,motiflength):
        if strandlength == (motiflength-1):
            category = _return_motif_categories()[-3]
        else:
            category = _return_motif_categories()[0].format(strandlength)
        current_indices = (0,)
        current_indices += (slice(None),)*int(motiflength>2)
        current_indices += (slice(1,None),)*(strandlength-int(motiflength>2))
        current_indices += (0,)*(motiflength-len(current_indices))
        motif_vector_dct[category] = motif_vector_array[current_indices]
    motif_categories = _return_motif_categories(motiflength=motiflength)
    for category in motif_categories[-2:]:
        strandlength = motiflength-1 + (category==motif_categories[-2])
        current_indices = (slice(1,None),)
        current_indices += (slice(None),)*int(motiflength>2)
        current_indices += (slice(1,None),)*(motiflength-2-int(motiflength>2)+int(category==motif_categories[-2]))
        current_indices += (0,)*(motiflength-len(current_indices))
        motif_vector_dct[category] = motif_vector_array[current_indices]
    return motif_vector_dct

def save_motif_vector(archive_path : str,
        motif_vector : MotifVector
        ) -> None:
    create_directory_path_if_not_already_existing(archive_path)
    jnp.save(archive_path+'motifs',
            _motif_vector_as_array(motif_vector)
            )

    with open(archive_path+'properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_vector.motiflength,
            'alphabet':motif_vector.alphabet,
            'unit':transform_unit_to_dict(motif_vector.unit)},
            yaml_file,
            indent=4)

def load_motif_vector(archive_path : str
        ) -> MotifVector:
    dct_filename =  archive_path+'properties'+'.yaml'
    array_filename = archive_path+'motifs'+'.npy'
    with open(dct_filename, 'r') as yaml_file:
        motif_vector_properties = yaml.safe_load(yaml_file)
    motif_vector_properties['unit'] = transform_dict_to_unit(motif_vector_properties['unit'])
    makeMotifVector = MotifVector(**motif_vector_properties)
    return makeMotifVector(
            _array_to_motif_vector_dct(jnp.load(array_filename),motif_vector_properties['motiflength'], motif_vector_properties['alphabet'])
            )
