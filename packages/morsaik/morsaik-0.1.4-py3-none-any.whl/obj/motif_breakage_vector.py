import numpy as np
import nifty8 as ift
from collections import namedtuple
from ..obj.units import make_unit, Unit

from ..domains.motif_space import _return_motif_categories
from ..domains.motif_breakage_space import MotifBreakageSpace

def MotifBreakageVector(motiflength : int,
                        alphabet : list,
                        unit : Unit):
    motif_categories = _return_motif_categories(motiflength=motiflength)[1:]
    motif_vector_properties = {'motiflength' : motiflength,
        'alphabet' : alphabet,
        'number_of_letters' : len(alphabet),
        'unit' : unit}
    def makeMotifBreakageVector(motif_breakage_vector_dct : dict):
        breakages = ift.MultiField.from_raw(MotifBreakageSpace.make(alphabet, motiflength),
                                            motif_breakage_vector_dct)
        motif_vector = namedtuple('MotifBreakageVector',
                ('breakages',) + tuple(motif_vector_properties.keys()))
        return motif_vector(**{**{'breakages': breakages}, **motif_vector_properties})
    return makeMotifBreakageVector

def _create_empty_motif_breakage_dct(motiflength : int,
        alphabet : list = ['a','b']) -> dict:
    number_of_letters = len(alphabet)

    empty_motif_vector = {}
    for strandlength in range(2,motiflength-1):
        category = _return_motif_categories()[0].format(strandlength)
        shape = (number_of_letters,)*strandlength
        for hyphen_index in range(1,strandlength):
            empty_motif_vector[category+'_{}'.format(hyphen_index)] = np.zeros(shape)
    motif_categories = _return_motif_categories(motiflength=motiflength)
    for category in motif_categories[-3:]:
        category_length = motiflength-1 + (category==motif_categories[-2])
        shape = (number_of_letters,)*category_length
        for hyphen_index in range(category_length):
            empty_motif_vector[category + '_{}'.format(hyphen_index)] = np.zeros(shape)
    return empty_motif_vector

