import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

def motif_production_rates(
        motif_production_rates,
        letters : list[str],
        plotpath : str = None,
        plotformats : str = ['.pdf','.pgf'],
        plot_parameters : list = [{
            'color' : 'b',
            'alpha' : 0.3,
            'label' : 'Strand',
        }],
        figname='motif_production_rates',
        ax = plt
        ):
    ax.imshow(motif_production_rates)
    cw = compute_words(letters,zeros=(1,0,0,1))
    # motif_production_rates = sort_by_length(np.array(motif_production_rates))
    # cw = sort_by_length(cw)
    ax.xticks(ticks=np.arange(0,len(cw.reshape(-1))), labels=cw.reshape(-1), fontsize='x-small', rotation=90)
    ax.yticks(ticks=np.arange(0,len(cw.reshape(-1))), labels=cw.reshape(-1), fontsize='x-small')
    if plotpath is not None:
        for plotformat in plotformats:
            plt.savefig(plotpath+figname+plotformat)
    #plot_rate_constants(motif_production_rates, 'Motif Production Rates', plotpath+'motif_production_rates.pdf')

def sort_by_length(x):
    shape = x.shape
    shape1 = shape[len(shape)//2:]
    shape2 = shape[:len(shape)//2]
    if shape1==shape2:
        if shape[1]==shape[0]:
            x = x[:,1:,1:,:,:,1:,1:,:]
            shape = x.shape
            shape1 = shape[len(shape)//2:]
            shape2 = shape[:len(shape)//2]
        dimers1 = x[0,:,:,0].reshape((-1,)+shape2)
        starts1 = x[0,:,:,1:].reshape((-1,)+shape2)
        continuations1 = x[1:,:,:,1:].reshape((-1,)+shape2)
        ends1 = x[1:,:,:,0].reshape((-1,)+shape2)
        rtrn = np.concatenate((dimers1, starts1, continuations1, ends1))
        dimers = rtrn[:,0,:,:,0].reshape((np.prod(shape1),-1))
        starts = rtrn[:,0,:,:,1:].reshape((np.prod(shape1),-1))
        continuations = rtrn[:,1:,:,:,1:].reshape((np.prod(shape1),-1))
        ends = rtrn[:,1:,:,:,0].reshape((np.prod(shape1),-1))
        rtrn = np.concatenate((dimers,starts,continuations,ends),axis=1)
    else:
        if shape[1]==shape[0]:
            x = x[:,1:,1:,:]
        dimers1 = x[0,:,:,0].reshape(-1)
        starts1 = x[0,:,:,1:].reshape(-1)
        continuations1 = x[1:,:,:,1:].reshape(-1)
        ends1 = x[1:,:,:,0].reshape(-1)
        rtrn = np.concatenate((dimers1, starts1, continuations1, ends1))
    return rtrn

def compute_words(letters,zeros=(1,0,0,1)): 
    zeros = np.asarray(zeros)
    nol = len(letters)
    shape = np.asarray((nol,)*len(zeros))
    shape = tuple(shape+zeros)
    ne = np.empty(shape, dtype=object)
    if zeros[0]:
        ne[0] = '0'
    for ii in range(nol):
        ne[ii+zeros[0]] = letters[ii]
    for jj in range(1,len(shape)):
        ne = np.swapaxes(ne,jj,0)
        if zeros[jj]:
            ne[0] += '0'
        for ii in range(nol):
            ne[ii+zeros[jj]] += letters[ii]
        ne = np.swapaxes(ne,jj,0)
    return ne

'''
def plot_rate_constants(rate_constants, title, figname,
        colorbar_norm = colors.LogNorm(),
        c_ref = trj.parameters['c_ref'],
        ticks = mean_ticks,
        ):
    fig_dct = {
            'legend' : False,
            'title' : title,
            'xlabel' : create_axis_label('template (complement)'),
            'ylabel' : create_axis_label('central produced motif'),
            'figname' : self.plotpath+figname,
            }
    plot_motifs_vs_motifs(rate_constants,
            trj.letters,
            c_ref = c_ref,
            complements = x.parameters['complements'],
            sorted_by_length = True,
            ticks = ticks,
            colorbar_norm = colorbar_norm,
            fig_dct = fig_dct
            )

def plot_motifs_vs_motifs(x,
        letters=['x','y'],
        zeros=(1,0,0,1),
        complements = None,
        c_ref = 1.,
        title=None,
        xlabel = None,
        ylabel = None,
        ticks = None,
        ax = plt,
        sorted_by_length = False,
        colorbar_norm = colors.LogNorm(),
        fig_dct = None,
        complemented_shall_be_added_to_xlabel = False
        ):
    x = transform_MultiField(x)
    if colorbar_norm is colors.LogNorm() and np.min(x)<=0:
        colorbar_norm = None
    #np.asarray(zeros+zeros)+len(letters)
    #x = x[:3,:2,:2,:3,:3,:2,:2,:3]
    if complements is not None:
        #check that complements has correct shape
        if len(complements)>len(x):
            warn("more letters given for complements than inside concentration vector. Will only take needed ones.")
        complements = complements[:len(x)]
        x = complement_template(x, complements)
        if fig_dct is not None and complemented_shall_be_added_to_xlabel:
            if fig_dct['xlabel'] is not None:
                fig_dct['xlabel'] += ' (complemented)' 
        elif complemented_shall_be_added_to_xlabel:
            if xlabel is not None:
                xlabel += ' (complemented)'
            else:
                xlabel = ' (complemented)'
    if sorted_by_length:
        x = sort_by_length(x)
        cw = sort_by_length(compute_words(letters,zeros=zeros))
    else:
        shape1 = np.prod(x.shape[:len(x.shape)//2])
        x = x.reshape((shape1,-1))
        cw = sort_by_length(compute_words(letters,zeros=zeros))
    if ticks is None:
        ticks = [None,None]
    imshow_dct = {}
    if colorbar_norm is colors.LogNorm():
        colorbar_norm = colors.LogNorm(vmin=ticks[0], vmax=ticks[1])
    else:
        imshow_dct['vmin']=ticks[0],
        imshow_dct['vmax'] = ticks[1]
    im =ax.imshow(x,
            origin='upper',
            #interpolation = 'none',
            norm = colorbar_norm,
            #FIXME: **imshow_dct
            )
    ax.colorbar(im)
    ax.xticks(ticks=np.arange(0,len(cw.reshape(-1))), labels=cw.reshape(-1), fontsize='x-small', rotation=90)
    ax.yticks(ticks=np.arange(0,len(cw.reshape(-1))), labels=cw.reshape(-1), fontsize='x-small')
    if fig_dct is not None:
        make_fig(fig_dct)
    else:
        ax.xlabel(xlabel)
        ax.ylabel(ylabel)
'''
