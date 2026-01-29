import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def _choose_color(
        color : LinearSegmentedColormap,
        color_parameter : float = 0
        ):
    if isinstance(color,LinearSegmentedColormap):
        return color(color_parameter)
    else:
        return color

def standard_colorbar():
    green = mcolors.CSS4_COLORS['darkgreen']
    darkgold = mcolors.CSS4_COLORS['darkgoldenrod']
    gold = mcolors.CSS4_COLORS['gold']
    edgecolors = mcolors.to_rgba_array([green,darkgold,gold])[:,:-1]
    return LinearSegmentedColormap.from_list('greengold',edgecolors,100)

def greenish_colorbar():
    darkgreen = mcolors.CSS4_COLORS['darkslategray']
    forestgreen = mcolors.CSS4_COLORS['forestgreen']
    lightgreen = mcolors.CSS4_COLORS['yellow']
    edgecolors = mcolors.to_rgba_array([darkgreen,forestgreen,lightgreen])[:,:-1]
    return LinearSegmentedColormap.from_list('darklightgreenish',edgecolors,100)

def green_colorbar():
    darkgreen = mcolors.CSS4_COLORS['darkgreen']
    forestgreen = mcolors.CSS4_COLORS['forestgreen']
    lightgreen = mcolors.CSS4_COLORS['lightgreen']
    edgecolors = mcolors.to_rgba_array([darkgreen,forestgreen,lightgreen])[:,:-1]
    return LinearSegmentedColormap.from_list('darklightgreen',edgecolors,100)

def colorbar_example():
    greengold_cmapp = standard_colorbar()
    data = np.linspace(1.,0.,1048)
    data = np.outer(data,np.ones(data.shape))
    fig,axs = plt.subplots(1,1)
    im = axs.imshow(data,cmap=greengold_cmapp)
    fig.colorbar(im,ax=axs)
