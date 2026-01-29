def split_config(config : dict, split_keys : list):
    """
    splits config dictionary infto list of config files
    by checking how many parameter sets there are for the split_keys
    and separating the config files at those split_keys.
    The keys of the config dictionary that are not split_keys,
    are the same for every config in the resulting list.
    """
    from copy import deepcopy
    splitted_config_len = len(config[split_keys[0]])
    splitted_config = [deepcopy(config) for jj in range(splitted_config_len)]

    key_values = {}
    for split_key in split_keys:
        vl = deepcopy(config[split_key])
        if isinstance(vl, list) and len(vl)==splitted_config_len:
            key_values[split_key] = vl
        else:
            key_values[split_key] = [vl,]*splitted_config_len

    for jj in range(splitted_config_len):
        for split_key in split_keys:
            splitted_config[jj][split_key] = key_values[split_key][jj]

    return splitted_config
