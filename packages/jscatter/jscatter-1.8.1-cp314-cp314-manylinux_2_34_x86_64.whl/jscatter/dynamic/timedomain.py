# -*- coding: utf-8 -*-
# written by Ralf Biehl at the Forschungszentrum Jülich ,
# Jülich Center for Neutron Science (JCNS-1)
#    Jscatter is a program to read, analyse and plot data
#    Copyright (C) 2015-2025  Ralf Biehl
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import inspect
import math
import os
import sys
import numbers

import numpy as np
from scipy import linalg as la
import scipy
import scipy.integrate
import scipy.interpolate
import scipy.constants
import scipy.special as special
try:
    from scipy.special import sph_harm_y as Ylm
except ImportError:
    def Ylm(n, m, theta, phi):
        return special.sph_harm(m, n, theta, phi)

from jscatter import dataArray as dA
from jscatter import dataList as dL
from jscatter import formel
from jscatter.formel import convolve

try:
    from jscatter.libs import fscatter

    useFortran = True
except ImportError:
    useFortran = False

__all__ = ['simpleDiffusion','cumulant','cumulantDLS','stretchedExp','jumpDiffusion',
           'methylRotation','methylRotation','diffusionHarmonicPotential',
           'diffusionHarmonicPotential','finiteZimm','fixedFiniteZimm','finiteRouse','fixedFiniteRouse',
           'diffusionPeriodicPotential','zilmanGranekBicontinious','zilmanGranekLamellar',
           'integralZimm','transRotDiffusion','resolution', 'doubleDiffusion',
           'linearChainORZ','multiArmStarORZ', 'solveOptimizedRouseZimm','ringChainORZ']

pi = np.pi
_path_ = os.path.realpath(os.path.dirname(__file__))

#: Planck constant in µeV*ns
h = scipy.constants.Planck / scipy.constants.e * 1E15  # µeV*ns

#: h/2π  reduced Planck constant in µeV*ns
hbar = h/2/pi  # µeV*ns

kb = 1.3806503e-23  # J/K in SI units

try:
    # change in scipy 18
    spjn = special.spherical_jn
except AttributeError:
    spjn = lambda n, z: special.jv(n + 1 / 2, z) * np.sqrt(pi / 2) / (np.sqrt(z))


def _diff(t, gamma):
    return dA(np.c_[t, np.exp(- gamma * t)].T)

def transDiff(t, q, D):
    r"""
    Translational diffusion intermediate scattering function in t domain.

    .. math:: I(t,q) =  e^{-q^2Dt}

    Parameters
    ----------
    t : array
        Frequencies in 1/ns
    q : float
        Wavevector in nm**-1
    D : float
        Diffusion constant in nm**2/ns

    Returns
    -------
         dataArray


    """
    gamma = q * q * D

    result = _diff(t, gamma)
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    result.modelname = inspect.currentframe().f_code.co_name
    result.wavevector = q
    result.D = D
    return result


def simpleDiffusion(t, gamma=None, q=None, D=None, s=0, beta=1, type='lognorm'):
    r"""
    Intermediate scattering function [g1(t)] for diffusing particles from distribution of relaxation rates.

    .. math:: I(q,t,D, \sigma ) = \beta \int g(\Gamma, \Gamma_0, \sigma ) e^{-\Gamma t}


    and relaxation rate :math:`\Gamma_0=q^2D`.

    Parameters
    ----------
    t : float, array
        Times
    gamma : float
        Mean relaxation rate in inverse t units.
        Overrides q and D if given. If q and D given gamma=q*q*D
    q : float, array
        Wavevector
    beta : float
        Intercept :math:`\beta` in DLS. The amplitude prefactor.
    D : float
        Mean diffusion coefficient.
    s : float
        Relative standard deviation of the diffusion coefficient distribution from e.g. polydispersity.
        In absolute units :math:`\sigma=s*q^2*D=w\Gamma`.
        For a typical DLS experiment `s≈0.25` just from instrument noise
        (e.g. noise ≈ 1e-3 Zetasizer Nano, Malvern)

        For s=0 a single exponential is used.
    type : 'truncnorm', default 'lognorm'
        Distribution shape.
         - 'lognorm' lognorm distribution as normal distribution on a log scale.

            .. math:: g(x, \mu, \sigma) = \frac{ 1 }{\ x\sigma\sqrt{2\pi}} exp(-\frac{\ln(x- \mu)^2}{ 2 \sigma^2 })

           This is approximately what you get from CONTIN or NNLS algorithm in DLS.
         - 'truncnorm' normal distribution cut at zero.

         .. math:: g(x, \mu, \sigma)= e^{-0.5(\frac{x-\mu}{\sigma})^2} / (\sigma\sqrt{2\pi}) \ \text{  for x>0}

    Returns
    -------
     out : dataArray
        intermediate scattering function or :math:`g_1`
         - .D, .wavevector, .beta  respective input parameters
         - pdf : Probability of the distribution in the interval around pdf[0,i]
           (half distance to neighboring points) that sum(pdf[2])==1 similar to CONTIN results.


    Notes
    -----
    Units of q, t and D result in unit-less [q*q*D*t] like q in 1/cm, t in s -> D in cm*cm/s .

    Remember that :math:`g_2(t)` (intensity correlation for DLS) is :math:`g_1^2(t)=g_2(t)-1`.

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np

     t = js.loglist(1e-6,10,1000) # in seconds

     # ≈ a protein with a MW of 140kDa
     D = 3e-7  # unit cm^2/s
     q = 4*np.pi/633e-7*np.sin(np.pi/4)  # 90º HeNe laser in DLS

     p=js.grace(1.8,1)
     p.multi(1,2)
     p[0].xaxis(label=r't / s ',scale='log')
     p[0].yaxis(label=r'g\s1\N(t) ')
     p[1].xaxis(label=r'\xG\f{} / 1/s ',scale='log')
     p[1].yaxis(label=[r'P(\xG\f{})',1,'opposite'],)

     for c,s in enumerate([0.25,0.5,1,2],1):
        dls = js.dynamic.simpleDiffusion(t=t,q=q,D=D,s=s)
        p[0].plot(dls,sy=0,li=[1,3,c],le=f's={s}')
        p[1].plot(dls.pdf[0], 20 * dls.pdf[1],sy=0,li=[1,3,c])

     p[0].legend(x=0.01,y=0.8)
     p[0].title('DLS correlation')
     p[1].title('rate distribution')
     # p.save(js.examples.imagepath+'/simpleDiffusion.jpg',size=(1.8,1))

    .. image:: ../../examples/images/simpleDiffusion.jpg
     :align: center
     :width: 50 %
     :alt: Zimm

    """
    if isinstance(D, numbers.Number) and isinstance(q, numbers.Number):
        gamma = q*q*D

    if s == 0:
        # no width or distribution
        result = _diff(t, gamma)
    else:
        if type[0] == 't':
            a = (0 - gamma) / (s * gamma)
            b = np.inf
            result = formel.pDA(_diff, s * gamma, parname='gamma', type='truncnorm', gamma=gamma, t=t, nGauss=30, a=a, b=b)
        else:
            result = formel.pDA(_diff, s * gamma, parname='gamma', type='lognorm', gamma=gamma, t=t, nGauss=30)

        # use interval probability
        dif = result.pdf[0] * 0
        dif[1:] = np.diff(result.pdf[0])
        dif[:-1] += dif[1:]
        dif /= 2
        result.pdf[1] = result.pdf[1] * dif

    result.Y = beta * result.Y
    result.beta = beta
    result.Diffusioncoefficient = D
    result.s = s
    result.wavevector = q
    result.Gamma = gamma
    result.columnname = 't;Iqt'
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


def doubleDiffusion(t, q=None, gamma1=None, D1=None, s1=0,
                    gamma2=None, D2=None, s2=0, frac=0.5, beta=1, type='lognorm'):
    r"""
    Intermediate scattering function [g1(t)] for diffusing particles from bimodal distribution of relaxation rates.

    .. math:: I_i(q,t,D_i,\sigma_i ) = \int g(\Gamma_i, \Gamma_{i,0} \sigma_i ) e^{-\Gamma_i t} d\Gamma_i

    .. math:: I(q,t) = beta [f\ I_1(q,t,D_i,\sigma_i ) + (1-f)\ I_2(q,t,D_2,\sigma_2 )]

    and relaxation rates :math:`\Gamma_{i,0}=q^2D_i`.

    Parameters
    ----------
    t : float, array
        Times
    gamma1,gamma2 : float
        Mean relaxation rates in inverse t units.
        Overrides q and D if given. If q and D given gamma=q*q*D
    q : float, array
        Wavevector
    beta : float
        Intercept :math:`\beta` in DLS. The amplitude prefactor.
    D1,D2 : float
        Mean diffusion coefficients.
    s1,s2 : float
        Relative standard deviations of the diffusion coefficient distributions.
        In absolute units :math:`\sigma=s*q^2*D`.
        For a typical DLS experiment `s≈0.25` just from instrument noise (e.g. noise ≈ 1e-3 Zetasizer Nano, Malvern)
    type : 'truncnorm', default 'lognorm'
        Distribution shape.
         - 'lognorm' lognorm distribution as normal distribution on a log scale.

            .. math:: g(x, \mu, \sigma) = \frac{ 1 }{\ x\sigma\sqrt{2\pi}} exp(-\frac{\ln(x- \mu)^2}{ 2 \sigma^2 })

         - 'truncnorm' normal distribution cut at zero.

         .. math:: g(x, \mu, \sigma)= e^{-0.5(\frac{x-\mu}{\sigma})^2} / (\sigma\sqrt{2\pi}) \ \text{  for x>0}

    Returns
    -------
     out : dataArray
        intermediate scattering function or :math:`g_1`
         - .D1, .D2, .wavevector, .beta  respective input parameters
         - pdf1, pdf2 : Probability of the distribution in the interval around pdf[0,i]
           (half distance to neighboring points) that sum(pdf[2])==1 similar to CONTIN results.


    Notes
    -----
    Units of q, t and D result in unit-less [q*q*D*t] like q in 1/cm, t in s -> D in cm*cm/s .


    Examples
    --------
    ::

     import jscatter as js
     import numpy as np

     t = js.loglist(1e-6,10,1000) # in seconds
     # ≈ a protein with a MW of 140kDa
     D1 = 3e-8  # unit cm^2/s
     D2 = 3e-5  # unit cm^2/s
     q = 4*np.pi/633e-7*np.sin(np.pi/4)  # 90º HeNe laser in DLS

     p=js.grace(1.8,1)
     p.multi(1,2)
     p[0].xaxis(label=r't / s ',scale='log')
     p[0].yaxis(label=r'g\s1\N(t) ')
     p[1].xaxis(label=r'\xG\f{} / 1/s ',scale='log')
     p[1].yaxis(label=[r'P(\xG\f{})',1,'opposite'],)

     for c,s in enumerate([0.25,0.5,1,2],1):
        dls = js.dynamic.doubleDiffusion(t=t,q=q,D1=D1,s1=s,D2=D2,s2=s,frac=0.4)
        p[0].plot(dls,sy=0,li=[1,3,c],le=f's={s}')
        p[1].plot(dls.pdf1[0], 20 * dls.pdf1[1],sy=0,li=[1,3,c])
        p[1].plot(dls.pdf2[0], 20 * dls.pdf2[1],sy=0,li=[1,3,c])

     p[0].legend(x=0.01,y=0.8)
     p[0].title('DLS correlation')
     p[1].title('rate distribution')
     # p.save(js.examples.imagepath+'/doubleDiffusion.jpg',size=(1.8,1))

    .. image:: ../../examples/images/doubleDiffusion.jpg
     :align: center
     :width: 50 %
     :alt: Zimm

    """
    result1 = simpleDiffusion(t, gamma=gamma1, q=q, D=D1, s=s1, beta=1, type=type)
    result2 = simpleDiffusion(t, gamma=gamma2, q=q, D=D2, s=s2, beta=1, type=type)

    result = result1.copy()
    result.Y = beta * (frac * result1.Y + (1-frac) * result2.Y)

    result.beta = beta
    result.wavevector = q
    result.frac = frac
    del result.Diffusioncoefficient
    del result.Gamma
    del result.pdf
    result.Diffusioncoefficient1 = D1
    result.s1 = s1
    result.Gamma1 = gamma1
    result.Diffusioncoefficient2 = D2
    result.s2 = s2
    result.Gamma2 = gamma2
    result.pdf1 = result1.pdf
    result.pdf2 = result2.pdf
    result.columnname = 't;Iqt'
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


def cumulant(x, k0=1, k1=0, k2=0, k3=0, k4=0, k5=0):
    r"""
    Cumulant of order ki.

    .. math:: I(x) = k_0 exp(-k_1x+1/2k_2x^2-1/6 k_3x^3+1/24k_4x^4-1/120k_5x^5)

    Cumulants can only be used in initial slope analysis and not for a full fit of DLS data to long times.
    It is necessary  to cut large x. See :py:func:`cumulantDLS` for DLS.

    Parameters
    ----------
    x : float
        Wavevector
    k0,k1, k2,k3,k4,k5 : float
        Cumulant coefficients;  units 1/x
         - k0 amplitude
         - k1 expected value
         - k2 variance with :math:`\sqrt(k2/k1) =` relative standard deviation
         - higher order see Wikipedia

    Returns
    -------
    dataArray

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np

     t = js.loglist(1e-6,10,1000) # in seconds

     p=js.grace()
     p.xaxis(scale='log')

     k1=1/0.001
     for f in [0,0.1,10.5]:
        cum=js.dynamic.cumulant(t,k1=k1,k2=f*2*k1)
        p.plot(cum,sy=0,li=-1)


    """
    x = np.atleast_1d(x)
    G = - k1 * x
    if k2 > 0:
        G += + 1 / 2. * k2 * x ** 2
    if k3 > 0: G += - 1 / 6. * k3 * x ** 3
    if k4 > 0: G *= + 1 / 24 * k4 * x ** 4
    if k5 > 0: G *= - 1 / 120 * k5 * x ** 5
    res = np.zeros_like(G)
    res[G < 1] = k0 * np.exp(G[G < 1])

    result = dA(np.c_[x, res].T)
    result.k0tok5 = [k0, k1, k2, k3, k4, k5]
    result.modelname = inspect.currentframe().f_code.co_name
    result.columnname = 't;Iqt'
    result.setColumnIndex(iey=None)
    return result


def cumulantDLS(t, A, G, sigma, skewness=0, bgr=0., g2=True):
    r"""
    Cumulant analysis for dynamic light scattering (DLS) or NSE assuming Gaussian size distribution.

    See Frisken et al [1]_ :

    .. math:: g_1(t) = A exp(-t/G) \big( 1+(sigma/G t)^2/2. - (skewness/G t)^3/6. \big) + bgr

    Returns  :math:`g_1^2=g_2-1` for DLS or :math:`g_1(t)` for NSE.

    Parameters
    ----------
    t : array
        Time
    A : float
        Amplitude at t=0; Intercept
    G : float
        Mean relaxation time as 1/decay rate in units of t.
    sigma : float
        - relative standard deviation if a gaussian distribution is assumed
        - should be smaller 1 or the Taylor expansion is not valid
        - k2=variance=sigma**2/G**2
    skewness : float,default 0
        Relative skewness k3=skewness**3/G**3
    bgr : float; default 0
        Constant background
    g2 : bool default = True
        Determines correlation type as field correlation (actually :math:`g_1^2=g_2-1`) or
        intensity correlation :math:`g_1`.

        - True is intensity correlations :math:`g_1^2=g_2-1`.
           Actually fitting the measured data is prefered, use this for DLS.
           This should be used for DLS as :math:`g_1^2(t \rightarrow \infty)` fluctuates around 0
           allowing negative values and  prevents a bias during fitting.
        - False is field correlations :math:`g_1`.
           Use this e.g. for NSE as the field correlation is measured directly.

    Returns
    -------
    dataArray

    Notes
    -----
    To fit diffusion constant D e.g. use
    ::

     def cDLS(t, A, D, sigma, q, bgr=0.0, g2=1):
        # g2=1 or 0 switches between g1 or g2minus1
        # diffusion coefficient in nm*nm/ns  if q in 1/nm and t in microseconds
        G=1/(D*q**2*1000)
        return js.dynamic.cumulantDLS(t=t, A=A, G=G, sigma=sigma, skewness=0, bgr=bgr, g2=True if g2!=0 else False)

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np

     # simulate data
     t=js.loglist(0.125,10000,1000)   #times in microseconds
     q=4*np.pi*1.333/632*np.sin(np.deg2rad(90)/2) # 90 degrees for 632 nm , unit is 1/nm**2
     D=0.01  # nm**2/ns * 1000 = units nm**2/microseconds
     noise=0.001  # typical < 1e-3
     G = 1/q**2*D
     g1 = 0.9*np.exp(-t/G)    # with 20x larger aggragates
     data=js.dA(np.c_[t,g1**2 + noise*np.random.randn(len(t))].T)  # intensity correlation with noise

     data.makeErrPlot(xscale='log')
     data.fit(js.dynamic.cumulantDLS,{'A':0.9, 'G':20, 'sigma':0,'bgr':0},{},{'t':'X'},condition=lambda a:a.Y>0.1)

    References
    ----------
    .. [1] Revisiting the method of cumulants for the analysis of dynamic light-scattering data
          Barbara J. Frisken APPLIED OPTICS  40, 4087 (2001)

    """
    t = np.atleast_1d(t)
    A = abs(A)

    if skewness == 0:
        g1 = A * np.exp(-t / G) * (1 + (sigma / G * t) ** 2 / 2.)
    else:
        g1 = A * np.exp(-t / G) * (1 + (sigma / G * t) ** 2 / 2. - (skewness / G * t) ** 3 / 6.)

    if g2:
        result = dA(np.c_[t, g1**2 + bgr].T)
        result.type = 'g2minus1'
    else:
        result = dA(np.c_[t, g1 + bgr].T)
        result.type = 'g1'

    result.columnname = 't;Iqt'
    result.A = A
    result.relaxationtime = G
    result.sigma = sigma
    result.skewness = skewness
    result.elastic = bgr
    result.modelname = inspect.currentframe().f_code.co_name

    result.setColumnIndex(iey=None)

    return result


def stretchedExp(t, gamma, beta, amp=1):
    r"""
    Stretched exponential function.

    .. math:: I(t) = amp\, e^{-(t\gamma)^\beta}

    Parameters
    ----------
    t : array
        Times
    gamma : float
        Relaxation rate in units 1/[unit t]
    beta : float
        Stretched exponent
    amp : float default 1
        Amplitude

    Returns
    -------
    dataArray

    """
    t = np.atleast_1d(t)
    res = amp * np.exp(-(t * gamma) ** beta)
    result = dA(np.c_[t, res].T)
    result.amp = amp
    result.gamma = gamma
    result.beta = beta
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    return result


def jumpDiffusion(t, Q, t0, l0):
    r"""
    Incoherent intermediate scattering function of translational jump diffusion in the time domain.

    Parameters
    ----------
    t : array
        Times, units ns
    Q : float
        Wavevector, units nm
    t0 : float
        Residence time, units ns
    l0 : float
        Mean square jump length, units nm

    Returns
    -------
        dataArray

    Notes
    -----
    We use equ. 3-5 from [1]_ for random jump diffusion as

    .. math:: T(Q,t) = exp(-\Gamma(Q)t)

    with residence time :math:`\tau_0` and mean jump length :math:`<l^2>^{1/2}_{av}`
    and diffusion constant :math:`D` in

    .. math:: \Gamma(Q) = \frac{DQ^2}{1+DQ^2\tau_0}

    .. math:: D=\frac{ <l^2>_{av}}{6\tau_0}



    References
    ----------
    .. [1]  Experimental determination of the nature of diffusive motions of water molecules at low temperatures
            J. Teixeira, M.-C. Bellissent-Funel, S. H. Chen, and A. J. Dianoux
            Phys. Rev. A 31, 1913 – Published 1 March 1985

    """
    t = np.atleast_1d(t)
    D = l0 ** 2 / 6. / t0
    gamma = D * Q * Q / (1 + D * Q * Q * t0)

    tdif = np.exp(-gamma * t)
    result = dA(np.c_[t, tdif].T)
    result.residencetime = t0
    result.jumplength = l0
    result.diffusioncoefficient = D
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    return result


def methylRotation(t, q, t0=0.001, fraction=1, rhh=0.12, beta=0.8):
    r"""
    Incoherent intermediate scattering function of CH3 methyl rotation in the time domain.

    Parameters
    ----------
    t : array
        List of times, units ns
    q : float
        Wavevector, units nm
    t0 : float, default 0.001
        Residence time, units ns
    fraction : float, default 1
        Fraction of protons contributing.
    rhh : float, default=0.12
        Mean square jump length, units nm
    beta : float, default 0.8
        exponent

    Returns
    -------
        dataArray

    Notes
    -----
    According to [1]_:

    .. math:: I(q,t) = (EISF + (1-EISF) e^{-(\frac{t}{t_0})^{\beta}} )

    .. math:: EISF=\frac{1}{3}+\frac{2}{3}\frac{sin(qr_{HH})}{qr_{HH}}

    with
    :math:`t_0` residence time,
    :math:`r_{HH}` proton jump distance.

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np
     # make a plot of the spectrum
     w=np.r_[-100:100]
     ql=np.r_[1:15:1]
     iqwCH3=js.dL([js.dynamic.time2frequencyFF(js.dynamic.methylRotation,'elastic',w=np.r_[-100:100:0.1],q=q )
                                                 for q in ql])
     p=js.grace()
     p.plot(iqwCH3,le='CH3')
     p.yaxis(min=1e-5,max=10,scale='l')


    References
    ----------
    .. [1] M. Bée, Quasielastic Neutron Scattering (Adam Hilger, 1988).
    .. [2] Monkenbusch et al. J. Chem. Phys. 143, 075101 (2015)


    """
    t = np.atleast_1d(t)
    EISF = (1 + 2 * np.sinc(q * rhh / np.pi)) / 3.
    Iqt = (1 - fraction) + fraction * (EISF + (1 - EISF) * np.exp(-(t / t0) ** beta))

    result = dA(np.c_[t, Iqt].T)
    result.wavevector = q
    result.residencetime = t0
    result.rhh = rhh
    result.beta = beta
    result.EISF = EISF
    result.methylfraction = fraction
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    return result


def diffusionHarmonicPotential(t, q, rmsd, tau, beta=0, ndim=3):
    r"""
    ISF corresponding to the standard OU process for diffusion in harmonic potential for dimension 1,2,3.

    The intermediate scattering function corresponding to the standard OU process
    for diffusion in an harmonic potential [1]_. It is used for localized translational motion in
    incoherent neutron scattering [2]_ as improvement for the diffusion in a sphere model.
    Atomic motion may be restricted to ndim=1,2,3 dimensions and are isotropic averaged.
    The correlation is assumed to be exponential decaying.

    Parameters
    ----------
    t : array
        Time values in units ns
    q : float
        Wavevector in unit 1/nm
    rmsd : float
        Root mean square displacement :math:`rmsd=\langle  u_x^2 \rangle ^{1/2}` in potential in units nm.
        :math:`\langle  u_x^2 \rangle ^{1/2}` is the width of the potential
        According to [2]_
        5*u**2=R**2:math:`5\langle  u_x^2 \rangle =R^2` compared to the diffusion in a sphere of radius R.
    tau : float
        Correlation time :math:`\tau_0` in units ns.
        Diffusion constant in sphere Ds=u**2/tau
    beta : float, default 0
        Exponent in correlation function :math:`\rho(t)`.
         - beta=0 :  :math:`\rho(t) = exp(-t/\tau_0)`
           normal liquids where memory effects are presumably weak or negligible [2]_.
         - 0<beta,inf : :math:`\rho(t,beta) = (1+\frac{t}{\beta\tau_0})^{-\beta}`. See [2]_ equ. 21a.
           supercooled liquids or polymers, where memory effects may be important correlation functions
           with slower decay rates should be introduced [2]_. See [2]_ equ. 21b.
    ndim : 1,2,3, default=3
        Dimensionality of the diffusion potential.

    Returns
    -------
        dataArray

    Notes
    -----
    We use equ. 18-20 from [2]_ and correlation time :math:`\tau_0`
    with equal amplitudes :math:`rmsd=\langle  u_x^2 \rangle ^{1/2}` in the dimensions as


    3 dim case:

    .. math:: I_s(Q,t) = e^{-Q^2\langle  u^2_x \rangle  (1-\rho(t))}

    2 dim case:

    .. math:: I_s(Q,t) = \frac{\pi^{0.5}}{2} e^{-g^2(t)} \frac{erfi(g(t))}{g(t)} \ with \
              g(t) = \sqrt{Q^2\langle  u^2_x \rangle  (1-\rho(t))}

    1 dim case:

    .. math:: I_s(Q,t) = \frac{\pi^{0.5}}{2} \frac{erf(g(t))}{g(t)} \ with \
              g(t) = \sqrt{Q^2\langle  u^2_x \rangle  (1-\rho(t))}

    with *erf* as the error function and *erfi* is the imaginary error function *erf(iz)/i*

    Examples
    --------
    ::

     import numpy as np
     import jscatter as js
     t=np.r_[0.1:6:0.1]
     p=js.grace(1,1)
     p.plot(js.dynamic.diffusionHarmonicPotential(t,1,2,1,1),le='1D ')
     p.plot(js.dynamic.diffusionHarmonicPotential(t,1,2,1,2),le='2D ')
     p.plot(js.dynamic.diffusionHarmonicPotential(t,1,2,1,3),le='3D ')
     p.legend()
     p.yaxis(label='I(Q,t)')
     p.xaxis(label='Q / ns')
     p.subtitle('Figure 2 of ref Volino J. Phys. Chem. B 110, 11217')
     # p.save(js.examples.imagepath+'/diffusionHarmonicPotential_t.jpg', size=(2,2))

    .. image:: ../../examples/images/diffusionHarmonicPotential_t.jpg
     :align: center
     :width: 50 %
     :alt: dynamic_t2f_examples.

    References
    ----------
    .. [1] Quasielastic neutron scattering and relaxation processes in proteins: analytical and simulation-based models
           G. R. Kneller Phys. ChemChemPhys. ,2005, 7,2641–2655
    .. [2] Gaussian model for localized translational motion: Application to incoherent neutron scattering
           F. Volino, J.-C. Perrin and S. Lyonnard, J. Phys. Chem. B 110, 11217–11223 (2006)

    """
    erf = special.erf
    erfi = special.erfi
    q2u2 = q ** 2 * rmsd ** 2
    if beta <=0:
        ft = (1 - np.exp(-t / tau))
    else:
        ft = (1 - (1+t/tau/beta)**(-beta))
    ft[t == 0] = 1e-8  # avoid zero to prevent zero division and overwrite later with EISF
    if ndim == 3:
        Iqt = np.exp(-q2u2 * ft)
        EISF = np.exp(-q2u2)
        Iqt[t == 0] = EISF
    elif ndim == 2:
        q2u2exp = q2u2 * ft
        Iqt = 0.5 * pi ** 0.5 * np.exp(-q2u2exp) * erfi(q2u2exp ** 0.5) / q2u2exp ** 0.5
        EISF = 0.5 * pi ** 0.5 * np.exp(-q2u2) * erfi(q2u2 ** 0.5) / q2u2 ** 0.5
        Iqt[t == 0] = EISF
    elif ndim == 1:
        q2u2exp = q2u2 * ft
        Iqt = 0.5 * pi ** 0.5 * erf(q2u2exp ** 0.5) / q2u2exp ** 0.5
        EISF = 0.5 * pi ** 0.5 * erf(q2u2 ** 0.5) / q2u2 ** 0.5
        Iqt[t == 0] = EISF
    else:
        raise Exception('ndim should be one of 1,2,3 ')

    result = dA(np.c_[t, Iqt].T)
    result.tau = tau
    result.Ds = rmsd ** 2 / tau
    result.rmsd = rmsd
    result.EISF = EISF
    result.wavevector = q
    result.dimension = ndim
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    return result


