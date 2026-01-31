.. baccoemu documentation master file, created by
   sphinx-quickstart on Tue Jul 14 12:02:47 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to baccoemu's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

``baccoemu`` is a collection of cosmological neural-network emulators for large-scale structure statistics. Specifically, we provide fast predictions for:

- the linear cold- and total-matter power spectrum (`Aricò et al. 2021a <https://arxiv.org/abs/2104.14568>`_, :ref:`tutorial <Tutorial-linear-emulators>`)
- the nonlinear cold-matter power spectrum (`Angulo et al. 2021 <https://arxiv.org/abs/2004.06245>`_, `Aricò et al. 2023 <https://arxiv.org/abs/2303.05537>`_, :ref:`tutorial <Tutorial-nonlinear-emulators>`)
- the modifications to the cold-matter power spectrum caused by baryonic physics  (`Aricò et al. 2021b <https://arxiv.org/abs/2011.15018>`_, :ref:`tutorial <Tutorial-baryon-corrected-Arico2021>`)
- the modifications to the cold-matter power spectrum and bispectrum caused by baryonic physics (`Burger et al. 2025 <https://arxiv.org/abs/2506.18974>`_, :ref:`tutorial <Tutorial-baryon-corrected-Burger2025>`)
- the power spectrum of biased tracers in real space in the context of the hybrid Lagrangian bias expansion (`Zennaro et al. 2023 <https://arxiv.org/abs/2101.12187>`_, :ref:`tutorial <Tutorial-biased-tracers-in-real-space>`)
- the power spectrum of biased tracers in redshift space in the context of the hybrid Lagrangian bias expansion (`Pellejero-Ibáñez et al. 2023 <https://arxiv.org/abs/2207.06437>`_)

in a wide cosmological parameter space, including dynamical dark energy and massive neutrinos. These emulators were developed as part of the
Bacco project -- for more details, visit our `main website <http://bacco.dipc.org>`_.

Our emulators are publicly available under MIT licence; please, follow the links above to be see te corresponding papers on the arXiv website, where you can find all the references to credit our work.

.. note::
   The bacco project is under constant development and new versions of the emulators become available as we improve them. Follow our `public repository <https://bitbucket.org/rangulo/baccoemu/src/master/>`_ to make sure you are always up to date with our latest release.



Installation
============

As a quick summary, you shouldn't need anything more than

::

   pip install baccoemu [--user]

You can also install the development version from `bitbucket <https://bitbucket.org/rangulo/baccoemu/src/master/>`_ by cloning and installing the source

::

   git clone https://bitbucket.org/rangulo/baccoemu.git
   cd baccoemu
   pip install . [--user]

You can then test that the installation was successful:

::

   python -m unittest test.test_baccoemu

It should take a couple of seconds and not return any errors.

.. warning::
   the bacco emulator only works in a
   Python 3 environment; the data file at its core cannot
   be unpickled by Python 2.x; in case your ``pip``
   command doesn't link to a Python 3 pip executable, please
   modify the line above accordingly (e.g. with ``pip3`` instead of ``pip``)

.. note::
   The bacco emulator depends on some external packages, namely

   #. numpy
   #. matplotlib
   #. scipy
   #. jax
   #. h5py
   #. progressbar2

   The installation process will automatically try to install them if they are not already present.

Loading and emulator info
=========================

There are four emulator classes, one for the matter power spectrum emulator (linear and nonlinear), one for the power spectrum of biased tracers in real space, one for biased tracers in redshift space, and one for matter bispectra (for now, only baryonic suppressions).
They can be loaded with

::

    import baccoemu
    mpk_emulator = baccoemu.Matter_powerspectrum()
    lbias_emulator = baccoemu.Lbias_expansion()
    lbias_emulator_RSD = baccoemu.Lbias_expansion_RSD()
    baccoemu.Matter_bispectrum()

Each emulator object holds some very useful information. For example, focusing on the linear emulator, to know the k-range on which the emulator is defined you can type

