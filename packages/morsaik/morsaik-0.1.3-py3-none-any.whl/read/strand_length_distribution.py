import numpy as np
from json import loads

from ..obj.units import make_unit, Unit

def strand_length_distribution(
        filepaths : list[str],
        alphabet : list[str],
        times_unit : Unit = make_unit('t_0'),
    ) -> dict:
    rtrn = {
        'steps' : [],
        'times' : [],
        'mean_length' : [],
        'strand_length_distribution' : np.empty((0,0))
    }

    for filepath in filepaths:
        _read_length_distribution(filepath)
        steps_times_lengths, length_distribution = _read_length_distribution(filepath)
        steps, simulation_time_array, mean_length = steps_times_lengths
        rtrn['steps'] = np.concatenate((rtrn['steps'], steps))
        rtrn['times'] = np.concatenate((rtrn['times'], simulation_time_array))
        rtrn['mean_length'] = np.concatenate((rtrn['mean_length'], mean_length))

        l_max = np.max([rtrn['strand_length_distribution'].shape[1],length_distribution.shape[1]])
        sld1 = np.zeros((rtrn['strand_length_distribution'].shape[0],l_max))
        sld1[:,:rtrn['strand_length_distribution'].shape[1]] += rtrn['strand_length_distribution']
        sld2 = np.zeros((length_distribution.shape[0],l_max))
        sld2[:,:length_distribution.shape[1]] += length_distribution
        rtrn['strand_length_distribution'] = np.concatenate((sld1,sld2),axis=0)
    return rtrn

def get_overall_length_distribution(length_distribution):
    # find maximum length
    maximum_length = np.max([len(length_distribution[ii]) for ii in range(len(length_distribution))])
    overall_length_distribution = np.zeros((len(length_distribution), maximum_length), dtype=int)
    for ii in range(len(length_distribution)):
        overall_length_distribution[ii,:len(length_distribution[ii])] = np.asarray(length_distribution[ii])
    return overall_length_distribution

def _read_length_distribution(fname = None,
            keywords = ['step', 'simulation_time', '<L>'],
        ):
    def read_first_line(line,
            keywords=keywords
            ):
        for keyword in keywords:
            line = line.replace(keyword+' = ','')
        line = line.split(' ')
        for ii in range(len(line)):
            line[ii] = loads(line[ii])
        return line

    def read_strand_length_frequency(line):
        return line.split('\t')

    def make_dct_to_array(dct):
        if not isinstance(dct,dict):
            warnings.warn('Not a dictionary.')
            return dct
        lengths = [int(key) for key in dct.keys()]
        rtrn = np.zeros(np.max(lengths))
        for key in dct.keys():
            rtrn[int(key)-1] = dct[key]
        return rtrn

    f=open(fname,'r')
    lines = f.readlines()
    measurement_number = -1
    statistics = []
    for line in lines:
        line = line.replace('\n','')
        if line[:6]=='strand':
            continue
        elif line[:4]==keywords[0]:
            measurement_number += 1
            statistics.append([[],[]])
            statistics[-1][0] = read_first_line(line,
                    keywords = keywords
                    )
            statistics[-1][1] = {}
        else:
            length, ocpn = read_strand_length_frequency(line)
            statistics[-1][1][str(length)] = ocpn
    for ii in range(len(statistics)):
        statistics[ii][1] = make_dct_to_array(statistics[ii][1])
    if measurement_number == -1:
        return (np.empty(0),np.empty(0), np.empty(0)), np.empty((0,0))
    length_distribution = get_overall_length_distribution(np.asarray(statistics, dtype=object)[:,1])
    statistics = np.asarray(statistics, dtype=object)[:,0]
    steps = np.asarray([statistics[ii][0] for ii in range(len(statistics))])
    simulation_time_array = np.asarray([statistics[ii][1] for ii in range(len(statistics))])
    mean_length = np.asarray([statistics[ii][2] for ii in range(len(statistics))])
    return (steps, simulation_time_array, mean_length), length_distribution
