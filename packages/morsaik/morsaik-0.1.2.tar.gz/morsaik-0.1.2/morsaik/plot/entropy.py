import matplotlib.pyplot as plt
import numpy as np

from ..obj.motif_trajectory import _motif_trajectory_as_array
from ..obj.units import transform_unit_to_str
from .colors import _choose_color

from matplotlib.colors import LinearSegmentedColormap

def entropy(times, 
        x_t,
        linestyle = '-',
        color = 'b',
        alpha = 1.,
        label = None,
        axis = None
    ) -> None:
    if axis is None:
        axis = plt.gca()
    x_t = x_t.reshape((len(x_t),-1))
    x_total = np.sum(x_t, axis=1)
    p = x_t / x_total[:,None]
    entrpy = np.zeros(p.shape)
    entrpy[p!=0] = p[p!=0]*np.log2(p[p!=0])
    entrpy = -np.sum(entrpy, axis = 1)
    axis.plot(times.val,
            entrpy, 
            linestyle = linestyle,
            color = color,
            alpha = alpha,
            label = label
        )
    axis.set_xlabel('Time ' + transform_unit_to_str(times.domain[0].units))
    axis.set_ylabel('Entropy [bits]')

def motif_entropy(
        motif_trajectory_ensemble,
        linestyle = '-',
        color = 'b',
        alpha = 1.,
        label = None,
        axis = None
    ) -> None:
    ii=0
    for motif_trajectory in motif_trajectory_ensemble.trajectories:
        colr = _choose_color(color, ii/np.max([1,len(motif_trajectory_ensemble.trajectories)-1]))
        times = motif_trajectory.times
        x_t, _ = _motif_trajectory_as_array(motif_trajectory)
        entropy(times,
                x_t,
                linestyle = linestyle,
                color = colr,
                alpha = alpha,
                label = label,
                axis = axis
        )
        ii += 1