::

    import baccoemu
    mpk_emulator = baccoemu.Matter_powerspectrum()
    print(mpk_emulator.emulator['linear']['k'])

Similarly, to know the free parameters on which the linear emulator is defined and which is the allowed range of each of them, you can type

::

    for key, bound in zip(mpk_emulator.emulator['linear']['keys'], mpk_emulator.emulator['linear']['bounds']):
        print(key, bound)

By changing ``linear`` to ``nonlinear``, you can find this kind of information for the nonlinear emulator.

The same thing applies to the biased tracers power spectrum emulator and all other emulators, for example

::

    import baccoemu
    lbias_emulator = baccoemu.Lbias_expansion()
    print(lbias_emulator.emulator['nonlinear']['k'])

.. _Tutorial-linear-emulators:

Tutorial linear emulators
=========================

Let's assume you want to evaluate the linear power spectra emulators at a given set of wavemodes and for a given cosmology and redshift. First, you should load baccoemu (and define your wavemodes vector)

::

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum()

    import numpy as np
    k = np.logspace(-2, np.log10(5), num=100)

All the bacco emulators take as an input a set of cosmological parameters. This can be passed as a dictionary, like

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83, # if A_s is not specified
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  1
    }

Please note that ``omega_cold`` and ``sigma8_cold`` refer to the density parameter and linear variance of cold matter (cdm + baryons), which does not correspond to the total matter content in massive neutrino cosmologies. Also note that  ``A_s`` can be specified instead of ``sigma8_cold``, but be aware these parameters are mutually exclusive.

You can evaluate the linear matter power spectrum emulator (for cold matter and total matter) via

::

    k, pk_lin_cold = emulator.get_linear_pk(k=k, cold=True, **params)
    k, pk_lin_total = emulator.get_linear_pk(k=k, cold=False, **params)


.. _Tutorial-nonlinear-emulators:

Tutorial nonlinear emulators
============================

Let's assume you want to evaluate the nonlinear power spectra emulators at a given set of wavemodes and for a given cosmology and redshift. You can choose between ``nonlinear_model_name='Angulo2021'`` (default) or ``nonlinear_model_name='Arico2023'``. First, you should load baccoemu (and define your wavemodes vector)

::

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum()
    # or emulator = baccoemu.Matter_powerspectrum(nonlinear_model_name='Arico2023') for the wider range emulator used in Aricò et al. (2023)

    import numpy as np
    k = np.logspace(-2, np.log10(emulator.emulator['nonlinear']['k'].max()), num=100)

All the bacco emulators take as an input a set of cosmological parameters. This can be passed as a dictionary, like

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83, # if A_s is not specified
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  1
    }

Please note that ``omega_cold`` and ``sigma8_cold`` refer to the density parameter and linear variance of cold matter (cdm + baryons), which does not correspond to the total matter content in massive neutrino cosmologies. Also note that  ``A_s`` can be specified instead of ``sigma8_cold``, but be aware these parameters are mutually exclusive.

You can evaluate the nonlinear boost and the nonlinear matter power spectrum emulator (for cold matter and total matter) via

::

    k, Q_cold = emulator.get_nonlinear_boost(k=k, cold=True, **params)
    k, Q_total = emulator.get_nonlinear_boost(k=k, cold=False, **params)
    k, pk_nl_cold = emulator.get_nonlinear_pk(k=k, cold=True, **params)
    k, pk_nl_total = emulator.get_nonlinear_pk(k=k, cold=False, **params)

These are the nonlinear boost ``Q`` (which, multiplied by the corresponding linear power spectrum gives the nonlinear power spectrum), the emulated linear power spectrum ``pk`` and the emulated nonlinear power spectrum ``pknl``. We can have a look at them