@formel.memoize()
def _bnmtzimm(t, NN, l, mu, modeamplist, tzp, fixedends):
    return fscatter.dynamic.bnmt(t, NN, l, mu, modeamplist, tzp, fixedends)


def finiteZimm(t, q, NN=None, pmax=None, l=None, Dcm=None, Dcmfkt=None, tintern=0., mu=0.5, viscosity=1.,
               ftype=None, rk=None, Temp=293):
    r"""
    Zimm dynamics of a finite chain with N beads with internal friction and hydrodynamic interactions.

    The Zimm model describes the conformational dynamics of an ideal chain with hydrodynamic interaction between beads.
    The single chain diffusion is represented by Brownian motion of beads connected by harmonic springs.
    Coherent + incoherent scattering.

    Parameters
    ----------
    t : array
        Time in units nanoseconds.
    q: float, array
        Scattering vector in units nm^-1.
        If q is list a dataList is returned  otherwise a dataArray is returned.
    NN : integer
        Number of chain beads.
        If not given calculated from Dcm,l, mu.
    l : float, default 1
        Bond length between beads; units nm.
        If not given calculated from Dcm, NN, mu .
    pmax : integer, list of float, default is NN
        - integer => maximum mode number taken into account.
        - list    => list of amplitudes :math:`a_p > 0` for individual modes
          to allow weighing. Not given modes have weight zero.
    Dcm : float
        Center of mass diffusion in nm²/ns if explicitly is given.
        If not given Dcm is calculated
         - :math:`=0.196 k_bT/(R_e visc)` for theta solvent with :math:`\nu=0.5`
         - :math:`=0.203 k_bT/(R_e visc)` for good solvent  with :math:`\nu=0.6`
         with :math:`R_e=lN^{\nu}` .
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi)] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor and hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    tintern : float>0
        Additional relaxation time due to internal friction between neighboring beads in units ns.
    mu : float in range [0.01,0.99]
        :math:`\nu` describes solvent quality.
         - <0.5 collapsed chain
         - =0.5 theta solvent 0.5 (gaussian chain)
         - =0.6 good solvent
         - >0.6 swollen chain
    viscosity : float
        :math:`\eta` in units cPoise=mPa*s

        e.g. water :math:`visc(T=293 K) =1 mPas`
    Temp : float, default 273+20
        Temperature  in Kelvin.
    ftype : 'czif', default = 'zif'
        Type of internal friction and interaction modification.
         - Default Zimm is used with :math:`t_{intern}=0`
         - 'zif' Internal friction between neighboring beads in chain [3]_.
            :math:`t_{zp}=t_z p^{-3\nu}+t_{intern}`
         - 'czif' Bead confining harmonic potential with internal friction, only for :math:`\nu=0.5` [6]_ .
            The beads are confined in an additional harmonic potential with :math:`\frac{1}{2}k_c(r_n-0)^2` leading to
            a more compact configuration.  :math:`rk= k_c/k` describes the relative strength
            compared to the force between beads :math:`k`.
    rk : None , float
        :math:`rk= k_c/k` describes the relative force constant for *ftype* 'czif'.

    Returns
    -------
     S(q,t)/S(q,0) : dataArray : for single q, dataList : for multiple q
      - [time; Sqt; Sqt_inf; Sqtinc; Sqtz]
      - time units ns
      - Sqt as S(q,t)/S(q,0) coherent scattering with diffusion and mode contributions
      - Sqt_inf is coherent scattering with ONLY diffusion (no internal modes)
      - Sqtinc is incoherent scattering with diffusion and mode contributions (no separate diffusion)
      - Sqtz is coherent scattering with diffusion and mode contributions, but no Dcmfkt => f(q)=1
      - .q wavevector
      - .modecontribution  :math:`a_p` of coherent modes i in sequence as in PRL 71, 4158 equ (3)
      - .Re
      - .tzimm => Zimm time or rotational correlation time
      - .t_p  characteristic times
      - .... use .attr for all attributes

    Notes
    -----
    The Zimm model describes beads connected by harmonic springs with hydrodynamic interaction and free ends.
    The :math:`\nu` parameter scales between theta solvent :math:`\nu=0.5` and good solvent :math:`\nu=0.6`
    (excluded volume or swollen chain). The coherent intermediate scattering function :math:`S(q,t)` is

    .. math:: S(q,t) = \frac{1}{N} e^{-q^2D_{cm}t}\sum_{n,m}^N e^{-\frac{1}{6}q^2B(n,m,t)}

    .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1}^{N-1} A_p cos(\pi pn/N)cos(\pi pm/N) (1-e^{-t/t_{zp}})

    and for incoherent intermediate scattering function the same with :math:`n=m` in the first sum.

    with
     - :math:`A_p = a_p\frac{4R_e^2}{\pi^2}\frac{1}{p^{2\nu+1}}` mode amplitude  (usual :math:`a_p=1`)
     - :math:`t_{zp} = t_z p^{-3\nu}` mode relaxation time
     - :math:`t_z = \eta R_e^3/(\sqrt(3\pi) k_bT)` Zimm mode relaxation time
     - :math:`R_e=l N^{\nu}` end to end distance
     - :math:`k=3kT/l^2`                      force constant between beads
     - :math:`\xi=6\pi\eta l`                single bead friction in solvent with viscosity :math:`\eta`
     - :math:`a_p` additional amplitude for suppression of specific modes e.g. by topological constraints (see [5]_).
     - :math:`D_{cm} = \frac{8}{3(6\pi^3)^{1/2}} \frac{k_bT}{\eta R_e} = 0.196 \frac{k_bT}{\eta R_e}`

    Modifications (*ftype*) for internal friction and additional interaction:

    - ZIF : Zimm with internal friction between neighboring beads in chain [3]_ [4]_.
            - :math:`t_{zp}=t_z p^{{-3\nu}}+t_{intern}`
            - :math:`\xi_i=t_{intern}k=t_{intern}3k_bT/l^2`  internal friction per bead

    - CZIF : Compacted Zimm with internal friction [6]_.
             Restricted to :math:`\nu=0.5` , a combination with excluded volume is not valid.
             In [9]_ the beads are confined in an additional harmonic potential around the origin with
             :math:`\frac{1}{2}k_c(r_n-0)^2` leading to a more compact configuration.
             :math:`rk= k_c/k` describes the relative strength compared to the force between beads :math:`k`.
             Typically :math:`rk << 1` .

             - The mode amplitude prefactor changes from Zimm type to modified confined amplitudes

               .. math:: A_p =\frac{4Nl^2}{\pi^2}\frac{1}{p^2}\Rightarrow
                         A_p^c = \frac{4Nl^2}{\pi^2}\frac{1}{\frac{N^2k_c}{\pi^2k}+p^2}

             - The mode relaxation time changes from Zimm type to modified confined
               with :math:`t_{z} = \frac{\eta N^{3/2} l^3}{\sqrt(3\pi) k_bT}`

               .. math:: t_{zp} = t_z \frac{1}{p^{3/2}} \Rightarrow
                         t_{zp}^c =  t_z \frac{p^{1/2}}{\frac{N^2k_c}{\pi^2k} + p^2}

             - :math:`R_e^c` allows to determine :math:`k_c/k` from small angle scattering data

                .. math:: (R_e^c)^2 = \frac{2l^2}{\sqrt{k_c/k}}tanh(\frac{N}{2}\sqrt{k_c/k})

             - For a free diffusing chain we assume here (not given in [9]_ ) that the additional potential
               is :math:`\frac{1}{2}k_c(r_n-r_0)^2` with :math:`r_0` as the polymer center of mass.
               As the Langevin equation only depends on position distances the internal motions are not affected.
               The center of mass diffusion :math:`D_{cm}` can be calculated similar to the Zimm  :math:`D_{cm}` in [1]_
               assuming a Gaussian configuration with width :math:`R_e`. We find

                .. math:: D_{cm} = \frac{kT}{\xi_{p=0}} = \frac{8}{3(6\pi^3)^{1/2}} \frac{kT}{\eta R_e}

             - With :math:`rk=k_c/k \rightarrow 0` the original Zimm is recovered for amplitudes,
               relaxation and :math:`R_e` .

    From above the triple Dcm,l,N are fixed.
     - If 2 are given 3rd is calculated.
     - If all 3 are given the given values are used.

    For an example see `example_Zimm` and
    :ref:`collectivezimmdynamics` .


    Examples
    --------
    Coherent and incoherent contributions to Zimm dynamics.
    To mix the individual q dependent contributions of coherent and incoherent these have to be weighted by
    the according formfactor respectively incoherent scattering length and instrument specific measurement technique.
    Typically, diffusion and mode contributions cannot be separated.
    At larger Q the diffusion contributes marginally while at low Q diffusion dominates.
    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.02, 100, 40)
     q=np.r_[0.1:2:0.2]
     l=0.38  # nm , bond length amino acids
     zz = js.dynamic.finiteZimm(t, q, 124, 7, l=0.38, Dcm=0.37, tintern=0., Temp=273 + 60)
     p=js.grace(2,2)
     p.multi(2,1)
     p[0].xaxis(scale='log')
     p[0].yaxis(label='I(q,t)\scoherent')
     p[1].xaxis(label=r't / ns',scale='log')
     p[1].yaxis(label=r'I(q,t)\sincoherent')
     p[0].title('Zimm dynamics in a solvent')
     for i, z in enumerate(zz, 1):
         p[0].plot(z.X, z.Y, line=[1, 1, i], symbol=0, legend='')
         p[0].plot(z.X, z._Sqt_inf, line=[3, 2, i], symbol=0, legend='')
         p[1].plot(z.X, z._Sqtinc, line=[1, 2, i], symbol=0, legend=fr'q={z.q:.1f} nm\S-1')
     p[1].legend(x=0.02,y=0.8,charsize=0.5)
     p[0].text('only diffusion', x=0.02,y=0.55)
     p[0].text('diffusion + modes', x=15,y=0.65,rot=305)

     # p.save(js.examples.imagepath+'/Zimmcohinc.jpg',size=(1,1))

    .. image:: ../../examples/images/Zimmcohinc.jpg
     :align: center
     :width: 50 %
     :alt: Zimm



    References
    ----------
    .. [1]  Doi Edwards Theory of Polymer dynamics
            in appendix the equation is found
    .. [2]  Nonflexible Coils in Solution: A Neutron Spin-Echo Investigation of
            Alkyl-Substituted Polynorbonenes in Tetrahydrofuran
            Michael Monkenbusch et al.Macromolecules 2006, 39, 9473-9479
            The exponential is missing a "t"
            http://dx.doi.org/10.1021/ma0618979

    about internal friction

    .. [3]  Exploring the role of internal friction in the dynamics of unfolded proteins using simple polymer models
            Cheng et al.JOURNAL OF CHEMICAL PHYSICS 138, 074112 (2013)  http://dx.doi.org/10.1063/1.4792206
    .. [4]  Rouse Model with Internal Friction: A Coarse Grained Framework for Single Biopolymer Dynamics
            Khatri, McLeish|  Macromolecules 2007, 40, 6770-6777  http://dx.doi.org/10.1021/ma071175x

    mode contribution factors from

    .. [5]  Onset of Topological Constraints in Polymer Melts: A Mode Analysis by Neutron Spin Echo Spectroscopy
            D. Richter et al.PRL 71,4158-4161 (1993)
    .. [6]  Looping dynamics of a flexible chain with internal friction at different degrees of compactness.
            Samanta, N., & Chakrabarti, R. (2015).
            Physica A: Statistical Mechanics and Its Applications, 436, 377–386.
            https://doi.org/10.1016/j.physa.2015.05.042

    """
    # convert to Pa*s
    viscosity *= 1e-3
    q = np.atleast_1d(q)
    # check mu between 0.1 and 0.9
    mu = max(mu, 0.01)
    mu = min(mu, 0.99)
    # avoid l=0 from stupid users
    if l == 0: l = None
    # and linear interpolate prefactor
    ffact = 8 / (3 * 6 ** 0.5 * np.pi ** (3 / 2))
    fact = ffact + (mu - 0.5) / (0.6 - 0.5) * (0.203 - 0.196)
    NN = int(NN)
    if pmax is None: pmax = NN
    # if a list pmax of modes is given these are amplitudes for the modes
    # pmax is length of list
    if isinstance(pmax, numbers.Number):
        pmax = min(int(pmax), NN)
        modeamplist = np.ones(pmax)
    elif isinstance(pmax, list):
        modeamplist = np.abs(pmax)
    else:
        raise TypeError('pmax should be integer or list of amplitudes')

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif isinstance(Dcmfkt,dA):
            Dcmfunktion = lambda qq: Dcmfkt.interp(qq)
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    if ftype == 'czif':
        # compacted zimm with internal friction
        if mu != 0.5:
            raise ValueError('For ftype "czif" only mu=0.5 is allowed. ')

        if Dcm is None and l is not None and NN is not None:
            # Re = end to end distance
            Re = (2 * l ** 2 / rk ** 0.5 * np.tanh(NN / 2 * rk ** 0.5))**0.5
            # center of mass diffusion constant  in nm^2/ns
            Dcm = fact * kb * Temp / (Re * 1e-9 * viscosity) * 1e9
        elif Dcm is not None and l is None and NN is not None:
            Re = fact * kb * Temp / (Dcm * 1e-9 * viscosity) * 1e9
            l = Re * (rk ** 0.5 / 2 / np.tanh(NN / 2 * rk ** 0.5)) ** 0.5
        elif Dcm is not None and l is not None and NN is None:
            Re = fact * kb * Temp / (Dcm * 1e-9 * viscosity) * 1e9
            NN = 2 / rk ** 0.5 * np.arctanh(rk * Re ** 2 / 2 / l ** 2 )
        elif Dcm is not None and l is not None and NN is not None:
            Re = 2 * l ** 2 / rk ** 0.5 * np.tanh(NN / 2 * rk ** 0.5)
        else:
            raise TypeError('finiteZimm takes at least 2 arguments from Dcm, NN, l')
        # determine mode relaxation times
        # slowest zimm time
        tz1 = viscosity * NN ** (3 / 2) * (l * 1e-9) ** 3 / (np.sqrt(3 * pi) * kb * Temp) * 1e9
        # mode amplitudes
        p = np.r_[1:len(modeamplist) + 1]
        modeamplist = 4 * NN * l ** 2 / pi ** 2 * modeamplist

        tzp = tz1 * p ** 0.5 / (NN ** 2 / np.pi ** 2 * rk + p ** 2) + abs(tintern)
        modeamplist = modeamplist / (NN ** 2 / np.pi ** 2 * rk + p ** (2 * mu + 1))
    else:
        # ZIF with constant internal friction time added as default

        if Dcm is None and l is not None and NN is not None:
            Re = l * NN ** mu  # end to end distance
            Dcm = fact * kb * Temp / (Re * 1e-9 * viscosity) * 1e9  # diffusion constant  in nm^2/ns
        elif Dcm is not None and l is None and NN is not None:
            Re = fact * kb * Temp / (Dcm * 1e-9 * viscosity) * 1e9  # end to end distance
            l = Re / NN ** mu  # bond length
        elif Dcm is not None and l is not None and NN is None:
            Re = fact * kb * Temp / (Dcm * 1e-9 * viscosity) * 1e9  # end to end distance
            NN = int((Re / l) ** (1. / mu))
        elif Dcm is not None and l is not None and NN is not None:
            Re = l * NN ** mu
        else:
            raise TypeError('finiteZimm takes at least 2 arguments from Dcm,NN,l')

        # determine mode relaxation times
        # slowest zimm time
        tz1 = viscosity * (Re * 1e-9) ** 3 / (np.sqrt(3 * pi) * kb * Temp) * 1e9
        # mode amplitudes
        p = np.r_[1:len(modeamplist) + 1]
        modeamplist = 4 * Re ** 2 / pi ** 2 * modeamplist
        # characteristic Zimm time of mode p adding internal friction ti
        tzp = tz1 * p ** (-3 * mu) + abs(tintern)
        modeamplist = modeamplist / (p ** (2 * mu + 1))
        ftype = 'zif'

    # prepend 0 and append infinite time
    t = np.r_[0, np.atleast_1d(t)]

    # calc array of mode contributions including first constant element as list

    # do the calculation as an array of bnm=[n*m , len(t)] elements
    # sum up contributions for modes: all, diff+ mode1, only diffusion, t=0 amplitude for normalisation
    if useFortran:
        BNM = _bnmtzimm(t=t, NN=NN, l=l, mu=mu, modeamplist=modeamplist, tzp=tzp, fixedends=0)
        BNMmodes = BNM[:, -len(modeamplist):]
        BNMi = BNM[:, len(t):2*len(t)]
        BNMinf = BNM[:, 2 * len(t) + 1]  # coherent t = inf
        BNM = BNM[:, :len(t)]

    else:
        raise ImportError('finiteZimm only with working Fortran.')

    result = dL()
    for qq in q:
        # diffusion for all t
        Sqt = np.exp(-qq ** 2 * Dcm * Dcmfunktion(qq) * t[1:])  # only diffusion contribution
        Sqt0 = np.exp(-qq ** 2 * Dcm * t[1:])  # only diffusion contribution
        # amplitude at t=0
        expB0 = np.sum(np.exp(-qq ** 2 / 6. * BNM[:, 0]))  # is S(qq,t=0) coherent
        expB0i = np.sum(np.exp(-qq ** 2 / 6. * BNMi[:, 0]))  # is S(qq,t=0) incoherent
        # diffusion for infinite times in modes
        expBinf = np.sum(np.exp(-qq ** 2 / 6. * BNMinf))  # is S(qq,t=inf)
        # contribution all modes
        expB = np.sum(np.exp(-qq ** 2 / 6. * BNM[:, 1:]), axis=0)  # coherent
        expBi = np.sum(np.exp(-qq ** 2 / 6. * BNMi[:, 1:]), axis=0)  # incoherent
        # contribution only first modes
        result.append(np.c_[t[1:],
                            Sqt * expB / expB0,  # Zimm with H/S
                            Sqt * expBinf / expB0,  # no internal modes
                            Sqt * expBi / expB0i,  # incoherent contributions
                            Sqt0 * expB / expB0].T)  # pure Zimm , no H/S modification
        result[-1].modecontribution = (np.sum(np.exp(-qq ** 2 / 6. * BNMmodes), axis=0) / expB0).flatten()
        result[-1].q = qq
        result[-1].Re = Re
        result[-1].ll = l
        result[-1].pmax = pmax
        result[-1].Dcm = Dcm
        result[-1].effectiveDCM = Dcm * Dcmfunktion(qq)
        DZimm = fact * kb * Temp / (Re * 1e-9 * viscosity) * 1e9
        result[-1].DZimm = DZimm
        result[-1].mu = mu
        result[-1].viscosity = viscosity
        result[-1].Temperature = Temp
        result[-1].tzimm = tz1
        result[-1].moderelaxationtimes = tzp
        result[-1].tintern = tintern
        result[-1].modeAmplist = modeamplist
        result[-1].Drot = 1. / 6. / tz1
        result[-1].N = NN
        result[-1].columnname = ' time; Sqt; Sqt_inf; Sqtinc; Sqtz'
        result[-1].ftype = ftype
        result[-1].rk = rk
    if len(result) == 1:
        return result[0]
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


