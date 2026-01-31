#!/usr/bin/env python3

# # SrTiO<sub>3</sub>

# In this example, we extract the self-energies and Eliashberg function from  
# a 2DEL in the $d_{xy}$ bands on the $\rm{TiO}_{2}$-terminated surface of  
# $\rm{SrTiO}_3$.

import matplotlib as mpl
mpl.use('Qt5Agg')

# Necessary packages
import xarpes
import matplotlib.pyplot as plt
import os

# Default plot configuration from xarpes.plotting.py
xarpes.plot_settings('default')

script_dir = xarpes.set_script_dir()

dfld = 'data_sets' # Folder containing the data
flnm = 'STO_2_0010STO_2_' # Name of the file
extn = '.ibw' # Extension of the file

data_file_path = os.path.join(script_dir, dfld, flnm + extn)

# The following cell instantiates band map class object based on the Igor Binary Wave (ibw) file. The subsequent cell illustrates how a band map object could be instantiated with NumPy arrays instead. Only one of the cells will have to be executed to populate the band map object.


fig = plt.figure(figsize=(8, 5)); ax = fig.gca()

bmap = xarpes.BandMap.from_ibw_file(data_file_path, energy_resolution=0.01,
                      angle_resolution=0.2, temperature=20)

bmap.shift_angles(shift=-0.57)

fig = bmap.plot(abscissa='angle', ordinate='kinetic_energy', ax=ax)


# import numpy as np

# intensities= np.load(os.path.join(dfld, "STO_2_0010STO_2_intensities.npy"))
# angles = np.load(os.path.join(dfld, "STO_2_0010STO_2_angles.npy"))
# ekin = np.load(os.path.join(dfld, "STO_2_0010STO_2_ekin.npy"))

# bmap = xarpes.BandMap.from_ibw_file(data_file_path, energy_resolution=0.01,
#                       angle_resolution=0.2, temperature=20)

# bmap.shift_angles(shift=-0.57)

# fig = plt.figure(figsize=(8, 5)); ax = fig.gca()

# fig = bmap.plot(abscissa='angle', ordinate='kinetic_energy', ax=ax)


fig = bmap.fit_fermi_edge(hnuminPhi_guess=42.24, background_guess=1e4,
                          integrated_weight_guess=1e6, angle_min=-5,
                          angle_max=5, ekin_min=42.22, ekin_max=42.3,
                          show=True, title='Fermi edge fit')

print('The optimised h nu - Phi = ' + f'{bmap.hnuminPhi:.4f}' + ' +/- '
      + f'{bmap.hnuminPhi_std:.4f}' + ' eV.')


k_0 = -0.0014 # 0.02
theta_0 = 0

guess_dists = xarpes.CreateDistributions([
xarpes.Constant(offset=600),
xarpes.SpectralQuadratic(amplitude=3800, peak=-2.45, broadening=0.00024,
            center_wavevector=k_0, name='Inner_band', index='1'),
xarpes.SpectralQuadratic(amplitude=1800, peak=-3.6, broadening=0.0004,
            center_wavevector=k_0, name='Outer_band', index='2')
])

import numpy as np

mat_el = lambda x: np.sin(np.deg2rad(x - theta_0)) ** 2

mat_args = {}

energy_range = [-0.1, 0.003]
angle_min = 0.0
angle_max = 4.8

mdcs = xarpes.MDCs(*bmap.mdc_set(angle_min, angle_max, energy_range=energy_range))

fig = plt.figure(figsize=(7, 5)); ax = fig.gca()

fig = mdcs.visualize_guess(distributions=guess_dists, matrix_element=mat_el,
                           matrix_args=mat_args, energy_value=-0.000, ax=ax)

# **Note on interactive figures**
# - The interactive figure might not work inside the Jupyter notebooks, despite our best efforts to ensure stability.
# - As a fallback, the user may switch from "%matplotlib widget" to "%matplotlib qt", after which the figure should pop up in an external window.
# - For some package versions, a static version of the interactive widget may spuriously show up inside other cells. In that case, uncomment the #get_ipython()... line in the first cell for your notebooks.


fig = plt.figure(figsize=(8, 6)); ax = fig.gca()

fig = mdcs.fit_selection(distributions=guess_dists, matrix_element=mat_el, 
                         matrix_args=mat_args, ax=ax)

# **Note on interactive figures**
# - The user has to explicitly assign the peaks as left-hand or right-hand side.  
# - In theory, one could incorporate such information in a minus sign of the peak position.  
# - However, this would also require setting boundaries for the fitting range.  
# - Instead, the user is advised to carefully check correspondence of peak maxima with MDC fitting results.

self_energy = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Inner_band_1', 
                                bare_mass=0.58997502, fermi_wavevector=0.1411192, side='right'))

self_two = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Outer_band_2',
                                bare_mass=0.6, fermi_wavevector=0.207))

self_two.side='right'


self_energies = xarpes.CreateSelfEnergies([self_energy, self_two])

fig = plt.figure(figsize=(8, 5)); ax = fig.gca()

fig = bmap.plot(abscissa='momentum', ordinate='kinetic_energy', 
                plot_dispersions='domain', 
                self_energies=self_energies, ax=ax)


fig = plt.figure(figsize=(9, 6)); ax = fig.gca()

self_energy.plot_both(ax=ax, show=False, fig_close=False)
self_two.plot_both(ax=ax, show=False, fig_close=False)

plt.legend(); plt.show()


guess_dists = xarpes.CreateDistributions([
xarpes.Constant(offset=600),

xarpes.SpectralQuadratic(amplitude=8, peak=2.45, broadening=0.00024,
            center_wavevector=k_0, name='Inner_nm', index='1'),

xarpes.SpectralQuadratic(amplitude=8, peak=3.6, broadening=0.0004,
            center_wavevector=k_0, name='Outer_nm', index='2')
])

