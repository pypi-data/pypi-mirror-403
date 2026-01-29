import nifty8 as ift
from .motif_space import MotifSpace, _return_motif_categories
from ..obj.units import make_unit, Unit

def makeExtentiveMotifBreakageSpace(alphabet : list,
                                motiflength : int,
                                units : Unit = None
                                ):
    ms = MotifSpace.make(alphabet,
                    motiflength,
                    units
                    )
    motif_categories = _return_motif_categories(motiflength)
    ending_categories = motif_categories[:-3]+(motif_categories[-1],)
    beginning_categories = motif_categories[:-2]

    ending_space = ift.MultiDomain.make(
        {k:ms[k] for k in ending_categories if k in ms.keys()}
        # https://stackoverflow.com/a/3953386 on 202311031800
        )
    beginning_space = ift.MultiDomain.make(
        {k:ms[k] for k in beginning_categories if k in ms.keys()}
        # https://stackoverflow.com/a/3953386 on 202311031800
        )
    extentive_hyphen_space = {}
    for ending_key in ending_space.keys():
        for beginning_key in beginning_space.keys():
            hyphen_key = ending_key + '-' + beginning_key
            extentive_hyphen_space[hyphen_key] = ift.DomainTuple.make((ending_space[ending_key][0],
                                                                       beginning_space[beginning_key][0]))
    extentive_hyphen_space = ift.MultiDomain.make(extentive_hyphen_space)
    return extentive_hyphen_space
