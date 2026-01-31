import numpy as np
import copy
import pickle
import os
import itertools
import time
import copy
from scipy.special import legendre
from .utils import _transform_space, MyProgressBar, load_model, \
    pkmulti, StandardScalerSimplified
from scipy import interpolate

__all__ = ["Lbias_expansion_RSD"]


class Lbias_expansion_RSD(object):
    """
    A class to load and call baccoemu for the Lagrangian bias expansion terms
    in redshift space. By default, the z-space nonlinear Lagrangian bias
    expansion terms emulator (described in Pellejero-Ibáñez et al, 2023) is
    loaded, along with an emulator of velocileptor (Chen et al, 2021)
    predictions used internally.

    :param lpt: whether to load the LPT emulator, defaults to True
    :type lpt: boolean, optional
    :param compute_sigma8: whether to load the sigma8 emulator, defaults
                           to True
    :type compute_sigma8: boolean, optional
    :param smeared_bao: whether to load the smeared bao, defaults to True
    :type smeared_bao: boolean, optional
    :param nonlinear_boost: whether to load the nonlinear boost emulator,
                            defaults to True
    :type nonlinear_boost: boolean, optional
    :param compute_sigma8: whether to load the sigma8 emulator, defaults
                           to True
    :type compute_sigma8: boolean, optional
    :param verbose: whether to activate the verbose mode, defaults to True
    :type verbose: boolean, optional

    """
    def __init__(self, lpt=True, smeared_bao=True, nonlinear_boost=True,
                 nonlinear_emu_path=None, nonlinear_emu_details=None,
                 lpt_folder=None, smeared_bao_folder=None,
                 compute_sigma8=True, verbose=True):

        self.verbose = verbose

        self.compute_lpt = True if lpt else False
        self.compute_smeared_bao = True if smeared_bao else False

        self.cosmo_keys = np.array(['omega_cold', 'sigma8_cold',
                                    'omega_baryon', 'ns',
                                    'hubble', 'neutrino_mass',
                                    'w0', 'wa', 'expfactor'])

        self.lb_term_labels = [r'$1 1$', r'$1 \delta$', r'$1 \delta^2$',
                               r'$1 s^2$', r'$ 1 \nabla^2\delta$',
                               r'$\delta \delta$', r'$\delta \delta^2$',
                               r'$\delta s^2$', r'$\delta \nabla^2\delta$',
                               r'$\delta^2 \delta^2$', r'$\delta^2 s^2$',
                               r'$\delta^2 \nabla^2\delta$',
                               r'$s^2 s^2$', r'$s^2 \nabla^2\delta$',
                               r'$\nabla^2\delta \nabla^2\delta$']

        self.emulator = {}
        if self.compute_lpt:
            self.emulator['lpt'] = load_lpt_emu(folder=lpt_folder)

        if self.compute_smeared_bao:
            self.emulator['smeared_bao'] = load_smeared_bao_emu(folder=smeared_bao_folder)

        self.compute_nonlinear_boost = True if nonlinear_boost else False
        if self.compute_nonlinear_boost:
            self.emulator['nonlinear'] = load_nonlinear_lbias_emu(
                nonlinear_emu_path=nonlinear_emu_path,
                nonlinear_emu_details=nonlinear_emu_details,
            )

        self.compute_sigma8 = True if compute_sigma8 else False

        if self.compute_sigma8:
            from .matter_powerspectrum import Matter_powerspectrum
            self.matter_powerspectrum_emulator = Matter_powerspectrum(
                linear=False, smeared_bao=False,
                nonlinear_boost=False, baryonic_boost=False,
                compute_sigma8=True, verbose=verbose)

    def _get_parameters(self, coordinates, which_emu, grid=None):
        """
        Function that returns a dictionary of cosmological parameters,
        computing derived cosmological parameters, if not
        already present in the given coordinates, and checking the relevant
        boundaries.
        :param coordinates: a set of coordinates in parameter space
        :type coordinates: dict
        :param which_emu: kind of emulator: options are 'linear', 'nonlinear',
                          'baryon','smeared_bao','sigma8'
        :type which_emu: str
        :param grid: dictionary with parameter and vector of values where to
                     evaluate the emulator, defaults to None
        :type grid: array_like, optional
        :return: coordinates with derived parameters
        :rtype: dict
        """
        coordinates = {key: np.atleast_1d(coordinates[key]) for key in set(
            list(coordinates.keys())) - set(['k', 'k_lin', 'pk_lin'])}

        avail_pars = [coo for coo in coordinates.keys(
        ) if coordinates[coo][0] is not None]  # parameters currently available
        # parameters strictly needed to evaluate the emulator
        eva_pars = self.emulator[which_emu]['keys']
        # parameters needed for a computation
        req_pars = self.emulator[which_emu]['keys']
        # parameters to be computed
        comp_pars = list(set(req_pars)-set(avail_pars))
        # derived parameters that can be computed
        deriv_pars = ['omega_cold', 'sigma8_cold', 'A_s']
        # parameters missing from coordinates
        miss_pars = list(set(comp_pars)-set(deriv_pars))
        # requested parameters not needed for evaluation
        extra_pars = list(set(req_pars)-set(eva_pars))
        if miss_pars:
            print(f"{which_emu} emulator:")
            print(
                f"  Please add the parameter(s) {miss_pars}"
                f" to your coordinates!")
            raise KeyError(
                f"{which_emu} emulator: coordinates need the"
                f" following parameters: ", miss_pars)

        if ('omega_cold' in avail_pars) & ('omega_matter' in avail_pars):
            assert len(coordinates['omega_cold']) == len(
                coordinates['omega_matter']), \
                    'Both omega_cold and omega_matter were' + \
                    'provided, but they have different len'
            om_from_oc = coordinates['omega_cold'] + \
                coordinates['neutrino_mass'] / 93.14 / coordinates['hubble']**2
            assert np.all(np.abs(coordinates['omega_matter'] - om_from_oc) <
                          1e-4), 'Both omega_cold and omega_matter' + \
                   'were provided, but they are inconsistent among each other'

        if 'omega_cold' in comp_pars:
            if 'omega_matter' not in avail_pars:
                raise KeyError(
                    'One parameter between omega_matter' +
                    'and omega_cold must be provided!')

            omega_nu = coordinates['neutrino_mass'] / \
                93.14 / coordinates['hubble']**2
            coordinates['omega_cold'] = coordinates['omega_matter'] - omega_nu

        if ('sigma8_cold' not in avail_pars) & ('A_s' not in avail_pars):
            raise KeyError(
                'One parameter between sigma8_cold and A_s must be provided!')

        if ('sigma8_cold' in avail_pars) & ('A_s' in avail_pars):
            # commented for the cases where one is computed and same value is
            # repeated
            # assert len(np.atleast_1d(coordinates['sigma8_cold'])) ==
            # len(atleast_1d(coordinates['A_s'])), 'Both sigma8_cold and
            # A_s were provided, but they have different len'

            ignore_s8_pars = copy.deepcopy(coordinates)
            del ignore_s8_pars['sigma8_cold']
            s8_from_A_s = self.matter_powerspectrum_emulator.get_sigma8(
                **ignore_s8_pars)
            assert np.all(np.abs(coordinates['sigma8_cold'] - s8_from_A_s) <
                          1e-4), 'Both sigma8_cold and A_s were' + \
                   'provided, but they are inconsistent among each other'

        if 'sigma8_cold' in comp_pars:
            tmp_coords = copy.deepcopy(coordinates)
            tmp_coords['cold'] = True
            coordinates['sigma8_cold'] = np.atleast_1d(
                self.matter_powerspectrum_emulator.get_sigma8(**tmp_coords))

        if 'A_s' in comp_pars:
            tmp_coords = copy.deepcopy(coordinates)
            del tmp_coords['sigma8_cold']
            tmp_coords['A_s'] = 2e-9
            tmp_coords['cold'] = True
            _s8 = self.matter_powerspectrum_emulator.get_sigma8(**tmp_coords)
            coordinates['A_s'] = np.atleast_1d(
                (coordinates['sigma8_cold'] / _s8**2) * tmp_coords['A_s'])

        pp = np.squeeze([coordinates[p][0] for p in eva_pars])
        coords_out = copy.deepcopy(coordinates)

        grid = {}
        for key in coordinates.keys():
            if len(np.atleast_1d(coordinates[key])) > 1:
                grid[key] = np.array(coordinates[key])

        if len(list(grid.keys())) == 0:
            grid = None
        else:
            grid_structure = []
            for key in grid.keys():
                grid_structure.append(len(grid[key]))
            grid_structure = np.array(grid_structure)
            values, counts = np.unique(grid_structure, return_counts=True)
            counts_but_highest = np.delete(counts, np.argmax(counts))
            assert np.all(counts == counts[0]) | np.all(
                counts_but_highest == 1), 'When passing multiple' + \
                'coordinate sets you should either vary only on parameter,' + \
                'or all parameters should have the same len'

        if grid is not None:
            # list of parameters that are varyied in a grid
            grid_pars = list(grid.keys())
            N = len(grid[grid_pars[0]])
            pp = np.tile(pp, (N, 1))
            for par in grid_pars:
                if par in eva_pars:
                    index = eva_pars.index(par)
                    pp[:, index] = np.float64(grid[par])
                if par in req_pars:
                    coords_out[par] = grid[par]
            pp = np.float64(pp)

        for i, par in enumerate(eva_pars):
            val = pp[i] if grid is None else pp[:, i]
            message = 'Param {}={} out of bounds [{}, {}]'.format(
                par, val, self.emulator[which_emu]['bounds'][i][0],
                self.emulator[which_emu]['bounds'][i][1])

            assert (np.all(val >= self.emulator[which_emu]['bounds'][i][0])
                    & np.all(val <= self.emulator[which_emu]['bounds'][i][1])
                    ), message

        if extra_pars:
            cc = np.squeeze([coords_out[p] for p in extra_pars])
            if None in cc:
                raise ValueError(f'None in parameters: {extra_pars} = {cc}!')

        return coords_out, pp, grid

    def get_galaxy_pk(self, bias=None, f_sat=None, lambda_FoG=None,
                      epsilon_1=None, epsilon_2=None, epsilon_3=None, mean_num_dens=None,
                      omega_cold=None, omega_matter=None, omega_baryon=None,
                      sigma8_cold=None, A_s=None, hubble=None, ns=None,
                      neutrino_mass=None, w0=None, wa=None,
                      expfactor=None, k=None, pk_lpt_in=None, pk_bao_in=None, **kwargs):
        """Compute the predicted galaxy auto pk and galaxy-matter cross pk \
            given a set of bias parameters

        :param bias: a list of bias parameters, including b1, b2, bs2,
                     blaplacian
        :type bias: array-like
        :param f_sat: satellite fraction for FoG
        :type f_sat: array-like
        :param lambda_FoG: lambda FoG
        :type lambda_FoG: array-like
        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array
        :param omega_matter: omega total matter (cdm + baryons + neutrinos),
                             either omega_cold or omega_matter should be
                             specified, if both are specified they should be
                             consistent
        :type omega_matter: float or array
        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
                            either sigma8_cold or A_s should be specified,
                            if both are specified they should be consistent
        :type sigma8_cold: float or array
        :param A_s: primordial scalar amplitude at k=0.05 1/Mpc, either
                    sigma8_cold or A_s should be specified, if both are
                    specified they should be consistent
        :type A_s: float or array
        :param hubble: adimensional Hubble parameters, h=H0/(100 km/s/Mpc)
        :type hubble: float or array
        :param ns: scalar spectral index
        :type ns: float or array
        :param neutrino_mass: total neutrino mass
        :type neutrino_mass: float or array
        :param w0: dark energy equation of state redshift 0 parameter
        :type w0: float or array
        :param wa: dark energy equation of state redshift dependent parameter
        :type wa: float or array
        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array
        :param k: a vector of wavemodes in h/Mpc at which the nonlinear boost
                  will be computed, if None the default wavemodes of the
                  nonlinear emulator will be used, defaults to None
        :type k: array_like, optional
        :return: k and P(k), a list of the emulated 15 LPT Lagrangian bias
                 expansion terms
        :rtype: tuple
        """
        _kwargs = locals()
        kwargs = {key: _kwargs[key] for key in set(
            list(_kwargs.keys())) - set(['self'])}

        import itertools
        from scipy.special import legendre

        assert len(bias) == 4, 'Please, pass a valid bias array, with b1, b2, \
                                bs2, blaplacian'

        k, pnn = self.get_nonlinear_pnn(**kwargs)

        bias = np.concatenate(([1], bias))
        prod = np.array(
            list(itertools.combinations_with_replacement(np.arange(len(bias)),
                                                         r=2)))

        pgal_mono = 0
        pgal_quad = 0
        pgal_hexa = 0
        for i in range(len(pnn[0])):
            fac = 2 if prod[i, 0] != prod[i, 1] else 1
            pgal_mono += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[0][i]
            pgal_quad += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[1][i]
            pgal_hexa += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[2][i]


        mu = np.arange(0, 1, 0.01)
        pk2d = []
        for _mu in mu:
            pk2d.append(pgal_mono*legendre(0)(_mu) + pgal_quad*legendre(2)(_mu)
                        + pgal_hexa*legendre(4)(_mu))
        pk2d = np.squeeze(np.array(pk2d))

        pk2d_FoG = np.zeros_like(pk2d)
        for ik in range(len(k)):
            pk2d_FoG[:, ik] = pk2d[:, ik] * ((1 - f_sat) + f_sat
                                             * lambda_FoG**2
                                             / (lambda_FoG**2
                                                + (k[ik] * mu)**2))**2


        if epsilon_1 is not None:
            assert epsilon_2 is not None
            assert mean_num_dens is not None

            pk2d_FoG_Noise = np.zeros_like(pk2d_FoG)
            for ik in range(len(k)):
                if epsilon_3 is None:
                    Noise_2D = 1 / mean_num_dens * (epsilon_1 + epsilon_2 * k[ik]**2)
                else:
                    Noise_2D = 1 / mean_num_dens * (epsilon_1 + epsilon_2 * k[ik]**2 + epsilon_3 * k[ik]**2*mu**2)
                pk2d_FoG_Noise[:, ik] = pk2d_FoG[:, ik] + Noise_2D
        else:
            pk2d_FoG_Noise = pk2d_FoG


        pmulti = pkmulti(k, mu, pk2d_FoG_Noise)[0]
        pk0, pk2, pk4 = pmulti

        return k, pk0, pk2, pk4


    def get_galaxy_2Dpk(self, bias=None, f_sat=None, lambda_FoG=None,
                        epsilon_1=None, epsilon_2=None, mean_num_dens=None,
                        omega_cold=None, omega_matter=None, omega_baryon=None,
                        sigma8_cold=None, A_s=None, hubble=None, ns=None,
                        neutrino_mass=None, w0=None, wa=None,
                        expfactor=None, k=None, mu=None, **kwargs):
        """Compute the predicted galaxy auto pk and galaxy-matter cross pk \
            given a set of bias parameters

        :param bias: a list of bias parameters, including b1, b2, bs2,
                     blaplacian
        :type bias: array-like
        :param f_sat: satellite fraction for FoG
        :type f_sat: array-like
        :param lambda_FoG: lambda FoG
        :type lambda_FoG: array-like
        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array
        :param omega_matter: omega total matter (cdm + baryons + neutrinos),
                             either omega_cold or omega_matter should be
                             specified, if both are specified they should
                             be consistent
        :type omega_matter: float or array
        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
                            either sigma8_cold or A_s should be specified,
                            if both are specified they should be consistent
        :type sigma8_cold: float or array
        :param A_s: primordial scalar amplitude at k=0.05 1/Mpc, either
                    sigma8_cold or A_s should be specified, if both
                    are specified they should be consistent
        :type A_s: float or array
        :param hubble: adimensional Hubble parameters, h=H0/(100 km/s/Mpc)
        :type hubble: float or array
        :param ns: scalar spectral index
        :type ns: float or array
        :param neutrino_mass: total neutrino mass
        :type neutrino_mass: float or array
        :param w0: dark energy equation of state redshift 0 parameter
        :type w0: float or array
        :param wa: dark energy equation of state redshift dependent parameter
        :type wa: float or array
        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array
        :param k: a vector of wavemodes in h/Mpc at which the nonlinear boost
                  will be computed, if None the default wavemodes of the
                  nonlinear emulator will be used, defaults to None
        :type k: array_like, optional
        :param mu: a vector of angles, if None
                   the default mu's are an array defined in the code,
                   defaults to None
        :type mu: array_like, optional
        :return: k, mu and 2DP(k), the 2D galaxy power spectrum
        :rtype: tuple
        """
        _kwargs = locals()
        kwargs = {key: _kwargs[key]
                  for key in set(list(_kwargs.keys())) - set(['self'])}

        import itertools
        from scipy.special import legendre

        assert len(bias) == 4, 'Please, pass a valid bias array, with b1, b2, \
            bs2, blaplacian'

        k, pnn = self.get_nonlinear_pnn(**kwargs)
        bias = np.concatenate(([1], bias))
        prod = np.array(list(
            itertools.combinations_with_replacement(np.arange(len(bias)),
                                                    r=2)))

        pgal_mono = 0
        pgal_quad = 0
        pgal_hexa = 0
        for i in range(len(pnn[0])):
            fac = 2 if prod[i, 0] != prod[i, 1] else 1
            pgal_mono += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[0][i]
            pgal_quad += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[1][i]
            pgal_hexa += bias[prod[i, 0]] * bias[prod[i, 1]] * fac * pnn[2][i]

        if mu is None:
            mu = np.arange(0, 1, 0.01)
        else:
            mu = mu

        if len(mu) == 1:
            pk2d = pgal_mono * legendre(0)(mu) + \
                pgal_quad * legendre(2)(mu) + pgal_hexa * legendre(4)(mu)
        else:
            pk2d = []
            for _mu in mu:
                pk2d.append(pgal_mono*legendre(0)(_mu) +
                            pgal_quad*legendre(2)(_mu) +
                            pgal_hexa*legendre(4)(_mu))
            pk2d = np.squeeze(np.array(pk2d))

        if (len(k) == 1) or (len(mu) == 1):
            pk2d_FoG = pk2d * ((1 - f_sat)
                               + f_sat * lambda_FoG**2
                               / (lambda_FoG**2 + (k * mu)**2))**2
        else:
            pk2d_FoG = np.zeros_like(pk2d)
            for ik in range(len(k)):
                pk2d_FoG[:, ik] = pk2d[:, ik] * ((1 - f_sat)
                                                 + f_sat * lambda_FoG**2
                                                 / (lambda_FoG**2
                                                    + (k[ik] * mu)**2))**2

        if epsilon_1 is not None:
            assert epsilon_2 is not None
            assert mean_num_dens is not None

            if (len(k) == 1) or (len(mu) == 1):
                Noise_2D = 1 / mean_num_dens * (epsilon_1 + epsilon_2 * k**2)
                pk2d_FoG_Noise = pk2d_FoG + Noise_2D
            else:
                pk2d_FoG_Noise = np.zeros_like(pk2d_FoG)
                for ik in range(len(k)):
                    Noise_2D = 1 / mean_num_dens * (epsilon_1 + epsilon_2
                                                    * k[ik]**2)
                    pk2d_FoG_Noise[:, ik] = pk2d_FoG[:, ik] + Noise_2D
        else:
            pk2d_FoG_Noise = pk2d_FoG

        return k, mu, pk2d_FoG_Noise

    def get_nonlinear_pnn(self, omega_cold=None, omega_matter=None,
                          omega_baryon=None, sigma8_cold=None, A_s=None,
                          hubble=None, ns=None, neutrino_mass=None,
                          w0=None, wa=None, expfactor=None, k=None, pk_lpt_in=None, pk_bao_in=None,
                          **kwargs):
        """Compute the prediction of the nonlinear cold matter power spectrum.

        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array
        :param omega_matter: omega total matter (cdm + baryons + neutrinos),
                             either omega_cold or omega_matter should be
                             specified, if both are specified they should
                             be consistent
        :type omega_matter: float or array
        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
                            either sigma8_cold or A_s should be specified,
                            if both are specified they should be
                            consistent
        :type sigma8_cold: float or array
        :param A_s: primordial scalar amplitude at k=0.05 1/Mpc, either
                    sigma8_cold or A_s should be specified, if both
                    are specified they should be consistent
        :type A_s: float or array
        :param hubble: adimensional Hubble parameters, h=H0/(100 km/s/Mpc)
        :type hubble: float or array
        :param ns: scalar spectral index
        :type ns: float or array
        :param neutrino_mass: total neutrino mass
        :type neutrino_mass: float or array
        :param w0: dark energy equation of state redshift 0 parameter
        :type w0: float or array
        :param wa: dark energy equation of state redshift dependent parameter
        :type wa: float or array
        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array
        :param k: a vector of wavemodes in h/Mpc at which the nonlinear
                  boost will be computed, if None the default wavemodes of
                  the nonlinear emulator will be used, defaults to None
        :type k: array_like, optional
        :return: k and P(k), a list of the emulated 15 LPT Lagrangian
                 bias expansion terms
        :rtype: tuple
        """
        _kwargs = locals()
        kwargs = {key: _kwargs[key] for key in _kwargs
          if key not in ['self', 'pk_lpt_in', 'pk_bao_in']}

        if not self.compute_nonlinear_boost:
            raise ValueError("Please enable the l-bias nonlinear boost!")

        coordinates, pp, grid = self._get_parameters(kwargs, 'nonlinear')
        emulator = self.emulator['nonlinear']

        n_log = [-1]

        _pp = _transform_space(
            np.array([pp]), space_rotation=False, bounds=emulator['bounds'])

        if pk_lpt_in is None:
            _, pk_lpt = self.get_lpt_pk(k=emulator['k'], **coordinates)
        else:
            pk_lpt = copy.deepcopy(pk_lpt_in)

        if pk_bao_in is None:
            _, pk_bao = self.get_smeared_bao_pk(k=emulator['k'], **coordinates)
        else:
            pk_bao = copy.deepcopy(pk_bao_in)

        for ell in range(3):
            for n in [4, 8, 13]:
                pk_lpt[ell][n] *= -1
        pk_lpt[1][9] = pk_lpt[1][7]

        mask_lpt = emulator['k'] > 0.2

        for n in [1, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14]:
            pk_lpt[2][n][mask_lpt] = pk_lpt[2][n][mask_lpt][0]

        for ell in range(3):
            pk_lpt[ell][0] = pk_bao[ell]

        pk_lpt[0][1] = np.mean(
            (pk_lpt[0][1] / pk_bao[0])[emulator['k'] < 0.05]) * pk_bao[0]
        pk_lpt[1][1] = np.mean(
            (pk_lpt[1][1] / pk_bao[1])[emulator['k'] < 0.05]) * pk_bao[1]

        pk_lpt[1][4] = -emulator['k']**2 * pk_lpt[1][1]

        pk_lpt[0][14] = emulator['k']**4 * pk_lpt[0][5]

        P_nn = [[], [], []]
        for ell in range(3):
            for n in range(15):
                prediction = emulator['model'][ell][n](
                    _pp.reshape(-1, 9))
                prediction = emulator['scaler'][ell][n].inverse_transform(
                    prediction)
                if n in n_log:
                    prediction = np.squeeze(np.exp(prediction))
                if (ell == 0) & (n == 10):
                    P_nn[ell].append(pk_lpt[ell][n])
                else:
                    P_nn[ell].append(np.squeeze(prediction) * pk_lpt[ell][n])

        if k is not None:
            if max(k) > max(emulator['k']):
                raise ValueError(f"""
            The maximum k of the l-bias nonlinear emulator
            must be {max(emulator['k'])} h/Mpc:
            the current value is {max(k)} h/Mpc""")
            if (min(k) <= 1e-2) & (self.verbose):
                print("WARNING: the nonlinear emulator is extrapolating"
                      + "to k < 0.01 h/Mpc!")

            new_P_nn = [[], [], []]
            for ell in range(3):
                for n in range(15):
                    # can happen when allowing extrapolation
                    unexpected_negative = np.any(P_nn[ell][n] <= 0.0)
                    if (n in n_log) & (unexpected_negative is False):
                        new_P_nn[ell].append(np.exp(interpolate.interp1d(
                            np.log(emulator['k']), np.log(P_nn[ell][n]),
                            kind='cubic', axis=0 if grid is None else 1,
                            fill_value='extrapolate')(np.log(k))))
                    else:
                        new_P_nn[ell].append(interpolate.interp1d(
                            np.log(emulator['k']), P_nn[ell][n], kind='cubic',
                            axis=0 if grid is None else 1,
                            fill_value='extrapolate')(np.log(k)))
            P_nn = np.array(new_P_nn)
        else:
            k = emulator['k']

        return k, P_nn

    def get_lpt_pk(self, omega_cold=None, omega_matter=None, omega_baryon=None,
                   sigma8_cold=None, A_s=None, hubble=None, ns=None,
                   neutrino_mass=None, w0=None, wa=None,
                   expfactor=None, k=None, **kwargs):
        """Compute the prediction of the 15 LPT Lagrangian bias expansion \
            terms.


        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array
        :param omega_matter: omega total matter (cdm + baryons + neutrinos),
                             either omega_cold or omega_matter should be
                             specified, if both are specified they should
                             be consistent
        :type omega_matter: float or array
        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
                            either sigma8_cold or A_s should be specified,
                            if both are specified they should be consistent
        :type sigma8_cold: float or array
        :param A_s: primordial scalar amplitude at k=0.05 1/Mpc, either
                    sigma8_cold or A_s should be specified, if both are
                    specified they should be consistent
        :type A_s: float or array
        :param hubble: adimensional Hubble parameters, h=H0/(100 km/s/Mpc)
        :type hubble: float or array
        :param ns: scalar spectral index
        :type ns: float or array
        :param neutrino_mass: total neutrino mass
        :type neutrino_mass: float or array
        :param w0: dark energy equation of state redshift 0 parameter
        :type w0: float or array
        :param wa: dark energy equation of state redshift dependent parameter
        :type wa: float or array
        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array
        :param k: a vector of wavemodes in h/Mpc at which the nonlinear boost
                  will be computed, if None the default wavemodes of the
                  nonlinear emulator will be used, defaults to None
        :type k: array_like, optional
        :return: k and P(k), a list of the emulated 15 LPT Lagrangian bias
                 expansion terms
        :rtype: tuple
        """
        _kwargs = locals()
        kwargs = {key: _kwargs[key] for key in set(list(
            _kwargs.keys())) - set(['self'])}

        if not self.compute_lpt:
            raise ValueError("Please enable the lpt emulator!")

        emulator = self.emulator['lpt']
        coordinates, pp, grid = self._get_parameters(kwargs, 'lpt')

        sub = emulator['sub']
        scaler = emulator['scaler']

        P_nn = [[], [], []]
        for ell in range(3):
            for n in range(15):
                pred = emulator['model'][ell][n](
                    pp.reshape(-1, 9))
                prediction = np.squeeze(scaler[ell][n].inverse_transform(pred))
                P_nn[ell].append(prediction)

        if k is not None:
            if max(k) > max(emulator['k']):
                raise ValueError(f"""
            The maximum k of the l-bias lpt emulator
            must be {max(emulator['k'])} h/Mpc:
            the current value is {max(k)} h/Mpc""")
            if (min(k) <= 1e-2) & (self.verbose):
                print("WARNING: the l-bias lpt emulator is extrapolating to"
                      + "k < 0.01 h/Mpc!")

            for ell in range(3):
                for n in range(15):
                    p_interp = interpolate.interp1d(
                        np.log(emulator['k']), P_nn[ell][n], kind='cubic',
                        axis=0 if grid is None else 1,
                        fill_value='extrapolate',
                        assume_sorted=True)
                    P_nn[ell][n] = p_interp(np.log(k))
        else:
            k = emulator['k']

        P_nn = np.array([[np.exp(P_nn[ell][n]) - sub[ell][n]
                          for n in range(15)] for ell in range(3)])
        return k, P_nn

    def get_smeared_bao_pk(self, omega_cold=None, omega_matter=None,
                           omega_baryon=None, sigma8_cold=None, A_s=None,
                           hubble=None, ns=None, neutrino_mass=None,
                           w0=None, wa=None, expfactor=None, k=None, **kwargs):
        """Evaluate the smeared bao emulator at a set of coordinates in \
           parameter space.

        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array
        :param omega_matter: omega total matter (cdm + baryons + neutrinos),
                             either omega_cold or omega_matter should be
                             specified, if both are specified they should
                             be consistent
        :type omega_matter: float or array
        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
                            either sigma8_cold or A_s should be specified,
                            if both are specified they should be
                            consistent
        :type sigma8_cold: float or array
        :param A_s: primordial scalar amplitude at k=0.05 1/Mpc, either
                    sigma8_cold or A_s should be specified, if both
                    are specified they should be consistent
        :type A_s: float or array
        :param hubble: adimensional Hubble parameters, h=H0/(100 km/s/Mpc)
        :type hubble: float or array
        :param ns: scalar spectral index
        :type ns: float or array
        :param neutrino_mass: total neutrino mass
        :type neutrino_mass: float or array
        :param w0: dark energy equation of state redshift 0 parameter
        :type w0: float or array
        :param wa: dark energy equation of state redshift dependent parameter
        :type wa: float or array
        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array
        :param k: a vector of wavemodes in h/Mpc at which the nonlinear boost
                  will be computed, if None the default wavemodes of the
                  nonlinear emulator will be used, defaults to None
        :type k: array_like, optional
        :return: k and P(k), a list of the emulated 15 LPT Lagrangian bias
                 expansion terms
        :rtype: tuple
        """
        _kwargs = locals()
        kwargs = {key: _kwargs[key] for key in set(
            list(_kwargs.keys())) - set(['self'])}

        if not self.compute_smeared_bao:
            raise ValueError("Please enable the smeared bao emulator!")

        emulator = self.emulator['smeared_bao']
        coordinates, pp, grid = self._get_parameters(kwargs, 'smeared_bao')

        pk_bao = [[], [], []]
        for ell in range(3):
            ypred = emulator['model'][ell](pp.reshape(-1, 9))
            pk_bao[ell] = np.squeeze(np.exp(
                emulator['scaler'][ell].inverse_transform(ypred))
                ) - emulator['sub'][ell]

        if k is not None:
            if (max(k) > 30.) | (min(k) < 1e-3):
                raise ValueError(f"""
                    A minimum k > 0.001 h/Mpc and a maximum
                    k < {max(emulator['k'])} h/Mpc
                    are required for the linear emulator:
                    the current values are {min(k)} h/Mpc and {max(k)} h/Mpc
                    """)

            else:
                for ell in range(3):
                    pk_bao[ell] = interpolate.interp1d(
                        np.log(emulator['k']), pk_bao[ell], kind='cubic',
                        axis=0 if grid is None else 1,
                        fill_value='extrapolate')(np.log(k))
        else:
            k = emulator['k']
        return k, pk_bao