def _breakage_array_indices(
        motiflength : int,
        strandlength : int,
        breakage_spot : int,
        sequence_is_beginning : bool
    ) -> tuple:
    """
    sets up the indices of the breakage array given the parameters.
    """
    end_overlap = max(0,strandlength-breakage_spot-motiflength//2)
    beginning_overlap = max(0, breakage_spot-motiflength+motiflength//2)
    end_length_without_overlap = strandlength-breakage_spot-end_overlap
    beginning_length_without_overlap = min(breakage_spot, motiflength-motiflength//2)
    zeros_between_end_overlap_and_beginning = max(int(sequence_is_beginning),motiflength-motiflength//2-end_overlap-beginning_length_without_overlap)
    zeros_between_end_and_beginning_overlap = max(0,motiflength//2-end_length_without_overlap-beginning_overlap)

    indices_sequence_arrays =  (slice(1,None),)*end_overlap
    indices_sequence_arrays +=  (0,)*zeros_between_end_overlap_and_beginning
    indices_sequence_arrays += (slice(1,None),)*(beginning_length_without_overlap-1)
    indices_sequence_arrays += (slice(None),)*2
    indices_sequence_arrays += (slice(1,None),)*(end_length_without_overlap-1)
    indices_sequence_arrays += (0,)*zeros_between_end_and_beginning_overlap
    indices_sequence_arrays += (slice(1,None),)*beginning_overlap
    return indices_sequence_arrays

def _transform_sequence_array_to_motif_breakage_array(
        sequence_array,
        motiflength : int,
        breakage_spot : int,
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

    indices_sequence_arrays = _breakage_array_indices(motiflength, strandlength, breakage_spot, sequence_is_beginning)

    motif_array_shape = (number_of_letters+1,)*int(motiflength>2)
    motif_array_shape += (number_of_letters,)*2
    motif_array_shape += (number_of_letters+1,)*(motiflength-2-int(motiflength>2))
    motif_array = np.zeros(motif_array_shape)

    motif_array[indices_sequence_arrays] = sequence_array
    return motif_array

def _motif_breakage_vector_as_array(
        motif_breakage_vector : MotifBreakageVector
        ) -> np.ndarray:
    """
    transforms a motif vector into a numpy-array

    Parameters:
    -----------
    motif_breakage_vector : MotifBreakageVector

    Returns:
    --------
    motif_breakage_array : np.ndarray
    """
    motiflength = motif_breakage_vector.motiflength
    number_of_letters = motif_breakage_vector.number_of_letters

    beginning_breakage_spots = (1, motiflength-motiflength//2)
    continuation_breakage_spots = (motiflength-motiflength//2,motiflength-motiflength//2+1)
    end_breakage_spots = (motiflength-motiflength//2, motiflength-1)
    bs = [beginning_breakage_spots, continuation_breakage_spots, end_breakage_spots]
    motif_categories = [(_return_motif_categories()[ii], breakage_spot) for ii in range(1,4) for breakage_spot in range(*bs[ii-1])]

    strand_categories = [(_return_motif_categories()[0].format(strandlength), breakage_spot) for strandlength in range(1,motiflength-1) for breakage_spot in range(1,strandlength)]

    motif_array_shape = (number_of_letters+1,)*int(motiflength>2)
    motif_array_shape += (number_of_letters,)*2
    motif_array_shape += (number_of_letters+1,)*(motiflength-2-int(motiflength>2))
    motif_array = np.zeros(motif_array_shape)

    for motif_category in strand_categories:
        breakage_spot = motif_category[1]
        motif_category = motif_category[0]+'_{}'.format(breakage_spot)
        motif_array += _transform_sequence_array_to_motif_breakage_array(
            motif_breakage_vector.breakages[motif_category].val,
            motiflength,
            breakage_spot,
            sequence_is_beginning = True
        )
    for motif_category in motif_categories:
        breakage_spot = motif_category[1]
        sequence_is_beginning = motif_category[0]=='beginning'
        motif_category = motif_category[0]+'_{}'.format(breakage_spot)
        motif_array += _transform_sequence_array_to_motif_breakage_array(
            motif_breakage_vector.breakages[motif_category].val,
            motiflength,
            breakage_spot,
            sequence_is_beginning = sequence_is_beginning
        )
    return motif_array

def _array_to_motif_breakage_vector(
        motif_breakage_vector_array : np.ndarray,
        motiflength : int,
        alphabet : list,
        unit : Unit
        ) -> MotifBreakageVector:
    if motiflength != len(motif_breakage_vector_array.shape):
        raise ValueError("motiflength inconsistent with array shape")
    number_of_letters = len(alphabet)
    if number_of_letters != motif_breakage_vector_array.shape[0]-1:
        raise ValueError("alphabet shape ({alphabet_shape}) inconsistent with motif_breakage_vector_array shape ({motif_vector_array_shape})".format(
            alphabet_shape = len(alphabet),
            motif_vector_array_shape = motif_breakage_vector_array.shape
                    ))

    beginning_breakage_spots = (1, motiflength-motiflength//2)
    continuation_breakage_spots = (motiflength-motiflength//2,motiflength-motiflength//2+1)
    end_breakage_spots = (motiflength-motiflength//2, motiflength-1)
    bs = [beginning_breakage_spots, continuation_breakage_spots, end_breakage_spots]

    motif_categories = [(_return_motif_categories()[ii], breakage_spot) for ii in range(1,4) for breakage_spot in range(*bs[ii-1])]
    strand_categories = [(_return_motif_categories()[0].format(strandlength), strandlength, breakage_spot) for strandlength in range(1,motiflength-1) for breakage_spot in range(1,strandlength)]

    motif_vector_dct = {}
    for motif_category in strand_categories:
        breakage_spot = motif_category[2]
        strandlength = motif_category[1]
        motif_category = motif_category[0]+'_{}'.format(breakage_spot)
        current_indices = _breakage_array_indices(motiflength, strandlength, breakage_spot, sequence_is_beginning=True)
        motif_vector_dct[motif_category] = motif_breakage_vector_array[current_indices]
    for motif_category in motif_categories:
        breakage_spot = motif_category[1]
        sequence_is_beginning = motif_category[0]=='beginning'
        strandlength = motiflength-int(motif_category[0]!='continuation')
        motif_category = motif_category[0]+'_{}'.format(breakage_spot)
        current_indices = _breakage_array_indices(motiflength, strandlength, breakage_spot, sequence_is_beginning)
        motif_vector_dct[motif_category] = motif_breakage_vector_array[current_indices]
    return motif_vector_dct

def isinstance_motifbreakagevector(obj) -> bool:
    is_motif_breakage_vector = True
    keys = ['motiflength','alphabet','number_of_letters','unit','breakages']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifBreakageVector, missing key: {}.'.format(key))
            return False
    keys = MotifBreakageSpace.make(obj.alphabet, obj.motiflength).keys()
    for key in obj.breakages.keys():
        if key not in keys:
            print('Not a MotifBreakageVector, missing key in breakages field: {}.'.format(key))
            return False
    is_motif_breakage_vector *= isinstance(obj, tuple)
    return bool(is_motif_breakage_vector)
