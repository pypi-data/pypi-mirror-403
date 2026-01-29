import morsaik as kdi
from numpy.testing import assert_equal

def test_transform_unit_to_dict_to_unit():
    q = kdi.make_unit('m')*kdi.make_unit('s')/kdi.make_unit('kg')
    qd = kdi.transform_unit_to_dict(q)
    actual = kdi.transform_dict_to_unit(qd)
    assert_equal(q,actual)
