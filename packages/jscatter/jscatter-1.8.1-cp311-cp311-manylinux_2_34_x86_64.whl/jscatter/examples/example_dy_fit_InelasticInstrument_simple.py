# A model for inspecting inelastic instruments like Backscattering
#
# We use real data gifted by Margarita Kruteva measured at EMU but a strongly simplified model.

import jscatter as js
import numpy as np
from jscatter.dynamic import convolve
from jscatter.dynamic import lorentz_w

js.usempl(True)

def readinx(filename, block, l2p, instrument):
    # reusable function for inx reading
    # neutron scatterers use strange data formats like .inx dependent on instrument and local contact
    # blocks start with number of channels. Spaces around the number (' 562 ') are important to find the starting line.
    # this might dependent on instrument
    data = js.dL(filename,
                 block=block,  # this finds the starting of the blocks of all angles or Q
                 usecols=[1, 2, 3],  # ignore the numbering at each line
                 lines2parameter=l2p)  # catch the parameters at beginning
    for da in data:
        da.channels = da.line_1[0]
        da.Q = da.line_3[0]  # in 1/A  # it might be necessary to calc the Q here
        da.incident_energy = da.line_3[1]  # in meV
        da.temperature = da.line_3[3]  # in K if given
        da.instrument = instrument
    return data

# data exported from Mantid look different, simpler. These have only the parameter Q in front of a block
# these can be read like this e.g. from EMU exported by Mantid
def readEMUdat(filename, wavelength=6.27084, temperature=0):
    """
    Read data form EMU@ANSTO as direct output from Mantid (No .inx conversion needed)
    """
    data = js.dL(filename, delimiter=',')
    for da in data:
        da.Q = np.round(float(da.comment[0]), 4)
        da.temperature = temperature
        da.wavelength = wavelength
    # cut the zero at the end
    for i in range(len(data)):
        data[i] = data[i, :, :-1]
    return data

def lo2_fitmodel(w, dw, Q, amp1, amp2, fwhm1, fwhm2, elastic, bgr, resolution, wmax=None):
    """
    Model : elastic with two Lorentz

    w : frequencies 1/ns
    dw : center shift
    amp,amp2 : Lorentz amplitudes
    fwhw1,fwhw2 : full width half maximum
    elastic : amplitude elastic contribution
    bgr : const background
    resolution : datalist with measured resolution and parameters Q same as in fit data
    wmax : cutoff frequency for resolution

    """
    if wmax is None:
        wmax = max(np.abs(w))

    # get right Q value of resolution for selected vana and prune to max frequency
    resolutionQ = resolution.filter(Q=Q)[0]

    # two Lorentz model and elastic , all same w
    model1 = lorentz_w(w, fwhm1)
    model1.Y = amp1 * model1.Y
    # model2 = transDiff_w(w, q=Q, D=Dt) # alternative model; parameters need to be adopted
    model2 = lorentz_w(w, fwhm2)
    model2.Y = amp1 * model2.Y

    # sum amplitudes and put in copied lorentz1
    both = model1.copy()
    both.Y = model1.Y + model2.Y

    # convolve with resolution; convolve also intermediate steps to use in later plots
    convboth = convolve(both, resolutionQ.prune(-wmax, wmax, weight=None), normB=True).interpolate(w)
    convmodel1 = convolve(model1, resolutionQ.prune(-wmax, wmax, weight=None), normB=True).interpolate(w)
    convmodel2 = convolve(model2, resolutionQ.prune(-wmax, wmax, weight=None), normB=True).interpolate(w)

    #  compose the data to return
    # use resolution as elastic contribution
    result = js.dA(np.c_[w,                                           # frequencies
                         convboth.Y + elastic * resolutionQ.Y + bgr,  # fit model
                         convmodel1.Y + bgr,                          # component 1
                         convmodel2.Y + bgr,                          # component 2
                         elastic*resolutionQ.Y+bgr].T)                # elastic contribution

    # append some of the intermediate contributions and add columnames to access components later
    result.columnname = 'w;both;m1;m2;el'
    result.elastic = elastic
    result.fwhm1 = fwhm1
    result.fwhm2 = fwhm2
    result.amp1 = amp1
    result.amp2 = amp2

    return result


# load experimental resolution and convert to 1/ns
# For emu the block is  '  314 ' with 2 spaces in front of the number and 1 after
# resolution experimental data
vanae = readEMUdat(js.examples.datapath + '/sample_5K_Q.dat.gz', temperature=5)
vana = js.dynamic.convert_e2w(vanae, 0, unit='meV')
# convert resolution to normalised data that elastic has meaning
for va in vana:
    va.Y = va.Y/np.trapezoid(va.Y,va.X)

# read new data and convert to 1/ns
same = readEMUdat(js.examples.datapath + '/sample_413K_Q.dat.gz',temperature=413)
sam = js.dynamic.convert_e2w(same, 293, unit='meV')

