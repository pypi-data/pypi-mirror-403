import numpy as np
import nifty8 as ift
from jax import numpy as jnp
from collections import namedtuple
from typing import Tuple
import itertools
from scipy.sparse import coo_matrix, save_npz, load_npz

import yaml

from ..domains.motif_space import _return_motif_categories
from ..domains.motif_production_space import (MotifProductionSpace,
                                              make_motif_production_dct,
                                              _determine_product_and_template_categories_and_ligation_spots,
                                              _production_channel_id,
                                              _valid_production_channel
                                              )

from .units import (Unit, make_unit,
                    transform_unit_to_dict, transform_dict_to_unit)

from ..utils.save import create_directory_path_if_not_already_existing

def _create_empty_motif_production_dict(motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int) -> dict:
    number_of_letters = len(alphabet)

    empty_motif_production_vector = {}
    mpd = make_motif_production_dct(
            alphabet,
            motiflength,
            maximum_ligation_window_length
            )
    for key in mpd.keys():
        empty_motif_production_vector[key] = np.zeros(mpd[key].shape)
    return empty_motif_production_vector

def MotifProductionVector(motiflength : int,
                          alphabet : list,
                          unit : Unit,
                          maximum_ligation_window_length : int
                          ) -> Tuple[object]:
    unit = make_unit(unit)
    if maximum_ligation_window_length is None:
        maximum_ligation_window_length = motiflength

    motif_production_vector_properties = {'motiflength' : motiflength,
        'alphabet' : alphabet,
        'number_of_letters' : len(alphabet),
        'unit' : unit,
        'maximum_ligation_window_length' : maximum_ligation_window_length
        }

    def makeMotifProductionVector(motif_production_vector_dct : dict):
        motif_production_vector = namedtuple('MotifProductionVector',
                ('productions',) + tuple(motif_production_vector_properties.keys()))
        productions = ift.MultiField.from_raw(
            MotifProductionSpace.make(alphabet,motiflength,maximum_ligation_window_length),
            motif_production_vector_dct,
            )
        return motif_production_vector(**{**{'productions' : productions}, **motif_production_vector_properties})
    return makeMotifProductionVector

def isinstance_motifproductionvector(obj) -> bool:
    is_motif_production_vector = True
    keys = ['motiflength','alphabet','number_of_letters','unit','maximum_ligation_window_length','productions']
    for key in obj._asdict().keys():
        if key not in keys:
            print('Not a MotifProductionVector, missing key: {}.'.format(key))
            return False
    keys = MotifProductionSpace(
        obj.alphabet,
        obj.motiflength,
        obj.maximum_ligation_window_length
    ).keys()
    for key in obj.motifs.keys():
        if key not in keys:
            print('Not a MotifVector, missing key in motifs field: {}.'.format(key))
            return False
    is_motif_vector *= isinstance(obj, tuple)
    return bool(is_motif_production_vector)