def fixedFiniteZimm(t, q, NN=None, pmax=None, l=None, Dcm=None, Dcmfkt=None, tintern=0., mu=0.5, viscosity=1.,
               ftype=None, rk=None, Temp=293, fixedends=1):
    r"""
    Zimm dynamics of a chain **with fixed ends** with internal friction and hydrodynamic interactions.

    Opposite to the :py:func:`finiteZimm` here one or both ends are fixed.
    This might be a chain tethered to a particle that defines the diffusion. Chains are non interacting.

    Parameters
    ----------
    fixedends : 0,1,2, default = 1
        Number of fixed ends. 0 is only for comparison and corresponds to :py:func:`finiteZimm` .
    t : array
        Time in units nanoseconds.
    q: float, array
        Scattering vector in units nm^-1.
        If q is list a dataList is returned  otherwise a dataArray is returned.
    NN : integer
        Number of chain beads.
    l : float, default 1
        Bond length between beads; units nm.
    pmax : integer, list of float, default is NN
        - integer => maximum mode number taken into account.
        - list    => list of amplitudes :math:`a_p > 0` for individual modes
          to allow weighing. Not given modes have weight zero.
    Dcm : float
        Center of mass diffusion in nm²/ns.
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi)] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor and hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    tintern : float>0
        Additional relaxation time due to internal friction between neighboring beads in units ns.
    mu : float in range [0.01,0.99]
        :math:`\nu` describes solvent quality.
         - <0.5 collapsed chain
         - =0.5 theta solvent 0.5 (gaussian chain)
         - =0.6 good solvent
         - >0.6 swollen chain
    viscosity : float
        :math:`\eta` in units cPoise=mPa*s  e.g. water :math:`visc(T=293 K) =1 mPas`
    Temp : float, default 273+20
        Temperature  in Kelvin.
    type : 'czif', default = 'zif'
        Type of internal friction and interaction modification.
         - Default Zimm is used with :math:`t_{intern}=0`
         - 'zif' Internal friction between neighboring beads in chain [3]_.
            :math:`t_{zp}=t_z p^{-3\nu}+t_{intern}`
         - 'czif' Bead confining harmonic potential with internal friction, only for :math:`\nu=0.5` [6]_ .
            The beads are confined in an additional harmonic potential with :math:`\frac{1}{2}k_c(r_n-0)^2` leading to
            a more compact configuration.  :math:`rk= k_c/k` describes the relative strength
            compared to the force between beads :math:`k`.
    rk : None , float
        :math:`rk= k_c/k` describes the relative force constant for *ftype* 'czif'.

    Returns
    -------
     S(q,t)/S(q,0) : dataArray : for single q, dataList : for multiple q
      - [time; Sqt; Sqt_inf; Sqtinc; Sqtz]
      - time units ns
      - Sqt is S(q,t)/S(q,0) coherent scattering with diffusion and mode contributions
      - Sqt_inf is coherent scattering with ONLY diffusion (no internal modes)
      - Sqtinc is incoherent scattering with diffusion and mode contributions (no separate diffusion)
      - Sqt0 is coherent scattering with diffusion and mode contributions, but no Dcmfkt => f(q)=1
      - .q wavevector
      - .modecontribution  :math:`a_p` of coherent modes i in sequence as in PRL 71, 4158 equ (3)
      - .Re is :math:`R_e=lN^{\nu}`
      - .tzimm => Zimm time or rotational correlation time
      - .t_p  characteristic times
      - .... use .attr for all attributes

    Notes
    -----
    The Zimm model describes beads connected by harmonic springs with hydrodynamic interaction (see 4.2 in [1]_).
    We find

    .. math:: S(q,t) = \frac{1}{N} e^{-q^2D_{cm}t}\sum_{n,m}^N e^{-\frac{1}{6}q^2B(n,m,t)}

    :math:`B(n,m,t)` describes the internal motions characterised by eigenmodes of the equation 4.II.6 in [1]_
    :math:`\frac{\zeta_p}{\zeta} k \frac{\partial^2 \Phi_{pn}}{\partial^2 n}=-k_p\Phi_{pn}`
    where :math:`\Phi_{pn}` describes the delocalisation of bead n in mode p.

    The boundary conditions select the eigenmodes from the general form :math:`\Phi_{pn} = A sin(kn) + Bcos(kn)`

    - Two free ends :math:`\partial\Phi_{pn}/\partial n=0 \text{ for  n=0 and n=N}`
      select A=0 and k=pπ/N (equ. 4.II.7+9 in [1]_):

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1}^{N-1} A_p cos(\pi pn/N)cos(\pi pm/N) (1-e^{-t/t_{zp}})

    - One fixed and one free end :math:`\partial\Phi_{pn}/\partial n=0 \text{ at n=0 and } \Phi_{pn}=0` at N
      select B=0 and k=(p-1/2)π/N (see [2]_):

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1-1/2}^{N-1-1/2} A_p sin(\pi pn/N) sin(\pi pm/N) (1-e^{-t/t_{zp}})

    - Two fixed ends :math:`\Phi_{pn}=0` at n=0 and n=N select B=0 and k=pπ/N:

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1}^{N-1} A_p sin(\pi pn/N)sin(\pi pm/N) (1-e^{-t/t_{zp}})


    For fixed ends the center of mass diffusion Dcm is that of the object where the chain is fixed.
    The chain dimension is defined by :math:`R_e=lN^{\nu}`.

    Unfortunately there are some papers that give wrong equations for fixed end Zimm or Rouse dynamics.
    The correct equations above can be retrieved from [1]_ appendix 4.II as solution of the
    differential equation 4.II.6 above which describes standing waves in a string or in a open tube.
    The classical Zimm/Rouse describe two open ends.

    For detailed description of parameters see :py:func:`finiteZimm`.


    Examples
    --------
    Let us assume we have a core shell micelle of diblock copolymers with a hydrophobic part that assemble in the core
    and the hydrophilic part extended into the solvent. The core is solvent matched and invisible.
    For low aggregation number the hydrophobic tails extending into the solvent dont interact and the
    motions are that of a Zimm chain with one fixed end. The center of mass diffusion is that of the micelle
    and much slower than :math:`D_{Zimm}` but could be determined by DLS dilution series or PFG-NMR.
    (See e.g. Mark et al. https://doi.org/10.1103/PhysRevLett.119.047801
    for silica nanoparticles with grafted chains)

    For comparison we think of a triblock with hydrophobic ends that will make a loop that both ends
    are fixed (but not at the same position). The hydrophilic is of same size.
    We neglect any influence of the core onto the chain configuration.

    We allow a Dcm ≈50 times slower than DZimm of the hydrophilic tail.

    We observe two relaxations, a faster of the internal dynamics and a slower because of diffusion.

    First compare one fixed end (full lines) with the free Zimm (broken lines).
    For long times the diffusion gets equal visible at low q for long times.

    Obviously the amplitude of mode relaxations is much stronger than for open ends due to the different eigenmodes.

    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.1, 1000, 40)
     q=np.r_[0.1:2:0.25]
     l=0.38  # nm , bond length amino acids

     p=js.grace(1.5,1.5)
     p.xaxis(label='q / ns',scale='log')
     p.yaxis(label='I(q,t)/I(q,0)')
     p.title('Compare 1 fixed to free ends')
     p.subtitle('solid line = one fixed end; broken lines = open ends')

     # free ends just for comapring
     fFZ0 = js.dynamic.fixedFiniteZimm(t, q, 124, 40, l=l, mu=0.5, Dcm=0.004,fixedends=0)
     # one fixed end
     fFZ1 = js.dynamic.fixedFiniteZimm(t, q, 124, 40, l=l, mu=0.5, Dcm=0.004,fixedends=1)

     for i, z in enumerate(fFZ1, 1):
         p.plot(z.X, z.Y, line=[1, 3, i], symbol=0, legend=fr'q={z.q:.1f} nm\S-1')
     for i, z in enumerate(fFZ0, 1):
         p.plot(z.X, z.Y, line=[3, 3, i], symbol=0, legend='')

     p.legend(x=0.2,y=0.4,charsize=0.6)

     # p.save(js.examples.imagepath+'/fixedZimm_vs_freeZimm.jpg',size=(1.,1.))

    .. image:: ../../examples/images/fixedZimm_vs_freeZimm.jpg
     :align: center
     :width: 50 %
     :alt: Zimm open vs. fixed ends


    Now we compare one and two open ends.
    The differences are marginally and will be difficult to discriminate in real measurements.
    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.1, 1000, 40)
     q=np.r_[0.1:2:0.25]
     l=0.38  # nm , bond length amino acids

     p=js.grace(1.5,1.5)
     p.xaxis(label='q / ns',scale='log')
     p.yaxis(label='I(q,t)/I(q,0)')
     p.title('Compare 1 fixed to 2 fixed ends')
     p.subtitle('solid line = one fixed end; broken lines = 2 fixed ends')

     # two fixed ends
     fFZ2 = js.dynamic.fixedFiniteZimm(t, q, 124, 40, l=l, mu=0.5, Dcm=0.004, fixedends=2)
     # one fixed end
     fFZ1 = js.dynamic.fixedFiniteZimm(t, q, 124, 40, l=l, mu=0.5, Dcm=0.004, fixedends=1)

     for i, z in enumerate(fFZ1, 1):
         p.plot(z.X, z.Y, line=[1, 3, i], symbol=0, legend=fr'q={z.q:.1f} nm\S-1')
     for i, z in enumerate(fFZ2, 1):
         p.plot(z.X, z.Y, line=[3, 3, i], symbol=0, legend='')

     p.legend(x=0.2,y=0.4,charsize=0.6)

     # p.save(js.examples.imagepath+'/fixedZimm_1vs2_fixed.jpg',size=(1,1))

    .. image:: ../../examples/images/fixedZimm_1vs2_fixed.jpg
     :align: center
     :width: 50 %
     :alt: Zimm 1 vs. 2 fixed ends



    References
    ----------
    .. [1] The Theory of Polymer dynamics
           Doi, M., & Edwards, S. F. (1988). Clarendon Press.

    .. [2] Normal Modes of Stretched Polymer Chains
           Y. Marciano and F. Brochard-Wyart
           Macromolecules 1995, 28, 985-990  https://doi.org/10.1021/ma00108a028


    """
    assert fixedends in [0, 1, 2]

    # convert to Pa*s
    viscosity *= 1e-3
    q = np.atleast_1d(q)
    # check mu between 0.1 and 0.9
    mu = max(mu, 0.01)
    mu = min(mu, 0.99)
    # avoid l=0 from stupid users
    if l == 0: l = None
    # and linear interpolate prefactor
    ffact = 8 / (3 * 6 ** 0.5 * np.pi ** (3 / 2))
    fact = ffact + (mu - 0.5) / (0.6 - 0.5) * (0.203 - 0.196)
    NN = int(NN)
    if pmax is None: pmax = NN
    # if a list pmax of modes is given these are amplitudes for the modes
    # pmax is length of list
    if isinstance(pmax, numbers.Number):
        pmax = min(int(pmax), NN)
        modeamplist = np.ones(pmax)
    elif isinstance(pmax, list):
        modeamplist = np.abs(pmax)
    else:
        raise TypeError('pmax should be integer or list of amplitudes')

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    if ftype == 'czif':
        # compacted zimm with internal friction
        if mu != 0.5:
            raise ValueError('For ftype "czif" only mu=0.5 is allowed. ')

        if Dcm is not None and l is not None and NN is not None:
            Re = 2 * l ** 2 / rk ** 0.5 * np.tanh(NN / 2 * rk ** 0.5)
        else:
            raise TypeError('fixedFiniteZimm needs NN, l, rk')
        # determine mode relaxation times
        # slowest zimm time
        tz1 = viscosity * NN ** (3 / 2) * (l * 1e-9) ** 3 / (np.sqrt(3 * pi) * kb * Temp) * 1e9
        # mode amplitudes
        p = np.r_[1:len(modeamplist) + 1]
        modeamplist = 4 * NN * l ** 2 / pi ** 2 * modeamplist

        tzp = tz1 * p ** 0.5 / (NN ** 2 / np.pi ** 2 * rk + p ** 2) + abs(tintern)
        modeamplist = modeamplist / (NN ** 2 / np.pi ** 2 * rk + p ** (2 * mu + 1))
    else:
        # ZIF with constant internal friction time added as default
        if Dcm is not None and l is not None and NN is not None:
            Re = l * NN ** mu
        else:
            raise TypeError('finiteZimm takes at least 2 arguments from Dcm,NN,l')

        # determine mode relaxation times
        # slowest zimm time
        tz1 = viscosity * (Re * 1e-9) ** 3 / (np.sqrt(3 * pi) * kb * Temp) * 1e9
        # mode amplitudes
        p = np.r_[1:len(modeamplist) + 1]
        modeamplist = 4 * Re ** 2 / pi ** 2 * modeamplist
        # characteristic Zimm time of mode p adding internal friction ti
        tzp = tz1 * p ** (-3 * mu) + abs(tintern)
        modeamplist = modeamplist / (p ** (2 * mu + 1))
        ftype = 'zif'

    # prepend 0 and append infinite time
    t = np.r_[0, np.atleast_1d(t)]

    # calc array of mode contributions including first constant element as list

    # do the calculation as an array of bnm=[n*m , len(t)] elements
    # sum up contributions for modes: all, diff+ mode1, only diffusion, t=0 amplitude for normalisation
    if useFortran:
        BNM = _bnmtzimm(t=t, NN=NN, l=l, mu=mu, modeamplist=modeamplist, tzp=tzp, fixedends=int(fixedends))
        BNMmodes = BNM[:, -len(modeamplist):]   # coh after infinite time  for each mode
        BNMi = BNM[:, len(t):2*len(t)]          # incoherent with mode contributions
        BNMinf = BNM[:, 2 * len(t) + 1]  # coherent t = inf
        BNM = BNM[:, :len(t)]                   # coh with mode contributions

    else:
        raise ImportError('finiteZimm only with working Fortran.')

    result = dL()
    for qq in q:
        # diffusion for all t
        Sqt = np.exp(-qq ** 2 * Dcm * Dcmfunktion(qq) * t[1:])  # only diffusion contribution
        Sqt0 = np.exp(-qq ** 2 * Dcm * t[1:])  # only diffusion contribution
        # amplitude at t=0
        expB0 = np.sum(np.exp(-qq ** 2 / 6. * BNM[:, 0]))  # is S(qq,t=0) coherent
        expB0i = np.sum(np.exp(-qq ** 2 / 6. * BNMi[:, 0]))  # is S(qq,t=0) incoherent
        # diffusion for infinite times in modes
        expBinf = np.sum(np.exp(-qq ** 2 / 6. * BNMinf))  # is S(qq,t=inf)
        # contribution all modes
        expB = np.sum(np.exp(-qq ** 2 / 6. * BNM[:, 1:]), axis=0)  # coherent
        expBi = np.sum(np.exp(-qq ** 2 / 6. * BNMi[:, 1:]), axis=0)  # incoherent
        # contribution only first modes
        result.append(np.c_[t[1:],
                            Sqt * expB / expB0,  # Zimm with H/S
                            Sqt * expBinf / expB0,  # no internal modes
                            Sqt * expBi / expB0i,  # incoherent contributions
                            Sqt0 * expB / expB0].T)  # pure Zimm , no H/S modification
        result[-1].modecontribution = (np.sum(np.exp(-qq ** 2 / 6. * BNMmodes), axis=0) / expB0).flatten()
        result[-1].q = qq
        result[-1].Re = Re
        result[-1].ll = l
        result[-1].pmax = pmax
        result[-1].Dcm = Dcm
        result[-1].effectiveDCM = Dcm * Dcmfunktion(qq)
        DZimm = fact * kb * Temp / (Re * 1e-9 * viscosity) * 1e9
        result[-1].DZimm = DZimm
        result[-1].mu = mu
        result[-1].viscosity = viscosity
        result[-1].Temperature = Temp
        result[-1].tzimm = tz1
        result[-1].moderelaxationtimes = tzp
        result[-1].tintern = tintern
        result[-1].modeAmplist = modeamplist
        result[-1].Drot = 1. / 6. / tz1
        result[-1].N = NN
        result[-1].columnname = ' time; Sqt; Sqt_inf; Sqtinc; Sqtz'
        result[-1].ftype = ftype
        result[-1].rk = rk
        result[-1].fixedends = fixedends

    if len(result) == 1:
        return result[0]
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


@formel.memoize()
def _bnmtrouse(t, NN, l, modeamplist, trp, fixedends=0):
    return fscatter.dynamic.bnmt(t, NN, l, 0.5, modeamplist, trp, fixedends)


def finiteRouse(t, q, NN=None, pmax=None, l=None, frict=None, Dcm=None, Wl4=None, Dcmfkt=None, tintern=0.,
                Temp=293, ftype=None, specm=None, specb=None, rk=None):
    r"""
    Rouse dynamics of a finite chain with N beads of bonds length l and internal friction.

    The Rouse model describes the conformational dynamics of an ideal chain.
    The single chain diffusion is represented by Brownian motion of beads connected by harmonic springs.
    No excluded volume, random thermal force, drag force with solvent,
    no hydrodynamic interaction and optional internal friction.
    Coherent + incoherent scattering.


    Parameters
    ----------
    t : array
        Time in units nanoseconds
    q : float, list
        Scattering vector, units nm^-1
        For a list a dataList is returned otherwise a dataArray is returned
    NN : integer
        Number of chain beads.
    l : float, default 1
        Bond length between beads; unit nm.
    pmax : integer, list of floats
        - integer => maximum mode number (:math:`a_p=1`)
        - list    => :math:`a_p` list of amplitudes>0 for individual modes
          to allow weighing; not given modes have weight zero
    frict : float
        Friction of a single bead/monomer in units `Pas*m=kg/s=1e-6 g/ns`
        :math:`\xi = 6\pi\eta l`, .
        A monomer bead with `l=R=0.1nm = 0.1e-9m` in H2O(20°C) (1 mPas) => 1.89e-12 Pas*m.
        Rouse dynamics in a melt needs the bead friction with effective viscosity of the melt.

    Wl4 : float
        :math:`W_l^4` Characteristic value to calc friction and Dcm.

        :math:`D_{cm}=\frac{W_l^4}{3R_e^2}` and characteristic Rouse variable
        :math:`\Omega_Rt=(q^2/6)^2 W_l^4 t`
    Dcm : float
        Center of mass diffusion in nm^2/ns.
         - :math:`D_{cm}=k_bT/(N\xi)`     with :math:`\xi` = friction of single bead in solvent
         - :math:`D_{cm}=W_l^4/(3Nl^2)=W_l^4/(3Re^2)`
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi) ] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor or hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    tintern : float>0
        Relaxation time due to internal friction between neighboring beads in ns.
    ftype : 'rni', 'rap','nonspec', 'specrif', 'crif', default = 'rif'
        Type of internal friction. See [7]_ for a description and respective references.
         - *'rif'*: Internal friction between neighboring beads in chain. :math:`t_{rp}=t_r p^{-2}+t_{intern}`
         - *'rni'*: Rouse model with non-local interactions (RNI).
           Additional friction between random close approaching beads. :math:`t_{rp}=t_r p^{-2}+N/p t_{intern}`
         - *'rap'*: Rouse model with anharmonic potentials due to stiffness of the chain
           :math:`t_{rp}=t_r p^{-2}+t_{intern}ln(N/p\pi)`
         - *'specrif'*: Specific interactions of strength :math:`b` between beads separated by *m* bonds.
           See [7]_. :math:`t_{rp}=t_r p^{-2} (1+bm^2)^{-1} + (1+m^2/(1+bm^2))t_{intern}`
         - *'crif'*: Bead confining potential with internal friction. The beads are confined in an additional
           harmonic potential with :math:`\frac{1}{2}k_c(r_n-0)^2` leading to a more compact configuration.
           :math:`rk= k_c/k` describes the relative strength compared to the force between beads :math:`k`.
    Temp : float
        Temperature  Kelvin = 273+T[°C]
    specm,specb: float
        Parameters *m, b* used in internal friction models 'spec' and 'specrif'.
    rk : None , float
        :math:`rk= k_c/k` describes the relative force constant for *ftype* 'crif'.

    Returns
    -------
     S(q,t)/S(q,0) : dataArray : for single q, dataList : multiple q
      - [time; Sqt; Sqt_inf; Sqtinc]
      - time units ns
      - Sqt is S(q,t)/S(q,0) coherent scattering with diffusion and mode contributions
      - Sqt_inf is coherent scattering with ONLY diffusion
      - Sqtinc is incoherent scattering with diffusion and mode contributions (no separate diffusion)
      - .q wavevector
      - .Iq normalized form factor
      - .Wl4
      - .Re     end to end distance :math:`R_e^2=l^2N`
      - .trouse rotational correlation time or rouse time
                :math:`tr_1 = \xi N^2 l^2/(3 \pi^2 k_bT)= <R_e^2>/(3\pi D_{cm}) = N^2\xi/(pi^2k)`
      - .tintern relaxation time due to internal friction
      - .tr_p characteristic times   :math:`tr_p=tr_1 p^{-2}+t_{intern}`
      - .beadfriction
      - .ftype type of internal friction
      - .... use .attr to see all attributes

    Notes
    -----
    The Rouse model describes beads connected by harmonic springs without hydrodynamic interactions and open ends.
    The coherent intermediate scattering function :math:`S(q,t)` is [1]_ [2]_ :

    .. math:: S(q,t) = \frac{1}{N} e^{-q^2D_{cm}t} \sum_{n,m}^N e^{-\frac{1}{6}q^2B(n,m,t)}

    .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 +
                                \sum_{p=1}^{N-1} A_p cos(\pi pn/N)cos(\pi pm/N) (1-e^{-t/t_{rp}})

    and for incoherent intermediate scattering function the same with :math:`n=m` in the first sum.

    with
     - :math:`A_p = a_p\frac{4R_e^2}{\pi^2}\frac{1}{p^2}` mode amplitude  (usual :math:`a_p=1`)
     - :math:`t_{rp} = \frac{t_r}{p^2}` mode relaxation time with Rouse time
       :math:`t_r =\frac{\xi N R_e^2 }{3\pi^2 k_bT} = \frac{R_e^2}{3\pi^2 D_{cm}} = \frac{N^2 \xi}{\pi^2 k}`
     - :math:`D_{cm}=kT/{N\xi}`        center of mass diffusion
     - :math:`k=3k_bT/l^2`             force constant k between beads.
     - :math:`\xi=6\pi visc R`         single bead friction :math:`\xi` in solvent (e.g. surrounding melt)
     - :math:`t_{intern}=\xi_i/k`        additional relaxation time due to internal friction :math:`\xi_i`

    Modifications (*ftype*) for internal friction and additional interaction (see [7]_ and [9]_):

    - RIF : Rouse with internal friction between neighboring beads in chain [3]_ [4]_.
            - :math:`t_{rp}=t_r p^{-2}+t_{intern}`
            - :math:`\xi_i=t_{intern}k=t_{intern}3k_bT/l^2`  internal friction per bead
    - RNI : Rouse model with non-local interactions as additional friction between spatial close beads [5]_ .
            - :math:`t_{rp}=t_r p^{-2}+Nt_{intern}/p`
    - RAP : Rouse model with anharmonic potentials in bonds describing the stiffness of the chain [6]_.
            - :math:`t_{rp}=t_r p^{-2}+t_{intern}ln(N/p\pi)`
    - SPECRIF : Specific interactions of relative strength :math:`b` between beads separated by *m* bonds.
            Internal friction between neighboring beads as in RIF is added.

            - :math:`t_{rp}=t_r p^{-2} (1+bm^2)^{-1} + (1+\frac{m^2}{1+bm^2})t_{intern}`
            - :math:`b=k_{specific}/k_{neighbor}` relative strength of both interactions.
            - The interaction is between **all** pairs separated by m.
    - CRIF : Compacted Rouse with internal friction [9]_.
             The beads are confined in an additional harmonic potential with
             :math:`\frac{1}{2}k_c(r_n-0)^2` leading to a more compact configuration.
             :math:`rk= k_c/k` describes the relative strength compared to the force between beads :math:`k`.
             Typically :math:`rk << 1` .

             - The mode amplitude prefactor changes from Rouse type to modified confined amplitudes

               .. math:: A_p =\frac{4R_e^2}{\pi^2}\frac{1}{p^2}\Rightarrow
                         A_p^c = \frac{4R_e^2}{\pi^2}\frac{1}{\frac{N^2k_c}{\pi^2k}+p^2}

             - The mode relaxation time changes from Rouse type to modified confined

               .. math:: t_{rp} = \frac{t_r}{p^2} \Rightarrow
                         t_{rp}^c =  \frac{t_r}{\frac{N^2k_c}{\pi^2k} + p^2}

             - :math:`R_e` allows to determine :math:`k_c/k` from small angle scattering data

                .. math:: R_e^2 = \frac{2l^2}{\sqrt{k_c/k}}tanh(\frac{N}{2}\sqrt{k_c/k})
             - We assume here that the additional potential is :math:`\frac{1}{2}k_c(r_n-r_0)^2` with :math:`r_0`
               as the polymer center of mass. As the Langevin equation only depends on relative distances the
               internal motions are not affected. The center of mass diffusion :math:`D_{cm}=f(R_e)` is not affected
               as the mode dependent friction coefficients don't change [9]_.
             - With :math:`rk=k_c/k \rightarrow 0` the original Rouse is recovered for amplitudes,
               relaxation and :math:`R_e` .

    A combination of different effects is possible [7]_ (but not implemented).

    The amplitude :math:`A_p` allows for additional suppression of specific modes
    e.g. by topological constraints (see [8]_).

    From above the triple Dcm,l,NN are fixed.
     - If 2 are given 3rd is calculated
     - If all 3 are given the given values are used

    For an example see `example_Zimm` and
    :ref:`collectivezimmdynamics` how to include collective effects.

    Examples
    --------
    Coherent and incoherent contributions to Rouse dynamics.
    To mix the individual q dependent contributions have to be weighted with the according formfactor respectivly
    incoherent scattering length and instrument specific measurement technique.
    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.02, 100, 40)
     q=np.r_[0.1:2:0.2]
     l=0.38  # nm , bond length amino acids
     rr = js.dynamic.finiteRouse(t, q, 124, 7, l=0.38, Dcm=0.37, tintern=0., Temp=273 + 60)
     p=js.grace()
     p.multi(2,1)
     p[0].xaxis(scale='log')
     p[0].yaxis(label='I(q,t)\scoherent')
     p[1].xaxis(label=r't / ns',scale='log')
     p[1].yaxis(label=r'I(q,t)\sincoherent')
     p[0].title('Rouse dynamics in a solvent')
     for i, z in enumerate(rr, 1):
         p[0].plot(z.X, z.Y, line=[1, 1, i], symbol=0, legend='q=%g' % z.q)
         p[0].plot(z.X, z._Sqt_inf, line=[3, 2, i], symbol=0, legend='q=%g diff' % z.q)
         p[1].plot(z.X, z._Sqtinc, line=[1, 2, i], symbol=0, legend='q=%g diff' % z.q)

     #p.save(js.examples.imagepath+'/Rousecohinc.jpg')

    .. image:: ../../examples/images/Rousecohinc.jpg
     :align: center
     :width: 50 %
     :alt: Rouse

    References
    ----------
    .. [1]  Doi Edwards Theory of Polymer dynamics
            in the appendix the equation is found
    .. [2]  Nonflexible Coils in Solution: A Neutron Spin-Echo Investigation of
            Alkyl-Substituted Polynorbonenes in Tetrahydrofuran
            Michael Monkenbusch et al.Macromolecules 2006, 39, 9473-9479
            The exponential is missing a "t"
            http://dx.doi.org/10.1021/ma0618979

    about internal friction

    .. [3]  Exploring the role of internal friction in the dynamics of unfolded proteins using simple polymer models
            Cheng et al.JOURNAL OF CHEMICAL PHYSICS 138, 074112 (2013)  http://dx.doi.org/10.1063/1.4792206
    .. [4]  Rouse Model with Internal Friction: A Coarse Grained Framework for Single Biopolymer Dynamics
            Khatri, McLeish|  Macromolecules 2007, 40, 6770-6777  http://dx.doi.org/10.1021/ma071175x
    .. [5]  Origin of internal viscosities in dilute polymer solutions
            P. G. de Gennes
            J. Chem. Phys. 66, 5825 (1977); https://doi.org/10.1063/1.433861
    .. [6]  Microscopic theory of polymer internal viscosity: Mode coupling approximation for the Rouse model.
            Adelman, S. A., & Freed, K. F. (1977).
            The Journal of Chemical Physics, 67(4), 1380–1393. https://doi.org/10.1063/1.435011
    .. [7]  Internal friction in an intrinsically disordered protein - Comparing Rouse-like models with experiments
            A. Soranno, F. Zosel, H. Hofmann
            J. Chem. Phys. 148, 123326 (2018)  http://aip.scitation.org/doi/10.1063/1.5009286
    .. [8]  Onset of topological constraints in polymer melts: A mode analysis by neutron spin echo spectroscopy
            D. Richter, L. Willner, A. Zirkel, B. Farago, L. J. Fetters, and J. S. Huang
            Phys. Rev. Lett. 71, 4158  https://doi.org/10.1103/PhysRevLett.71.4158
    .. [9]  Looping dynamics of a flexible chain with internal friction at different degrees of compactness.
            Samanta, N., & Chakrabarti, R. (2015).
            Physica A: Statistical Mechanics and Its Applications, 436, 377–386.
            https://doi.org/10.1016/j.physa.2015.05.042

    """
    # assure flatt arrays
    t = np.atleast_1d(t)
    q = np.atleast_1d(q)
    # avoid l=0
    if l == 0: l = None
    NN = int(NN)
    if pmax is None: pmax = NN
    # if a list pmax of modes is given these are amplitudes for the modes
    # pmax is length of list
    if isinstance(pmax, numbers.Number):
        pmax = min(int(pmax), NN)
        modeamplist = np.ones(pmax)
    elif isinstance(pmax, list):
        modeamplist = np.abs(pmax)
    else:
        raise TypeError('pmax should be integer or list of amplitudes')

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    # calc the cases of not given parameters for Dcm,NN,l
    # kB*Temp is in SI so convert all to SI then back to ns
    if rk is not None:
        # [9]_ equ 17  for rk->0 this goes to l*NN**0.5
        Re = 2 * l ** 2 / rk ** 0.5 * np.tanh(NN / 2 * rk ** 0.5)
    else:
        # end to end distance
        Re = l * np.sqrt(NN)
    # friction or Dcm must be given
    # Dcm is independent of rk as no HI in Rouse
    if Dcm is not None and frict is not None:
        pass
    elif Dcm is not None and frict is None:
        frict = kb * Temp / NN / (Dcm * 1e-9)  # diffusion constant  in nm^2/ns
    elif Dcm is None and frict is not None:
        Dcm = kb * Temp / NN / frict * 1e9  # diffusion constant  in nm^2/ns
    elif Dcm is None and frict is None and Wl4 is not None:
        Dcm = Wl4 / (3 * Re ** 2)
        frict = kb * Temp / NN / (Dcm * 1e-9)
    else:
        raise TypeError('fqtfiniteRouse takes at least 1 arguments from Dcm, frict, Wl4')

    # slowest relaxation time is rouse time
    tr1 = frict * NN ** 2 * l ** 2 / (3 * pi ** 2 * kb * Temp) * 1e-9
    # different models for internal friction
    p = np.r_[1:len(modeamplist) + 1]
    modeamplist = 4 * Re ** 2 / pi ** 2 * modeamplist
    if ftype == 'rni':
        # rouse with non-local interactions
        # frict = f_s + p *f_i
        trp = tr1 / p ** 2 + NN * abs(tintern) / p
        modeamplist = modeamplist / p ** 2
    elif ftype == 'rap':
        # rouse model with anharmonic potentials
        trp = tr1 / p ** 2 + abs(tintern) * np.log(NN / p * np.pi)
        modeamplist = modeamplist / p ** 2
    elif ftype == 'specrif':
        # rouse model with specific interactions between bead separated by specm of relative strength specb
        # + rif
        trp = tr1 / p ** 2 / (1 + specb * specm ** 2) + (1 + specm ** 2 / (1 + specb * specm ** 2)) * abs(tintern)
        modeamplist = modeamplist / p ** 2
    elif ftype == 'crif':
        # compacted rouse with internal friction
        trp = tr1 / (NN ** 2 / np.pi ** 2 * rk + p ** 2) + abs(tintern)
        modeamplist = modeamplist / (NN ** 2 / np.pi ** 2 * rk + p ** 2)
    else:
        # RIF with constant internal friction time added as default
        trp = tr1 / p ** 2 + abs(tintern)
        modeamplist = modeamplist / p ** 2
        ftype = 'rif'

    # prepend 0
    t = np.r_[0, np.atleast_1d(t)]

    # do the calculation as an 2D array of bnm=[n*m , len(t) +len(t)+len(modeamplist)] elements
    if useFortran:
        RNM = _bnmtrouse(t=t, NN=NN, l=l, modeamplist=modeamplist, trp=trp)
        RNMmodes = RNM[:, -len(modeamplist):]
        RNMi = RNM[:, len(t):(2*len(t))]  # incoherent
        RNMinf = RNM[:, 2*len(t)+1]  # coherent t = inf
        RNM = RNM[:, :len(t)]  # coherent
    else:
        raise ImportError('finiteRouse only with working Fortran.')

    result = dL()
    for qq in q:
        # diffusion for all t
        exp_q2Dt = np.exp(-qq ** 2 * Dcm * Dcmfunktion(qq) * t[1:])  # only diffusion contribution
        # amplitude at t=0
        expB0 = np.sum(np.exp(-qq ** 2 / 6. * RNM[:, 0]))  # is S(qq,t=0)  # coherent t=0
        expB0i = np.sum(np.exp(-qq ** 2 / 6. * RNMi[:, 0]))  # is S(qq,t=0)  # incoherent t=0
        # diffusion for infinite times in modes
        expBinf = np.sum(np.exp(-qq ** 2 / 6. * RNMinf))  # is S(qq,t=inf)
        # contribution all modes
        expB = np.sum(np.exp(-qq ** 2 / 6. * RNM[:, 1:]), axis=0)  # coherent
        expBi = np.sum(np.exp(-qq ** 2 / 6. * RNMi[:, 1:]), axis=0)  # incoherent

        # contribution only first modes
        result.append(dA(np.c_[t[1:],                          # times
                               exp_q2Dt * expB / expB0,        # Sqt
                               exp_q2Dt * expBinf / expB0,     # Sqt_inf
                               exp_q2Dt * expBi / expB0i].T))  # inc

        result[-1].setColumnIndex(iey=None)
        result[-1].columnname = 'time; Sqt; Sqt_inf; Sqtinc'
        result[-1].modecontribution = (np.sum(np.exp(-qq ** 2 / 6. * RNMmodes), axis=0) / expB0).flatten()
        result[-1].Iq = expB0 / NN**2  # normalised form factor
        result[-1].q = qq
        result[-1].Re = Re
        result[-1].ll = l
        result[-1].pmax = pmax
        result[-1].Dcm = Dcm
        result[-1].effectiveDCM = Dcm * Dcmfunktion(qq)
        result[-1].Dcmrouse = kb * Temp / NN / frict * 1e9
        result[-1].Temperature = Temp
        result[-1].trouse = tr1
        result[-1].tintern = tintern
        result[-1].moderelaxationtimes = trp
        result[-1].modeamplitudes = modeamplist
        result[-1].beadfriction = frict
        result[-1].Drot = 1. / 6. / tr1
        result[-1].N = NN
        result[-1].internalfriction_g_ns = (tintern * 1e-9) * 3 * kb * Temp / (l * 1e-9) ** 2 * 1e-6
        result[-1].ftype = ftype
        result[-1].rk = rk
        if specm is not None:
            result[-1].specm = specm
            result[-1].specb = specb
    if len(result) == 1:
        return result[0]
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


