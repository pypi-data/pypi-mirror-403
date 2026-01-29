from ..obj.units import make_unit

def config(config_yaml_path : str) -> dict:
    """
    reads yml file and returns it as dictionary

    Parameters:
    -----------
    config_yaml_path : string
        path of the yml-file

    Returns:
    --------
    config_dct : dict
    """
    import yaml
    with open(config_yaml_path) as f:
        config_dct = yaml.safe_load(f)
    print("Read config yaml.")
    return config_dct

def symbol_config(
        symbol : str = None,
        unitformat : bool = False
    ) -> dict:
    if symbol is None:
        return config('./config/symbols.yml')
    else:
        if unitformat:
            return make_unit(config('./config/symbols.yml')[symbol][1])
        else:
            return config('./config/symbols.yml')[symbol]
