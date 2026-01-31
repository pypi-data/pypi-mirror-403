import os, sys
import numpy as np
#import matplotlib.pyplot as pl

from prospect.sources import FastStepBasis, StepSFHBasis


agelims = [0.0,8.0,8.5,9.0,9.5,9.8,10.14]
agebins = np.array([agelims[:-1], agelims[1:]])
dt = np.diff(10**agebins, axis=0)
mformed = dt * np.exp(-10**agebins.mean(axis=0)/3e9)


params = {}
params['agebins'] = agebins.T
params['mass'] = mformed
params['zred'] = 0.0
params['mass_units'] = 'mformed'
params['sfh'] = 0

sps = FastStepBasis(zcontinuous=1)
fs, fp, fx = sps.get_spectrum(**params)
#fs, fp, fx = sps.get_spectrum(logzsol=np.random.uniform(-1, 0), **params)


sps = StepSFHBasis(zcontinuous=1)
ss, sp, sx = sps.get_spectrum( **params)

fig, axes = pl.subplots(2, 1)
axes[0].plot(sps.ssp.wavelengths, ss, label='old')
axes[0].plot(sps.ssp.wavelengths, fs, label='new')

axes[1].plot(sps.ssp.wavelengths, ss/fs - 1, label='(old-new)/new')

[ax.set_xlim(1e3, 2e4) for ax in axes.flat]
[ax.set_xscale('log') for ax in axes.flat]

fig.show()
sys.exit()

fn = os.path.join(os.environ['SPS_HOME'], 'data/sfh.dat')
age, sfr, z = np.genfromtxt(fn, unpack=True, skip_header=0)
sps.ssp.params['sfh'] = 3
sps.ssp.set_tabular_sfh(age, sfr)
w, spec = sps.ssp.get_spectrum(tage=0)

bt, bsfr, tmax = sps.convert_sfh(params['agebins'], params['mass'])
sps.ssp.set_tabular_sfh(bt, bsfr)
w, spec = sps.ssp.get_spectrum(tage=0)
