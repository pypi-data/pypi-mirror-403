import numpy as np
from typing import Union
from .config import symbol_config as read_symbol_config
from ..obj.motif_trajectory import MotifTrajectory
from ..obj.motif_vector import MotifVector, are_compatible_motif_vectors
from ..obj.times_vector import TimesVector
from ..obj.units import Unit
from warnings import warn

def strand_motifs_trajectory(filepaths : list,
                             alphabet : list,
                             motiflength : int = 4,
                             times_unit : Unit = None,
                             skiprows : int =2
                             ) -> MotifTrajectory:
    """
    reads from the complexes.txt of the RNAReactor simulation output and returns corresponding
    concentration vectors in motif space.

    PARAMETERS:
    -----------
    filepaths : string or list of strings
        Output file of the RNAReactor simulation
    skiprow : int, optional
        Skip the first `skiprow` lines, including comments
        when reading the file;
        default : 2

    RETURN:
    -------
    strand_motifs_trajectory : MotifTrajectory
    """
    if filepaths is str:
        filepaths = [filepaths,]
    if not isinstance(filepaths, list):
        raise ValueError("filepaths needs to be list.")
    motif_vectors = []
    times = []
    if times_unit is None:
        times_unit = read_symbol_config('time', unitformat=True)

    for filepath in filepaths:
        _, current_times, sequence_trajectory = steps_and_times_and_sequence_trajectory_from_complexes_txt(
                filepath, skiprows=skiprows)
        if len(current_times) == 0:
            continue
        motif_vectors += _transform_sequence_trajectory_into_motif_vector_list(sequence_trajectory, alphabet, motiflength)
        if (len(times)>1):
            if not are_compatible_motif_vectors(motif_vectors[0],motif_vectors[-1]):
                raise ValueError("Non compatible motif vectors.")
            if (times[-1]>current_times[0]):
                warn("Times of initialized motif trajectory will not be chronologically.")
        times += list(current_times)
    times = TimesVector(times,times_unit)
    return MotifTrajectory(motif_vectors,times)

def steps_and_times_and_complexes_from_complexes_txt(filepath : str,
        skiprows : int = 2,
        ) -> Union[np.array, np.array, list]:
    """
    Parameters:
    -----------
    filepath : str,
    skiprows : int = 2,
        skip the first <skiprows> lines of the complex.txt file

    Returns:
    --------
    steps : nd-array with dtype int
    total_physical_time : nd-array with dtype np.float64
    complexes : list
        with every element of list is the list of complexes at that time
        the list of complexes at given time is again a list of the format
        complexes[time_index][complex_index]=[number_of_complex : int, structure_of_complex : str]
    """
    if len(list(open(filepath))) == 0:
        warn("complexes.txt file is empty")
        nl = np.empty((0,3), dtype=str)
    else:
        nl = np.loadtxt(filepath, skiprows=skiprows, dtype=str, ndmin = 2)
    steps = np.array(nl[:,0], dtype = int)
    total_physical_time = np.array(nl[:,1], dtype = np.float64)
    number_and_structure_of_complexes = nl[:,2]
    from json import loads
    number_and_structure_of_complexes = [
            loads(number_and_structure_of_complexes[ii].replace('None','"none"'))
            for ii in range(len(number_and_structure_of_complexes))
            ]
    return steps, total_physical_time, number_and_structure_of_complexes