def load_lpt_emu(verbose=True, folder=None):
    """Loads in memory the lpt emulator in z-space

    :return: a dictionary containing the emulator object
    :rtype: dict
    """

    if verbose:
        print('Loading l-bias lpt emulator...')

    basefold = os.path.dirname(os.path.abspath(__file__))

    old_names = [(basefold + '/' + "lpt_emulator"),
                 (basefold + '/' + "velocileptor_emulator_v1.0.0"),
                 (basefold + '/' + "velocileptor_emulator_v1.0.1"),
                 ]
    for old_name in old_names:
        if os.path.exists(old_name):
            import shutil
            shutil.rmtree(old_name)

    emulator_name = (basefold + '/' +
                     "velocileptor_emulator_v1.0.2")

    if (not os.path.exists(emulator_name)):
        import urllib.request
        import tarfile
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print('Downloading emulator data (34 Mb)...')
        urllib.request.urlretrieve(
            'https://bacco.dipc.org/velocileptor_emulator_v1.0.2.tar',
            emulator_name + '.tar',
            MyProgressBar())
        tf = tarfile.open(emulator_name+'.tar', 'r')
        tf.extractall(path=basefold, filter='tar')
        tf.close()
        os.remove(emulator_name + '.tar')

    emulator = {}
    emulator['emu_type'] = 'nn'

    emulator['model'] = [[], [], []]
    emulator['sub'] = [[], [], []]
    emulator['scaler'] = [[], [], []]
    for ell in range(3):
        for n in range(15):
            i_emulator_name = f'{emulator_name}/nfield{n}_ell{2*ell}'

            file_to_read = open(f"{i_emulator_name}/details.pickle", "rb")
            nn_details = pickle.load(file_to_read)

            emulator['model'][ell].append(load_model((i_emulator_name +
                                                      f'/nfield{n}_ell{2*ell}'
                                                      + '.h5')))
            emulator['scaler'][ell].append(StandardScalerSimplified(np.array(nn_details['scaler_mean'])))
            emulator['sub'][ell].append(nn_details['subtract'])

    emulator['k'] = np.array(nn_details['k'])
    emulator['keys'] = ['omega_cold', 'sigma8_cold', 'omega_baryon', 'ns',
                        'hubble', 'neutrino_mass', 'w0', 'wa', 'expfactor']
    emulator['bounds'] = np.array(nn_details['bounds'])

    if verbose:
        print('L-bias lpt emulator loaded in memory.')

    return emulator