def _motif_production_array_shape(number_of_letters : int,
        maximum_ligation_window_length : int
        ) -> tuple:
    motif_production_array_shape = (number_of_letters+1,)*(maximum_ligation_window_length-maximum_ligation_window_length//2-1)
    motif_production_array_shape += (number_of_letters,)*2
    motif_production_array_shape += (number_of_letters+1,)*(maximum_ligation_window_length//2-1)
    motif_production_array_shape += motif_production_array_shape[::-1]
    return motif_production_array_shape

def _motif_production_vector_as_array(
        motif_production_vector : MotifProductionVector,
        ) -> np.ndarray:
    """
    transforms a motif vector into a numpy-array

    Parameters:
    -----------
    motif_production_vector : MotifProductionVector

    Returns:
    --------
    motif_production_array : np.ndarray
    """
    motiflength = motif_production_vector.motiflength
    number_of_letters = motif_production_vector.number_of_letters
    maximum_ligation_window_length = motif_production_vector.maximum_ligation_window_length

    motif_categories = _return_motif_categories(motiflength)

    motif_production_array = np.zeros(_motif_production_array_shape(number_of_letters,maximum_ligation_window_length))

    if maximum_ligation_window_length < 4:
        ligation_window_lengths = np.array([maximum_ligation_window_length])
    else:
        ligation_window_lengths = np.arange(4,maximum_ligation_window_length+1)

    for ligation_window_length in ligation_window_lengths:
        product_categories, template_categories, ligation_spots = _determine_product_and_template_categories_and_ligation_spots(motiflength,
                maximum_ligation_window_length,
                ligation_window_length
                )

        for product_category, template_category, ligation_spot in itertools.product(product_categories, template_categories, ligation_spots):
            if not _valid_production_channel(product_category, template_category,
                ligation_window_length, ligation_spot,
                maximum_ligation_window_length):
                continue
            reaction_key = _production_channel_id(product_category, template_category,
                    ligation_window_length, ligation_spot)

            destination_axes, source_axes = _moved_axes(ligation_window_length,ligation_spot, maximum_ligation_window_length)
            mpa_indices = _reaction_indices(product_category, template_category,
                    ligation_window_length, ligation_spot,
                    maximum_ligation_window_length, axes_moved=False)
            np.moveaxis(motif_production_array,source_axes,destination_axes)[mpa_indices] = motif_production_vector.productions[reaction_key].val
    return motif_production_array

def save_motif_production_vector(
        archive_path : str,
        motif_production_vector : MotifProductionVector,
        file_sparse : bool = True
        ):
    create_directory_path_if_not_already_existing(archive_path)
    if file_sparse:
        save_npz(archive_path+'motif_productions',
                coo_matrix(_motif_production_vector_as_array(motif_production_vector).reshape(1,-1)))
    else:
        np.save(archive_path+'motif_productions',
                _motif_production_vector_as_array(motif_production_vector)
                )

    with open(archive_path+'properties.yaml','w') as yaml_file:
        yaml.dump({'motiflength':motif_production_vector.motiflength,
            'alphabet':motif_production_vector.alphabet,
            'unit':transform_unit_to_dict(motif_production_vector.unit),
            'maximum_ligation_window_length' : motif_production_vector.maximum_ligation_window_length
            },
            yaml_file,
            indent=4)

def load_motif_production_vector(archive_path : str,
        file_sparse : bool = True
        ) -> MotifProductionVector:
    dct_filename = archive_path+'properties.yaml'
    productions_filename = archive_path+'motif_productions'
    productions_filename += '.np'+'z'*file_sparse+'y'*(1-file_sparse)
    with open(dct_filename, 'r') as yaml_file:
        properties = yaml.safe_load(yaml_file)
    if file_sparse:
        motif_production_array = np.asarray(coo_matrix.todense(load_npz(productions_filename)))
        motif_production_array = motif_production_array.reshape(
                _motif_production_array_shape(len(properties["alphabet"]),
                    properties["maximum_ligation_window_length"])
                ) 
    else:
        motif_production_array = np.load(productions_filename)
    properties['unit'] = transform_dict_to_unit(properties['unit'])
    motif_production_vec = _array_to_motif_production_vector(motif_production_array,
            **properties
            )
    return motif_production_vec

def _array_to_motif_production_vector(motif_production_array: np.ndarray,
        motiflength : int,
        alphabet : list,
        unit : Unit,
        maximum_ligation_window_length : int
        ) -> MotifProductionVector:
    unit = make_unit(unit)
    makeMotifProductionVector = MotifProductionVector(motiflength, alphabet,
            unit, maximum_ligation_window_length)
    motif_production_vector_dct = _motif_production_array_to_dct(motif_production_array,
            motiflength, alphabet, maximum_ligation_window_length
            )
    return makeMotifProductionVector(motif_production_vector_dct)

def _motif_production_array_to_dct(motif_production_array: np.ndarray,
        motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int
        ) -> dict:
    """
    transforms a motif array into a motif vector

    Parameters:
    -----------
    motif_production_array : np.ndarray

    Returns:
    --------
    motif_production_vector : MotifProductionVector
    """
    motif_production_vector_dct = {}
    number_of_letters = len(alphabet)

    motif_categories = _return_motif_categories(motiflength)

    if maximum_ligation_window_length < 4:
        ligation_window_lengths = np.array([maximum_ligation_window_length])
    else:
        ligation_window_lengths = np.arange(4,maximum_ligation_window_length+1)

    mpd = make_motif_production_dct(
            alphabet,
            motiflength,
            maximum_ligation_window_length
            )
    for ligation_window_length in ligation_window_lengths:
        product_categories, template_categories, ligation_spots = _determine_product_and_template_categories_and_ligation_spots(motiflength,
                maximum_ligation_window_length,
                ligation_window_length
                )

        for product_category, template_category, ligation_spot in itertools.product(product_categories, template_categories, ligation_spots):
            if not _valid_production_channel(product_category, template_category,
                ligation_window_length, ligation_spot,
                maximum_ligation_window_length):
                continue
            reaction_key = _production_channel_id(product_category, template_category,
                    ligation_window_length, ligation_spot)
            mpa_indices = _reaction_indices(product_category, template_category,
                    ligation_window_length, ligation_spot,
                    maximum_ligation_window_length, axes_moved=False)

            destination_axes , source_axes= _moved_axes(ligation_window_length,ligation_spot,
                    maximum_ligation_window_length)
            motif_production_vector_dct[reaction_key] = np.moveaxis(
                    motif_production_array,
                    source_axes,
                    destination_axes)[mpa_indices]
    return motif_production_vector_dct

def _moved_axes(ligation_window_length : int,
        ligation_spot : int,
        maximum_ligation_window_length : int):
    """
    returns the axes_indixes of the overlap
    in the vector (source) and in the array (destination)
    such that the motif is not interrupted in the vector and the ligation spot
    is in the center of the ligation window for the array.
    For the array, periodic boundary conditions treat longer arrays,
    where the end of the motifs is indicated by a 0 either in the motif itself
    or its hybridized partner.
    """
    ligation_spot_relative_to_center = ligation_spot-(ligation_window_length-ligation_window_length//2-1)
    source = np.arange(min(0,ligation_spot_relative_to_center),max(0,ligation_spot_relative_to_center))
    product_source = (maximum_ligation_window_length+source)%maximum_ligation_window_length
    product_destination = (maximum_ligation_window_length-source[::-1]-1)%maximum_ligation_window_length
    template_source = maximum_ligation_window_length+product_destination
    template_destination = maximum_ligation_window_length+product_source
    source = list(product_source) + list(template_source)
    destination = list(product_destination) + list(template_destination)
    return source, destination


def _reaction_indices(product_category : str,
        template_category : str,
        ligation_window_length : int,
        ligation_spot : int,
        maximum_ligation_window_length : int,
        axes_moved : bool = True
        ) -> tuple:
    motif_categories = _return_motif_categories(maximum_ligation_window_length)#FIXME: ignore monomers
    product_length = (ligation_window_length
            -int(product_category not in motif_categories[-2:])
            -int(product_category not in motif_categories[-3:-1])
            )
    # product
    left_reactant_length = ligation_spot+int(product_category in motif_categories[-2:])
    right_reactant_length = product_length-left_reactant_length
    product_first_part_overlap_length = max(0,
            left_reactant_length-maximum_ligation_window_length+maximum_ligation_window_length//2)
    product_second_part_overlap_length = max(0,
            right_reactant_length - maximum_ligation_window_length//2)
    length_from_first_product_part = min(left_reactant_length,
            maximum_ligation_window_length-maximum_ligation_window_length//2)
    length_from_second_product_part = min(right_reactant_length,
            maximum_ligation_window_length//2)
    left_ligation_window_length = left_reactant_length + int(product_category not in motif_categories[-2:])
    right_ligation_window_length = ligation_window_length-left_ligation_window_length
    ligation_window_shift = ligation_spot-ligation_window_length+ligation_window_length//2+1
    #assert(left_ligation_window_length+product_second_part_overlap_length)
    #length_from_first_product_part-product_second_part_overlap_length-int(product_category in motif_categories[-1:])

    if axes_moved:
        mpa_indices = (slice(1,None),)*product_second_part_overlap_length
        mpa_indices += (0,)*(maximum_ligation_window_length-maximum_ligation_window_length//2-length_from_first_product_part-product_second_part_overlap_length)
        mpa_indices += (slice(1,None),)*(length_from_first_product_part-1)
        mpa_indices += (slice(None),)*2
        mpa_indices += (slice(1,None),)*(length_from_second_product_part-1)
        mpa_indices += (0,)*(maximum_ligation_window_length-len(mpa_indices)-product_first_part_overlap_length)
        mpa_indices += (slice(1,None),)*product_first_part_overlap_length
    else:
        mpa_indices = (0,)*max(0,maximum_ligation_window_length-maximum_ligation_window_length//2-left_ligation_window_length+ligation_window_shift)
        mpa_indices += (0,)*int(product_category not in motif_categories[-2:])
        mpa_indices += (slice(1,None),)*(left_reactant_length-1)
        mpa_indices += (slice(None),)*2
        mpa_indices += (slice(1,None),)*(right_reactant_length-1)
        mpa_indices += (0,)*(max(0,maximum_ligation_window_length-len(mpa_indices)))

    #template
    template_length = (ligation_window_length
            -int(template_category not in motif_categories[-2:])
            -int(template_category not in motif_categories[-3:-1])
            )
    template_second_part_length = ligation_spot+int(template_category in motif_categories[-3:-1])
    template_first_part_length = template_length-template_second_part_length
    length_from_first_template_part = min(template_first_part_length,
            maximum_ligation_window_length//2)
    length_from_second_template_part = min(template_second_part_length,
            maximum_ligation_window_length-maximum_ligation_window_length//2)
    template_first_part_overlap_length = template_first_part_length-length_from_first_template_part
    template_second_part_overlap_length = template_second_part_length-length_from_second_template_part
    if ((product_second_part_overlap_length
            +length_from_first_product_part)
            >=(maximum_ligation_window_length
            -maximum_ligation_window_length//2
            +int((product_second_part_overlap_length==0)
                or (template_second_part_length<length_from_first_product_part)))
            ):
        raise ValueError('Expected: '
                + str(product_second_part_overlap_length)+'+'
                + str(length_from_first_product_part)+'<'
                + str(maximum_ligation_window_length)+'-'
                + str(maximum_ligation_window_length//2)+'+int('
                + str(product_second_part_overlap_length)+'==0 or '
                + str(template_second_part_length) + '<'
                + str(length_from_first_product_part) +')'
                + _production_channel_id(product_category, template_category,
                    ligation_window_length, ligation_spot)
                )
    if (product_first_part_overlap_length
            +length_from_second_product_part
            >=
            maximum_ligation_window_length//2
            +int(product_first_part_overlap_length==0 or length_from_first_template_part<length_from_second_product_part)):
        raise ValueError(str(product_first_part_overlap_length)+'+'
            +str(length_from_second_product_part) +'>='
            +str(maximum_ligation_window_length) + '//2 + int('
            +str(product_first_part_overlap_length) + '==0 or '
            +str(length_from_first_template_part) +'<'
            +str(length_from_second_product_part)+'))')
    if axes_moved:
        mpa_indices += (slice(1,None),)*template_second_part_overlap_length
        mpa_indices += (0,)*(maximum_ligation_window_length//2-length_from_first_template_part-template_second_part_overlap_length)
        mpa_indices += (slice(1,None),)*(length_from_first_template_part-1)
        mpa_indices += (slice(None),)*2
        mpa_indices += (slice(1,None),)*(length_from_second_template_part-1)
        mpa_indices += (0,)*(2*maximum_ligation_window_length-len(mpa_indices)-template_first_part_overlap_length)
        mpa_indices += (slice(1,None),)*template_first_part_overlap_length
    else:
        mpa_indices += (0,)*max(0,maximum_ligation_window_length//2-right_ligation_window_length-ligation_window_shift)
        mpa_indices += (0,)*int(template_category not in motif_categories[-2:])
        mpa_indices += (slice(1,None),)*(template_first_part_length-1)
        mpa_indices += (slice(None),)*2
        mpa_indices += (slice(1,None),)*(template_second_part_length-1)
        mpa_indices += (0,)*(2*maximum_ligation_window_length-len(mpa_indices))
    return mpa_indices