energy_range = [-0.1, 0.003]
angle_min=-5.0
angle_max=0.0

mdcs = xarpes.MDCs(*bmap.mdc_set(angle_min, angle_max, energy_range=energy_range))

fig = plt.figure(figsize=(8, 6)); ax = fig.gca()

fig = mdcs.visualize_guess(distributions=guess_dists, ax=ax, energy_value=0)


fig = plt.figure(figsize=(8, 6)); ax = fig.gca()

fig = mdcs.fit_selection(distributions=guess_dists, ax=ax)

self_three = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Inner_nm_1', side='left',
                                bare_mass=0.5, fermi_wavevector=0.142))

self_four = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Outer_nm_2', side='left',
                                bare_mass=0.62, fermi_wavevector=0.207))


fig = plt.figure(figsize=(12, 6))
ax = fig.gca()

self_total = xarpes.CreateSelfEnergies([
    self_energy, self_two,
    self_three, self_four
])

fig = bmap.plot(abscissa='momentum', ordinate='electron_energy', ax=ax, 
                self_energies=self_total, plot_dispersions='domain')


guess_dists = xarpes.CreateDistributions([
xarpes.Constant(offset=600),
xarpes.SpectralQuadratic(amplitude=3600, peak=-2.45, broadening=0.00024,
            center_wavevector=k_0, name='Inner_left', index='5'),
xarpes.SpectralQuadratic(amplitude=1800, peak=-3.6, broadening=0.0004,
            center_wavevector=k_0, name='Outer_left', index='6')
])

mat_el = lambda x: np.sin(np.deg2rad(x - theta_0)) ** 2

mat_args = {}

energy_range = [-0.1, 0.003]
angle_min=-5.0
angle_max=0.0


mdcs = xarpes.MDCs(*bmap.mdc_set(angle_min, angle_max, energy_range=energy_range))

fig = plt.figure(figsize=(7, 5)); ax = fig.gca()

fig = mdcs.visualize_guess(distributions=guess_dists, matrix_element=mat_el,
                           matrix_args=mat_args, energy_value=0.000, ax=ax)


fig = plt.figure(figsize=(8, 6)); ax = fig.gca()

fig = mdcs.fit_selection(distributions=guess_dists, matrix_element=mat_el, 
                         matrix_args=mat_args, ax=ax)

self_five = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Inner_left_5',
                                bare_mass=0.59521794, fermi_wavevector=0.141069758, side='left'))

self_six = xarpes.SelfEnergy(*mdcs.expose_parameters(select_label='Outer_left_6', 
                                bare_mass=0.58997502, fermi_wavevector=0.1411192, side='left'))

self_five.plot_both()


spectrum, model = self_energy.extract_a2f(omega_min=0.5, omega_max=120, omega_num=250, omega_I=20,
                                omega_M=100, omega_S=1.0, alpha_min=0.0,
                                alpha_max=8.0, alpha_num=10, parts='both',
                                ecut_left=3.0, h_n=0.0741008, impurity_magnitude=16.475007)

spectrum_left, _, = self_five.extract_a2f(omega_min=0.5, omega_max=120, omega_num=250, omega_I=20,
                                omega_M=100, omega_S=1.0, alpha_min=0.0,
                                alpha_max=8.0, alpha_num=10, parts='both',
                                ecut_left=3.0, h_n=0.0743720, impurity_magnitude=15.882396)

omega_range = np.linspace(0.5, 120, 250)
plt.figure(figsize=(7, 4))
plt.xlim([-120, 0]); plt.ylim([0, 0.6])
plt.xlabel(r'$\omega$ (meV)'); plt.ylabel(r'$\alpha^2F_n(\omega)~(-)$')
plt.plot(-omega_range, model, color='darkgoldenrod', linestyle='-.')
plt.plot(-omega_range, spectrum, color='tab:blue', linewidth=2, label='Inner right', zorder=10)
plt.plot(-omega_range, spectrum_left, color='tab:red', linewidth=2, label='Inner left')
plt.legend(); plt.show()

cost, spectrum, model, alpha_select, params = self_energy.bayesian_loop(omega_min=0.5,
            omega_max=120, omega_num=250, omega_I=20, omega_M=100, omega_S=1.0,
            alpha_min=0.0, alpha_max=8.0, alpha_num=10, method='chi2kink',
            parts='both', ecut_left=3, iter_max=1e4, t_criterion=1e-8,
            power=4, bare_mass = 0.5939648580991967, fermi_wavevector = 0.14096599149347405,
            h_n = 0.14453652120992496, impurity_magnitude = 16.472274264782957, lambda_el = 6.40542820041109e-07,
            vary=("impurity_magnitude", "lambda_el", "fermi_wavevector", "bare_mass", 
                "h_n"), scale_imp=1.0, scale_lambda_el=1.0, scale_kF=0.1, scale_mb=1.0, scale_hn=1.0)

# Optimised parameters:
#   fermi_velocity = 2.8590279150001967
#   fermi_wavevector = 0.3580104700929503
#   h_n = 0.13784830295580716
#   impurity_magnitude = 120.90250207340154
#   lambda_el = 2.4801500927868874e-08

plt.figure(figsize=(9, 5))
plt.xlim([0, 250]); plt.ylim([0, 0.5])
# plt.xlabel(r'$\omega$ (meV)')
plt.ylabel(r'$\alpha^2F_n(\omega)~(-)$')
plt.plot(spectrum[::-1])
plt.show()