def load_smeared_bao_emu(verbose=True, folder=None):
    """Loads in memory the smeared BAO pk in z-space

    :return: a dictionary containing the emulator object
    :rtype: dict
    """

    if verbose:
        print('Loading l-bias smeared BAO emulator...')

    basefold = os.path.dirname(os.path.abspath(__file__))

    old_names = [(basefold + '/' + "smeared_BAO_emulator_RSD"),
                 (basefold + '/' + "zspace_smeared_bao_emulator_v1.0.0"),
                 (basefold + '/' + "zspace_smeared_bao_emulator_v1.0.1")]
    for old_name in old_names:
        if os.path.exists(old_name):
            import shutil
            shutil.rmtree(old_name)

    emulator_name = (basefold + '/' +
                     "zspace_smeared_bao_emulator_v1.0.2")

    if (not os.path.exists(emulator_name)):
        import urllib.request
        import tarfile
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print('Downloading emulator data (34 Mb)...')
        urllib.request.urlretrieve(
            'https://bacco.dipc.org/zspace_smeared_bao_emulator_v1.0.2.tar',
            emulator_name + '.tar',
            MyProgressBar())
        tf = tarfile.open(emulator_name+'.tar', 'r')
        tf.extractall(path=basefold, filter='tar')
        tf.close()
        os.remove(emulator_name + '.tar')

    emulator = {}
    emulator['emu_type'] = 'nn'

    emulator['model'] = [[], [], []]
    emulator['sub'] = [[], [], []]
    emulator['scaler'] = [[], [], []]
    for ell in range(3):
        i_emulator_name = f'{emulator_name}/ell{2*ell}'

        file_to_read = open(f"{i_emulator_name}/details.pickle", "rb")
        nn_details = pickle.load(file_to_read)

        emulator['model'][ell] = load_model((i_emulator_name +
                                             f'/ell{2*ell}.h5'))
        emulator['scaler'][ell] = StandardScalerSimplified(np.array(nn_details['scaler_mean']))
        emulator['sub'][ell] = nn_details['subtract']

    emulator['k'] = np.array(nn_details['k'])
    emulator['keys'] = ['omega_cold', 'sigma8_cold', 'omega_baryon', 'ns',
                        'hubble', 'neutrino_mass', 'w0', 'wa', 'expfactor']
    emulator['bounds'] = np.array(nn_details['bounds'])

    if verbose:
        print('L-bias lpt emulator loaded in memory.')

    return emulator