::

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1,2, figsize=(10,5))
    ax[0].loglog(k, Q_cold)
    ax[1].loglog(k, pk_lin, label="Linear Power Spectrum")
    ax[1].loglog(k, pk_nl_cold, label="Nonlinear Power Spectrum")
    ax[0].set_xlabel("k [h/Mpc]"); ax[1].set_xlabel("k [h/Mpc]");
    ax[0].set_ylabel("Q"); ax[1].set_ylabel("P(k)");
    plt.legend()

.. image:: baccoemu.png
  :width: 700


Note that to get the nonlinear power spectrum, baccoemu will internally multiply the boost factor ``Q`` by the emulated linear power spectrum. If you want to use another linear power spectrum, you can pass it via

::

    k, pknl = emulator.get_nonlinear_pk(params, k=k, baryonic_boost=False, k_lin=your_k, pk_lin=your_linear_pk)


.. _Tutorial-baryon-corrected-Arico2021:

Tutorial baryon-corrected power spectrum emulator, Aricò et al. (2021)
======================================================================

First, you should load baccoemu (and define your wavemodes vector)

::

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum()

    import numpy as np
    k = np.logspace(-2, np.log10(emulator.emulator['nonlinear']['k'].max()), num=100)

When baryonic corrections are required, the parameter dictionary must include the relevant parameters, such as

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83,
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  1,

        'M_c'           :  14,
        'eta'           : -0.3,
        'beta'          : -0.22,
        'M1_z0_cen'     : 10.5,
        'theta_out'     : 0.25,
        'theta_inn'     : -0.86,
        'M_inn'         : 13.4
    }

In this case, the baryonic boost is obtained through

::

    k, S = emulator.get_baryonic_boost(k=k, **params)


which is defined as the ratio between the power spectrum under the effect of baryons to that considering only gravitational forces.
Finally, the nonlinear matter power spectrum with baryonic effects can be obtained with

::

   k, pknl = emulator.get_nonlinear_pk(k=k, baryonic_boost=True, **params)

We note that baryonic_boost is using the Arico et al. (2021) baryonic correction.

We can display them both:

::

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1,2, figsize=(10,5))
    ax[0].semilogx(ks, S)

    ax[1].loglog(knl, pk, label="Linear P(k)")
    ax[1].loglog(knl, pknl, label="Nonlinear P(k)")
    ax[1].loglog(knl, pknl_b, label="Nonlinear P(k) & Baryons")

    ax[0].set_xlabel("k [h/Mpc]"); ax[1].set_xlabel("k [h/Mpc]");

    ax[0].set_ylabel(r"$S=P_{\rm baryons}/P_{\rm gravity\,only}$"); ax[1].set_ylabel("$P(k)\,[h^{-3}\,\mathrm{Mpc}^{3}]$");
    plt.legend()


.. image:: baccoemu_bcm.png
  :width: 700

.. _Tutorial-baryon-corrected-Burger2025:

Tutorial baryon-corrected power spectrum emulator, Burger et al. (2025)
=======================================================================

First, you should load baccoemu (and define your wavemodes vector)

::

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum(baryonic_model_name='Burger2025')

    import numpy as np
    k = np.logspace(-2, np.log10(emulator.emulator['nonlinear']['k'].max()), num=100)

When baryonic corrections are required, the parameter dictionary must include the relevant parameters, such as

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83,
        'omega_baryon'  :  0.05,
        'expfactor'     :  1,

        'M_c'           :  14,
        'eta'           : -0.3,
        'beta'          : -0.22,
        'M1_z0_cen'     : 10.5,
        'theta_inn'     : -0.86,
    }

In this case, the baryonic boost is obtained through

::

    k, S, extrapolation_flags = emulator.get_baryonic_boost(k=k, **params)


which is defined as the ratio between the power spectrum under the effect of baryons to that considering only gravitational forces.
The extrapolation_flags tells you now where the emulator extrapolated to `k` values that are wither larger or smaller than the trained `k`-values.
We note that this emualtor has fixed 'theta_out' and 'M_inn' (see the :ref:`Parameter-space` section below for more details).


Tutorial baryon-corrected bispectrum emulator, Burger et al. (2025)
===================================================================

