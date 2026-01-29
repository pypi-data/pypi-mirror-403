import numpy as np
from nifty8 import DomainTuple
from nifty8.utilities import check_object_identity, frozendict, indent
import itertools
from typing import Union
from ..obj.units import make_unit

from .hamming_space import HammingSpace
from .motif_space import MotifSpace
from .motif_space import _return_motif_categories
# MotifDomain -> MotifSpace
# ExtensionRates, Motif fields
# st = StrandTrajectory
## -> motif concentrations(time) DomainTuple((TimeSpace,MotifSpace),
##    motif productions(time): DomainTuple((TimeSpace,MPRCSpace)
##    length distribution
##    parameters
##    
# st.motif_trajectory, st.ligation_counts, st.params = st(complexes, ligation_statistics, parameters)
# te = TrajectoryEnsemble([st for st in sts])
# ri = RateInference(method,...)
# extension_rates = ri(te)
# er = extension_rates 
# oi = ODEIntegrator(...)
# mt = oi(er,initial_motifs)

def _return_motif_production_categories(motiflength : int,
        alphabet : list,
        maximum_ligation_window_length : int
        ) -> tuple:
    return tuple(make_motif_production_dct(
        alphabet,
        motiflength,
        maximum_ligation_window_length).keys()
        )

def _production_channel_id(product_category : str,
        template_category : str,
        ligation_window_length : int,
        ligation_spot : int) -> str:
    """
    The production channel id is given by the categories of the product
    and the template as well as the ligation window length and the ligation
    spot.
    The ligation window is set such that it captures the whole hybridization
    site up to one dangling nucleotide, this means, all spots are occupied by
    letters, but the very outer ones which can (but don't have to) also be
    empty.
    """
    return product_category + '_{}_'.format(ligation_window_length) + '{}_'.format(ligation_spot) + template_category

def _determine_product_and_template_categories_and_ligation_spots(motiflength : int,
        maximum_ligation_window_length : int,
        ligation_window_length : int
        ) -> Union[list,list]:
    if maximum_ligation_window_length < 4:
        ligation_spots = np.array([maximum_ligation_window_length])-2

        product_categories = [product_category for product_category in _return_motif_categories()[-2-int(motiflength>2):-1]]
        template_categories = [template_category for template_category in _return_motif_categories()[-2:-1 if (motiflength<3) else None]]
    else:
        ligation_spots = np.arange(1,ligation_window_length-2)

        product_categories = [product_category.format(ligation_window_length-2) for product_category in _return_motif_categories()]
        template_categories = product_categories
    return product_categories, template_categories, ligation_spots

def _valid_production_channel(product_category : str,
        template_category : str,
        ligation_window_length : int,
        ligation_spot : int,
        maximum_ligation_window_length : int
        ) -> bool:
    if ligation_window_length < maximum_ligation_window_length:
        if (product_category, template_category) in itertools.product(_return_motif_categories()[-3:-1],_return_motif_categories()[-2:]):
            return False
        if (product_category, template_category) in itertools.product(_return_motif_categories()[-2:],_return_motif_categories()[-3:-1]):
            return False
    elif (product_category in _return_motif_categories()[-2:]
            and template_category in _return_motif_categories()[-3:-1]
            and ligation_spot<ligation_window_length-ligation_window_length//2-1
            ):#FIXME
        return False
    elif (product_category in _return_motif_categories()[-3:-1]
            and template_category in _return_motif_categories()[-2:]
            and ligation_spot>ligation_window_length-ligation_window_length//2-1
            ):#FIXME
        return False
    return True

