import units
from warnings import warn
from typing import Union

units_dct = {} #_load_units()
Unit = units.quantity.Quantity

def make_unit(unit : Union[units.unit, Unit, str], prefactor : float = 1.):
    """
    checks if unit is a units object or quantity and multiplies (weights) it with the quantity value,
    if it is a string, it transforms it and returns the string as a units.quantity.Quantity
    else it raises an ValueError

    Parameters:
    -----------
    unit : units.unit or str

    Returns:
    --------
    unit : units.quantity.Quantity
    """
    if isunits_unit(unit):
        return unit(prefactor)
    elif isunit(unit):
        return prefactor*unit
    elif unit in ['', '1.'] or unit is None or unit==1.:
        warn("unit not specified, will treat it as one.")
        return 1.
    elif unit in ['1'] or unit == 1:
        warn("unit not specified, will treat it as one.")
        return 1
    elif isinstance(unit,dict):
        return transform_dict_to_unit(unit)
    elif isinstance(unit, str):
        warn("unit is string, will make it units object but this can lead to misinterpretation")
        return units.unit(unit)(prefactor)
    else:
        raise ValueError("unit {} is not a units.unit nor units.quantity.Quantity nor string".format(unit))

def isunits_unit(unit):
    return isinstance(unit, (units.LeafUnit,units.ComposedUnit, units.NamedComposedUnit))

def isunit(unit):
    return isinstance(unit, Unit)

def _load_units(symbol_config_path : str):
    """
    """
    raise NotImplementedError("load units not implemented yet. Sorry for the inconvenience.")

def transform_unit_to_dict(unit : Unit) -> dict:
    unit_dct = {}
    try:
        unit_dct['prefactor'] = unit.get_num()
    except AttributeError:
        if isinstance(unit,int) or isinstance(unit,float):
            unit_dct['prefactor'] = unit
            unit_dct['numerator_units'] = [None,]
            unit_dct['denominator_units'] = [None,]
            unit_dct['multiplier'] = 1.
            return unit_dct
        else:
            unit_dct['prefactor'] = 1.
            unit_dct['numerator_units'] = [str(unit),]
            unit_dct['denominator_units'] = [None,]
            unit_dct['multiplier'] = 1.
            return unit_dct
    unit = unit.get_unit()
    if isinstance(unit,units.LeafUnit):
        unit_dct['numerator_units'] = [unit.specifier,]
        unit_dct['denominator_units'] = [None,]
        unit_dct['multiplier'] = 1.
    else:
        unit_dct['numerator_units'] = [uu.specifier for uu in unit.orig_numer]
        unit_dct['denominator_units'] = [uu.specifier for uu in unit.orig_denom]
        unit_dct['multiplier'] = unit.orig_multiplier
    return unit_dct

def transform_dict_to_unit(unit_dct : dict) -> Unit:
    unit = 1.
    for numerator_unit in unit_dct['numerator_units']:
        unit = unit*make_unit(numerator_unit)
    for denominator_unit in unit_dct['denominator_units']:
        unit = unit/make_unit(denominator_unit)
    try:
        unit.orig_mutliplier = unit_dct['multiplier']
    except AttributeError:
        unit *= unit_dct['multiplier']
    return make_unit(unit, unit_dct['prefactor'])

def transform_unit_to_str(unit : Unit) -> str:
    unit = transform_unit_to_dict(unit)
    prefactor = unit['multiplier']*unit['prefactor']
    if prefactor == 1.:
        prefactor = ''
    else:
        prefactor = str(prefactor)
    numerator_units = ''
    for nu in unit['numerator_units']:
        numerator_units += str(nu) + ' '
    if unit['denominator_units'] == [None,]:
        unit =  numerator_units
    else:
        denominator_units = ''
        for du in unit['denominator_units']:
            denominator_units += str(du) + ' '
        unit = "\\frac\{" + numerator_units + "\}\{"+  denominator_units + "\}"
    if len(unit)*len(prefactor) > 0:
        prefactor += ' '
    print(prefactor)
    print(unit)
    return '$[' + prefactor + unit + ']$'