First, you should load baccoemu (and define your wavemodes vector)

::

    import baccoemu
    emulator = baccoemu.Matter_bispectrum()

    import numpy as np
    k1 = np.logspace(-2, 20, num=100)
    k2 = np.logspace(-2, 20, num=100)
    k3 = np.logspace(-2, 20, num=100)

When baryonic corrections are required, the parameter dictionary must include the relevant parameters, such as

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83,
        'omega_baryon'  :  0.05,
        'expfactor'     :  1,

        'M_c'           :  14,
        'eta'           : -0.3,
        'beta'          : -0.22,
        'M1_z0_cen'     : 10.5,
        'theta_inn'     : -0.86,
    }

In this case, the baryonic boost is obtained through

::


    k, R, extrapolation_flags  = emulator.get_baryonic_boost(k1=k1, k3=k3, k3=k3, **params)


which is defined as the ratio between the power spectrum under the effect of baryons to that considering only gravitational forces.
The extrapolation_flags tells you now where the emulator extrapolated to `k` values that are wither larger or smaller than the trained `k`-values.
We note that this emualtor has fixed 'theta_out' and 'M_inn' (see the :ref:`Parameter-space` section below for more details).



.. _Tutorial-biased-tracers-in-real-space:


Tutorial biased tracers in real space
=====================================

The biased tracers power spectrum emulator is loaded with (including accessing to its k vector)

::

    import baccoemu
    emulator = baccoemu.Lbias_expansion()

    import numpy as np
    k = np.logspace(-2, np.log10(emulator.emulator['nonlinear']['k'].max()), num=100)

The cosmological parameters are specified in the same way as for the other emulators

::

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83, # if A_s is not specified
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  1
    }

In this case we can obtain the 15 terms needed for reconstructing the biased tracers power spectrum with

::

    k, pnn = emulator.get_nonlinear_pnn(k=k, **params)

Here ``pnn`` is a list of 15 power spectra (each of length ``len(k)``) corresponding to the terms :math:`11`, :math:`1\delta`, :math:`1\delta^2`, :math:`1s^2`, :math:`1\nabla^2\delta`, :math:`\delta \delta`, :math:`\delta \delta^2`, :math:`\delta s^2`, :math:`\delta \nabla^2\delta`,  :math:`\delta^2 \delta^2`, :math:`\delta^2 s^2`, :math:`\delta^2 \nabla^2\delta`, :math:`s^2 s^2`, :math:`s^2 \nabla^2\delta`, :math:`\nabla^2\delta \nabla^2\delta`.

Alternatevely, instead of manually combining these terms, one can get the galaxy-galaxy and galaxy-matter power spectra by specifying the bias parameters and using the following method

::

    bias_params = [0.75, 0.25, 0.1, 1.4] # b1, b2, bs2, blaplacian
    k, p_gg, p_gm = emulator.get_galaxy_real_pk(bias=bias_params, k=k, **params)

Note that this does not include any stocastic noise, so the user shoud add it manually to the ``p_gg`` vector.

.. _Vectorized-usage:

Vectorized usage
================

You can evaluate the baccoemu emulators at many coordinates at the same time. For the vectorized version of baccoemu, you can vary one or more parameters at the same time.

In the first case, you will have to define the parameters as

::

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum()

    import numpy as np
    k = np.logspace(-2, np.log10(5), num=100)

    params = {
        'omega_cold'    :  0.315,
        'sigma8_cold'   :  0.83, # if A_s is not specified
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  np.linspace(0.5, 1, 10)
    }

    k, pk_i = emulator.get_nonlinear_pk(k=k, **params)

In the second case you will have to pass you parameters like