def make_motif_production_dct(alphabet : list,
        motiflength : int,
        maximum_ligation_window_length : int,
        ) -> dict:
    """
    Creates a motif production dictionary.
    For the production channel id, see morsaik.domains._production_channel_id
    The main concept behind the productions is that the hybridization
    and the ligation kinetics are only characterized by the hybridization sites
    and maximally one further nucleotide of a dangling strand.
    Thus, the motif productions are specified by a ligation window that
    captures the exact hybridization and this potentially dangling end.
    In the keys, we iterate over all possible ligation windows with different
    length.
    The maximum length can be set optionally,
    else it is the motiflength, which is also the maximum
    maximum_ligation_window_length, one can set.
    For the maximum_ligation_window_length, also fully occupied strands are
    tracked, for ligation_window_lengths that are smaller than the
    maximum_ligation_window_length, those are not tracked, since they are
    considered by larger ligation windows.
    """
    if maximum_ligation_window_length is None:
        maximum_ligation_window_length = motiflength
    elif maximum_ligation_window_length > motiflength:
        raise ValueError("Maximum ligation window length needs to be smaller or equal to the motif length")
    if maximum_ligation_window_length < 4:
        ligation_window_lengths = np.array([maximum_ligation_window_length])
    else:
        ligation_window_lengths = np.arange(4,maximum_ligation_window_length+1)
    domain_dct = {}
    for ligation_window_length in ligation_window_lengths:
        product_categories, template_categories, ligation_spots = _determine_product_and_template_categories_and_ligation_spots(motiflength,
                maximum_ligation_window_length,
                ligation_window_length
                )

        central_produced_motif_space = MotifSpace.make(alphabet,ligation_window_length,monomers_included=False)
        template_motif_space = MotifSpace.make(alphabet,ligation_window_length,monomers_included=False)

        for product_category, template_category, ligation_spot in itertools.product(product_categories, template_categories, ligation_spots):
            if not _valid_production_channel(product_category, template_category,
                ligation_window_length, ligation_spot,
                maximum_ligation_window_length):
                continue
            product_space = central_produced_motif_space[product_category]
            template_space = template_motif_space[template_category]
            reaction_key = _production_channel_id(product_category, template_category,
                    ligation_window_length, ligation_spot)
            domain_dct[reaction_key] = DomainTuple.make(product_space[:]+template_space[:])
    return domain_dct

class MotifProductionSpace(MotifSpace):
    """
    Domain of Motif Productions,
    like motif production rate constants,
    ligations projected onto motif space.
    """
    def __init__(self, dct,
            alphabet = None,
            motiflength = None,
            maximum_ligation_window_length=None,
            units ='bits',
            _callingfrommake=False):
        if not _callingfrommake:
            raise NotImplementedError(
                'To create a MultiDomain call `MultiDomain.make()`.')
        self._alphabet = alphabet
        self._motiflength = motiflength
        self._units = make_unit(units)
        self._maximum_ligation_window_length = motiflength if maximum_ligation_window_length is None else maximum_ligation_window_length
        self._keys = tuple(sorted(dct.keys()))
        self._domains = tuple(dct[key] for key in self._keys)
        self._idx = frozendict({key: i for i, key in enumerate(self._keys)})

    @staticmethod
    def make(alphabet : list,
             motiflength : int,
             maximum_ligation_window_length : int
             ) -> object:
        """Creates a MultiDomain object from a dictionary of names and domains

        Parameters
        ----------
        inp : MultiDomain or dict{name: DomainTuple}
            The already built MultiDomain or a dictionary of DomainTuples

        Returns
        ------
        A MultiDomain with the input Domains as domains
        """
        if isinstance(alphabet,int):
            alphabet = list(1 + np.arange(alphabet))

        inp = make_motif_production_dct(alphabet,
                motiflength,
                maximum_ligation_window_length)

        if isinstance(inp, MotifProductionSpace):
            return inp
        if not isinstance(inp, dict):
            raise TypeError("dict expected")
        tmp = {}
        for key, value in inp.items():
            if not isinstance(key, str):
                raise TypeError("keys must be strings")
            tmp[key] = DomainTuple.make(value)
        tmp = frozendict(tmp)
        obj = MotifProductionSpace._domainCache.get(tmp)
        if obj is not None:
            return obj
        obj = MotifProductionSpace(tmp, alphabet=alphabet, motiflength=motiflength, maximum_ligation_window_length=maximum_ligation_window_length, _callingfrommake=True)
        MotifProductionSpace._domainCache[tmp] = obj
        return obj

    @property
    def alphabet(self):
        return self._alphabet

    @property
    def number_of_letters(self):
        return len(self._alphabet)

    @property
    def maximum_ligation_window_length(self):
        return self._maximum_ligation_window_length

    @property
    def motiflength(self):
        return self._motiflength
