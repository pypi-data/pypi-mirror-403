.. :changelog:

History
-------------

[Unreleased]
============

- Emulator of 15 cross-spectra defining a 2nd-order bias expansion, as computed with N-body simulations

2.1.0 (2021-12-1)
=================
Added
+++++
- Emulator of 15 cross-spectra defining a 2nd-order bias expansion, as computed with Lagrangian Perturbation Theory


Fixed
+++++
- Fixed a bug in the nonlinear emulator related to the BAO smearing. The datafile has been change and now version 1.0.1 is used by default.
- bug fix for emulator calls with sigma8_cold, and for multiple values of sigma8

Removed
+++++++
- Deprecated function _bacco_evaluate_emulator() and outdated comments


2.0.0 (2021-11-17)
==================
Added
+++++
- New Neural network (NN) emulator for total and cold matter linear power spectrum
- New NN emulator for the nonlinear smearing of the BAO feature in the linear power spectrum
- New emulator for the relation between the amplitude of the primordial power spectrum, As, and the RMS fluctuations in 8 Mpc/h spheres, sigma8.
- New emulator for the impact of baryons on the power spectrum via the Baryonic Correction Model (BCM)
- New function get_baryon_fractions() to obtain the gas/star mass fraction in halos for a given BCM model
- Linear neutrino term to compute the non-linear total matter power spectrum
- Script to measure the performance of the emulator
- More safety checks on input parameters

Changed
+++++++
- The input parameters are now passed as named arguments (instead of a dictionary)
- The emulators now accept an array of cosmologies, which can speed up significantly the execution time
- sigma8 is now sigma8_cold to make explicit they refer to quantities defined for the cold matter power spectrum.
- omega_matter is now omega_cold to make explicit it refers to the density of cold matter (baryons and cold dark matter, without including massive neutrinos).
- Omega_matter, if passed, refers to the density of baryons, cold dark matter, and massive neutrinos
- Updated documentation

Removed
+++++++
- The option of emulating the nonlinear power spectrum with Gaussian Processes GP emulation
- Support for python 2.x

Fixed
+++++
- Several bugs fixed related to the smearing of the BAO peak, and the call of linear pk with massive neutrinos, and to the documentation


1.1.1 (2020-7-14)
====================

Added
+++++
- Reimplemented dewiggling using real space procedure
- New version of NN and GP emulators


0.9 (2020-7-9)
==================

Added
+++++

- New computation of dewiggled power spectrum and smeared-BAO power spectrum
- Updated GP emulator
- Nonlinear pk now defined with respect to the smeared bao pk
- Added possibility to choose neural network as an emulator

Fixed
+++++

- Fixes in the definition of requested redshift and in the obtaining of sigma_8_z0 of the cold component from camb


0.3 (2020-4-15)
==================

- Initial release