def fixedFiniteRouse(t, q, NN=None, pmax=None, l=None, frict=None, Dcm=None, Wl4=None, Dcmfkt=None, tintern=0.,
                Temp=293, ftype=None, specm=None, specb=None, rk=None, fixedends=1):
    r"""
    Rouse dynamics of a chain **with fixed ends** with N beads of bonds length l and internal friction.

    Opposite to the :py:func:`finiteRouse` here one or both ends are fixed.
    This might be a chain tethered to a particle that defines the diffusion. Chains are non interacting.

    Parameters
    ----------
    fixedends : 0,1,2, default = 1
        Number of fixed ends. 0 is only for comparison and corresponds to :py:func:`finiteZimm` .
    t : array
        Time in units nanoseconds
    q : float, list
        Scattering vector, units nm^-1
        For a list a dataList is returned otherwise a dataArray is returned
    NN : integer
        Number of chain beads.
    l : float, default 1
        Bond length between beads; unit nm.
    pmax : integer, list of floats
        - integer => maximum mode number (:math:`a_p=1`)
        - list    => :math:`a_p` list of amplitudes>0 for individual modes
          to allow weighing; not given modes have weight zero
    frict : float
        Friction of a single bead/monomer in units `Pas*m=kg/s=1e-6 g/ns`:math:`\xi = 6\pi\eta l`, .

        A monomer bead with `l=R=0.1nm = 0.1e-9m`  in H2O(20°C) (1 mPas) => 1.89e-12 Pas*m.

        Rouse dynamics in a melt needs the bead friction with effective viscosity of the melt
        which should be much higher than water.
        Polymer melts are typically examined above the glass temperature of the polymer.

    Wl4 : float
        :math:`W_l^4` Characteristic value to calc friction and Dcm.

        :math:`\Omega_Rt=(q^2/6)^2 W_l^4 t`
    Dcm : float
        Center of mass diffusion in nm^2/ns.
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi) ] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor or hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    tintern : float>0
        Relaxation time due to internal friction between neighboring beads in ns.
    ftype : 'rni', 'rap','nonspec', 'specrif', 'crif', default = 'rif'
        Type of internal friction. See [7]_ for a description and respective references.
         - *'rif'*: Internal friction between neighboring beads in chain. :math:`t_{rp}=t_r p^{-2}+t_{intern}`
         - *'rni'*: Rouse model with non-local interactions (RNI).
           Additional friction between random close approaching beads. :math:`t_{rp}=t_r p^{-2}+N/p t_{intern}`
         - *'rap'*: Rouse model with anharmonic potentials due to stiffness of the chain
           :math:`t_{rp}=t_r p^{-2}+t_{intern}ln(N/p\pi)`
         - *'specrif'*: Specific interactions of strength :math:`b` between beads separated by *m* bonds.
           See [7]_. :math:`t_{rp}=t_r p^{-2} (1+bm^2)^{-1} + (1+m^2/(1+bm^2))t_{intern}`
         - *'crif'*: Bead confining potential with internal friction. The beads are confined in an additional
           harmonic potential with :math:`\frac{1}{2}k_c(r_n-0)^2` leading to a more compact configuration.
           :math:`rk= k_c/k` describes the relative strength compared to the force between beads :math:`k`.
    Temp : float
        Temperature  Kelvin = 273+T[°C]
    specm,specb: float
        Parameters *m, b* used in internal friction models 'spec' and 'specrif'.
    rk : None , float
        :math:`rk= k_c/k` describes the relative force constant for *ftype* 'crif'.

    Returns
    -------
     S(q,t)/S(q,0) : dataArray  for single q, dataList for multiple q
      - [time; Sqt; Sqt_inf; Sqtinc]
      - time units ns
      - Sqt is S(q,t)/S(q,0) coherent scattering with diffusion and mode contributions
      - Sqt_inf is coherent scattering with ONLY diffusion
      - Sqtinc is incoherent scattering with diffusion and mode contributions (no separate diffusion)
      - .q wavevector
      - .Wl4
      - .Re     end to end distance :math:`R_e^2=l^2N`
      - .trouse rotational correlation time or rouse time
                :math:`tr_1 = \xi N^2 l^2/(3 \pi^2 k_bT)= <R_e^2>/(3\pi D_{cm}) = N^2\xi/(pi^2k)`
      - .tintern relaxation time due to internal friction
      - .tr_p characteristic times   :math:`tr_p=tr_1 p^{-2}+t_{intern}`
      - .beadfriction
      - .ftype type of internal friction
      - .... use .attr to see all attributes

    Notes
    -----
    The Rouse model describes beads connected by harmonic springs without hydrodynamic interactions and open ends.
    The coherent intermediate scattering function :math:`S(q,t)` is [1]_ [2]_ :

    .. math:: S(q,t) = \frac{1}{N} e^{-q^2D_{cm}t} \sum_{n,m}^N e^{-\frac{1}{6}q^2B(n,m,t)}

    :math:`B(n,m,t)` describes the internal motions characterised by eigenmodes of the equation 4.II.6 in [1]_
    :math:`\frac{\zeta_p}{\zeta} k \frac{\partial^2 \Phi_{pn}}{\partial^2 n}=-k_p\Phi_{pn}`
    where :math:`\Phi_{pn}` describes the delocalisation of bead n in mode p.

    The boundary conditions select the eigenmodes from the general form :math:`\Phi_{pn} = A sin(kn) + Bcos(kn)`

    - Two free ends :math:`\partial\Phi_{pn}/\partial n=0 \text{ for  n=0 and n=N}`
      select A=0 and k=pπ/N (equ. 4.II.7+9 in [1]_):

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1}^{N-1} A_p cos(\pi pn/N)cos(\pi pm/N) (1-e^{-t/t_{zp}})

    - One fixed and one free end :math:`\partial\Phi_{pn}/\partial n=0 \text{ at n=0 and } \Phi_{pn}=0` at N
      select B=0 and k=(p-1/2)π/N (see [3]_):

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1-1/2}^{N-1-1/2} A_p sin(\pi pn/N) sin(\pi pm/N) (1-e^{-t/t_{zp}})

      With the ends interchanged this can be written like [4]_ (same result)

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1-1/2}^{N-1-1/2} A_p cos(\pi pn/N) cos(\pi pm/N) (1-e^{-t/t_{zp}})

    - Two fixed ends :math:`\Phi_{pn}=0` at n=0 and n=N select B=0 and k=pπ/N:

      .. math:: B(n,m,t)=|n-m|^{2\nu}l^2 + \sum_{p=1}^{N-1} A_p sin(\pi pn/N)sin(\pi pm/N) (1-e^{-t/t_{zp}})


    For fixed ends the center of mass diffusion Dcm is that of the object where the chain is fixed.
    The chain dimension is defined by :math:`R_e=lN^{0.5}`.

    Unfortunately there are some papers that give wrong equations for fixed ends Zimmm or Rouse dynamics.
    The correct equations above can be retrieved from [1]_ appendix 4.II as solution of the
    differential equation 4.II.6 above which describes standing waves in a string or in a open tube.
    The classical Zimm/Rouse describe two open ends.

    For detailed description of parameters see :py:func:`finiteRouse`.


    Examples
    --------
    Let us assume we have a core-shell particle with grafted chains on a core
    (See e.g. Mark et al. [4]_ for silica nanoparticles with grafted chains)
    For low aggregation number the chains dont interact and the
    motions are that of a Rouse chain with one fixed end. The center of mass diffusion is that of the core-shell
    particle and much slower than :math:`D_{Rouse}` but could be determined by PFG-NMR.

    For comparison we think of both ends grafted that will make a loop that both ends
    are fixed (but not at the same position).
    We neglect any influence of the core onto the chain configuration (at least its only a half space).

    We allow a Dcm ≈50 times slower than DRouse.

    We observe two relaxations, a faster of the internal dynamics and a slower because of diffusion.

    First compare one fixed end (full lines) with the free Rouse (broken lines).
    For long times the diffusion gets equal visible at low q for long times.

    The internal relaxation times are similar as the single chains relax in the same way which we see at larger Q.
    The amplitude of mode relaxations is weaker for open ends (the diffusion plateau is higher)
    due to the different eigenmodes. The effect is already present in the first mode (pmax=1).
    It seems to result from the decorrelation of fixed and open end
    compared to the correlated motion with both ends open.

    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.1, 1000, 40)
     q=np.r_[0.1:2:0.25]
     l=0.38  # nm , bond length amino acids

     p=js.grace(1.5,1.5)
     p.xaxis(label='q / ns',scale='log')
     p.yaxis(label='I(q,t)/I(q,0)')
     p.title('Compare 1 fixed to free ends')
     p.subtitle('solid line = one fixed end; broken lines = open ends')

     # free ends just for comapring
     fFR0 = js.dynamic.fixedFiniteRouse(t, q, 124, 40, l=l, Dcm=0.004,frict=9e-14,fixedends=0)
     # one fixed end
     fFR1 = js.dynamic.fixedFiniteRouse(t, q, 124, 40, l=l, Dcm=0.004,frict=9e-14,fixedends=1)

     for i, z in enumerate(fFR1, 1):
         p.plot(z.X, z.Y, line=[1, 3, i], symbol=0, legend=fr'q={z.q:.1f} nm\S-1')
     for i, z in enumerate(fFR0, 1):
         p.plot(z.X, z.Y, line=[3, 3, i], symbol=0, legend='')

     p.legend(x=0.2,y=0.4,charsize=0.6)

     # p.save(js.examples.imagepath+'/fixed_vs_freeRouse.jpg',size=(1.1,1.1))

    .. image:: ../../examples/images/fixed_vs_freeRouse.jpg
     :align: center
     :width: 50 %
     :alt: Zimm open vs. fixed ends


    Now we compare one and two open ends.
    The differences are marginally and only significant at larger Q for long times as the plateau is different.
    The changes will be difficult to discriminate in real measurements.
    ::

     import jscatter as js
     import numpy as np
     t = js.loglist(0.01, 1000, 50)
     q=np.r_[0.1:4:0.4]
     l=0.38  # nm , bond length amino acids

     p=js.grace(1.5,1.5)
     p.xaxis(label='q / ns',scale='log')
     p.yaxis(label='I(q,t)/I(q,0)')
     p.title('Compare 1 fixed to 2 fixed ends')
     p.subtitle('solid line = one fixed end; broken lines = 2 fixed ends')

     # two fixed ends
     fFR2 = js.dynamic.fixedFiniteRouse(t, q, 124, l=l, Dcm=0.004, frict=9e-14, fixedends=2)
     # one fixed end
     fFR1 = js.dynamic.fixedFiniteRouse(t, q, 124, l=l, Dcm=0.004, frict=9e-14, fixedends=1)

     for i, z in enumerate(fFR1, 1):
         p.plot(z.X, z.Y, line=[1, 3, i], symbol=0, legend=fr'q={z.q:.1f} nm\S-1')
     for i, z in enumerate(fFR2, 1):
         p.plot(z.X, z.Y, line=[3, 3, i], symbol=0, legend='')

     p.legend(x=100,y=0.95,charsize=0.6)

     # p.save(js.examples.imagepath+'/fixedRouse_1vs2.jpg',size=(2,2))

    .. image:: ../../examples/images/fixedRouse_1vs2.jpg
     :align: center
     :width: 50 %
     :alt: Zimm 1 vs. 2 fixed ends


    References
    ----------
    .. [1]  Doi Edwards Theory of Polymer dynamics
            in the appendix the equation is found
    .. [2]  Nonflexible Coils in Solution: A Neutron Spin-Echo Investigation of
            Alkyl-Substituted Polynorbonenes in Tetrahydrofuran
            Michael Monkenbusch et al.Macromolecules 2006, 39, 9473-9479
            The exponential is missing a "t"
            http://dx.doi.org/10.1021/ma0618979
    .. [3]  Normal Modes of Stretched Polymer Chains
            Y. Marciano and F. Brochard-Wyart
            Macromolecules 1995, 28, 985-990 https://doi.org/10.1021/ma00108a028
    .. [4] Polymer Chain Conformation and Dynamical Confinement in a Model One-Component Nanocomposite
           C. Mark, O. Holderer, J. Allgaier, E. Hübner, W. Pyckhout-Hintzen, M. Zamponi, A. Radulescu,
           A. Feoktystov, M. Monkenbusch, N. Jalarvo, and D. Richter
           Phys. Rev. Lett. 119, 047801 (2017),  https://doi.org/10.1103/PhysRevLett.119.047801

    about internal friction

    .. [7]  Internal friction in an intrinsically disordered protein - Comparing Rouse-like models with experiments
            A. Soranno, F. Zosel, H. Hofmann
            J. Chem. Phys. 148, 123326 (2018)  http://aip.scitation.org/doi/10.1063/1.5009286

    """
    assert fixedends in [0, 1, 2]

    # assure flatt arrays
    t = np.atleast_1d(t)
    q = np.atleast_1d(q)
    # avoid l=0
    if l == 0: l = None
    NN = int(NN)
    if pmax is None: pmax = NN
    # if a list pmax of modes is given these are amplitudes for the modes
    # pmax is length of list
    if isinstance(pmax, numbers.Number):
        pmax = min(int(pmax), NN)
        modeamplist = np.ones(pmax)
    elif isinstance(pmax, list):
        modeamplist = np.abs(pmax)
    else:
        raise TypeError('pmax should be integer or list of amplitudes')

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    # calc the cases of not given parameters for Dcm,NN,l
    # kB*Temp is in SI so convert all to SI then back to ns
    if rk is not None:
        # [9]_ equ 17  for rk->0 this goes to l*NN**0.5
        Re = 2 * l ** 2 / rk ** 0.5 * np.tanh(NN / 2 * rk ** 0.5)
    else:
        # end to end distance
        Re = l * np.sqrt(NN)
    # friction or Dcm must be given
    # Dcm is independent of rk as no HI in Rouse
    if Dcm is None and frict is None:
        raise TypeError('fqtfiniteRouse needs Dcm, NN, l and frict')

    # slowest relaxation time is rouse time
    tr1 = frict * NN ** 2 * l ** 2 / (3 * pi ** 2 * kb * Temp) * 1e-9
    # different models for internal friction
    p = np.r_[1:len(modeamplist) + 1]
    modeamplist = 4 * Re ** 2 / pi ** 2 * modeamplist
    if ftype == 'rni':
        # rouse with non-local interactions
        # frict = f_s + p *f_i
        trp = tr1 / p ** 2 + NN * abs(tintern) / p
        modeamplist = modeamplist / p ** 2
    elif ftype == 'rap':
        # rouse model with anharmonic potentials
        trp = tr1 / p ** 2 + abs(tintern) * np.log(NN / p * np.pi)
        modeamplist = modeamplist / p ** 2
    elif ftype == 'specrif':
        # rouse model with specific interactions between bead separated by specm of relative strength specb
        # + rif
        trp = tr1 / p ** 2 / (1 + specb * specm ** 2) + (1 + specm ** 2 / (1 + specb * specm ** 2)) * abs(tintern)
        modeamplist = modeamplist / p ** 2
    elif ftype == 'crif':
        # compacted rouse with internal friction
        trp = tr1 / (NN ** 2 / np.pi ** 2 * rk + p ** 2) + abs(tintern)
        modeamplist = modeamplist / (NN ** 2 / np.pi ** 2 * rk + p ** 2)
    else:
        # RIF with constant internal friction time added as default
        trp = tr1 / p ** 2 + abs(tintern)
        modeamplist = modeamplist / p ** 2
        ftype = 'rif'

    # prepend 0
    t = np.r_[0, np.atleast_1d(t)]

    # do the calculation as an array of bnm=[n*m , len(t)] elements
    # sum up contributions for modes: all, diff+ mode1, only diffusion, t=0 amplitude for normalisation
    if useFortran:
        RNM = _bnmtrouse(t=t, NN=NN, l=l, modeamplist=modeamplist, trp=trp, fixedends=fixedends)
        RNMmodes = RNM[:, -len(modeamplist):]
        RNMi = RNM[:, len(t):(2*len(t))]  # incoherent
        RNMinf = RNM[:, 2 * len(t) + 1]  # coherent t = inf
        RNM = RNM[:, :len(t)]             # coherent
    else:
        raise ImportError('fixedFiniteRouse only with working Fortran.')

    result = dL()
    for qq in q:
        # diffusion for all t
        Sqt = np.exp(-qq ** 2 * Dcm * Dcmfunktion(qq) * t[1:])  # only diffusion contribution
        # amplitude at t=0
        expB0 = np.sum(np.exp(-qq ** 2 / 6. * RNM[:, 0]))  # is S(qq,t=0)/Sqt  # coherent
        expB0i = np.sum(np.exp(-qq ** 2 / 6. * RNMi[:, 0]))  # is S(qq,t=0)/Sqt incoherent
        # diffusion for infinite times in modes
        expBinf = np.sum(np.exp(-qq ** 2 / 6. * RNMinf))  # is S(qq,t=inf)/Sqt
        # contribution all modes
        expB = np.sum(np.exp(-qq ** 2 / 6. * RNM[:, 1:]), axis=0)  # coherent
        expBi = np.sum(np.exp(-qq ** 2 / 6. * RNMi[:, 1:]), axis=0)  # incoherent
        # contribution only first modes
        result.append(dA(np.c_[t[1:],
                               Sqt * expB / expB0,
                               Sqt * expBinf / expB0,
                               Sqt * expBi / expB0i].T))
        result[-1].setColumnIndex(iey=None)
        result[-1].modecontribution = (np.sum(np.exp(-qq ** 2 / 6. * RNMmodes), axis=0) / expB0).flatten()
        result[-1].q = qq
        result[-1].Re = Re
        result[-1].ll = l
        result[-1].pmax = pmax
        result[-1].Dcm = Dcm
        result[-1].effectiveDCM = Dcm * Dcmfunktion(qq)
        result[-1].Dcmrouse = kb * Temp / NN / frict * 1e9
        result[-1].Temperature = Temp
        result[-1].trouse = tr1
        result[-1].tintern = tintern
        result[-1].moderelaxationtimes = trp
        result[-1].modeamplitudes = modeamplist
        result[-1].beadfriction = frict
        result[-1].Drot = 1. / 6. / tr1
        result[-1].N = NN
        result[-1].internalfriction_g_ns = (tintern * 1e-9) * 3 * kb * Temp / (l * 1e-9) ** 2 * 1e-6
        result[-1].columnname = 'time; Sqt; Sqt_inf; Sqtinc'
        result[-1].ftype = ftype
        result[-1].rk = rk
        result[-1].fixedends = fixedends

        if specm is not None:
            result[-1].specm = specm
            result[-1].specb = specb
    if len(result) == 1:
        return result[0]
    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    return result


@formel.memoize()
def _msd_trap(t, u, rt, gamma=1):
    # defined here to memoize it
    #  msd in trap ; equ 4 right part
    res = np.zeros_like(t) + u ** 2
    res[t < rt * 30] = 6 * u ** 2 * (1 - formel.Ea(-(t[t < rt * 30] / rt) ** gamma, gamma))
    return res