::

    import numpy as np
    k = np.logspace(-2, np.log10(5), num=100)

    import baccoemu
    emulator = baccoemu.Matter_powerspectrum()

    params = {
        'omega_cold'    :  [ 0.315, 0.27],
        'sigma8_cold'   :  [ 0.83,  0.83],
        'omega_baryon'  :  [ 0.05,  0.04],
        'ns'            :  [ 0.96,  0.98],
        'hubble'        :  [ 0.67,  0.73],
        'neutrino_mass' :   0.0,
        'w0'            :  -1.0,
        'wa'            :   0.0,
        'expfactor'     :  [ 0.5,   1.0]
    }

    k, pk_i = emulator.get_nonlinear_pk(k=k, **params)

Note that not all the parameters have to be varied (you can keep one or more fixed), but the ones that are varied must have the same array length.

The vectorised usage is available for all of our emulators, linear and nonlinear power spectrum, and biased tracers power spectra.


.. _Parameter-space:

Parameter space
===============

The parameters used for the different emulators must be enclosed within the following boundaries

**linear cold and total matter spectrum emulator**

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_cold``     | 0.15        | 0.6         | :math:`\Omega_{cb} = \Omega_{cdm} + \Omega_{b}` (cdm+baryons) |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_baryon``   | 0.03        | 0.07        | :math:`\Omega_{b}`                                            |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``A_s``            | any         | any         | :math:`A_s`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``sigma8_cold``    | any         | any         | :math:`\sigma_{8,cb}` (cdm+baryons)                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``ns``             | any         | any         | :math:`n_s`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``hubble``         | 0.5         | 0.9         | :math:`h = H_0/100`                                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``neutrino_mass``  | 0           | 0.5         | :math:`M_\nu = \sum m_{\nu,i} [\mathrm{eV}]`                  |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``w0``             | -1.3        | -0.7        | :math:`w_0`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``wa``             | -0.5        | 0.5         | :math:`w_a`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``expfactor``      | 0.25        | 1           | :math:`a = 1 / (1 + z)`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [10^{-4}, 50]\,\, h \,\, \mathrm{Mpc}^{-1}`

**nonlinear matter power spectrum emulator**

For ``nonlinear_model_name='Angulo2021'``:

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_cold``     | 0.23        | 0.4         | :math:`\Omega_{cb} = \Omega_{cdm} + \Omega_{b}` (cdm+baryons) |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_baryon``   | 0.04        | 0.06        | :math:`\Omega_{b}`                                            |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``sigma8_cold``    | 0.73        | 0.9         | :math:`\sigma_{8,cb}` (cdm+baryons)                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``ns``             | 0.92        | 1.01        | :math:`n_s`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``hubble``         | 0.6         | 0.8         | :math:`h = H_0/100`                                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``neutrino_mass``  | 0           | 0.4         | :math:`M_\nu = \sum m_{\nu,i} [\mathrm{eV}]`                  |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``w0``             | -1.15       | -0.85       | :math:`w_0`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``wa``             | -0.3        | 0.3         | :math:`w_a`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``expfactor``      | 0.4         | 1           | :math:`a = 1 / (1 + z)`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [10^{-2}, 5] \,\, h \,\, \mathrm{Mpc}^{-1}`

For ``nonlinear_model_name='Arico2023'``:

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_cold``     | 0.15        | 0.47        | :math:`\Omega_{cb} = \Omega_{cdm} + \Omega_{b}` (cdm+baryons) |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_baryon``   | 0.03        | 0.07        | :math:`\Omega_{b}`                                            |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``sigma8_cold``    | 0.4         | 1.15        | :math:`\sigma_{8,cb}` (cdm+baryons)                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``ns``             | 0.83        | 1.1         | :math:`n_s`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``hubble``         | 0.5         | 0.9         | :math:`h = H_0/100`                                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``neutrino_mass``  | 0           | 0.4         | :math:`M_\nu = \sum m_{\nu,i} [\mathrm{eV}]`                  |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``w0``             | -1.4        | -0.6        | :math:`w_0`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``wa``             | -0.5        | 0.5         | :math:`w_a`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``expfactor``      | 0.275       | 1           | :math:`a = 1 / (1 + z)`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [10^{-2}, 10] \,\, h \,\, \mathrm{Mpc}^{-1}`

**baryonic boost emulator, Arico et al. (2021)**

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``M_c``            | 9           | 15          | :math:`\log_{10}[M_{\rm c} / (M_\odot/h)]`                    |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``eta``            | -0.69       | 0.69        | :math:`\log_{10}[\eta]`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``beta``           | -1          | 0.69        | :math:`\log_{10}[\beta]`                                      |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``M1_z0_cen``      | 9           | 13          | :math:`\log_{10}[M_{z_0,\mathrm{cen}} / (M_\odot/h)]`         |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``theta_out``      | 0           | 0.47        | :math:`\log_{10}[\vartheta_{\rm out}]`                        |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``theta_inn``      | -2          | -0.52       | :math:`\log_{10}[\vartheta_{\rm inn}]`                        |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``M_inn``          | 9           | 13.5        | :math:`\log_{10}[M_{\rm inn} / (M_\odot/h)]`                  |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [10^{-2}, 5] \,\, h \,\, \mathrm{Mpc}^{-1}`


