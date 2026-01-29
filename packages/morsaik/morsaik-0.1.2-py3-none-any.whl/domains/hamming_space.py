import numpy as np
from nifty8 import RGSpace
from functools import reduce

class HammingSpace(RGSpace):
    """Represents a Hamming Space

    Parameters:
    -----------
    alphabet : list of strings
        alphabet of the Hamming space.
    wordlength : int
        Number of letters in each word.
    """
    def __init__(self, alphabet, wordlength):
        self._harmonic = False
        if not isinstance(wordlength,(int,np.int64)):
            raise ValueError('Non-integer wordlength encountered')
        if not isinstance(alphabet,list):
            raise ValueError('Alphabet needs to be a list')
        self._alphabet = alphabet
        self._wordlength = wordlength
        self._shape = (len(self.alphabet),)*self.wordlength
        #
        distances = 1.
        self._rdistances = (float(distances),) * len(self._shape)
        self._hdistances = tuple(
            1. / (np.array(self.shape)*np.array(self._rdistances)))
        #
        self._dvol = 1.
        self._size = int(reduce(lambda x, y: x*y, self._shape))

    def __repr__(self):
        return ("HammingSpace(alphabet={}, wordlength={})"
                .format(self.alphabet, self.wordlength))

    @property
    def alphabet(self):
        return self._alphabet

    @property
    def wordlength(self):
        return self._wordlength
