import numpy as np
import nifty8 as ift
from nifty8 import MultiDomain, DomainTuple
from nifty8.utilities import check_object_identity, frozendict, indent

from warnings import warn

from typing import Union

from .hamming_space import HammingSpace
from .motif_space import MotifSpace
from ..obj.units import make_unit, Unit
from .motif_space import _return_motif_categories

def MotifHyphenSpace(alphabet : list,
                         motiflength : int,
                         units : Unit,
                         ) -> MotifSpace:
    ms = MotifSpace.make(alphabet, motiflength, units=units, monomers_included = False)
    dct = {}
    for key in ms.keys():
        for hyphen_index in range(1,ms[key][0].wordlength):
            hyphen_key = key + '_{}'.format(hyphen_index)
            dct[hyphen_key] = ms[key][0]
    return ift.MultiDomain.make(dct)

class MotifHyphenSpace(MotifSpace):
    """
    Domain of Motif Hyphens,
    like motif breakage rate constants,
    ligations projected onto motif space.
    """

    @staticmethod
    def make(alphabet, motiflength, units : Unit = None):
        """Creates a MultiDomain object from a dictionary of names and domains

        Parameters
        ----------
        inp : MultiDomain or dict{name: DomainTuple}
            The already built MultiDomain or a dictionary of DomainTuples

        Returns
        ------
        A MultiDomain with the input Domains as domains
        """
        if units is None:
            units = make_unit('bits',np.log2(len(alphabet)))
        else:
            units = make_unit(units)
        if (units/make_unit('bits', np.log2(len(alphabet))))!=1.:
            warn("Length of alphabet suggests that units of MotifSpace is {}".format(make_unit('bits', np.log2(len(alphabet))))+'but given units are {}.'.format(units))
        if isinstance(alphabet,int):
            alphabet = list(1 + np.arange(alphabet))
        inp = make_hyphen_dct(alphabet, motiflength)

        if isinstance(inp, MotifHyphenSpace):
            return inp
        if not isinstance(inp, dict):
            raise TypeError("dict expected")
        tmp = {}
        for key, value in inp.items():
            if not isinstance(key, str):
                raise TypeError("keys must be strings")
            tmp[key] = DomainTuple.make(value)
        tmp = frozendict(tmp)
        obj = MotifHyphenSpace._domainCache.get(tmp)
        if obj is not None:
            return obj
        obj = MotifHyphenSpace(tmp,
                alphabet=alphabet,
                motiflength=motiflength,
                units=units,
                _callingfrommake=True)
        MotifHyphenSpace._domainCache[tmp] = obj
        return obj
    @property
    def motiflength(self):
        return self._motiflength
    @property
    def alphabet(self):
        return self._alphabet
    @property
    def number_of_letters(self):
        return len(self._alphabet)
    @property
    def units(self):
        return self._units

def _hyphen_id(motif_category : str,
        hyphen_spot : int) -> str:
    """
    The hyphen id is given by the categories of the motif
    and hyphen spot.
    """
    return motif_category + '_{}'.format(hyphen_spot)

def _determine_motif_categories_and_hyphen_spots(motiflength : int,
        ) -> Union[list,list]:
    if motiflength < 4:
        # Hyphen spot goes for motiflength = 2 only one value for continuations, for beginnings and endings no value
        # for motiflength = 3 for ending no value (already considered in continuation),
        # for beginning and for continuation one value
        hyphen_spots = np.array([motiflength])-2

        motif_categories = _return_motif_categories()[-2-int(motiflength>2):-1]
    else:
        """
        all central hyphens are considered no matter the category, additionally
        - for strands: all hyphen spots
        - for beginnings: all hyphens before the central hyphen
        - for ends: all hyphens after the central hyphen
        """
        ligation_spots = np.arange(1,motiflength-2)

        product_categories = [product_category.format(ligation_window_length-2) for product_category in _return_motif_categories()]
    return product_categories, template_categories, ligation_spots


def make_hyphen_dct(alphabet : list,
                          motiflength : int,
                          ) -> dict:
    """
    Creates a motif hyphen dictionary.
    Parameters:
    -----------
    alphabet : list
    motiflength : int,

    Returns:
    --------
    motif_hyphen_dct : dict
    """
    hyphen_dct = {}
    hamming = lambda ii : HammingSpace(alphabet,ii)
    motif_categories = _return_motif_categories(motiflength=motiflength)
    # completely captured strands (1-mers don't have hyphens)
    for strandlength in range(2,motiflength-1):
        motif_category = motif_categories[:-3][strandlength-1]
        hyphen_ids =[_hyphen_id(motif_category,hyphen_spot) for hyphen_spot in np.arange(1,strandlength)]
        for hyphen_key in hyphen_ids:
            hyphen_dct[hyphen_key] = hamming(strandlength)
    # beginnings
    motif_category = motif_categories[-3]
    hyphen_ids =[_hyphen_id(motif_category,hyphen_spot) for hyphen_spot in np.arange(1,motiflength-motiflength//2)]
    for hyphen_key in hyphen_ids:
        hyphen_dct[hyphen_key] = hamming(motiflength-1)
    # continuations
    motif_category = motif_categories[-2]
    hyphen_ids = [_hyphen_id(motif_category, motiflength-motiflength//2)]
    for hyphen_key in hyphen_ids:
        hyphen_dct[hyphen_key] = hamming(motiflength)
    # ends
    motif_category = motif_categories[-1]
    hyphen_ids =[_hyphen_id(motif_category,hyphen_spot) for hyphen_spot in np.arange(motiflength-motiflength//2,motiflength-1)]
    for hyphen_key in hyphen_ids:
        hyphen_dct[hyphen_key] = hamming(motiflength-1)
        for key in hyphen_dct.keys():
            print(key)
    return hyphen_dct