**baryonic boost emulator, Burger et al. (2025)**

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_cold``     | 0.23        | 0.4         | :math:`\Omega_{cb} = \Omega_{cdm} + \Omega_{b}` (cdm+baryons) |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_baryon``   | 0.04        | 0.06        | :math:`\Omega_{b}`                                            |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``sigma8_cold``    | 0.73        | 0.9         | :math:`\sigma_{8,cb}` (cdm+baryons)                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``M_c``            | 10          | 16          | :math:`\log_{10}[M_{\rm c} / (M_\odot/h)]`                    |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``eta``            | -0.7        | 0.2         | :math:`\log_{10}[\eta]`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``beta``           | -1          | 0.7         | :math:`\log_{10}[\beta]`                                      |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``M1_z0_cen``      | 9           | 13          | :math:`\log_{10}[M_{z_0,\mathrm{cen}} / (M_\odot/h)]`         |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``theta_inn``      | -2          | 0.0         | :math:`\log_{10}[\vartheta_{\rm inn}]`                        |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [0.017, 17.655] \,\, h \,\, \mathrm{Mpc}^{-1}`, :math:`\theta_\mathrm{out} = 0`, :math:`M_\mathrm{inn} = 2.3 \times 10^{13}\, h^{-1} \, M_\odot`

**biased tracers real space power spectrum emulator**

+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_cold``     | 0.23        | 0.4         | :math:`\Omega_{cb} = \Omega_{cdm} + \Omega_{b}` (cdm+baryons) |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``omega_baryon``   | 0.04        | 0.06        | :math:`\Omega_{b}`                                            |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``sigma8_cold``    | 0.73        | 0.9         | :math:`\sigma_{8,cb}` (cdm+baryons)                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``ns``             | 0.92        | 1.01        | :math:`n_s`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``hubble``         | 0.6         | 0.8         | :math:`h = H_0/100`                                           |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``neutrino_mass``  | 0           | 0.4         | :math:`M_\nu = \sum m_{\nu,i} [\mathrm{eV}]`                  |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``w0``             | -1.15       | -0.85       | :math:`w_0`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``wa``             | -0.3        | 0.3         | :math:`w_a`                                                   |
+--------------------+-------------+-------------+---------------------------------------------------------------+
| ``expfactor``      | 0.4         | 1           | :math:`a = 1 / (1 + z)`                                       |
+--------------------+-------------+-------------+---------------------------------------------------------------+

:math:`k \in [10^{-2}, 0.71] \,\, h \,\, \mathrm{Mpc}^{-1}`

Complete API
============

.. autoclass:: baccoemu.Matter_powerspectrum
    :members:
.. autoclass:: baccoemu.Matter_bispectrum
    :members:
.. autofunction:: baccoemu.baryonic_boost.get_baryon_fractions
.. autoclass:: baccoemu.Lbias_expansion
    :members:
.. autoclass:: baccoemu.Lbias_expansion_RSD
    :members: