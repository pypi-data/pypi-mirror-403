import numpy as np
from json import loads
from typing import Union

from ..obj.units import make_unit
from ..utils.manage_strand_reactor_files import read_txt

from .strand_motifs_trajectory import _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex
from .strand_motifs_trajectory import _transform_motif_string_to_index_tuple

from ..obj.times_vector import TimesVector
from ..obj.motif_production_vector import MotifProductionVector
from ..obj.motif_production_vector import _create_empty_motif_production_dict
from ..obj.motif_production_trajectory import MotifProductionTrajectory

from ..domains.motif_production_space import make_motif_production_dct, _production_channel_id
from ..domains.motif_space import _return_motif_categories, _motif_categories

def strand_motifs_productions_trajectory(filepaths : list,
        alphabet : list,
        motiflength : int,
        maximum_ligation_window_length : int
    ) -> MotifProductionTrajectory:
    time_unit = make_unit('t_0')
    motif_production_vectors = []
    total_physical_times = []
    for filepath in filepaths:
        step, current_physical_times, ligstr = _step_simulation_and_ligation_strands_array(filepath)
        total_physical_times = total_physical_times + list(current_physical_times)
        for time_index in range(len(current_physical_times)):
            motif_production_vectors = motif_production_vectors + [_extract_motif_production_vector(ligstr[time_index],
                    motiflength,
                    alphabet,
                    maximum_ligation_window_length)]
    total_physical_times = TimesVector(np.asarray(total_physical_times), time_unit)
    return MotifProductionTrajectory(motif_production_vectors,total_physical_times)

def _calculate_ligation_window_length_and_spot_and_motifs(ending_strand : str,
        leaving_strand : str,
        template_strand_1st_part : str,
        template_strand_2nd_part :str,
        motiflength : int,
        maximum_ligation_window_length : int
        ) -> Union[int,int,str,str,str,str,str]:
    """
    Returns:
    --------
    ligation_window_length : int,
    ligation_spot : int,
    product_motif : str,
    ending_motif : str,
    leaving_motif : str
    template_motif_1st_part : str,
    template_motif_2nd_part : str
    """
    left_ligation_window_length = min(
            len(ending_strand),
            len(template_strand_2nd_part)
            ) + 1
    right_ligation_window_length = min(
            len(leaving_strand),
            len(template_strand_1st_part)
            ) + 1
    ligation_window_length = left_ligation_window_length + right_ligation_window_length
    if ligation_window_length > maximum_ligation_window_length:
        if (left_ligation_window_length
                > (maximum_ligation_window_length -
                    maximum_ligation_window_length//2)):
            if right_ligation_window_length > maximum_ligation_window_length//2:
                left_ligation_window_length = (maximum_ligation_window_length - maximum_ligation_window_length//2)
                right_ligation_window_length = maximum_ligation_window_length//2
            else:
                left_ligation_window_length = (maximum_ligation_window_length
                        - right_ligation_window_length)
        else:
            right_ligation_window_length = maximum_ligation_window_length - left_ligation_window_length
        ligation_window_length = left_ligation_window_length + right_ligation_window_length
    ligation_spot = left_ligation_window_length-1
    ending_motif = ending_strand[-(motiflength-1):]
    leaving_motif = leaving_strand[:(motiflength-1)]
    product_motif = ending_motif[-left_ligation_window_length:] + leaving_motif[:right_ligation_window_length]
    template_motif_1st_part = template_strand_1st_part[-right_ligation_window_length:]
    template_motif_2nd_part = template_strand_2nd_part[:left_ligation_window_length]
    return ligation_window_length, ligation_spot, product_motif, ending_motif, leaving_motif, template_motif_1st_part, template_motif_2nd_part

def _extract_motif_production_vector(ligstr,
        motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int
        ) -> MotifProductionVector:
    motif_production_dct = _create_empty_motif_production_dict(motiflength,
            alphabet,
            maximum_ligation_window_length)
    for reaction_index in range(len(ligstr)):
        (central_produced_motif,
                ending_motif,
                leaving_motif,
                template_motif,
                production_channel_id
                ) = _motif_production_reactants(
                        *ligstr[reaction_index],
                        motiflength,
                        maximum_ligation_window_length
                        )
        production_index = _transform_motif_string_to_index_tuple(central_produced_motif+template_motif,
                alphabet)
        try:
            motif_production_dct[production_channel_id][production_index] += 1
        except KeyError:
            print(motiflength)
            print(motif_production_dct.keys())
            print(production_index)
            print(central_produced_motif)
            print(template_motif)
            print(production_channel_id)
            raise KeyError
    motif_production_vector = MotifProductionVector(motiflength,alphabet, '1', maximum_ligation_window_length)
    return motif_production_vector(motif_production_dct)

def _load_complex(cc):
    cc = '['+str(cc)+']'
    return cc.replace('”','"').replace('−','-').replace("None","0")

def _read_key(keys : str) -> Union[tuple,str]:
    '''
    returns a tuple of the first ligation statistics stated in keys
    according to the formula below
    and the remaining string

    key: ll-lr|LS-LR|LT|nl-nr|sl-sr|kl-kr|lt|es-ls:n,
    value: #

    ll = length of left segment
    lr = lenght of right segment
    LL = length of left strand (note: segment != strand)
    LR = lnegth of right strand (note: segment != strand)
    LT = length of template strand (note: segment != strand)
    
    nl = number of mismatches of left segment
    nr = number of mismatches of right segment
    sl = number of mismatches left of ligation site
    sr = number of mismatches right of ligation site
    kl = dehyb rate of left segment
    kr = dehyb rate of right segment

    lt = ligation triplex
    es = ending strand
    ls = leaving strand
    n = occupation number?

    PARAMETERS:
    -----------
    keys : string
        string in the format ll-lr|LS-LR|LT|nl-nr|sl-sr|kl-kr|lt|es-ls:n,
        and eventually further ligations afterwards

    RETURN:
    -------
    rtrn : tuple
        in the format (ll,lr,LS,LR,LT,nl,nr,sl,sr,kl,kr,lt,es,ls,n)
    keys : string
        remaining string, i.e. the original string after lstripping the rtrn
        tuple
    '''
    separators = ['-','|','-','|','|','-','|','-','|','-','|[',']|','-',':',',']
    types = [int,int,int,int,int,
            int,int,int,int,np.float64,np.float64,
            _load_complex,str,str,int]
    rtrn = ()
    for ii in range(len(separators)):
        current, _, keys = keys.partition(separators[ii])
        rtrn += (types[ii](current),)
    return rtrn, keys

def _ligation_statistics(fname : str = None,
        skiprows : int = 2) -> Union[np.ndarray,np.ndarray,list]:
    '''
    reads the "ligation_statistics.txt" output file and returns the output as
    lists
    
    PARAMETERS:
    -----------
    fname : string (optional)
        path to the ligation_statistics file
        default : './data/ligation_statistics.txt'
    skiprows : int, optional
        Skip the first `skiprows` lines, including comments
        when reading the file;
        default : 2

    RETURN:
    -------
    step : np.array
        the simulation steps
    total_physical_time : array
        corresponding physical times
    ligation_statistics : list of tuples
        ligation_statistics at corresponding simulation step in the format
        (ll,lr,LS,LR,LT,nl,nr,sl,sr,kl,kr,lt,es,ls,n)
    '''
    replace=[['step = ',''],[' simulation_time = ',';'],['\n{',';{'],[' ',''],[';',' ']]
    x = read_txt(fname, replace=replace)
    x = np.array(x.split()).reshape(-1,3).transpose()
    step = np.array(x[0], dtype = float)
    total_physical_time = np.array(x[1], dtype = float)
    complexes=x[2]
    ligation_statistics = [[]]*len(step)
    for ii in range(len(step)):
        keys = complexes[ii].lstrip('{').rstrip('}')
        ligation_statistics[ii] = []
        while keys != '':
            lg, keys = _read_key(keys)
            ligation_statistics[ii].append(lg)
    return step, total_physical_time, ligation_statistics

def _step_simulation_and_ligation_strands_array(fname : str =None,
        skiprows : int = 2) -> Union[list,list,list]:
    """
    Reads the ligation file and returns its content.

    PARAMETERS:
    -----------
    fname : string
        The filename (and path) of the ligation_statistics file
        default: None
    skiprows : int
        Integer of how many lines are skipped in the ligation_statistics file
        because they indicate the columns
        default : 2

    RETURNS:
    --------
    step : integer list
        Computation steps at which ligations have been measured
    total_physical_time : list
        The physical time at those steps
    ligation_strands : list
        List of tuples of the format
        (ending_strand, leaving_strand, leaving_template, ending_template)
        Like the output of _splitted_template_strand
    """
    step, total_physical_time, ligation_statistics = _ligation_statistics(fname=fname, skiprows=2)
    rtrn = [[]]*len(step)
    for ii in range(len(step)):
        rtrn[ii] = []
        if len(ligation_statistics[ii])!=0:
            for ls in ligation_statistics[ii]:
                binary_complex = ls[-4]
                ending_segment = ls[-3]
                leaving_segment = ls[-2]
                rtrn[ii].append(tuple(
                _strip_zeros(sequence) for sequence in _splitted_template_strand(binary_complex,
                        ending_segment,
                        leaving_segment)
                ))
    return step, total_physical_time, rtrn

def _strip_zeros(sequence : str):
    return sequence.lstrip('0').rstrip('0')

def _ligation_spot(binary_complex, ending_segment, leaving_segment):
    '''
    returns the index of the ligation spot in terms of segments
    '''
    try:
        binary_complex = loads(binary_complex)
    except:
        print("binary_complex cannot be interpreted by json.loads. I assume, it already is a list.")
    # check indices of upper strand
    index_ending_segment = np.where(np.array(binary_complex)==('5'+ending_segment+'3'))
    index_leaving_segment = np.where(np.array(binary_complex)==('5'+leaving_segment+'3'))
    ligation_spot = []
    if len(index_ending_segment[0])>0 and len(index_leaving_segment[0])>0:
        # check that the indices fulfill i2-i1=2
        # and that in between there is a ligation spot
        for ii in index_ending_segment[0][index_ending_segment[1]==0]+1:
            if ii in index_leaving_segment[0][index_leaving_segment[1]==0]-1:
                if binary_complex[ii] == ["|","-"]:
                    ligation_spot.append([ii,0])
    # check indices of lower strand
    index_ending_segment = np.where(np.array(binary_complex)==('3'+ending_segment[::-1]+'5'))
    index_leaving_segment = np.where(np.array(binary_complex)==('3'+leaving_segment[::-1]+'5'))
    if len(index_ending_segment[0])>0 and len(index_leaving_segment[0])>0:
        # check that the indices fulfill i2-i1=2
        # (note that in the lower strand we go from right to left)
        # and that in between there is a ligation spot
        for ii in index_ending_segment[0][index_ending_segment[1]==1]-1:
            if ii in index_leaving_segment[0][index_leaving_segment[1]==1]+1:
                if binary_complex[ii] ==["-","|"]:
                    ligation_spot.append([ii,1])
    if len(ligation_spot) > 1:
        print("Warning: more than one possible ligation spot.")
    elif len(ligation_spot) == 0:
        print("Warning: Did not find any one possible ligation spot.")
        print(binary_complex,"\n", ending_segment,"\n", leaving_segment)
    return np.array(ligation_spot).transpose()

def _splitted_template_strand(binary_complex : str,
        ending_segment : str,
        leaving_segment : str) -> Union[str,str,str,str]:
    '''
    gives the leaving strand, the ending strand and the two parts of the
    template in clockwise direction, i.e.
    ending_strand | leaving_strand
    etalpmet_gnidne - etalpmet_gnivael
    resp. if ligation_happens_in_lower_strand
    leaving_template - ending_template
    dnarts_gniveal | dnarts_gnidne

    PARAMETERS:
    -----------
    binary_complex : string
    ending_segment : string
    leaving_segment : string

    RETURNS:
    --------
    ending_strand : string
        left strand from 5' to 3'
    leaving_strand : string
        right strand from 5' to 3'
    leaving_template : string
        left template strand from 5' to 3'
    ending_template : string
        right template strand from 5' to 3'
    '''
    ligation_spot = _ligation_spot(binary_complex, ending_segment, leaving_segment)
    if ligation_spot[1][0] != 1 and ligation_spot[1][0]!=0:
        raise NotImplementedError("The ligation spot seems to be neither in the lower nor the upper strand")
    if len(ligation_spot[0])>1:
        print("I'll consider the first ligation spot")
    ligation_happens_in_lower_strand = bool(ligation_spot[1][0])
    ligation_spot = ligation_spot[0][0]
    try:
        binary_complex = loads(binary_complex)
    except:
        pass
    try:
        binary_complex = np.array(binary_complex)
    except:
        pass
    left_complexpart = binary_complex[:ligation_spot]
    right_complexpart = binary_complex[ligation_spot+1:]
    if ligation_happens_in_lower_strand:
        leaving_template , leaving_strand = _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(left_complexpart)
        ending_template, ending_strand = _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(right_complexpart)
    else:
        ending_strand, ending_template = _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(left_complexpart)
        leaving_strand, leaving_template = _extract_upper_and_lower_strands_as_continuous_strings_from_structure_of_complex(right_complexpart)
    ending_strand = _strip_zeros(ending_strand).split('0')[-1]
    leaving_strand = _strip_zeros(leaving_strand).split('0')[0]
    leaving_template = _strip_zeros(leaving_template).split('0')[-1]
    ending_template = _strip_zeros(ending_template).split('0')[0]
    return ending_strand, leaving_strand, leaving_template, ending_template

def _determine_production_channel_id(
        ending_motif : str,
        leaving_motif : str,
        template_motif_1st_part : str,
        template_motif_2nd_part : str,
        ligation_window_length : int,
        ligation_spot : int,
        motiflength:int,
        )->str:
    motif_categories = [motif_category.format(ligation_window_length-2) for motif_category in _motif_categories()]
    if len(ending_motif)<ligation_spot+1:
        product_begins = True
    else:
        product_begins = False
    if len(leaving_motif)<ligation_window_length-(ligation_spot+1):
        product_ends = True
    else:
        product_ends = False
    if len(template_motif_2nd_part)<ligation_spot+1:
        template_ends = True
    else:
        template_ends = False
    if len(template_motif_1st_part)<ligation_window_length-(ligation_spot+1):
        template_begins = True
    else:
        template_begins = False

    if product_begins or not product_ends:
        product_category = motif_categories[-2-product_begins-product_ends]
    else:
        product_category = motif_categories[-1]

    if template_begins or not template_ends:
        template_category = motif_categories[-2-template_begins-template_ends]
    else:
        template_category = motif_categories[-1]
    return _production_channel_id(product_category, template_category,
            ligation_window_length, ligation_spot)

def _motif_production_reactants(ending_sequence : str,
        leaving_sequence : str,
        leaving_template_sequence : str,
        ending_template_sequence : str,
        motiflength : int,
        maximum_ligation_window_length : int
        ) -> Union[str,str,str,str,str]:
    """
    Returns:
    --------
    product_motif : str,
    ending_motif : str,
    leaving_motif : str,
    template_motif : str,
    production_channel_id : str
    """
    ending_motif = ending_sequence[-(motiflength-1):]
    leaving_motif = leaving_sequence[:(motiflength-1)]

    (ligation_window_length,
            ligation_spot,
            product_motif,
            ending_motif,
            leaving_motif,
            template_motif_1st_part,
            template_motif_2nd_part
            ) = _calculate_ligation_window_length_and_spot_and_motifs(
                    ending_sequence,
                    leaving_sequence,
                    leaving_template_sequence,
                    ending_template_sequence,
                    motiflength,
                    maximum_ligation_window_length
                    )
    production_channel_id = _determine_production_channel_id(
            ending_motif,
            leaving_motif,
            template_motif_1st_part,
            template_motif_2nd_part,
            ligation_window_length,
            ligation_spot,
            motiflength
            )

    template_motif = template_motif_1st_part+template_motif_2nd_part
    return product_motif, ending_motif, leaving_motif, template_motif, production_channel_id