def steps_and_times_and_sequence_trajectory_from_complexes_txt(filepath : str,
        skiprows : int = 2,
        ) -> Union[np.array, np.array, list]:
    """
    Parameters:
    -----------
    filepath : str,
    skiprows : int = 2,
        skip the first <skiprows> lines of the complex.txt file

    Returns:
    --------
    steps : nd-array with dtype int
    total_physical_time : nd-array with dtype np.float64
    complexes : list
        with every element of list is the list of complexes at that time
        the list of complexes at given time is again a list of the format
        complexes[time_index][complex_index]=[number_of_complex : int, structure_of_complex : str]
    """
    steps, total_physical_time, number_and_structure_of_complexes = steps_and_times_and_complexes_from_complexes_txt(filepath,skiprows=skiprows)
    sequence_number_trajectory = [{} for ii in range(len(total_physical_time))]
    for time_idx in range(len(total_physical_time)):
        current_number_and_structure_of_complexes = number_and_structure_of_complexes[time_idx]
        for complex_index in range(len(current_number_and_structure_of_complexes)):
            number_of_complex = current_number_and_structure_of_complexes[complex_index][0]
            structure_of_complex = current_number_and_structure_of_complexes[complex_index][1]
            upper_strands_as_continuous_string, lower_strands_as_continuous_string  = _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(structure_of_complex)
            upper_separate_strand_sequences = _cut_strands_as_continuous_string_into_separate_strand_sequences(upper_strands_as_continuous_string)
            lower_separate_strand_sequences = _cut_strands_as_continuous_string_into_separate_strand_sequences(lower_strands_as_continuous_string)
            for upper_separate_strand_sequence in list(upper_separate_strand_sequences):
                if upper_separate_strand_sequence in sequence_number_trajectory[time_idx].keys():
                    sequence_number_trajectory[time_idx][upper_separate_strand_sequence] += number_of_complex
                else:
                    sequence_number_trajectory[time_idx][upper_separate_strand_sequence] = number_of_complex
            for lower_separate_strand_sequence in lower_separate_strand_sequences:
                if lower_separate_strand_sequence in sequence_number_trajectory[time_idx].keys():
                    sequence_number_trajectory[time_idx][lower_separate_strand_sequence] += number_of_complex
                else:
                    sequence_number_trajectory[time_idx][lower_separate_strand_sequence] = number_of_complex
    return steps, total_physical_time, sequence_number_trajectory

def _reverse_segments(list_of_strand_segments):
    """
    reverses a strand
    """
    return [letter[::-1] for letter in list_of_strand_segments[::-1]]

def _extract_upper_and_lower_segments(structure_of_complex : list) -> Union[np.array,np.array]:
    list_of_upper_segments = np.array(structure_of_complex)[:,0]
    list_of_lower_segments =  np.array(structure_of_complex)[:,1]
    return list_of_upper_segments, list_of_lower_segments 

def _transform_list_of_segments_to_string(list_of_segments : list,
        list_of_strings_that_are_replaced : list = [('|',0),('-',''),('X',0),('x',0),('none',''),('enon',''),('00','0')]
        ) -> str:
    """
    transforms a list_of_segments into strands as continuous string
    """
    for ii in range(len(list_of_segments)):
        list_of_segments[ii] = list_of_segments[ii].replace(' ','').lstrip('5').rstrip('3')
    strands_as_continuous_string = ''.join(list_of_segments)
    for string_replace_tuple in list_of_strings_that_are_replaced:
        strands_as_continuous_string = strands_as_continuous_string.replace(str(string_replace_tuple[0]),str(string_replace_tuple[1]))
    if len(strands_as_continuous_string)>0:
        if strands_as_continuous_string[0]!='0':
            strands_as_continuous_string = '0'+strands_as_continuous_string
        if strands_as_continuous_string[-1]!='0':
            strands_as_continuous_string = strands_as_continuous_string +'0'
    return strands_as_continuous_string

def _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(structure_of_complex : list) -> Union[str,str]:
    """
    takes structure_of_complex from the RNA Strand Reactor output
    and returns the upper strands sequences and the lower strands sequences.

    Parameters:
    ---------- 
    structure_of_complex : list or numpy.array

    Returns:
    --------
    upper_strands_sequences : list of str
    lower_strands_sequences : list of str
    """
    # segments are continuous parts of a complex without the end or beginning of a strand
    list_of_upper_segments, list_of_lower_segments = _extract_upper_and_lower_segments(structure_of_complex)
    list_of_reversed_lower_segments = _reverse_segments(list_of_lower_segments)
    upper_strands_as_continuous_string = _transform_list_of_segments_to_string(list_of_upper_segments)
    lower_strands_as_continuous_string = _transform_list_of_segments_to_string(list_of_reversed_lower_segments)
    return upper_strands_as_continuous_string, lower_strands_as_continuous_string