def load_nonlinear_lbias_emu(emu_type='nn', nonlinear_emu_path=None,
                             nonlinear_emu_details=None, verbose=True):
    """Loads in memory the nonlinear emulator described in \
        Pellejero-Ibáñez et al. 2022.

    :param emu_type: type of emulator, can be 'gp' for the gaussian process, ot
                 'nn' for the neural network
    :type emu_type: str

    :return: a dictionary containing the emulator object
    :rtype: dict
    """
    if verbose:
        print('Loading non-linear l-bias emulator...')

    if nonlinear_emu_path is None:
        basefold = os.path.dirname(os.path.abspath(__file__))

        old_names = [(basefold + '/' + "lbias_emulator_RSD_1.0.0"),
                     (basefold + '/' + "lbias_emulator_RSD_1.0.1")]
        for old_name in old_names:
            if os.path.exists(old_name):
                import shutil
                shutil.rmtree(old_name)

        emulator_name = (basefold + '/' + "lbias_emulator_RSD_1.0.2")

        if (not os.path.exists(emulator_name)):
            import urllib.request
            import tarfile
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            print('Downloading emulator data (34Mb)...')
            urllib.request.urlretrieve(
                'https://bacco.dipc.org/lbias_emulator_RSD_1.0.2.tar',
                emulator_name + '.tar',
                MyProgressBar())
            tf = tarfile.open(emulator_name+'.tar', 'r')
            tf.extractall(path=basefold, filter='tar')
            tf.close()
            os.remove(emulator_name + '.tar')
    else:
        emulator_name = nonlinear_emu_path

    emulator = {}
    emulator['emu_type'] = 'nn'
    emulator['model'] = [[], [], []]
    emulator['scaler'] = [[], [], []]
    for ell in range(3):
        for n in range(15):
            detail_name = f'ell{2*ell}_details.pickle'
            i_emulator_name = \
                (f'{emulator_name}/field{n}_ell{2*ell}' +
                 f'/field{n}_ell{2*ell}.h5')
            emulator['model'][ell].append(load_model(i_emulator_name))

        with open(os.path.join(emulator_name, detail_name), 'rb') as f:
            details = pickle.load(f)
        emulator['scaler'][ell] = [StandardScalerSimplified(np.array(details['scaler_mean'][i])) for i in range(15)]
        emulator['k'] = np.array(details['k'])
        emulator['bounds'] = np.array(details['bounds'])
    emulator['keys'] = ['omega_cold', 'sigma8_cold', 'omega_baryon', 'ns',
                        'hubble', 'neutrino_mass', 'w0', 'wa', 'expfactor']

    if verbose:
        print('Nonlinear l-bias emulator loaded in memory.')
    return emulator