def diffusionPeriodicPotential(t, q, u, rt, Dg, gamma=1):
    r"""
    Fractional diffusion of a particle in a periodic potential.

    The diffusion describes a fast dynamics inside of the potential trap with a mean square displacement
    before a jump and a fractional long time diffusion. For fractional coefficient gamma=1 normal diffusion
    is recovered.

    Parameters
    ----------
    t : array
        Time points, units ns.
    q : float
        Wavevector, units 1/nm
    u : float
        Root mean square displacement in the trap, units nm.
    rt : float
        Relaxation time  of fast dynamics in the trap; units ns ( = 1/lambda in [1]_ )
    gamma : float
        Fractional exponent gamma=1 is normal diffusion
    Dg : float
        Long time fractional diffusion coefficient; units nm**2/ns.

    Returns
    -------
    dataArray :
        [t, Iqt , Iqt_diff, Iqt_trap]

    Notes
    -----
    We use equ. 4 of [1]_ for fractional diffusion coefficient :math:`D_{\gamma}` with fraction :math:`\gamma` as

    .. math:: I(Q,t) = exp(-\frac{1}{6}Q^2 msd(t))

    .. math:: msd(t) = \langle  (x(t)-x(0))^2 \rangle  =
              6\Gamma^{-1}(\gamma+1)D_{\gamma}t^{\gamma} + 6\langle  u^2 \rangle  (1-E_{\gamma}(-(\lambda t)^{\gamma}))

    with the Mittag Leffler function :math:`E_{\gamma}(-at^{\gamma})` and Gamma function :math:`\Gamma`
    and :math:`\lambda =1/r_t`.

    The first term in *msd* describes the long time fractional diffusion
    while the second describes the additional mean-square displacement inside the trap :math:`\langle  u^2 \rangle `.

    For :math:`\gamma=1 \to E_{\gamma}(-at^{\gamma}) \to exp(-at)` simplifying the equation to normal diffusion
    with traps.

    Examples
    --------
    Example similar to protein diffusion in a mesh of high molecular weight PEG as found in [1]_.
    ::

     import jscatter as js
     import numpy as np
     t=js.loglist(0.1,50,100)
     p=js.grace()
     for i,q in enumerate(np.r_[0.1:2:0.3],1):
         iq=js.dynamic.diffusionPeriodicPotential(t,q,0.5,5,0.036)
         p.plot(iq,symbol=[1,0.3,i],legend='q=$wavevector')
         p.plot(iq.X,iq._Iqt_diff,sy=0,li=[1,0.5,i])
     p.title('Diffusion in periodic potential traps')
     p.subtitle('lines show long time diffusion contribution')
     p.yaxis(max=1,min=1e-2,scale='log',label='I(Q,t)/I(Q,0)')
     p.xaxis(min=0,max=50,label='t / ns')
     p.legend(x=110,y=0.8)
     # p.save(js.examples.imagepath+'/fractalDiff.jpg')

    .. image:: ../../examples/images/fractalDiff.jpg
     :align: center
     :height: 300px
     :alt: fractalDiff


    References
    ----------
    .. [1] Gupta, S.; Biehl, R.; Sill, C.; Allgaier, J.; Sharp, M.; Ohl, M.; Richter, D.
           Macromolecules 49 (5), 1941 (2016). https://doi.org/10.1021/acs.macromol.5b02281

    """
    # q=np.atleast_1d(q)
    # mean square displacement for diffusion in periodic potential no trap; equ 4 left part
    msd = lambda t, Dg, u, rt, gamma=1: 6 * Dg * t ** gamma / scipy.special.gamma(gamma + 1)

    # Trap contribution in _msd_trap. This is memoized as it is independent of the wavevector
    # but for fitting with several Q it is needed multiple times. Cache size is 128 entries.

    # the above but extrapolation to t=0 without trap as contribution of long time diffusion at short times
    msd_0 = lambda t, Dg, u, rt, gamma=1: 6 * Dg * t ** gamma / scipy.special.gamma(gamma + 1) + 6 * u ** 2
    # intermediate scattering function of diffusion in periodic...
    sqt = lambda q, t, Dg, u, rt, gamma=1: np.exp(-q ** 2 / 6 * (msd(t, Dg, u, rt, gamma)))
    sqttrap = lambda q, t, Dg, u, rt, gamma=1: np.exp(-q ** 2 / 6 * (_msd_trap(t, u, rt, gamma)))
    sqt_0 = lambda q, t, Dg, u, rt, gamma=1: np.exp(-q ** 2 / 6 * msd_0(t, Dg, u, rt, gamma))

    result = dA(np.c_[t, sqt(q, t, Dg, u, rt, gamma) * sqttrap(q, t, Dg, u, rt, gamma),
                      sqt_0(q, t, Dg, u, rt, gamma),
                      sqttrap(q, t, Dg,u, rt, gamma)].T)
    result.wavevector = q
    result.fractionalDiffusionCoefficient = Dg
    result.displacement_u = u
    result.relaxationtime = rt
    result.fractionalCoefficient_gamma = gamma
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt;Iqt_diff;Iqt_trap'
    return result


def zilmanGranekBicontinious(t, q, xi, kappa, eta, mt=1, amp=1, eps=1, nGauss=60):
    r"""
    Dynamics of bicontinuous micro emulsion phases. Zilman-Granek model as equ B10 in [1]_. Coherent scattering.

    On very local scales (however larger than the molecular size) Zilman and Granek represent the amphiphile layer
    in the bicontinuous network as consisting of an ensemble of independent patches at random orientation of size
    equal to the correlation length xi.
    Uses Gauss integration and multiprocessing.

    Parameters
    ----------
    t : array
        Time values in ns
    q : float
        Scattering vector in 1/A
    xi : float
        Correlation length related to the size of patches which are locally planar
        and determine the width of the peak in static data. unit A
        A result of the teubnerStrey model to e.g. SANS data. Determines kmin=eps*pi/xi .
    kappa : float
        Apparent single membrane bending modulus, unit kT
    eta : float
        Solvent viscosity, unit kT*A^3/ns=100/(1.38065*T)*eta[unit Pa*s]
        Water about 0.001 Pa*s = 0.000243 kT*A^3/ns
    amp : float, default = 1
        Amplitude scaling factor
    eps : float, default=1
        Scaling factor in range [1..1.3] for kmin=eps*pi/xi and rmax=xi/eps. See [1]_.
    mt : float, default 0.1
        Membrane thickness in unit A as approximated from molecular size of material. Determines kmax=pi/mt.
        About 12 Angstrom for tenside C10E4.
    nGauss : int, default 60
        Number of points in Gauss integration

    Returns
    -------
        dataList

    Notes
    -----
    See equ B10 in [1]_ :

    .. math:: S(q,t) = \frac{2\pi\xi^2}{a^4} \int_0^1 d\mu \int_0^{r_{max}} dr rJ_0(qr\sqrt{1-\mu^2})
                       e^{-kT/(2\pi\kappa)q^2\mu^2 \int_{k_{min}}^{k_{max}} dk[1-J_0(kr)e^{w(k)t}]/k^3}

    with :math:`\mu = cos(\sphericalangle(q,surface normal))` , :math:`J_0` as Bessel function of order 0

    - For technical reasons, in order to avoid numerical difficulties,
      the real space upper (rmax integration) cutoff was realized by multiplying the
      integrand with a Gaussian having a width of eps*xi and integrating over [0,3*eps*xi].

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np
     t=js.loglist(0.1,30,20)
     p=js.grace()
     iqt=js.dynamic.zilmanGranekBicontinious(t=t,q=np.r_[0.03:0.2:0.04],xi=110,kappa=1.,eta=0.24e-3,nGauss=60)
     p.plot(iqt)

     # to use the multiprocessing in a fit of data use memoize
     data=iqt                          # this represent your measured data
     tt=list(set(data.X.flatten))      # a list of all time values
     tt.sort()

     # use correct values from data for q     -> interpolation is exact for q and tt
     zGBmem=js.formel.memoize(q=data.q,t=tt)(js.dynamic.zilmanGranekBicontinious)
     def mfitfunc(t, q, xi, kappa, eta, amp):
        # this will calculate in each fit step for for Q (but calc all) and then take from memoized values
        res= zGBmem(t=t, q=q, xi=xi, kappa=kappa, eta=eta, amp=amp)
        return res.interpolate(q=q,X=t)[0]
     # use mfitfunc for fitting with multiprocessing


    References
    ----------
    .. [1] Dynamics of bicontinuous microemulsion phases with and without amphiphilic block-copolymers
           M. Mihailescu, M. Monkenbusch et al
           J. Chem. Phys. 115, 9563 (2001); http://dx.doi.org/10.1063/1.1413509

    """

    tt = np.r_[0., t]
    qq = np.r_[q]
    result = dL()
    nres = formel.doForList(_zgbicintegral, looplist=qq, loopover='q', t=tt, xi=xi, kappa=kappa, eta=eta, mt=mt,
                              eps=eps, nGauss=nGauss)
    for qi, res in zip(qq, nres):
        S0 = res[0]
        result.append(dA(np.c_[t, res[1:]].T))
        result[-1].setColumnIndex(iey=None)
        result[-1].Y *= amp / S0
        result[-1].q = qi
        result[-1].xi = xi
        result[-1].kappa = kappa
        result[-1].eta = eta
        result[-1].eps = eps
        result[-1].mt = mt
        result[-1].amp = amp
        result[-1].setColumnIndex(iey=None)
        result[-1].columnname = 't;Iqt'

    return result


def _zgbicintegral(t, q, xi, kappa, eta, eps, mt, nGauss):
    """integration of gl. B10 in Mihailescu, JCP 2001"""
    quad = formel.parQuadratureFixedGauss
    aquad = formel.parQuadratureAdaptiveGauss

    def _zgintegrand_k(k, r, t, kappa, eta):
        """kmin-kmax integrand of gl. B10 in Mihailescu, JCP 2001"""
        tmp = -kappa / 4. / eta * k ** 3 * t
        res = (1. - special.j0(k * r) * np.exp(tmp)) / k ** 3
        return res

    def _zgintegral_k(r, t, xi, kappa, eta):
        """kmin-kmax integration of gl. B10 in Mihailescu, JCP 2001
        integration is done in 2 intervals to weight the lower stronger.
        """
        kmax = pi / mt
        # use higher accuracy at lower k
        res0 = aquad(_zgintegrand_k, eps * pi / xi, kmax / 8., 'k', r=r, t=t[None, :], kappa=kappa, eta=eta,
                     rtol=0.1 / nGauss, maxiter=250)
        res1 = aquad(_zgintegrand_k, kmax / 8., kmax, 'k', r=r, t=t[None, :], kappa=kappa, eta=eta, rtol=1. / nGauss,
                     maxiter=250)
        return res0 + res1

    def _zgintegrand_mu_r(r, mu, q, t, xi, kappa, eta):
        """Mu-r integration of gl. B10 in Mihailescu, JCP 2001
        aus numerischen Gruenden Multiplikation mit Gaussfunktion mit Breite xi"""
        tmp = (-1 / (2 * pi * kappa) * q * q * mu * mu * _zgintegral_k(r, t, xi, kappa, eta)[0] - r * r / (
                2 * (eps * xi) ** 2))
        tmp[tmp < -500] = -500  # otherwise overflow error in np.exp
        y = r * special.j0(q * r * np.sqrt(1 - mu ** 2)) * np.exp(tmp - r ** 2 / (2 * (eps * xi) ** 2))
        return y

    def _gaussBorder(mu, q, t, xi, kappa, eta):
        # For technical reasons, in order to avoid numerical difficulties, the real
        # space upper cutoff was realized by multiplying the integrand with a
        # Gaussian having a width of eps*xi.
        y = quad(_zgintegrand_mu_r, 0, eps * 3 * xi, 'r', mu=mu, q=q, t=t, xi=xi, kappa=kappa, eta=eta, n=nGauss)
        return y

    y = quad(_gaussBorder, 0., 1., 'mu', q=q, t=t, xi=xi, kappa=kappa, eta=eta, n=nGauss)
    return y


def zilmanGranekLamellar(t, q, df, kappa, eta, mu=0.001, eps=1, amp=1, mt=0.1, nGauss=40):
    r"""
    Dynamics of lamellar microemulsion phases.  Zilman-Granek model as Equ 16 in [1]_. Coherent scattering.

    Oriented lamellar phases at the length scale of the inter membrane distance and beyond are performed
    using small-angle neutrons scattering and neutron spin-echo spectroscopy.

    Parameters
    ----------
    t : array
        Time in ns
    q : float
        Scattering vector
    df : float
        - film-film distance. unit A
        - This represents half the periodicity of the structure,
          generally denoted by d=0.5df which determines the peak position and determines kmin=eps*pi/df
    kappa : float
        Apparent single membrane bending modulus, unit kT
    mu : float, default 0.001
        Angle between q and surface normal in unit rad.
        For lamellar oriented system this is close to zero in NSE.
    eta : float
        Solvent viscosity, unit kT*A^3/ns = 100/(1.38065*T)*eta[unit Pa*s]
        Water about 0.001 Pa*s = 0.000243 kT*A^3/ns
    eps : float, default=1
        Scaling factor in range [1..1.3] for kmin=eps*pi/xi and rmax=xi/eps
    amp : float, default 1
        Amplitude scaling factor
    mt : float, default 0.1
        Membrane thickness in unit A as approximated from molecular size of material. Determines kmax=pi/mt
        About 12 Angstrom for  tenside C10E4.
    nGauss : int, default 40
        Number of points in Gauss integration

    Returns
    -------
        dataList

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np
     t=js.loglist(0.1,30,20)
     ql=np.r_[0.08:0.261:0.03]
     p=js.grace()
     iqt=js.dynamic.zilmanGranekLamellar(t=t,q=ql,df=100,kappa=1,eta=2*0.24e-3)
     p.plot(iqt)
     p.yaxis(label=r'I(Q,t)',min=1e-6,max=1)
     p.xaxis(label=r'Q / nm\S-1')
     # p.save(js.examples.imagepath+'/zilmanGranekLamellar.jpg', size=(2,2))

    .. image:: ../../examples/images/zilmanGranekLamellar.jpg
     :align: center
     :width: 50 %
     :alt: dynamic_t2f_examples.

    Notes
    -----
    See equ 16 in [1]_ :

    .. math:: S(q,t) \propto \int_0^{r_{max}} dr r J_0(q_{\perp}r)
                      exp \Big( -\frac{kT}{2\pi\kappa} q^2\mu^2
                      \int_{k_{min}}^{k_{max}} \frac{dk}{k^3} [1-J_0(kr) e^{w^\infty(k)t}] \Big)

    with :math:`w^{\infty(k) = k^3\kappa/4\overline{\eta}}`, :math:`\mu = cos(\sphericalangle(q,surface normal))` ,
     :math:`J_0` as Bessel function of order 0. For details see [1]_.



    The integrations are done by nGauss point Gauss quadrature, except for the kmax-kmin integration which is done by
    adaptive Gauss integration with rtol=0.1/nGauss k< kmax/8 and rtol=1./nGauss k> kmax/8.

    References
    ----------
    .. [1] Neutron scattering study on the structure and dynamics of oriented lamellar phase microemulsions
           M. Mihailescu, M. Monkenbusch, J. Allgaier, H. Frielinghaus, D. Richter, B. Jakobs, and T. Sottmann
           Phys. Rev. E 66, 041504 (2002)

    """

    tt = np.r_[0., t]
    qq = np.atleast_1d(q)
    result = dL()
    nres = formel.doForList(_zglamintegral, looplist=qq, loopover='q', t=tt, kappa=kappa, eta=eta, df=df, mu=mu,
                              mt=mt, eps=eps, nGauss=nGauss)
    for qi, res in zip(qq, nres):
        S0 = res[0]
        result.append(dA(np.c_[t, res[1:]].T))
        result[-1].setColumnIndex(iey=None)
        result[-1].Y *= amp / S0
        result[-1].q = qi
        result[-1].df = df
        result[-1].kappa = kappa
        result[-1].eta = eta
        result[-1].eps = eps
        result[-1].mt = mt
        result[-1].amp = amp
        result[-1].setColumnIndex(iey=None)
        result[-1].columnname = 't;Iqt'

    return result


def _zglamintegral(t, q, df, kappa, eta, eps, mu, mt, nGauss):
    """integration of gl. 16"""
    # quad=scipy.integrate.quad
    quad = formel.parQuadratureFixedGauss
    aquad = formel.parQuadratureAdaptiveGauss

    def _zgintegrand_k(k, r, t, kappa, eta):
        """kmin-kmax integrand o"""
        tmp = -kappa / 4. / eta * k ** 3 * t
        res = (1. - special.j0(k * r) * np.exp(tmp)) / k ** 3
        return res

    def _zgintegral_k(r, t, df, kappa, eta):
        """
        kmin-kmax integration of gl. B10 in Mihailescu, JCP 2001
        """
        kmax = pi / mt
        # use higher accuracy at lower k
        res0 = aquad(_zgintegrand_k, eps * pi / df, kmax / 8., 'k', r=r, t=t[None, :], kappa=kappa, eta=eta,
                     rtol=0.1 / nGauss, maxiter=250)
        res1 = aquad(_zgintegrand_k, kmax / 8., kmax, 'k', r=r, t=t[None, :], kappa=kappa, eta=eta, rtol=1. / nGauss,
                     maxiter=250)
        return res0 + res1

    def _zgintegrand_r(r, mu, q, t, df, kappa, eta):
        """Mu-r integration """
        smu = np.sin(mu)
        tmp = (-1 / (2 * pi * kappa) * q * q * (1 - smu ** 2) * _zgintegral_k(r, t, df, kappa, eta)[0])
        tmp[tmp < -500] = -500  # otherwise overflow error in np.exp
        y = r * special.j0(q * r * smu) * np.exp(tmp)
        return y

    y = quad(_zgintegrand_r, 0, df / eps, 'r', mu=mu, q=q, t=t, df=df, kappa=kappa, eta=eta, n=nGauss)
    return y


def integralZimm(t, q, Temp=293, viscosity=1.0e-3, amp=1, rtol=0.02, tol=0.02, limit=50):
    r"""
    Conformational dynamics of an ideal chain with hydrodynamic interaction, coherent scattering.

    Integral version Zimm dynamics.

    Parameters
    ----------
    t : array
        Time points in ns
    q : float
        Wavevector in 1/nm
    Temp : float
        Temperature in K
    viscosity : float
        Viscosity in cP=mPa*s
    amp : float
        Amplitude
    rtol,tol : float
        Relative and absolute tolerance in scipy.integrate.quad
    limit : int
        Limit in scipy.integrate.quad.

    Returns
    -------
        dataArray

    Notes
    -----
    The Zimm model describes the conformational dynamics of an ideal chain with hydrodynamic
    interaction between beads. We use equ 85 and 86 from [1]_ as

    .. math:: S(Q,t) = \frac{12}{Q^2l^2} \int_0^{\infty} e^{-u-(\Omega_Z t)^{2/3} g(u(\Omega_Z t)^{2/3})} du

    with

    .. math:: g(y) = \frac{2}{\pi} \int_0^{\infty} x^{-2}cos(xy)(1-e^{-2^{-0.5}x^{2/3}}) dx

    .. math:: \Omega_z = \frac{kTQ^3}{6\pi\eta_s}

    See [1]_ for details.

    Examples
    --------
    ::

     import jscatter as js
     import numpy as np
     t=np.r_[0:10:0.2]
     p=js.grace()
     for q in np.r_[0.26,0.40,0.53,0.79,1.06]:
        iqt=js.dynamic.integralZimm(t=t,q=q,viscosity=0.2e-3)
        p.plot((iqt.X*iqt.q**3)**(2/3.),iqt.Y)
     p.xaxis(label=r'(Q\S3\Nt)\S2/3')
     p.yaxis(label=r'I(Q,t)/I(Q,0)')
     p.title('integral Zimm rescaled by characteristic time')
     # p.save(js.examples.imagepath+'/integralZimm.jpg')

    .. image:: ../../examples/images/integralZimm.jpg
     :width: 50 %
     :align: center
     :alt: integralZimm

    References
    ----------
    .. [1] Neutron Spin Echo Investigations on the Segmental Dynamics of Polymers in Melts, Networks and Solutions
           in Neutron Spin Echo Spectroscopy Viscoelasticity Rheology
           Volume 134 of the series Advances in Polymer Science pp 1-129
           DOI 10.1007/3-540-68449-2_1

    """
    quad = scipy.integrate.quad
    tt = np.r_[t] * 1e-9
    tt[t == 0] = 1e-20  # avoid zero

    # Zimm diffusion coefficient
    OmegaZ = (q * 1e9) ** 3 * kb * Temp / (6 * pi * viscosity)

    _g_integrand = lambda x, y: math.cos(y * x) / x / x * (1 - math.exp(-x ** (3. / 2.) / math.sqrt(2)))
    _g = lambda y: 2. / pi * quad(_g_integrand, 0, np.inf, args=(y,), epsrel=rtol, epsabs=tol, limit=limit)[0]

    _z_integrand = lambda u, t: math.exp(-u - (OmegaZ * t) ** (2. / 3.) * _g(u * (OmegaZ * t) ** (2. / 3.)))

    y1 = [quad(_z_integrand, 0, np.inf, args=(ttt,), epsrel=rtol, epsabs=tol, limit=limit)[0] for ttt in tt]

    result = dA(np.c_[t, amp * np.r_[y1]].T)
    result.setColumnIndex(iey=None)
    result.columnname = 't;Iqt'
    result.q = q
    result.OmegaZimm = OmegaZ
    result.Temperature = Temp
    result.viscosity = viscosity
    result.amplitude = amp
    return result


def transRotDiffusion(t, q, cloud, Dr, Dt=0, lmax='auto'):
    r"""
    Translational + rotational diffusion of an object (dummy atoms); dynamic structure factor in time domain.

    A cloud of dummy atoms can be used for coarse graining of a non-spherical object e.g. for amino acids in proteins.
    On the other hand its just a way to integrate over an object e.g. a sphere or ellipsoid (see example).
    We use [2]_ for an objekt of arbitrary shape modified for incoherent scattering.

    Parameters
    ----------
    t : array
        Times in ns.
    q : float
        Wavevector in units 1/nm
    cloud : array Nx3, Nx4 or Nx5 or float
        - A cloud of N dummy atoms with positions cloud[:3] in units nm that describe an object .
        - If given, cloud[3] is the incoherent scattering length :math:`b_{inc}` otherwise its equal 1.
        - If given, cloud[4] is the coherent scattering length :math:`b_{coh}` otherwise its equal 1.
        - If cloud is single float the value is used as radius of a sphere with 10x10x10 grid points.
    Dr : float
        Rotational diffusion constant (scalar) in units 1/ns.
    Dt : float, default=0
        Translational diffusion constant (scalar) in units nm²/ns.
    lmax : int
        Maximum order of spherical bessel function.
        'auto' -> lmax > 2π r.max()*q/6.

    Returns
    -------
        dataArray :
            Columns [t; Iqtinc; Iqtcoh; Iqttrans]
             - .radiusOfGyration
             - .Iq_coh  coherent scattering (formfactor)
             - .Iq_inc  incoherent scattering
             - .wavevector
             - .rotDiffusion
             - .transDiffusion
             - .lmax

    Notes
    -----
    We calculate the field autocorrelation function given in equ 24 in [2]_ for an arbitrary rigid object
    without additional internal dynamic as

    .. math:: I(q,t) = e^{-q^2D_tt} I_{rot}(q,t) = e^{-q^2D_tt} \sum_l S_{l,i/c}(q)e^{-l(l+1)D_rt}

    where :math:`I_{rot}(q,t)` is the rotational diffusion contribution and

    .. math:: S_{l,c}(q) &= 4\pi \sum_m |\sum_i b_{i,coh} j_l(qr_i) Y_{l,m}(\Omega_i)|^2  & coherent scattering \\

              S_{l,i}(q) &= \sum_m \sum_i (2l+1) b_{i,inc}^2 |j_l(qr_i)|^2   & incoherent scattering\\

    and coh/inc scattering length :math:`b_{i,coh/inc}`, position vector :math:`r_i` and orientation of atoms
    :math:`\Omega_i`, spherical Bessel function :math:`j_l(x)`, spherical harmonics :math:`Y_{l,m}(\Omega_i)`.


    - The incoherent intermediate scattering function is res.Y/res.Iq_inc or res._Iqtinc/res.Iq_inc
    - The coherent   intermediate scattering function is res._Iqtcoh/res.Iq_coh
    - For real scattering data as backscattering or spinecho coherent and incoherent have to be mixed according
      to the polarisation conditions of the experiment accounting also for spin flip probability of coherent and
      incoherent scattering. For the simple case of non-polarised  measurement we get

    .. math:: I(q,t)/I(q,0) = \frac{I_{coh}(q,t)+I_{inc}(q,t)}{I_{coh}(q,0)+I_{inc}(q,0)}



    Examples
    --------
    A bit artificial look at only rotational diffusion of a superball build from dummy atoms.
    (rotational diffusion should only show if also translational diffusion is seen)
    Change p to change from spherical shape (p=1) to cube (p>10) or star like (p<0.5)
    (use grid.show() to take a look at the shape)
    The coherent contribution is suppressed for low q if the particle is spherical .
    ::

     import jscatter as js
     import numpy as np
     R=2;NN=10
     ql=np.r_[0.4:2.:0.3,2.1:15:2]
     t=js.loglist(0.001,50,50)
     # get superball
     p2=1
     grid=js.ff.superball(ql,R,p=p2,nGrid=NN,returngrid=True)
     Drot=js.formel.Drot(R)
     Dtrans=js.formel.Dtrans(R)
     p=js.grace(1.5,1)
     p.new_graph(xmin=0.23,xmax=0.43,ymin=0.25,ymax=0.55)
     iqt=js.dL([js.dynamic.transRotDiffusion(t,q,grid.XYZ,Drot,lmax=30) for q in ql])

     for i,iiqt in enumerate(iqt,1):
         p[0].plot(iiqt.X,iiqt.Y/iiqt.Iq_inc,li=[1,3,i],sy=0,le=f'q={iiqt.wavevector:.1f} nm\S-1')
         p[0].plot(iiqt.X,iiqt._Iqtcoh/iiqt.Iq_coh,li=[3,3,i],sy=0,le=f'q={iiqt.wavevector:.1f} nm\S-1')

     p[1].plot(iqt.wavevector,iqt.Iq_coh.array/grid.numberOfAtoms(),li=1)
     p[1].plot(iqt.wavevector,iqt.Iq_inc.array/grid.numberOfAtoms(),li=1)
     p[0].xaxis(scale='l',label='t / ns',max=200,min=0.001)
     p[0].yaxis(scale='n',label='I(q,t)/I(q,0)')
     p[1].xaxis(scale='n',label='q / nm\S-1')
     p[1].yaxis(scale='l',label='I(q,t=0)')

     p[0].legend(x=60,y=1.1,charsize=0.7)
     p[0].title(f'rotational diffusion of superball with p={p2:.2f}')
     p[0].subtitle(f'coh relevant only at high q for sphere')
     p[1].subtitle('coh + inc scattering')
     p[0].text(x=0.0015,y=0.8,string=r'lines inc\ndashed coh',charsize=1.5)
     #p.save(js.examples.imagepath+'/rotDiffusion.jpg')

     # Second example
     # non-polarized experiment
     p=js.grace(1.5,1)
     grid=js.ff.superball(ql,R,p=1.,nGrid=10,returngrid=True)
     iqt=js.dL([js.dynamic.transRotDiffusion(t,q,grid.XYZ,Drot,Dtrans,lmax=30) for q in ql])
     for i,iiqt in enumerate(iqt,1):
         p.plot(iiqt.X,(iiqt._Iqtinc+iiqt._Iqtcoh)/(iiqt.Iq_inc+iiqt.Iq_coh),li=[1,3,i],sy=0,le=f'q={iiqt.wavevector:.1f} nm\S-1')
         p.plot(iiqt.X,iiqt._Iqtcoh/iiqt.Iq_coh,li=[3,3,i],sy=0,le=f'q={iiqt.wavevector:.1f} nm\S-1')

     p.xaxis(scale='l',label='t / ns',max=200,min=0.001)
     p.yaxis(scale='n',label='I(q,t)/I(q,0)')
     p[0].legend(x=60,y=1.1,charsize=0.7)
     p[0].title(f'translational/rotational diffusion of superball with p={p2:.2f}')
     p[0].text(x=0.0015,y=0.5,string=r'lines coh+inc\ndashed only coh',charsize=1.5)
     #p.save(js.examples.imagepath+'/transrotDiffusion.jpg')

    .. image:: ../../examples/images/rotDiffusion.jpg
     :width: 50 %
     :align: center
     :alt: rotDiffusion

    .. image:: ../../examples/images/transrotDiffusion.jpg
     :width: 50 %
     :align: center
     :alt: transrotDiffusion



    References
    ----------
    .. [1] Incoherent scattering law for neutron quasi-elastic scattering in liquid crystals.
           Dianoux, A., Volino, F. & Hervet, H. Mol. Phys. 30, 37–41 (1975).
    .. [2] Effect of rotational diffusion on quasielastic light scattering from fractal colloid aggregates.
           Lindsay, H., Klein, R., Weitz, D., Lin, M. & Meakin, P. Phys. Rev. A 38, 2614–2626 (1988).

    """
    #: Lorentzian
    expo = lambda t, ll1D: np.exp(-ll1D * t)
    if isinstance(cloud, numbers.Number):
        R = cloud
        NN = 10
        grid = np.mgrid[-R:R:1j * NN, -R:R:1j * NN, -R:R:1j * NN].reshape(3, -1).T
        inside = lambda xyz, R: la.norm(grid, axis=1) < R
        cloud = grid[inside(grid, R)]
    if cloud.shape[1] == 5:
        # last columns are incoherent and coherent scattering length
        blinc = cloud[:, 3]
        blcoh = cloud[:, 4]
        cloud = cloud[:, :3]
    elif cloud.shape[1] == 4:
        # last column is scattering length
        blinc = cloud[:, 3]
        blcoh = np.ones(cloud.shape[0])
        cloud = cloud[:, :3]
    else:
        blinc = np.ones(cloud.shape[0])
        blcoh = blinc
    t = np.array(t, float)
    bi2 = blinc ** 2
    r, p, th = formel.xyz2rphitheta(cloud).T
    pp = p[:, None]
    tt = th[:, None]
    qr = q * r
    if not isinstance(lmax, numbers.Integral):
        # lmax = pi * r.max() * q  / 6. # a la Cryson
        lmax = min(max(2 * int(pi * qr.max() / 6.), 6), 100)

    # We calc here the field autocorrelation function as in equ 24
    # incoherent with i=j ->  Sum_m(Ylm) leads to (2l+1)/4pi
    bjlylminc = [(bi2 * spjn(l, qr) ** 2 * (2 * l + 1)).sum() for l in np.r_[:lmax + 1]]
    # add time dependence
    Iqtinc = np.c_[[bjlylminc[l].real * expo(t, l * (l + 1) * Dr) for l in np.r_[:lmax + 1]]].sum(axis=0)
    Iq_inc = np.sum(bjlylminc).real

    # coh is sum over i then (abs)squared and sum over m    see Lindsay equ 19 or 20
    bjlylmcoh = [4 * np.pi * np.sum(np.abs((blcoh * spjn(l, qr) * Ylm(l, np.r_[-l:l + 1], pp, tt).T).sum(axis=1)) ** 2)
                 for l in np.r_[:lmax + 1]]
    Iqtcoh = np.c_[[bjlylmcoh[l].real * expo(t, l * (l + 1) * Dr) for l in np.r_[:lmax + 1]]].sum(axis=0)
    Iq_coh = np.sum(bjlylmcoh).real

    Iq_trans = np.exp(-q ** 2 * Dt * t)
    result = dA(np.c_[t, Iq_trans * Iqtinc, Iq_trans * Iqtcoh].T)
    result.modelname = inspect.currentframe().f_code.co_name
    result.setColumnIndex(iey=None)
    result.columnname = 't; Iqtinc; Iqtcoh; Iqttrans'
    result.radiusOfGyration = np.sum(r ** 2) ** 0.5
    result.Iq_coh = Iq_coh
    result.Iq_inc = Iq_inc
    result.wavevector = q
    result.rotDiffusion = Dr
    result.transDiffusion = Dt
    result.lmax = lmax
    return result


def solveOptimizedRouseZimm(A, reducedfriction=0.25):
    r"""
    Solve optimized Rouse-Zimm (ORZ) approximation to the diffusion equation of a polymer in solution.

    From [1]_ :
    A generalization of some work by Bixon on the theoretical foundations of the Rouse-Zimm model in
    polymer solution dynamics. In particular, a procedure is described for constructing the "best possible"
    Rouse-Zimm model for an arbitrary polymer, starting from the equilibrium distribution of polymer conformations
    and using either Kirkwood's generalized diffusion dynamics or stochastic dynamics.
    The method is based on an application of linear response theory to the calculation
    of certain time correlation functions for polymer dynamics.

    Parameters
    ----------
    A : [N,N] array
        Structural matrix.

    reducedfriction : float
        Reduced friction :math:`\zeta_r= \zeta/6\pi\eta_s l` in matrix of the preaveraged hydrodynamic interactions
        :math:`H_{ij}=\delta_{ij} + \zeta_r \langle l/R_{ij}\rangle (1-\delta_{ij})`.
        The default 0.25 is in accordance with experimental data for theta solvents [2]_.

         - =0 : free draining limit, no HI, Rouse dynamics. H is identity matrix that :math:`HA=A`.
         - >0 : with HI typically <0.5. For h>0.5 we may get negative eigenvalues.

        [3]_ : The value of :math:`\zeta_r = 0.25` ensures that the matrix [H] is
        positive definite and does not show any instabilities related to
        the appearance of negative unphysical eigenvalues. Such
        eigenvalues occur when the parameter :math:`\zeta_r` exceeds a critical
        value :math:`\zeta_r^*` which corresponds to the non-overlapping
        condition :math:`r/b=\frac{bead radius}{bond length} ≤ 0.5` for the monomers.

        [6]_ : The abrupt change in :math:`\phi_{max}` at r/b~O.43 indicates that a large perturbation takes
        place in the modes. Therefore, this value has to be considered an upper limit to the strength of
        the hydrodynamic interaction. More restrictive conditions, physically reasonable though arbitrary,
        fall in the range of r/b lower than 0.43 but do not apparently give rise to anomalies in the modes.
        In the application to intrinsic viscosity in ideal solvents, presented in Sec. III,
        we shall therefore take r/b in the range 0-0.40.

    Returns
    -------
        evalHA, evecHA, A, loverR, Rg2_red, Rij2_red : array's
            evalHA : 1D array
                Eigenvalues :math:`\lambda_a` of :math:`HA`.
            evecHA : 2D array
                Eigenvectors :math:`Q_{ia}` of :math:`HA`.
            mu : 1D array
                Diagonal elements :math:`\mu_a = (Q^TAQ)_{aa}`
            loverR : 2D array
                Adimensional mean inverse distance matrix equ. 25 in [4]_ :
                :math:`\langle l/R_{ij}\rangle =l(6/\pi)^{1/2}(\langle R^2_{ij}\rangle )^{-1/2}` .
            Rg2_red : float
                Reduced radius of gyration (equ 3.2 in [2]_) :math:`R_g^2/l^2 = \sum_{ij} \langle R^2_{ij}\rangle  / (2N^2)`
            Rij2_red : 2D array
                Reduced second moments for the distance between any two chain atoms equ. 3.1 in [2]_ :

                 .. math::  \langle R^2_{ij}\rangle /l^2= \sum_{k=1}^{N} (Q_{ik} - Q_{jk})^2/\lambda_k
            A : 2D array
                Dimesionless structural matrix :math:`A = M[1:,:].T * U * M[1:,:]`
                (or force constant matrix as :math:`3kT/l^2 A` or connectivity matrix)


    Notes
    -----
    In the **ORZ approximation** to the Kirkwood configurational diffusion equation,
    the bead coordinates of a chain of N beads (or monomers) of friction coefficient :math:`\zeta` jointed by equal
    links of mean square length :math:`l^2` and forceconstant :math:`\kappa` obey a Langevin equation of the form

    .. math:: \zeta \frac{\partial}{\partial t} R_i(t) + \kappa \sum_{j} (HA)_{ij} R_j(t) = v_i(t)  \\
             \frac{\partial}{\partial t} R_i(t) + \sigma \sum_{j} (HA)_{ij} R_j(t) = v_i(t)

    were :math:`v_i` is the random velocity, :math:`\sigma=\kappa/\zeta=3kT/l^2\zeta` and  bead coordinates :math:`R_i`.
    :math:`\zeta=6\pi\eta_0l` is the bead friction with the surrounding/solvent.

    The structural matrix :math:`A` depends on the actual shape of the polymer (e.g. linear, star or ring).

    The matrix H is the preaveraged hydrodynamic matrix with elements

    .. math:: H_{ij} = \delta_{ij} + \zeta_r\langle l/R_{ij}\rangle (1-\delta_{ij})

    with :math:`R_{ij}` as distance between beads i and j, reduced friction per chain atom
    :math:`\zeta_r=\zeta/6\pi\eta_0l` and :math:`\eta_0` as solvent viscosity.

    The structural matrix A of a **linear** polymer  is

    .. math:: A = M^T \left( \begin{array}{cc} 0 & 0 \\ 0 & U \end{array} \right) M = M[1:,:]^T U M[1:,:]

    with the transfer matrix M in dimsionless form (the first row is not needed)

    .. math:: M = \left ( \begin{array}{cccc} 1/N & 1/N & ... & 1/N \\
                          -1 & 1 & 0 & 0..0 \\
                           0 & -1 & 1 & 0..0 \\
                            ... \end{array} \right )

    In the first dimension is the center of mass that is basically not needed.
      Elements of :math:`M_{ij}` are −1 if the bond vector :math:`l_i` starts at monomer `i` and
      +1 if bond vector :math:`l_i` points to bead `i`, else 0.

    U can be retrieved from (depends on the model: freely jointed chain (FJC), free rotating chain (FRC), RIS,...)

    .. math:: U^{-1}_{ij} = \langle l_i\cdot l_j\rangle /l^2

    - Freely jointed linear chain and bead spring model:

      .. math::   \langle l_i\cdot l_j\rangle /l^2 = \delta_{ij} \Rightarrow  \langle R^2_{ij}\rangle  = l^2 |i-j|

    - Free rotating linear chain with bond angles :math:`g=-cos(\theta)` (:math:`\theta=\pi` is rigid rod)

      .. math:: \langle l_i\cdot l_j\rangle/l^2 = g^{|i-j|} \Rightarrow
                     \langle R^2_{ij}\rangle  = l^2 |i-j| [\frac{1+g}{1-g} -\frac{2g}{|i-j|}\frac{1-g^{|i-j|}}{(1-g)^2}]

      Persistence length is :math:`nl=l/(1-g)` and :math:`\langle R^2_{ij}\rangle` from [5]_.
      For :math:`g=0` we yield the FJC.


    The **solution of a ORZ model** can be described by normal modes and corresponding eigenvalues
    :math:`Q_a, \lambda_a`  of the matrix :math:`HA` yielding normal coordinates :math:`\Xi_k`,
    mode relaxation times :math:`\tau_a`
    and mean square displacements :math:`\langle \xi^2_a \rangle` and

    .. math:: \xi_k(t) = Q_{ki} R_i(t)

    .. math:: \tau_a=(\sigma \lambda_a)^{-1}

    .. math:: \langle \xi^2_a\rangle  = l^2 \mu_a^{-1}

    where :math:`\mu_a= (Q^TAQ)_{aa}`. For free draining (:math:`\zeta_r=0`) :math:`\mu_a=\lambda_a`

    According to the usual Zimm notation, the mode :math:`a=0` describes the translational mode of
    the center of resistance, always characterized by a constant eigenvector :math:`Q_{k,0} = N^{-1/2}` and
    a zero relaxation rate :math:`\lambda_0 = 0`

    The dynamic correlation between beads i and j is [1]_ :

    .. math:: \langle |R_i(t) -R_j(0)|^2\rangle  &= l^2 \sum_{a=1}^{N-1} \mu_a^{-1} [|Q_{ia}|^2+|Q_{ja}|^2 -
                                              (Q_{ia}Q_{ka}^* + Q_{ia}Q_{ka}^*) exp(-\sigma\lambda_at)] \\
                       &= l^2 \sum_{a=1}^N \mu_a^{-1} [|Q_{ia}|^2+|Q_{ja}|^2 - 2Q_{ia}Q_{ka} exp(-\sigma\lambda_at)] \\
                       &= l^2 d_{ij}^2

    where the first refers to complex eigenvectors [2]_ and the later to real eigenvectors [4]_.

    The dynamic structure factor (measured by DLS or NSE) is [4]_
    (here extended by bead scattering amplitudes :math:`f_{i}`):

    .. math:: S(q,t)/S(q,0) &= \frac{1}{F(q)} \sum_{ij}^{N} f_{i}f_{j} exp(-q^2/6\langle |R_i(t) -R_j(0)|^2\rangle ) \\
                     &= \frac{1}{F(q)} exp(-q^2Dt) \sum_{ij}^{N} f_{i}f_{j }exp(-q^2l^2/6 \cdot d_{ij}^2)

    with the form factor :math:`F(q)` and (equ. 8 in [4]_)

    .. math:: d_{ij}^2 = \sum_{a=1}^N \mu_a^{-1} [|Q_{ia}|^2+|Q_{ja}|^2 - 2Q_{ia}Q_{ka} exp(-\sigma\lambda_at))]

    .. note::
       One should recognize the similarity in the description to normal modes of biomacromolecules reprectively proteins
       as described in the Ornstein-Uhlenbeck process :py:func:`jscatter.bio.scatter.intScatFuncOU`.
       The difference is the explicit usage of coordinates in :py:func:`jscatter.bio.scatter.intScatFuncOU`
       while in the ORZ model statistical averages of :math:`d_{ij}` without explicit coordinates are used.

    We yield the static form factor as for :math:`t \rightarrow 0`

    .. math:: F(Q) &= S(q,0) =& \sum_{ij}^N f_{i}f_{j}exp(-\frac{q^2}{6}\langle R_{ij}^2\rangle ) \\
              \hat{F}(Q) &=             & \frac{1}{N^2}\sum_{ij}^N exp(-\frac{q^2}{6}\langle R_{ij}^2\rangle )

    where the second line is the normalized form factor equ. 2 in [4] with :math:`f_i=1`.

    The translational diffusion coefficient is equ. 24 in [4]:

    .. math::  D = kT/N\zeta [1 + \frac{\zeta_r}{N}\sum_{ij} (1-\delta_{ij}) \langle l/R_{ij}\rangle ]

    The first cumulant observed in an experiment at short times
    (initial slope :math:`\Omega(q)=-(d/dt)ln(S(q,t))|_{t=0}=\Omega(q)`) is equ. 13 in [4]_ for :math:`f_i=1`:

    .. math:: \Omega(q) = q^2D_{cum} = q^2 \frac{\sigma l^2}{3N} \frac{1}{\hat{F}(q)} [1 + \frac{\zeta_r}{N}
                            \sum_{ij} (1-\delta_{ij}) \langle l/R_{ij}\rangle  exp(-q^2l^2/6 \cdot d_{ij}^2(0) )]

    The prefactor is :math:`\sigma l^2/(3N)=kT/N\zeta` as in the equation above.

    Taking into account the scattering amplitudes :math:`f_i` we yield with the NOT normalized form factor :math:`F(q)`

    .. math:: \Omega(q) = q^2 D_{cum} = q^2 \frac{\sigma l^2}{3} \frac{1}{F(q)F(0)}
                        [\sum_{i=j}f_i^2 + \sum_{i\neq j}
                        f_i f_j \zeta_r \langle l/R_{ij}\rangle  exp(-q^2l^2/6 \cdot d_{ij}^2(0) )]

    Here we see that specific bead/arm contributions can be suppressed if the respective beads
    are matched to the surrounding solvent.
    Nevertheless, the overall tranlational diffusion will not change by matching.

    The dynamic intrinsic viscosity can be calculated from the relaxation times equ. 21 in [5]_ :

    .. math:: [\eta(\omega)] = \frac{N_akT}{M\eta_0} \sum_{a} \frac{\tau_a}{1+i\omega\tau_a}

    with M as molecular weight and :math:`N_a` as Avogadro constant.

    .. note::
       It should be pointed out that the matrix :math:`U^{-1}` geht highly singular if the model
       is applied to more rigid chains or rodlike parts resulting in negative eigenvalues.


    **Internal friction**

    Internal friction :math:`\zeta_{int}` between neigboring beads can be included in analogy to Soranno [7]_

    .. math:: \zeta \frac{\partial}{\partial t} R_i(t) + \kappa \sum_{j} (HA)_{ij} R_j(t) +
                                \zeta_{int} \frac{\partial}{\partial t} (HA)_{ij} R_j(t) = v_i(t)

    with the additional friction term. Using the above eigenvectors of :math:`HA` this leads to

    .. math:: \zeta \frac{\partial}{\partial t} \xi_k(t) + \kappa \lambda_k \xi_k(t) +
                    \zeta_{int} \frac{\partial}{\partial t} \lambda_k \xi_k(t) &= w_k(t) \\
            [(\zeta +\zeta_{int} \lambda_k)\frac{\partial}{\partial t}\xi_k(t) = - \kappa \lambda_k \xi_k(t)  + w_k(t)

    and result in same eigenvectors but changed relaxation times
    :math:`\tau_{a,int}=(\sigma \lambda_a)^{-1} + \tau_{int} = \tau_a + \tau_{int}`
    with :math:`\tau_{int} = \zeta_{int}/\kappa` as presented by Sorrano for standard Rouse/Zimm model [7]_.
    The additional internal friction is here independent of the modes and has a stronger effect on higher modes.

    In above corrrelation functions we need to change

    .. math::  &exp(-\sigma\lambda_a t)=exp(- \frac{t}{\tau_a}) \rightarrow \\
              &exp(-\frac{\sigma \lambda_a}{1+\sigma \lambda_a \tau_{int}}t)=exp(-\frac{t}{\tau_a+\tau_{int}})

    Here :math:`\tau_a` contains implicitly the mode dependence :math:`\tau_{zp}=\tau_zp^{-3\nu}` for Zimm or
    :math:`\tau_{rp}=\tau_zp^{-2}` for Rouse like systems (see :py:func:`finiteRouse`, :py:func:`finiteZimm`)
    but the additional mode independent internal friction is the same.
    Correspondingly in the cumulant a correction is needed
    :math:`\langle l/R_{ij}\rangle \rightarrow \langle l/R_{ij}\rangle \sum_a 1/(1+\sigma\lambda_a \tau_{int})`

    Examples
    --------
    Example to reproduce Fig 6 of [2]_ (only left subplot) but in simpler model (not RIS)
    just using bead-spring (FJC) and free rotating chain models for linear polymers:

    Non-vanishing bond correlations increase size.
    Draining increases relaxation times but not the msd of the movements.

    ::

     import jscatter as js
     import numpy as np

     p = js.grace(1.9,1.)
     p.multi(1,3,hgap=0.25)
     p[0].yaxis(label=r'\xl\f{}\sa')
     p[1].yaxis(label=r'\xt\f{}\sa\N\xs',scale='log',ticklabel=['power',0])
     p[2].yaxis(label=r'\x<z\f{}\S2\N\sa\N>/l\S2',scale='log',ticklabel=['power',0])
     p[0].xaxis(label=r'a')
     p[1].xaxis(label=r'a',scale='log')
     p[2].xaxis(label=r'a',scale='log')

     # matrices for linear chain
     N=100
     M = np.diag([1.]*(N+1)) +  np.diag([-1.]*N,-1)
     U = np.diag([1.]*N)
     A = M[1:,:].T @ U @ M[1:,:]
     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0.25)[:3]
     a = np.r_[1:ev.shape[0]]
     p[0].plot(a, ev[1:],le='FJC partial draining')
     p[1].plot(a, 1/ev[1:],le='FJC partial draining')
     p[2].plot(a, 1/mu[1:],le='FJC partial draining')

     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0)[:3]
     a = np.r_[1:ev.shape[0]]
     p[0].plot(a, ev[1:],le='FJC free draining')
     p[1].plot(a, 1/ev[1:],le='FJC free draining')
     p[2].plot(a, 1/mu[1:],le='FJC free draining')


     # matrices for linear chain but non-vanishing bond correlation
     costheta = 0.65
     i,j = np.indices([N,N])
     Uinv = costheta**np.abs(i-j)
     U = np.linalg.inv(Uinv)
     A = M[1:,:].T @ U @ M[1:,:]
     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0.25)[:3]
     a = np.r_[1:ev.shape[0]]
     p[0].plot(a, ev[1:],le='FRC partial draining')
     p[1].plot(a, 1/ev[1:],le='FRC partial draining')
     p[2].plot(a, 1/mu[1:],le='FRC partial draining')

     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0)[:3]
     a = np.r_[1:ev.shape[0]]
     p[0].plot(a, ev[1:],le='FRC free draining')
     p[1].plot(a, 1/ev[1:],le='FRC free draining')
     p[2].plot(a, 1/mu[1:],le='FRC free draining')

     p[0].subtitle('eigenvalue spectra')
     p[1].subtitle('relaxation times')
     p[2].subtitle('mean square displacements')
     p[1].title('model FJC + FRC free draining and partial draining')
     p[1].legend(x=1.4,y=1,charsize=0.8)
     # p.save(js.examples.imagepath+'/ORZeigenvalue.jpg',size=(1.9,1.),dpi=200)

    .. image:: ../../examples/images/ORZeigenvalue.jpg
     :align: center
     :width: 80 %
     :alt: ORZ eigenvalue and more

    Correctness of the solution can be verified by comparing to Table I of [6]_.
    The parameter `h` in [6]_ corresponds to reducedfriction :math:`=r/b= (\pi/(3N))^{1/2}h \approx 0.1023 h`

    Today the eigenvalue problem can be solved directly and is more accurate.
    ::

     import jscatter as js
     import numpy as np


     # matrices for linear chain
     N=100
     M = np.diag([1.]*(N+1)) +  np.diag([-1.]*N,-1)
     U = np.diag([1.]*N)
     A = M[1:,:].T @ U @ M[1:,:]
     # for h=1 or 2 compare to :math:`\lambda_k` (second and 4th column) and :math:`\mu_k` for h=0 to exact solution.
     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0.2)[:3]
     ev[-1]  # ~ 2.66
     mu[-1]  # ~ 3.99
     ev, evec, mu = js.dynamic.timedomain.solveOptimizedRouseZimm(A, reducedfriction=0.1)[:3]
     ev[-1]  # ~ 3.33
     mu[-1]  # ~ 3.99



    References
    ----------
    .. [1] Theoretical basis for the Rouse‐Zimm model in polymer solution dynamics.
           Zwanzig, R. The Journal of Chemical Physics 60, 2717–2720 (1974) https://doi.org/10.1063/1.1681433
    .. [2] A hierarchy of models for the dynamics of polymer chains in dilute solution.
           Perico, A., Ganazzoli, F. & Allegra, G.
           The Journal of Chemical Physics 87, 3677–3686 (1987). https://doi.org/10.1063/1.452966
    .. [3] Intramolecular relaxation dynamics in semiflexible dendrimers.
           Kumar, A. & Biswas, P.  Journal of Chemical Physics 134, (2011). https://doi.org/10.1063/1.3598336
    .. [4] Static and Dynamic Structure Factors for Star Polymers in θ Conditions.
           Guenza, M. & Perico, A.
           Macromolecules 26, 4196–4202 (1993). https://doi.org/10.1021/ma00068a020
    .. [5] Optimized Rouse–Zimm theory for stiff polymers
           M. Bixon; R. Zwanzig
           J. Chem. Phys. 68, 1896–1902 (1978) https://doi.org/10.1063/1.435916
    .. [6] Dynamics of chain molecules. I. Solutions to the hydrodynamic equation and intrinsic viscosity.
           Perico, A., Piaggio, P. & Cuniberti, C.
           The Journal of Chemical Physics 62, 4911–4918 (1975). https://doi.org/10.1063/1.430404
    .. [7] Internal friction in an intrinsically disordered protein - Comparing Rouse-like models with experiments
           A. Soranno, F. Zosel, H. Hofmann
           J. Chem. Phys. 148, 123326 (2018) http://aip.scitation.org/doi/10.1063/1.5009286

    """
    N = A.shape[0]

    # eigenvalues of static problem (H=Identity) give Rij2
    # [2] equ 3.1 and below
    # also Kumar et al J. Chem. Phys. 138, 104902 (2013) equ 3 But not mentioning using static problem
    # numpy : The column evec[:, i] is the normalized eigenvector to the eigenvalue eval[i]. evals are sorted
    evalA, evecA= la.eigh(A)
    Rij2_red = fscatter.dynamic.eigvector2rij2(evalA, evecA)  # not including l**2

    # [2] equ 3.2 + 3.3 without lo**2
    # Rg2_red = Rg2/ l**2 =  np.sum(Rij2_red)/N**2/2 or
    Rg2_red = np.sum(1/evalA[1:]) / N

    # get loverR, catch diagonal zeros
    np.fill_diagonal(Rij2_red, 1)
    loverR = (6 / np.pi)**0.5 * Rij2_red ** -0.5
    np.fill_diagonal(Rij2_red, 0)
    np.fill_diagonal(loverR, 0)

    if reducedfriction > 0:
        # H = hydrodynamic matrix, [1] equ 9
        H = np.diag([1]*N) + reducedfriction * loverR
        # print(f'H has {np.sum(la.eigvals(H) <0)} neg eigenvalues. NOT positive definite ')

        # if A is symmetric and H symmetric and positive definite then H@A can be diagonalized
        evalHA, evecHA = la.eigh(H @ A)

        # calc mode amplitude factor   (evec.T @ A @ evec) is diagonal up to numerical precision
        muHA = np.diag(evecHA.T @ A @ evecHA)

        return evalHA, evecHA, muHA, loverR, Rg2_red, Rij2_red, A

    else:
        # Rouse = no HI interaction => H ==identity
        # calc mode amplitude factor   (evec.T @ A @ evec) is diagonal up to numerical precision
        muA = np.diag(evecA.T @ A @ evecA)

        return evalA, evecA, muA, loverR, Rg2_red, Rij2_red, A


@formel.memoize()
def _linearStructuralMatrix(N, costheta):
    """
    Create for a star the  bond correlation matrix U^-1 and bead-to-bond vector transformation matrix M

    This part is in reduced units that bond length is not used.

    """
    # see references in main function

    # bond correlation matrix U_ij^-1 = <l_i*l_j>/l**2 ; with N-1 bonds
    if isinstance(costheta, numbers.Number):
        if costheta==0:
            # identity for uncorrelated bonds , freely jointed chain no correlation except self correlation
            Uinv = np.diag([1]*(N-1))
            U = Uinv  # np.linalg.inv(Uinv)
        else:
            # free rotating chain FRC with  <li*lj> /l**2 = cos(theta)^(|j-i|) or Prod[cos(theta_i)]
            # eg. https://dasher.wustl.edu/bio5357/readings/rubinstein-chapter2.pdf  2.20
            # [1] equ. 30-33 ff
            i,j = np.indices([N-1,N-1])

            # same arm => difference in indices gives distance
            Uinv = costheta**np.abs(i-j)  # |i-j| < n_arm
            Uinv[Uinv < 0.001] = 0
            U = np.linalg.inv(Uinv)

    elif isinstance(costheta, (list, np.ndarray)):
        assert len(costheta) == N-2, 'costheta should be list of len N-2.'
        assert np.all(np.array(costheta) < 1) & np.all(
            0 <= np.array(costheta)), 'costheta should be 0 <= cos(theta) < 1 !'

        i,j = np.indices([N-1,N-1])
        Uinv = fscatter.dynamic.cumcos(costheta, i, j)
        Uinv[Uinv < 0.001] = 0
        U = np.linalg.inv(Uinv)

    else:
        # for later cos theta depends on bead
        raise TypeError('costheta should be float or list of len N-1.')

    # bead-to-bond vector transformation matrix [1] equ 25 particular for star
    # indices in paper run from 1 to n , here 0 to N-1
    M = np.diag([0.]+[1.]*(N-1)) +  np.diag([-1.]*(N-1),-1)

    # [2] equ 2.7 A.T@U @ A with a = M[1:,:]
    A = M[1:,:].T @ U @ M[1:,:]
    return A


def linearChainORZ(t, q, N=100, l=1, fa=None, Dcm=None, Dcmfkt=None,
                 viscosity=1, costheta=0., T=293, reducedfriction=0.25, tintern=0):
    r"""
    Dynamics of a linear polymer chain using optimized Rouse-Zimm approximation (ORZ).

    The linear dynamic structure factor is calculated in analogy to the star described by Guenza [1]_.

    The linear chain dynamics is decribed within the more general optimized Rouse-Zimm (ORZ) approximation
    introduced by Bixon and Zwanzig [3]_ [4]_ . See :py:func:`solveOptimizedRouseZimm`.

    We extend this here using bead scattering lengths for partial matching and allow individual bond correlations.

    To speedup fitting use the memoize function as described in :py:func:`~.formel.memoize`.

    Parameters
    ----------
    t : array
        timepoints in units ns.
    q : array
        Scattering vectors in units 1/nm.
    N : int
        Number of beads .
    l : float, default = 0.38 nm (amino acid)
        Bond length or Kuhn length in units nm.
    fa : None, list of float
        Scattering length of bead/monomer :math:`fa_i`. Can be used to match parts of the star to the solvent.

        - None : Equal 1 for all beads.
        - list: length N as scattering length of beads in sequence
    Dcm : float
        Center of mass diffusion in units nm**2/ns.
        If `None` the calculated value D_ORZ is used.
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi) ] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor or hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    costheta : float, list of float, 0 <= costheta < 1
        Cos of bond correlation angle :math:`\langle  \vec{l_i} \cdot \vec{l_j} \rangle /l^2  = cos(theta)`
        between normalized bonds :math:`l_i`  with :math:`0 \le cos(\theta) \le 1`.

        - costheta = 0 : FJC (freely jointed chain) model, no bond correlation, Rouse dynamics, No HI .
        - float :math:`0 < cos(\theta) \le 1` : FRC (free rotating chain). With
          :math:`R_{ee} = Nl^2C_{\infty}=Nl^2 \frac{1+cos(\theta)}{1-cos(\theta)}` .
        - list of float length N-2 : FRC with individual :math:`cos(\theta_i)` for each pair of N-2 bonds.

          - ``costheta=([0.1]*24+[0.7]*24)`` for stretched beginning and flexible end of 50 beads.
          - ``costheta=0.8 * np.cos(np.pi*np.r_[:1:(N-2)*1j])**2 + 0.1`` for flexible center and stretched ends.

          For fitting encapsulate the model in a function where you parametrize your model for costheta.

        e.g. (from [5]_ p. 53) :math:`C_{\infty} | Kuhn length [A] | cos(theta)`
         - polyisoprene  4.6 |  8.2 | 0.783
         - polyethylene oxide 6.7 | 11 | 0.85
         - polyethylene 7.4 | 14 | 0.865
         - atactic polystyrene 9.5 | 18 | 0.895

        - During fits use ``limits(costheta=[None,None,0.001,0.999])`` to avoid singular matrices.

    viscosity : float, default=1 (H2O@20C )
        :math:`\eta` in units cPoise=mPa*s  e.g. water :math:`visc(T=293 K) =1 mPas`
    T : float, default 273+20
        Temperature  in Kelvin.
    reducedfriction : float, default 0.25
        Reduced friction :math:`\zeta_r = \zeta/6\pi\eta_sl` in hydrodynamic tensor H.
         - =0 : free draining limit, no HI, Rouse dynamics.
         - >0 : with HI typically <0.5. For h>0.5 we get negative eigenvalues.

        See :py:func:`solveOptimizedRouseZimm`.

        During fits use ``limits(reducedfriction=[0,0.43,0.,0.5])`` to avoid singular matrices.
    tintern : float>0, default 0
        Relaxation time due to internal friction between neighboring beads in ns.

    Returns
    -------
    sqt : dataList
        Intermediate scattering function of  a star for given q.

        - [times; Sqt; Sqt only diffusion; Sqt cumulant]
        - columnname = 't;Sqt;Sqt_inf;Sqt_cum'
        - .q : scattering vector
        - .D_ORZcum : diffusion coefficinet in initial slope (cumulant)
        - .D_ORZ : translational diffusion ORZ model
        - .Dcm  :  used center of friction/mass diffusion
        - .Fq : form factor
        - .Fq_inf : form factor t=inf
        - .beadfriction : bead friction
        - .bondrateconstant : bondrateconstant in 1/ns
        - .moderelaxationtimes : used moderelaxationtimes in ns [4] equ 2.17
        - .mode_rmsd : used mode rmsd as math:`l/\mu^{0.5}  # [4] equ 2.19
        - .reducedfriction : reducedfriction
        - .costheta : costheta
        - .eigenvalues : all evals
        - .mu : all mu
        - .l : bondlength l
        - .N : Number of beads
        - .Rg : radius of gyration in nm
        - .Rg_red : reduced radius of gyration

    Notes
    -----
    See :py:func:`solveOptimizedRouseZimm` for a description of the ORZ model with respective parameters and
    the dynamic structure factor :math:`S(q,t)/S(q,0)` .


    Here we use a linear chain with N beads and set elements :math:`U^{-1}_{ij} <0.001 \rightarrow 0`.

    The inverse of the static bond correlation matrix :math:`U_{ij}^{-1} = \langle l_i\cdot l_j\rangle /l^2`
    in dimesionless form is

    .. math:: U_{ij}^{-1}  &= \delta_{i,j}           &\text{ for uncorrelated bonds } \\
                           &= \prod_{n=i}^{j} g_n  \;  &\text{ for individual } g_i \text{ including constant g}

    The transfer matrix M  is

    .. math:: M = \delta_{i,j} - \delta_{i+1,j}


    Examples
    --------
    Here we examine how changig stiffness influences dynamics.
    ::

     import jscatter as js
     import numpy as np

     q= np.r_[0.01,0.1:2:0.2]
     t = np.r_[0:1:0.02,1:20:1,20:100:5]

     def stiffendschain(t, q, N, l=0.5, cosmin =0.05,cosmax=0.8,rf=0.25):
        costheta = (cosmax-cosmin) * np.cos(np.pi*np.r_[:1:(N-2)*1j])**2 + cosmin
        sqt = js.dynamic.linearChainORZ(t, q, N, l=0.5, costheta = costheta , reducedfriction=rf)
        return sqt

     p = js.grace()
     p.xaxis(label='t / ns')

     sqt = stiffendschain(t, q, 100, l=1, cosmin =0.1,cosmax=0.5)
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[1,1,c],sy=0,le=f'{sq.q:.2f} nm\\S-1')

     sqt = stiffendschain(t, q, 100, l=1, cosmin =0.1,cosmax=0.1)
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[3,1,c],sy=0,le='')

     p.yaxis(label='S(Q,t),S(Q,0)',scale='log',min=0.01,max=1)
     p.legend(charsize=0.7)
     p.title('chain with stiff ends ')
     p.subtitle('solid: stiff ends; broken: flexible ends')

     # p.save(js.examples.imagepath+'/ORZ_linearstiffends.png',size=(1.5,1.5),dpi=300)

    .. image:: ../../examples/images/ORZ_linearstiffends.png
     :align: center
     :width: 60 %
     :alt: ORZ eigenvalue and more

    References
    ----------
    .. [1] Static and Dynamic Structure Factors for Star Polymers in θ Conditions.
           Guenza, M. & Perico, A.
           Macromolecules 26, 4196–4202 (1993). https://doi.org/10.1021/ma00068a020
    .. [2] A Local Approach to the Dynamics of Star Polymers.
           Guenza, M., Mormino, M. & Perico, A.
           Macromolecules 24, 6168–6174 (1991). https://doi.org/10.1021/ma00023a018
    .. [3] Theoretical basis for the Rouse‐Zimm model in polymer solution dynamics.
           Zwanzig, R. The Journal of Chemical Physics 60, 2717–2720 (1974) https://doi.org/10.1063/1.1681433
    .. [4] A hierarchy of models for the dynamics of polymer chains in dilute solution.
           Perico, A., Ganazzoli, F. & Allegra, G.
           The Journal of Chemical Physics 87, 3677–3686 (1987). https://doi.org/10.1063/1.452966
    .. [5] Rubinstein, M. & Colby, R. H. Polymer Physics. (OUP Oxford, 2003).
    .. [6] Intramolecular relaxation dynamics in semiflexible dendrimers.
           Kumar, A. & Biswas, P.  Journal of Chemical Physics 134, (2011). https://doi.org/10.1063/1.3598336


    """


    if fa is None:
        fa = np.ones(N)
    assert len(fa) == N, 'fa should be of length N.'
    fa = np.array(fa)
    q =np.atleast_1d(q)

    t0 = np.r_[0,t]

    # bead friction coefficient
    friction = 6 * np.pi * (viscosity*1e-3) * (l * 1e-9)  # l in nm; viscosity in Pa*s

    # bond rate constant brc, sometimes named W
    brc = (3 * kb * T / (l*1e-9)**2 / friction) * 1e-9 # l in nm  # brc is 1/s => *1e-9 in 1/ns
    reducedfriction = max(min(reducedfriction, 1), 0)

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    # create bond matrix and transfer matrix for a star
    A = _linearStructuralMatrix(N, costheta)

    # compute Eigenvectors and Eigenvalues for ORZ in reduced units
    evals, evec, mu, loverR, Rg2_red, Rij2_red2, _ = solveOptimizedRouseZimm(A, reducedfriction)
    if np.any(evals[1:] < 0):
        raise UserWarning(f'There are {np.sum(evals[1:]<0)} negative eigenvalues in ORZ solution. '
                          f'reducedfriction should be smaller.')

    # >95% of computing time in this call for N=100 that already uses omp
    # array dim [Q values x time values+2]
    # first is sqt(0), last element is sum in equation 13 for initial cumulant, second last t=inf
    # first eval is COM diffusion and large eval and large mu dont contribute much
    lowev =  np.r_[[False], (brc * evals[1:] < 15) | (1/mu[1:] > max(0.001/mu[1:]))]
    sqt = fscatter.dynamic.sqtnonlinearpolymer(evec[:,1:], evals[1:], mu[1:], fa, q, t0, l, brc, loverR, tintern)

    # [1] equ 24 for center of mass diffusion
    Dcm_ORZ = kb * T / N / friction * 1e9  # in nm**2/ns
    if reducedfriction>0:
                Dcm_ORZ *= (1 + reducedfriction/N * np.sum(loverR))


    results = dL()
    for i, sqti in enumerate(sqt):
        # calc initial slope diffusion  as first cumulant/q**2  [1] equ 13
        D_cum_ORZ = brc * l**2/3/sqti[0] * (np.sum(fa**2) + reducedfriction * sqti[-1])
        if Dcm is None:
            Dcm = Dcm_ORZ

        results.append(np.c_[t0[1:],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[1:-2]/sqti[0],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[-2]/sqti[0],
                       np.exp(-q[i]**2 * (D_cum_ORZ - Dcm + Dcm * Dcmfunktion(q[i])) * t0[1:]) ].T)

        results[-1].setColumnIndex(iey=None)
        results[-1].columnname = 't;Sqt;Sqt_inf;Sqt_cum'

        results[-1].viscosity = viscosity
        results[-1].q = q[i]
        results[-1].D_ORZcum = D_cum_ORZ
        results[-1].D_ORZ = Dcm_ORZ
        results[-1].Dcm = Dcm
        results[-1].Fq = sqti[0] / np.sum(fa)**2  # form factor t=0
        results[-1].Fq_inf = sqti[-2] / np.sum(fa)**2  # form factor t=inf
        results[-1].beadfriction = friction
        results[-1].bondrateconstant = brc  # in 1/ns
        results[-1].moderelaxationtimes = 1 / (brc * evals[lowev]) + tintern # [4] equ 2.17
        results[-1].mode_rmsd = l / mu[lowev]**0.5  # [4] equ 2.19
        results[-1].reducedfriction = reducedfriction
        results[-1].costheta = costheta
        results[-1].eigenvalues = evals
        results[-1].mu = mu
        results[-1].l = l
        results[-1].tintern = tintern
        results[-1].N = evec.shape[0]
        results[-1].Rg = l * Rg2_red**0.5
        results[-1].Rg_red = Rg2_red**0.5
        results[-1].modelname = inspect.currentframe().f_code.co_name

    if len(results) == 1:
        return results[0]

    return results


@formel.memoize()
def _starStructuralMatrix(f_arm, n_arm, costheta):
    """
    Create for a star the  bond correlation matrix U^-1 and bead-to-bond vector transformation matrix M

    This part is in reduced units that bond length is not used.

    """
    # see references in main function

    # f_arms number of arms
    # n_arms number of beads in arm
    N = f_arm * n_arm + 1  # total number of beads, first index is center of the star

    # bond correlation matrix U_ij^-1 = <l_i*l_j>/l**2 ; with N-1 bonds
    if isinstance(costheta, numbers.Number):
        if costheta==0:
            # identity for uncorrelated bonds , freely jointed chain no correlation except self correlation
            Uinv = np.diag([1]*(N-1))
            U = Uinv  # np.linalg.inv(Uinv)
        else:
            # free rotating chain FRC with  <li*lj> /l**2 = cos(theta)^(|j-i|) or Prod[cos(theta_i)]
            # eg. https://dasher.wustl.edu/bio5357/readings/rubinstein-chapter2.pdf  2.20
            # [1] equ. 30-33 ff
            i,j = np.indices([N-1,N-1])
            Uinv = np.zeros([N-1,N-1])

            # same arm => difference in indices gives distance
            same = (i//n_arm == j // n_arm)
            Uinv[same] = costheta**np.abs(i-j)[same]  # |i-j| < n_arm

            # different arms => each distance to center + center arm correlation
            # similar to equ [1] 32,33 but a=1/(1-f)  and indices i,j start at 0 not 1 like paper [1]
            different = (i//n_arm != j // n_arm)
            if f_arm > 2:
                # center is symmetric
                Uinv[different] = (1/(f_arm -1) * costheta**(i%n_arm + j%n_arm ))[different]
            else:
                # for linear case there is no special about the center, 1/(f-1) makes a singular matrix
                Uinv[different] = (costheta * costheta**(i % n_arm + j % n_arm))[different]
            Uinv[Uinv < 0.001] = 0
            U = np.linalg.inv(Uinv)

    elif isinstance(costheta, (list, np.ndarray)):
        #raise UserWarning('not yet implemented')
        assert len(costheta) == n_arm-1, 'costheta should be list of len n_arm-1.'
        assert np.all(np.array(costheta) < 1) & np.all(
            0 <= np.array(costheta)), 'costheta should be 0 <= cos(theta) < 1 !'
        cumcos = fscatter.dynamic.cumcos
        i,j = np.indices([N-1,N-1])
        Uinv = np.zeros([N-1,N-1])

        same = (i//n_arm == j // n_arm)
        Uinv[same] = cumcos(costheta, i%n_arm, j%n_arm)[same]  # calcs for to much, cut these by [same]

        # different arms => each distance to center + center arm correlation
        # similar to equ [1] 32,33 but a=1/(1-f)  and indices i,j start at 0 not 1 like paper [1]
        different = (i//n_arm != j // n_arm)
        z0 = np.zeros_like(i)
        if f_arm > 2:
            # center is symmetric, we use 1/(f-1) (see paper [2])
            Uinv[different] = (1/(f_arm -1) * cumcos(costheta,z0, j%n_arm) *
                                              cumcos(costheta,z0, i%n_arm))[different]
        else:
            # for linear case there is no special about the center, 1/(f-1) would make a singular matrix
            Uinv[different] = (costheta[0] * cumcos(costheta,z0, j%n_arm) *
                                             cumcos(costheta,z0, i%n_arm))[different]
        Uinv[Uinv < 0.001] = 0
        U = np.linalg.inv(Uinv)

    else:
        # for later cos theta depends on bead
        raise TypeError('costheta should be float or list of len n_arm.')

    # bead-to-bond vector transformation matrix [1] equ 25 particular for star
    # indices in paper run from 1 to n , here 0 to N-1
    M = np.diag([0.]+[1.]*(N-1))
    # M[0,:] = 1/N  # this is never accessed or used
    for j in np.r_[:f_arm]:
        for i in np.r_[1:n_arm]:
            ij = n_arm * j + i
            M[ij+1,ij] = -1.
    for j in np.r_[:f_arm]:
        i = 1 + j * n_arm
        M[j*n_arm+1,0] = -1.

    # [2] equ 2.7 A.T@U @ A with a = M[1:,:]
    A = M[1:,:].T @ U @ M[1:,:]
    return A


def multiArmStarORZ(t, q, f_arm=4, n_arm=10, l=1, fa=None, Dcm=None, Dcmfkt=None,
                 viscosity=1, costheta=0., T=293, reducedfriction=0.25, tintern=0):
    r"""
    Dynamics of a symmetric multi arm star of polymer chains using optimized Rouse-Zimm approximation (ORZ).

    The star dynamic structure factor is explicitly described by Guenza [1]_ and extended to partially stretched stars
    in [2]_.

    The star polymer dynamics is decribed within the more general optimized Rouse-Zimm (ORZ) approximation
    introduced by Bixon and Zwanzig [3]_ [4]_ . See :py:func:`solveOptimizedRouseZimm`.

    We extend this here using bead scattering lengths for partial matching and allow individual bond correlations.

    To speedup fitting use the memoize function as described in :py:func:`~.formel.memoize`.

    Parameters
    ----------
    t : array
        timepoints in units ns.
    q : array
        Scattering vectors in units 1/nm.
    f_arm : int
        Number of arms :math:`f_{arm}`.
    n_arm : int
        Number of beads per arm :math:`n_{arm}` excluding the center common for all arms.
    l : float, default = 0.38 nm (amino acid)
        Bond length or Kuhn length in units nm.
    fa : None, list of float
        Scattering length of bead/monomer :math:`fa_i`. Can be used to match parts of the star to the solvent.

        - None : Equal 1 for all beads.
        - list: length (1 + f_arm * n_arm) as scattering length of beads in sequence
          [center, 1..n_arm first arm,1..n_arm second arm,....]

          e.g. ``fa=[0] + ([0]*5+[1]*6)*4``
          for a 4 arm star of 11 beads per arm with the center and 5 innermost beads matched.
    Dcm : float
        Center of mass diffusion in units nm**2/ns.
        If `None` the calculated value D_ORZ is used.
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi) ] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor or hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    costheta : float, list of float, 0 <= costheta < 0.1
        Cos of bond correlation angle :math:`\langle  \vec{l_i} \cdot \vec{l_j} \rangle /l^2 = cos(theta)`
        between normalized bonds :math:`l_i`  with :math:`0 \le cos(\theta) \le 1`.

        - costheta = 0 : FJC (freely jointed chain) model, no bond correlation, Rouse dynamics, No HI .
        - float :math:`0 < cos(\theta) \le 1` : FRC (free rotating chain). With
          :math:`R_{ee} = Nl^2C_{\infty}=Nl^2 \frac{1+cos(\theta)}{1-cos(\theta)}` .
        - list of float of length ``n_arm-1`` for the consecutive bonds of a arm.
          e.g ``fa=([0.5]*5+[0.1]*6)`` for stretched inner and flexible outer arms. For the core see below

        e.g. (from [5]_ p. 53) :math:`C_{\infty} | Kuhn length [A] | cos(theta)`
         - polyisoprene  4.6 |  8.2 | 0.783
         - polyethylene oxide 6.7 | 11 | 0.85
         - polyethylene 7.4 | 14 | 0.865
         - atactic polystyrene 9.5 | 18 | 0.895

        - costheta of the core bonds is :math:`cos(\theta) = (f_{arm}-1)^{-1}` to yield a symmetric core.
          For :math:`f_{arm}=2` the core is not special and we use costheta of the innermost bead in an arm
          to result in a linear chain.
        - During fits use ``limits(costheta=[None,None,0.00,0.999])`` to avoid singular matrices.

    viscosity : float, default=1 (H2O@20C )
        :math:`\eta` in units cPoise=mPa*s  e.g. water :math:`visc(T=293 K) =1 mPas`
    T : float, default 273+20
        Temperature  in Kelvin.
    reducedfriction : float, default 0.25
        Reduced friction :math:`\zeta_r = \zeta/6\pi\eta_sl` in hydrodynamic tensor H.
         - =0 : free draining limit, no HI, Rouse dynamics.
         - >0 : with HI typically <0.5. For h>0.5 we get negative eigenvalues.

        See :py:func:`solveOptimizedRouseZimm`.

        During fits use ``limits(reducedfriction=[0,0.43,0.,0.5])`` to avoid singular matrices.
    tintern : float>0, default 0
        Relaxation time due to internal friction between neighboring beads in ns.

    Returns
    -------
    sqt : dataList
        Intermediate scattering function of  a star for given q.

        - [times; Sqt; Sqt only diffusion; Sqt cumulant]
        - columnname = 't;Sqt;Sqt_inf;Sqt_cum'
        - .q : scattering vector
        - .D_ORZcum : diffusion coefficinet in initial slope (cumulant)
        - .D_ORZ : translational diffusion ORZ model
        - .Dcm  :  used center of friction/mass diffusion
        - .Fq : normalized form factor
        - .Fq_inf : normalized form factor t=inf
        - .beadfriction : bead friction
        - .bondrateconstant : bondrateconstant in 1/ns
        - .moderelaxationtimes : used moderelaxationtimes in ns [4] equ 2.17
        - .mode_rmsd : used mode rmsd as math:`l/\mu^{0.5}  # [4] equ 2.19
        - .reducedfriction : reducedfriction
        - .costheta : costheta
        - .eigenvalues : all evals
        - .mu : all mu
        - .l : bondlength l
        - .N : Number of beads
        - .Rg : radius of gyration in nm
        - .Rg_red : reduced radius of gyration

    Notes
    -----
    See :py:func:`solveOptimizedRouseZimm` for a description of the ORZ model with respective parameters and
    the dynamic structure factor :math:`S(q,t)/S(q,0)` .

    Here we use a symetric star with `f_arm` arms of each `n_arm` beads and a connecting bead
    as described by Guenza [1]_ and set elements :math:`U^{-1}_{ij} <0.001 \rightarrow 0`.

    The inverse of the static bond correlation matrix :math:`U_{ij}^{-1} = \langle l_i\cdot l_j\rangle /l^2`
    in dimesionless form is

    .. math:: U_{ij}^{-1}  &= \delta_{i,j}                           &\text{ for uncorrelated bonds } \\

    For individual :math:`g_i` including that g all are the same and core :math:`g_0` (indexing start at 1)

    .. math::
        U_{ij}^{-1}  &= \prod_{n=i}^{j} g_n                          &\text{  for i,j on the same arm} \\
                     &= g_0 \prod_{n=1}^{j} g_n \prod_{m=1}^{i} g_m  &\text{  for i,j on different arms}

    The transfer matrix M  is (ignoring the not used :math:`M_{1i}`) accordig to [2]_ :

    .. math::
       \begin{align}
        &M_{1,i}    &= 1/N   &\text{ for }i=1..n_{arm} \\
        &M_{i,i}    &= 1     &\text{ for }i=2..n_{arm} \\
        &M_{i+1,i}  &= -1    &\text{ for }i=2..n_{arm},n_{arm}+2..2n_{arm},...,(f_{arm}-1)N+2...f_{arm}n_{arm} \\
        &M_{i,1}    &= -1    &\text{ for }i=2, n_{arm}+2,2n_{arm}+2,...,(f_{arm}-1)N+2 \\
        &M_{i,j}    &= 0     &\text{ all others}
       \end{align}

    Examples
    --------
    Here we compare the FJC with FRC (costheta=0.1) of a 5 arm star in water.
    We see the tranlational diffusion component at longer times (extrapolated to short times) and the faster relaxation
    of internal modes at short times approaching the cumulant at shortest times.
    ::

     import jscatter as js
     import numpy as np

     q= np.r_[0.01,0.1:2:0.2]
     t = np.r_[0:1:0.02,1:20:1,20:400:5]


     p = js.grace()
     p.xaxis(label='t / ns')

     sqt = js.dynamic.multiArmStarORZ(t, q, 5, 50, l=0.5, costheta = 0, reducedfriction=0.)
     tt = t<20  # for cumulant
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[1,1,c],sy=0,le=f'{sq.q:.2f} nm\S-1')
         p.plot(sq.X, sq._Sqt_inf, li=[2, 1, c], sy=0, )
         p.plot(sq.X[tt], sq._Sqt_cum[tt], li=[2, 1, 1], sy=0, )

     # small
     sqt = js.dynamic.multiArmStarORZ(t, q, 5, 50, l=0.5, costheta = 0.1, reducedfriction=0)
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[3,1,c],sy=0)

     p.yaxis(label='S(Q,t),S(Q,0)',scale='log',min=0.01,max=1)
     p.legend(charsize=0.7)
     p.title('5 arm star ORZ model: no HI and costheta=0, 0.1')
     p.text('trans diffusion',x=30,y=0.16,rot=330)
     p.text('costheta=0',x=300,y=0.031,rot=330)
     p.text('costheta=0.1',x=300,y=0.022,rot=330)
     p.text('cumulant diffusion',x=-20,y=0.3,rot=90)
     # p.save(js.examples.imagepath+'/ORZ_Star.png',size=(1.5,1.5),dpi=300)

    .. image:: ../../examples/images/ORZ_Star.png
     :align: center
     :width: 60 %
     :alt: ORZ 5 arm star

    We compare a flexible 10 arm star with a star that has bonds close to the core stretched.
    We use a simple linear profile while in [1] a two step profile is used.

    We observe that the stiff core increases tranlational diffusion (Dcm: 2.1 -> 1.58 nm²/ns) as the star gets larger
    (Rg: 2.43 -> 3.99 nm). Additional the internal contribution increase in amplitude which might be a result
    of the increased size as the arms are more extended.
    ::

     import jscatter as js
     import numpy as np

     q= np.r_[0.01,0.1:2:0.2]
     t = np.r_[0:1:0.02,1:20:1,20:100:5]


     p = js.grace()
     p.xaxis(label='t / ns')

     sqt0 = js.dynamic.multiArmStarORZ(t, q, 10, 50, l=0.5, costheta = 0, reducedfriction=0.2)
     for c,sq in enumerate(sqt0,1):
         p.plot(sq.X,sq._Sqt,li=[1,1,c],sy=0,le=f'{sq.q:.2f} nm\\S-1')

     # costheta is linear increasing from stretched center to free ends
     sqt1 = js.dynamic.multiArmStarORZ(t, q, 5, 50, l=0.5, costheta = np.r_[0.7:0.1:49j], reducedfriction=0.2)
     for c,sq in enumerate(sqt1,1):
         p.plot(sq.X,sq._Sqt,li=[3,1,c],sy=0)

     p.yaxis(label='S(Q,t),S(Q,0)',scale='log',min=0.01,max=1)
     p.legend(charsize=0.7)
     p.title('10 arm star ORZ model:')
     p.subtitle('solid: costheta=0; broken costheta linear increasing')
     p.text('costheta=0',x=300,y=0.031,rot=330)
     p.text('costheta=0.1',x=300,y=0.022,rot=330)
     # p.save(js.examples.imagepath+'/ORZ_10armStarblob.png',size=(1.5,1.5),dpi=300)

    .. image:: ../../examples/images/ORZ_10armStarblob.png
     :align: center
     :width: 60 %
     :alt: ORZ  arm star blob model


    References
    ----------
    .. [1] Static and Dynamic Structure Factors for Star Polymers in θ Conditions.
           Guenza, M. & Perico, A.
           Macromolecules 26, 4196–4202 (1993). https://doi.org/10.1021/ma00068a020
    .. [2] A Local Approach to the Dynamics of Star Polymers.
           Guenza, M., Mormino, M. & Perico, A.
           Macromolecules 24, 6168–6174 (1991). https://doi.org/10.1021/ma00023a018
    .. [3] Theoretical basis for the Rouse‐Zimm model in polymer solution dynamics.
           Zwanzig, R. The Journal of Chemical Physics 60, 2717–2720 (1974) https://doi.org/10.1063/1.1681433
    .. [4] A hierarchy of models for the dynamics of polymer chains in dilute solution.
           Perico, A., Ganazzoli, F. & Allegra, G.
           The Journal of Chemical Physics 87, 3677–3686 (1987). https://doi.org/10.1063/1.452966
    .. [5] Rubinstein, M. & Colby, R. H. Polymer Physics. (OUP Oxford, 2003).
    .. [6] Intramolecular relaxation dynamics in semiflexible dendrimers.
           Kumar, A. & Biswas, P.  Journal of Chemical Physics 134, (2011). https://doi.org/10.1063/1.3598336


    """
    assert np.all(np.array(costheta)<1) & np.all(0<= np.array(costheta)), 'costheta should be 0 <= cos(theta) < 1 !'

    N = f_arm * n_arm + 1
    if fa is None:
        fa = np.ones(N)
    assert len(fa) == N, 'fa should be of length f_arm * n_arm + 1.'
    fa = np.array(fa)
    q = np.atleast_1d(q)

    t0 = np.r_[0,t]

    # bead friction coefficient
    friction = 6 * np.pi * (viscosity*1e-3) * (l * 1e-9)  # l in nm; viscosity in Pa*s

    # bond rate constant brc, sometimes named W
    brc = (3 * kb * T / (l*1e-9)**2 / friction) * 1e-9 # l in nm  # brc is 1/s => *1e-9 in 1/ns
    reducedfriction = max(min(reducedfriction, 1), 0)

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    # create bond matrix and transfer matrix for a star
    A = _starStructuralMatrix(f_arm, n_arm, costheta)

    # compute Eigenvectors and Eigenvalues for ORZ in reduced units
    evals, evec, mu, loverR, Rg2_red, Rij2_red2, _ = solveOptimizedRouseZimm(A, reducedfriction)
    if np.any(evals[1:] < 0):
        raise UserWarning(f'There are {np.sum(evals[1:] < 0)} negative eigenvalues in ORZ solution. '
                          f'reducedfriction should be smaller.')

    # >95% of computing time in this call for N=100 that already uses omp
    # array dim [Q values x time values+2]
    # first is sqt(0), last element is sum in equation 13 for initial cumulant, second last t=inf
    # first eval is COM diffusion and large eval and large mu dont contribute much
    lowev =  np.r_[[False], (brc * evals[1:] < 15) | (1/mu[1:] > max(0.001/mu[1:]))]
    sqt = fscatter.dynamic.sqtnonlinearpolymer(evec[:,1:], evals[1:], mu[1:], fa, q, t0, l, brc, loverR, tintern)

    # [1] equ 24 for center of mass diffusion
    Dcm_ORZ = kb * T / N / friction * 1e9  # in nm**2/ns
    if reducedfriction>0:
                Dcm_ORZ *= (1 + reducedfriction/N * np.sum(loverR))

    results = dL()
    for i, sqti in enumerate(sqt):
        # calc initial slope diffusion  as first cumulant/q**2  [1] equ 13
        D_cum_ORZ = brc * l**2/3/sqti[0] * (np.sum(fa**2) + reducedfriction * sqti[-1])
        if Dcm is None:
            Dcm = Dcm_ORZ

        results.append(np.c_[t0[1:],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[1:-2]/sqti[0],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[-2]/sqti[0],
                       np.exp(-q[i]**2 * (D_cum_ORZ - Dcm + Dcm * Dcmfunktion(q[i])) * t0[1:]) ].T)


        results[-1].setColumnIndex(iey=None)
        results[-1].columnname = 't;Sqt;Sqt_inf;Sqt_cum'

        results[-1].viscosity = viscosity
        results[-1].q = q[i]
        results[-1].D_ORZcum = D_cum_ORZ
        results[-1].D_ORZ = Dcm_ORZ
        results[-1].Dcm = Dcm
        results[-1].Fq = sqti[0] / np.sum(fa)**2  # form factor t=0
        results[-1].Fq_inf = sqti[-2] / np.sum(fa)**2 # form factor t=inf
        results[-1].beadfriction = friction
        results[-1].bondrateconstant = brc  # in 1/ns
        results[-1].moderelaxationtimes = 1 / (brc * evals[lowev]) + tintern  # [4] equ 2.17
        results[-1].mode_rmsd = l / mu[lowev]**0.5  # [4] equ 2.19
        results[-1].reducedfriction = reducedfriction
        results[-1].costheta = costheta
        results[-1].eigenvalues = evals
        results[-1].mu = mu
        results[-1].l = l
        results[-1].tintern = tintern
        results[-1].N = evec.shape[0]
        results[-1].Rg = l * Rg2_red**0.5
        results[-1].Rg_red = Rg2_red**0.5
        results[-1].modelname = inspect.currentframe().f_code.co_name

    if len(results) == 1:
        return results[0]

    return results


@formel.memoize()
def _ringStructuralMatrix(N):
    """
    Create for a ring the  bstructural matrix for uncorrelated bonds.

    This part is in reduced units that bond length is not used.

    """
    # see references in main function

    A = np.diag([2.]*N) +  np.diag([-1.]*(N-1),-1) + np.diag([-1.]*(N-1),1)
    A[0,-1] = -1
    A[-1,0 ] = -1
    return A


def ringChainORZ(t, q, N=100, l=1, fa=None, Dcm=None, Dcmfkt=None,
                 viscosity=1, T=293, reducedfriction=0.25, tintern=0):
    r"""
    Dynamics of a ring polymer using optimized Rouse-Zimm approximation (ORZ).

    The ring dynamic structure factor is calculated in analogy to the star described by Guenza [1]_.

    The ring chain dynamics is decribed within the more general optimized Rouse-Zimm (ORZ) approximation
    introduced by Bixon and Zwanzig [3]_ [4]_ . See :py:func:`solveOptimizedRouseZimm`.

    We extend this here using bead scattering lengths for partial matching and allow individual bond correlations.

    To speedup fitting use the memoize function as described in :py:func:`~.formel.memoize`.

    Parameters
    ----------
    t : array
        timepoints in units ns.
    q : array
        Scattering vectors in units 1/nm.
    N : int
        Number of beads .
    l : float, default = 0.38 nm (amino acid)
        Bond length or Kuhn length in units nm.
    fa : None, list of float
        Scattering length of bead/monomer :math:`fa_i`. Can be used to match parts of the star to the solvent.

        - None : Equal 1 for all beads.
        - list: length N as scattering length of beads in sequence
    Dcm : float
        Center of mass diffusion in units nm**2/ns.
        If `None` the calculated value D_ORZ is used.
    Dcmfkt : array 2xN, function
        Function f(q) or array with [qi, f(qi) ] as correction for Dcm like Diff = Dcm*f(q).
        e.g. for inclusion of structure factor or hydrodynamic function with f(q)=H(Q)/S(q).
        Missing values are interpolated.
    viscosity : float, default=1 (H2O@20C )
        :math:`\eta` in units cPoise=mPa*s  e.g. water :math:`visc(T=293 K) =1 mPas`
    T : float, default 273+20
        Temperature  in Kelvin.
    reducedfriction : float, default 0.25
        Reduced friction :math:`\zeta_r = \zeta/6\pi\eta_sl` in hydrodynamic tensor H.
         - =0 : free draining limit, no HI, Rouse dynamics.
         - >0 : with HI typically <0.5. For h>0.5 we get negative eigenvalues.

        See :py:func:`solveOptimizedRouseZimm`.

        During fits use ``limits(reducedfriction=[0,0.43,0.,0.5])`` to avoid singular matrices.
    tintern : float>0, default 0
        Relaxation time due to internal friction between neighboring beads in ns.

    Returns
    -------
    sqt : dataList
        Intermediate scattering function of  a star for given q.

        - [times; Sqt; Sqt only diffusion; Sqt cumulant]
        - columnname = 't;Sqt;Sqt_inf;Sqt_cum'
        - .q : scattering vector
        - .D_ORZcum : diffusion coefficinet in initial slope (cumulant)
        - .D_ORZ : translational diffusion ORZ model
        - .Dcm  :  used center of friction/mass diffusion
        - .Fq : form factor
        - .Fq_inf : form factor t=inf
        - .beadfriction : bead friction
        - .bondrateconstant : bondrateconstant in 1/ns
        - .moderelaxationtimes : used moderelaxationtimes in ns [4] equ 2.17
        - .mode_rmsd : used mode rmsd as math:`l/\mu^{0.5}  # [4] equ 2.19
        - .reducedfriction : reducedfriction
        - .eigenvalues : all evals
        - .mu : all mu
        - .l : bondlength l
        - .N : Number of beads
        - .Rg : radius of gyration in nm
        - .Rg_red : reduced radius of gyration

    Notes
    -----
    See :py:func:`solveOptimizedRouseZimm` for a description of the ORZ model with respective parameters and
    the dynamic structure factor :math:`S(q,t)/S(q,0)` .


    Here we use a ring chain with N beads of uncorelated beads with `costheta=0` .

    The structural matrix has diagonal elements, :math:`A_{ii}=2` and :math:`A_{i\neq j}=-1` if the ith and jth monomers
    are connected to each other or zero otherwise.

    Examples
    --------
    Here we examine how HI changes dynamics.
    ::

     import jscatter as js
     import numpy as np

     q= np.r_[0.01,0.1:2:0.2]
     t = np.r_[0:1:0.02,1:20:1,20:100:5]

     p = js.grace()
     p.xaxis(label='t / ns')

     sqt = js.dynamic.ringChainORZ(t, q, 100, l=0.5, reducedfriction=0)
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[1,1,c],sy=0,le=f'{sq.q:.2f} nm\\S-1')

     sqt = js.dynamic.ringChainORZ(t, q, 100, l=0.5, reducedfriction=0.05)
     for c,sq in enumerate(sqt,1):
         p.plot(sq.X,sq._Sqt,li=[3,1,c],sy=0,le='')

     p.yaxis(label='S(Q,t),S(Q,0)',scale='log',min=0.1,max=1)
     p.legend(charsize=0.7)
     p.title('rings with and without HI ')
     p.subtitle('solid: no HI; broken: with HI')

     # p.save(js.examples.imagepath+'/ORZ_ringHI.png',size=(1.5,1.5),dpi=300)

    .. image:: ../../examples/images/ORZ_ringHI.png
     :align: center
     :width: 60 %
     :alt: ORZ eigenvalue and more

    References
    ----------
    .. [1] Static and Dynamic Structure Factors for Star Polymers in θ Conditions.
           Guenza, M. & Perico, A.
           Macromolecules 26, 4196–4202 (1993). https://doi.org/10.1021/ma00068a020
    .. [2] A Local Approach to the Dynamics of Star Polymers.
           Guenza, M., Mormino, M. & Perico, A.
           Macromolecules 24, 6168–6174 (1991). https://doi.org/10.1021/ma00023a018
    .. [3] Theoretical basis for the Rouse‐Zimm model in polymer solution dynamics.
           Zwanzig, R. The Journal of Chemical Physics 60, 2717–2720 (1974) https://doi.org/10.1063/1.1681433
    .. [4] A hierarchy of models for the dynamics of polymer chains in dilute solution.
           Perico, A., Ganazzoli, F. & Allegra, G.
           The Journal of Chemical Physics 87, 3677–3686 (1987). https://doi.org/10.1063/1.452966
    .. [5] Rubinstein, M. & Colby, R. H. Polymer Physics. (OUP Oxford, 2003).
    .. [6] Intramolecular relaxation dynamics in semiflexible dendrimers.
           Kumar, A. & Biswas, P.  Journal of Chemical Physics 134, (2011). https://doi.org/10.1063/1.3598336


    """


    if fa is None:
        fa = np.ones(N)
    assert len(fa) == N, 'fa should be of length N.'
    fa = np.array(fa)
    q = np.atleast_1d(q)

    t0 = np.r_[0,t]

    # bead friction coefficient
    friction = 6 * np.pi * (viscosity*1e-3) * (l * 1e-9)  # l in nm; viscosity in Pa*s

    # bond rate constant brc, sometimes named W
    brc = (3 * kb * T / (l*1e-9)**2 / friction) * 1e-9 # l in nm  # brc is 1/s => *1e-9 in 1/ns
    reducedfriction = max(min(reducedfriction, 1), 0)

    # create correction for diffusion
    if Dcmfkt is not None:
        if formel._getFuncCode(Dcmfkt):
            # is already an interpolation function
            Dcmfunktion = Dcmfkt
        elif np.shape(Dcmfkt)[0] == 2:
            Dcmfunktion = lambda qq: dA(Dcmfkt).interp(qq)
        else:
            raise TypeError('Shape of Dcmfkt is not 2xN!')
    else:
        # by default no correction
        Dcmfunktion = lambda qq: 1.

    # create bond matrix and transfer matrix for a star
    A = _ringStructuralMatrix(N)

    # compute Eigenvectors and Eigenvalues for ORZ in reduced units
    evals, evec, mu, loverR, Rg2_red, Rij2_red2, _ = solveOptimizedRouseZimm(A, reducedfriction)
    if np.any(evals[1:] < 0):
        raise UserWarning(f'There are {np.sum(evals[1:]<0)} negative eigenvalues in ORZ solution. '
                          f'reducedfriction should be smaller.')

    # >95% of computing time in this call for N=100 that already uses omp
    # array dim [Q values x time values+2]
    # first is sqt(0), last element is sum in equation 13 for initial cumulant, second last t=inf
    # first eval is COM diffusion and large eval and large mu dont contribute much
    lowev =  np.r_[[False], (brc * evals[1:] < 15) | (1/mu[1:] > max(0.001/mu[1:]))]
    sqt = fscatter.dynamic.sqtnonlinearpolymer(evec[:,1:], evals[1:], mu[1:], fa, q, t0, l, brc, loverR, tintern)

    # [1] equ 24 for center of mass diffusion
    Dcm_ORZ = kb * T / N / friction * 1e9  # in nm**2/ns
    if reducedfriction>0:
                Dcm_ORZ *= (1 + reducedfriction/N * np.sum(loverR))


    results = dL()
    for i, sqti in enumerate(sqt):
        # calc initial slope diffusion  as first cumulant/q**2  [1] equ 13
        D_cum_ORZ = brc * l**2/3/sqti[0] * (np.sum(fa**2) + reducedfriction * sqti[-1])
        if Dcm is None:
            Dcm = Dcm_ORZ

        results.append(np.c_[t0[1:],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[1:-2]/sqti[0],
                       np.exp(-q[i]**2 * Dcm * Dcmfunktion(q[i]) * t0[1:]) * sqti[-2]/sqti[0],
                       np.exp(-q[i]**2 * (D_cum_ORZ - Dcm + Dcm * Dcmfunktion(q[i])) * t0[1:]) ].T)

        results[-1].setColumnIndex(iey=None)
        results[-1].columnname = 't;Sqt;Sqt_inf;Sqt_cum'

        results[-1].viscosity = viscosity
        results[-1].q = q[i]
        results[-1].D_ORZcum = D_cum_ORZ
        results[-1].D_ORZ = Dcm_ORZ
        results[-1].Dcm = Dcm
        results[-1].Fq = sqti[0] / np.sum(fa)**2  # form factor t=0
        results[-1].Fq_inf = sqti[-2] / np.sum(fa)**2  # form factor t=inf
        results[-1].beadfriction = friction
        results[-1].bondrateconstant = brc  # in 1/ns
        results[-1].moderelaxationtimes = 1 / (brc * evals[lowev]) + tintern # [4] equ 2.17
        results[-1].mode_rmsd = l / mu[lowev]**0.5  # [4] equ 2.19
        results[-1].reducedfriction = reducedfriction
        results[-1].eigenvalues = evals
        results[-1].mu = mu
        results[-1].l = l
        results[-1].tintern = tintern
        results[-1].N = evec.shape[0]
        results[-1].Rg = l * Rg2_red**0.5
        results[-1].Rg_red = Rg2_red**0.5
        results[-1].modelname = inspect.currentframe().f_code.co_name

    if len(results) == 1:
        return results[0]

    return results


def _gauss_norm(x, mean, sigma):
    return np.exp(-0.5 * (x - mean) ** 2 / sigma ** 2) / np.sqrt(2 * pi) / sigma


# noinspection PyIncorrectDocstring
def resolution(t, s0=1, m0=0, s1=None, m1=None, s2=None, m2=None, s3=None, m3=None,
               s4=None, m4=None, s5=None, m5=None, s6=None, m6=None, s7=None, m7=None,
               a0=1, a1=1, a2=1, a3=1, a4=1, a5=1, a6=1, a7=1, bgr=0, resolution=None):
    r"""
    Resolution in time domain as multiple Gaussians for inelastic measurement
    as back scattering or time of flight instrument.

    Multiple Gaussians define the function to describe a resolution measurement.
    Use ```resolution_w``` to fit with the appropriate normalized Gaussians and this function
    to implicit Fourier transform a signal. See Notes.

    Parameters
    ----------
    t : array
        Times
    s0,s1,... : float
        Width of Gaussian functions representing a resolution measurement.
        The number of si not None determines the number of Gaussians.
    m0, m1,.... : float, None
        Means of the Gaussian functions representing a resolution measurement.
    a0, a1,.... : float, None
        Amplitudes of the Gaussian functions representing a resolution measurement.
    bgr : float, default=0
        Background
    resolution : dataArray
        Resolution with attributes sigmas, amps which are used instead of si, ai.
         - If resolution is from `w` domain this represents the Fourier transform from `w` to `t` domain.
           `means` are NOT used from `w` domain as these result only in a phase shift, instead m0..m5 are used.
           If mi is not give zero is assumed.
         - If from `t` domain the resolution is recalculated with same parameters for new t.

    Returns
    -------
        dataArray

    Notes
    -----
    In a typical inelastic experiment the resolution is measured by e.g. a vanadium measurement (elastic scatterer).
    In `t` domain (Neutron Spin Echo) this is a carbon black sample for small Q or e.g. Zirconium for higher Q.
    In `w` domain the resolution is described by a multi Gaussian function as in resw=resolution_w(w,...) with
    amplitudes :math:`ai_w`, width :math:`si_w` and common mean :math:`m_w`.

    resolution(t,resolution_w=resw) defines the Fourier transform of resolution_w using the same coefficients
    as an implicit Fourier transform.
    :math:`mi_t` are set by default to zero as :math:`mi_w` lead only to a phase shift.
    It is easiest to shift w values in w domain as it corresponds to a shift of the elastic line.

    Beside the fitting of resolution measurements the pair of `resolution_w` and `resolution` allows
    a Fourier transform from `w` to `t` domain of any signal. If `resolution_w` is used for fitting
    of data in the `w` domain then ```ft = resolution(t=..,resolution=resolution_w_fit)```
    represents the Fourier transform of the fitted data.

    The used Gaussians are normalized that they are a pair of Fourier transforms:

    .. math:: R_t(t,m_i,s_i,a_i)=\sum_i a_i s_i e^{-\frac{1}{2}s_i^2 t^2} \Leftrightarrow
              R_w(w,m_i,s_i,a_i)= \sum_i a_i e^{-\frac{1}{2}(\frac{w-m_i}{s_i})^2}

    under the Fourier transform defined as

    .. math:: F(f(t)) =  \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{\infty} f(t) e^{-i\omega t} dt

    .. math:: F(f(w)) =  \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{\infty} f(\omega) e^{i\omega t} d\omega


    Examples
    --------
    Using the result of a fit in w domain to represent the resolution in time domain :
    ::

     import jscatter as js
     import numpy as np

     # resw is a resolution in w domain maybe as a result from a fit to vanadium data
     # resw contains all parameters
     w = np.r_[-100:100:0.5]
     resw = js.dynamic.resolution_w(w, s0=12, m0=0, a0=2)

     # representing the Fourier transform of resw as a gaussian transforms to time domain
     t = np.r_[0:1:0.01]
     rest = js.dynamic.resolution(t,resolution=resw)
     t2 = np.r_[0:0.5:0.005]
     rest2 = js.dynamic.resolution(t2,resolution=rest)


    """
    # we keep None to allow change of single Gaussians
    if resolution is None:
        means = [m0, m1, m2, m3, m4, m5, m6, m7]
        sigmas = [s0, s1, s2, s3, s4, s5, s6, s7]
        amps = [a0, a1, a2, a3, a4, a5, a6, a7]
    else:
        if resolution.modelname[-1] == 'w':
            means = [0 if m is None else m for m in [m0, m1, m2, m3, m4, m5, m6, m7]]
            sigmas = [1. / s if s is not None else s for s in resolution.sigmas]
            amps = resolution.amps
        else:
            means = resolution.means
            sigmas = resolution.sigmas
            amps = resolution.amps

    t = np.atleast_1d(t)

    # filter Nones
    sma = np.array([[s, m, a] for s, m, a in zip(sigmas, means, amps) if None not in [s, m, a]]).T
    Y = np.sum(sma[2][:, None] * _gauss_norm(x=t, mean=sma[1][:, None], sigma=sma[0][:, None]), axis=0)

    result = dA(np.c_[t, Y + bgr].T)

    result.setColumnIndex(iey=None)
    result.modelname = inspect.currentframe().f_code.co_name
    result.columnname = 't; Rqt'
    result.means = means
    result.sigmas = sigmas
    result.amps = amps

    return result