def _cut_strands_as_continuous_string_into_separate_strand_sequences(strands_as_continuous_string : str) -> list:
    """
    cut the upper strand of a complex into its single continuous strands
    """
    strands_as_continuous_string_array = np.array(list(strands_as_continuous_string))
    indices_of_empty_spots = np.where(strands_as_continuous_string_array=='0')[0]
    separate_strand_sequences = [[]]*(indices_of_empty_spots.size-1)
    for ii in range(indices_of_empty_spots.size-1):
        separate_strand_sequences[ii] = strands_as_continuous_string[indices_of_empty_spots[ii]+1:(indices_of_empty_spots[ii+1])]
    return separate_strand_sequences

def _transform_sequence_trajectory_into_motif_vector_list(
        sequence_trajectory : list,
        alphabet : list,
        motiflength : int) -> list:
    """
    Returns:
    --------
    motif_vectors : list
        list of MotifVectors
    """
    motif_vectors = [[]]*len(sequence_trajectory)
    for time_index in range(len(sequence_trajectory)):
        sequence_vector = sequence_trajectory[time_index]
        motif_vectors[time_index] = _transform_sequence_vector_into_motif_vector(sequence_vector,
                alphabet,
                motiflength)
    return motif_vectors

def _translate_letters_to_numbers(alphabet:list,
        zero_is_a_letter : bool = False):
    """
    dictionary to translate letters into numbers
    """
    if zero_is_a_letter:
        dct = { '0' : 0 }
    else:
        dct = {}
    for ii in range(len(alphabet)):
        dct[alphabet[ii]] = ii+zero_is_a_letter
    return dct

def _transform_motif_string_to_index_tuple(motif_string : str,
        alphabet : list) -> tuple:
    motif_as_tuple_of_letters = tuple(motif_string)
    """
    transforms a motif e.g. ('0','A','T','C') to corresponding indices, e.g. (0,1,3,2)

    PARAMETERS:
    -----------
    motif : array of letters

    RETURNS:
    --------
    indices
    """
    transdict = _translate_letters_to_numbers(alphabet)
    return tuple(transdict[letter] for letter in motif_as_tuple_of_letters)

def _transform_sequence_vector_into_motif_vector(sequence_vector : dict,
        alphabet : list,
        motiflength : int) -> MotifVector:
    from ..obj.motif_vector import _create_empty_motif_vector_dct
    motif_vector_dct = _create_empty_motif_vector_dct(motiflength,alphabet=alphabet)
    from ..domains.motif_space import _motif_categories
    motif_categories = _motif_categories()
    for sequence in sequence_vector.keys():
        strandlength = len(sequence)
        if (strandlength < (motiflength-1)):
            motif_category = motif_categories[0].format(strandlength)
            motif_index_tuple = _transform_motif_string_to_index_tuple(sequence,alphabet)
            motif_vector_dct[motif_category][motif_index_tuple] += sequence_vector[sequence]
        else:
            occupation_number = sequence_vector[sequence]
            # add beginning
            motif_category = motif_categories[-3]
            motif_string = sequence[:(motiflength-1)]
            motif_index_tuple = _transform_motif_string_to_index_tuple(motif_string, alphabet)
            motif_vector_dct[motif_category][motif_index_tuple] += occupation_number
            # add ending
            motif_category = motif_categories[-1]
            motif_string = sequence[-(motiflength-1):]
            motif_index_tuple = _transform_motif_string_to_index_tuple(motif_string, alphabet)
            motif_vector_dct[motif_category][motif_index_tuple] += occupation_number
            # add continuations
            motif_category = motif_categories[-2]
            for motif_index in range(len(sequence)-motiflength+1):
                motif_string = sequence[motif_index:motif_index+motiflength]
                motif_index_tuple = _transform_motif_string_to_index_tuple(motif_string, alphabet)
                motif_vector_dct[motif_category][motif_index_tuple] += occupation_number
    motif_vector = MotifVector(motiflength,alphabet,'1')
    return motif_vector(motif_vector_dct)
