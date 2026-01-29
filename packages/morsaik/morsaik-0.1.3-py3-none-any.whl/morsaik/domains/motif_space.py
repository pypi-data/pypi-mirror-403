import numpy as np
from nifty8 import MultiDomain, DomainTuple
from .hamming_space import HammingSpace
from nifty8.utilities import check_object_identity, frozendict, indent
from ..obj.units import make_unit, Unit
from warnings import warn

def _motif_categories():
    return 'length{}strand','beginning','continuation','end'

def _return_motif_categories(motiflength : int = None):
    if motiflength is None:
        return _motif_categories()
    elif motiflength < 2:
        raise("motiflength needs to be at least 2")
    elif motiflength == 2:
        return _motif_categories()[1:]
    else:
        captured_strands = tuple([_motif_categories()[0].format(ii)
            for ii in range(1,motiflength-1)])
        return captured_strands+_motif_categories()[1:]

def make_hamming_dct(alphabet, motiflength, monomers_included=True):
        hamming = lambda ii : HammingSpace(alphabet,ii)
        # domain = \sum_{k=1}^{motiflength} hamming0 * hamming**k hamming0
        # consider all strands shorter than motiflength
        monomers_untracked = 1-monomers_included
        domain = [(_return_motif_categories()[0].format(ii+1), hamming(ii+1)) for ii in range(monomers_untracked,motiflength-2)]
        # add beginnings
        domain += [(_return_motif_categories()[1], hamming(motiflength-1))]
        # add continuations
        domain += [(_return_motif_categories()[2], hamming(motiflength))]
        # add ends
        domain += [(_return_motif_categories()[3],hamming(motiflength-1))]
        domain_dct = {}
        for dom in domain:
            domain_dct[dom[0]] = dom[1]
        return domain_dct

class MotifSpace(MultiDomain):
    def __init__(self, dct,
            alphabet = None,
            motiflength = None,
            units ='bits',
            _callingfrommake=False):
        if not _callingfrommake:
            raise NotImplementedError(
                'To create a MultiDomain call `MultiDomain.make()`.')
        self._alphabet = alphabet
        self._motiflength = motiflength
        self._units = make_unit(units)
        self._keys = tuple(sorted(dct.keys()))
        self._domains = tuple(dct[key] for key in self._keys)
        self._idx = frozendict({key: i for i, key in enumerate(self._keys)})

    @staticmethod
    def make(alphabet, motiflength, units : Unit = None, monomers_included=True):
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
            warn("Length of alphabet suggests that units of MotifSpace is {}".format(make_unit('bits',np.log2(len(alphabet))))+'but given units are {}.'.format(units))
        if isinstance(alphabet,int):
            alphabet = list(1 + np.arange(alphabet))
        inp = make_hamming_dct(alphabet, motiflength, monomers_included=monomers_included)

        if isinstance(inp, MotifSpace):
            return inp
        if not isinstance(inp, dict):
            raise TypeError("dict expected")
        tmp = {}
        for key, value in inp.items():
            if not isinstance(key, str):
                raise TypeError("keys must be strings")
            tmp[key] = DomainTuple.make(value)
        tmp = frozendict(tmp)
        obj = MotifSpace._domainCache.get(tmp)
        if obj is not None:
            return obj
        obj = MotifSpace(tmp,
                alphabet=alphabet,
                motiflength=motiflength,
                units=units,
                _callingfrommake=True)
        MotifSpace._domainCache[tmp] = obj
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