# ----------------------------------------------------
# fit single dataset and plot addition thing in the errplot
n = 1
# sam[n].makeErrPlot(yscale='log', title=str(sam[1].Q) + ' A\S-1')
sam[n].setlimit()  # removes limits
sam[n].setlimit(elastic=[0, 10000], bgr=[0.0, 2])
sam[n].setlimit(amp1=[0], amp2=[0])  # no negative ampitudes
sam[n].setlimit(fwhm1=[1, 30], fwhm2=[0, 10])  # no negative and some max fwhm
sam[n].fit(model=lo2_fitmodel,
           freepar={'elastic': 0.7, 'bgr': 0.1, 'amp1': 1, 'amp2': 3, 'fwhm1': 20, 'fwhm2': 8, },
           fixpar={'dw': [0], 'wmax': 10,'resolution':vana},
           mapNames={'w': 'X'},
           method='Nelder-Mead', max_nfev=20000)

sam[n].showlastErrPlot(title='Q='+str(sam[n].Q)+' 1/A', yscale='log')
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._m1,sy=0,li=[1,2,3],le='Lorentz 1')  # add
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._m2,sy=0,li=[1,2,4],le='Lorentz 2')
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._el,sy=0,li=[1,2,5],le='elastic')
sam[n].errplot.Yaxis(min=1e-4,max=1)
sam[n].errplot.Save('inelasticInstruments_simple_residuals.png', size=(10, 8), dpi=100)

# ----------------------------------------------
# Fit one after the other
for n in np.r_[0:len(sam)]:
    # sam[n].makeErrPlot(yscale='log', title=str(sam[1].Q) + ' A\S-1')
    sam[n].setlimit()  # removes limits
    sam[n].setlimit(el=[0, 10000], bgr=[0.0, 1])
    sam[n].setlimit(amp1=[0], amp2=[0])  # no negative ampitudes
    sam[n].setlimit(fwhm1=[0, 30], fwhm2=[0, 30])  # no negative and some max fwhm
    sam[n].fit(lo2_fitmodel,
               {'elastic': 1, 'bgr': 1e-5, 'amp1': 1, 'amp2': 3, 'fwhm1': 20, 'fwhm2': 8,  },
               {'dw': [0], 'wmax': 6,'resolution':vana},
               {'w': 'X'},
               method='Nelder-Mead', max_nfev=20000)
    # sam[n].killErrPlot()  # close it , or uncomment to have them open
# look at one single errplot
n = 2
sam[n].showlastErrPlot(title='Q='+str(sam[n].Q)+' 1/A', yscale='log')
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._m1,sy=0,li=[1,2,3],le='Lorentz 1')  # add
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._m2,sy=0,li=[1,2,4],le='Lorentz 2')
sam[n].errPlot(sam[n].lastfit.X,sam[n].lastfit._el,sy=0,li=[1,2,5],le='elastic')
sam[n].errplot.Yaxis(min=1e-5,max=0.2)

# make plot of fit parameters
p1 = js.mplot()
p1.Plot(sam.Q, sam.fwhm1, sam.fwhm1)
p1.Plot(sam.Q, sam.fwhm2, sam.fwhm2)
# if you want to calculate somthing use .array
# p1.Plot(sam.Q, sam.fwhm1.array*sam.Q.array)
p1.Xaxis(label='Q')
p1.Yaxis(label='fwhm', scale='norm', min=0, max=50)  # scale='log' or 'norm'


# -----------------------------------------------------
# fit all together , takes longer
# sam.makeErrPlot(yscale='log', title=str(sam.Q) + ' A\S-1')
sam.setlimit()  # removes limits
sam.setlimit(elastic=[0, 10000], bgr=[0.0, 2])
sam.setlimit(amp1=[0], amp2=[0])  # no negative ampitudes
sam.setlimit(fwhm1=[0, 30], fwhm2=[0, 30])  # no negative and some max fwhm

# here 'fwhm1': 0.0 means a common fit parameters and 'fwhm2': [0.001] is individual fit parameter
sam.fit(lo2_fitmodel,
        {'elastic': [1], 'bgr': [0.1], 'amp1': [1], 'amp2': [3], 'fwhm1': 20, 'fwhm2': [1], },
        {'dw': [0], 'wmax': 10,'resolution':vana},
        {'w': 'X'},
        method='lm', max_nfev=20000, workers=0)  # workers=1 uses only one cpu, =0 uses all
sam.showlastErrPlot(title='all together', yscale='log')

# ------------------------------------------------------
# inspect one of the overall fit
n = 5  # which one to plot
p = js.mplot()
p.Yaxis(scale='log')
p.Title(f'Q={sam[n].Q} ')
p.Plot(sam[n])
p.Plot(sam.lastfit[n], sy=0, li=[1, 2, 14], le='fit')
p.Plot(sam.lastfit[n].X, sam.lastfit[n]._m1, sy=0, li=[1, 2, 10], le='common fwhm1')
p.Plot(sam.lastfit[n].X, sam.lastfit[n]._m2, sy=0, li=[2, 2, 4], le='individual fwhm2')
p.Plot(sam.lastfit[n].X, sam.lastfit[n]._el, sy=0, li=[3, 2, 6], le='elastic')
p.Legend()
# p.Save('inelasticInstruments_simple.png', size=(5, 4), dpi=400)
