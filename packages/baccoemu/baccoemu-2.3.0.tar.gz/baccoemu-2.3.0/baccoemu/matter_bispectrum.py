from .baryonic_boost import load_bispecrum_baryonic_emu
from .utils import EmulatorJAX
import jax.numpy as jnp
import numpy as np
import copy

__all__ = ["Matter_bispectrum"]


class Matter_bispectrum(object):
    """
    A class to load and call the baccoemu for the matter bispectrum.
    By default, the baryonic boost (described in Burger et al. 2025) is loaded.

    The baryonic boost is defined as the ratio between the non-linear
    matter bispectrum in hydrodynamical simulations and that in dark-matter-only simulations.
    At large or small scales (k < 0.01 or k > 17), the prediction is extrapolated and should be taken with caution.

    :param compute_baryonic_boost:  Whether to load and apply the baryonic boost emulator.
    :type compute_baryonic_boost: bool, optional
    :param baryonic_emu_path: Path to the baryonic emulator files.
    :type baryonic_emu_path: str, optional
    :param verbose: Whether to print messages during extrapolation.
    :type verbose: bool, optional
    """

    def __init__(self, compute_baryonic_boost=True,
                 baryonic_emu_path=None,
                 verbose=True):

        self.verbose = verbose
        self.compute_baryonic_boost = True if compute_baryonic_boost else False
        self.emulator = {}

        # Load the baryonic boost emulator if required
        if self.compute_baryonic_boost:
            self.emulator['baryon'] = load_bispecrum_baryonic_emu(
                fold_name=baryonic_emu_path,
                verbose=verbose)


    def _get_parameters(self, coordinates, which_emu):
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
        :return: coordinates with derived parameters
        :rtype: dict
        """
        coordinates = {key: np.atleast_1d(coordinates[key]) for key in
                       set(list(coordinates.keys()))
                       - set(['k','k1','k2','k3', 'k_lin', 'pk_lin'])}

        # parameters currently available
        avail_pars = [coo for coo in coordinates.keys() if coordinates[coo][0]
                      is not None]
        # parameters strictly needed to evaluate the emulator
        eva_pars = self.emulator[which_emu]['keys']
        # parameters to be computed
        req_pars = self.emulator[which_emu]['keys'] if which_emu != 'linear' \
            else self.emulator[which_emu]['full_keys']
        # parameters needed for a computation
        comp_pars = list(set(req_pars)-set(avail_pars))
        # derived parameters that can be computed
        deriv_pars = ['omega_cold', 'sigma8_cold', 'A_s']
        # parameters missing from coordinates
        miss_pars = list(set(comp_pars)-set(deriv_pars))
        # requested parameters not needed for evaluation
        extra_pars = list(set(req_pars)-set(eva_pars))

        if miss_pars:
            print(f"{which_emu} emulator:")
            print(f"  Please add the parameter(s) {miss_pars}"
                  f" to your coordinates!")
            raise KeyError(f"{which_emu} emulator: coordinates need the"
                           f" following parameters: ", miss_pars)

        if ('omega_cold' in avail_pars) & ('omega_matter' in avail_pars):
            assert len(coordinates['omega_cold']) == \
                len(coordinates['omega_matter']), \
                'Both omega_cold and omega_matter were provided, ' \
                + 'but they have different len'
            om_from_oc = coordinates['omega_cold'] \
                + coordinates['neutrino_mass'] / 93.14 \
                / coordinates['hubble']**2
            assert np.all(np.abs(coordinates['omega_matter'] - om_from_oc)
                          < 1e-4), 'Both omega_cold and omega_matter were' \
                + ' provided, but they are inconsistent among each other'

        if 'omega_cold' in comp_pars:
            if 'omega_matter' not in avail_pars:
                raise KeyError('One parameter between omega_matter and'
                               ' omega_cold must be provided!')

            omega_nu = coordinates['neutrino_mass'] / 93.14 \
                / coordinates['hubble']**2
            coordinates['omega_cold'] = coordinates['omega_matter'] - omega_nu

        if ('sigma8_cold' not in avail_pars) & ('A_s' not in avail_pars):
            raise KeyError('One parameter between sigma8_cold and A_s must'
                           'be provided!')

        if ('sigma8_cold' in avail_pars) & ('A_s' in avail_pars):
            # commented for the cases where one is computed
            # and same value is repeated
            # assert len(np.atleast_1d(coordinates['sigma8_cold']))
            # == len(atleast_1d(coordinates['A_s'])),
            # 'Both sigma8_cold and A_s were provided,
            # but they have different len'

            ignore_s8_pars = copy.deepcopy(coordinates)
            del ignore_s8_pars['sigma8_cold']
            ignore_s8_pars['cold'] = True
            s8_from_A_s = self.get_sigma8(**ignore_s8_pars)
            assert np.all(np.abs(coordinates['sigma8_cold'] - s8_from_A_s)
                          < 1e-4), \
                'Both sigma8_cold and A_s were provided, but they are' \
                + 'inconsistent among each other'

        if 'sigma8_cold' in comp_pars:
            tmp_coords = copy.deepcopy(coordinates)
            tmp_coords['cold'] = True
            coordinates['sigma8_cold'] = np.atleast_1d(
                self.get_sigma8(**tmp_coords))

        if 'A_s' in comp_pars:
            tmp_coords = copy.deepcopy(coordinates)
            del tmp_coords['sigma8_cold']
            tmp_coords['A_s'] = 2e-9
            tmp_coords['cold'] = True
            coordinates['A_s'] = np.atleast_1d(
                (coordinates['sigma8_cold'] / self.get_sigma8(**tmp_coords))**2
                * tmp_coords['A_s'])

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
            assert (np.all(counts == counts[0])
                    | np.all(counts_but_highest == 1)), 'When passing' \
                ' multiple coordinate sets you should either vary only on' \
                ' parameter, or all parameters should have the same len'

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
            cc = [coords_out[p] for p in extra_pars]
            if np.any(cc is None):
                raise ValueError(f'None in parameters: {extra_pars} = {cc}!')

        return coords_out, pp, grid



    def get_baryonic_boost(self, omega_cold=None,
                           omega_baryon=None, sigma8_cold=None, expfactor=None, M_c=None,
                           eta=None, beta=None, M1_z0_cen=None,
                           theta_inn=None, k1=None, k2=None, k3=None, check_parameter_boundaries=True, check_k_extrapolation=True, **kwargs):
        """
        Computes the baryonic boost for a set of bispectrum triangle configurations a set of coordinates in \
        parameter space.

        :param omega_cold: omega cold matter (cdm + baryons), either omega_cold
                           or omega_matter should be specified, if both are
                           specified they should be consistent
        :type omega_cold: float or array

        :param omega_baryon: omega baryonic matter (baryons)
        :type omega_baryon: float or array

        :param sigma8_cold: rms of cold (cdm + baryons) linear perturbations,
        :type sigma8_cold: float or array

        :param expfactor: expansion factor a = 1 / (1 + z)
        :type expfactor: float or array

        :param M_c: mass fraction of hot gas in haloes
        :type M_c: float or array

        :param eta: extent of ejected gas
        :type eta: float or array

        :param beta: mass fraction of hot gas in haloes
        :type beta: float or array

        :param M1_z0_cen: characteristic halo mass scale for central galaxy
        :type M1_z0_cen: float or array

        :param theta_inn: density profile of hot gas in haloes
        :type theta_inn: float or array


        :param k: a vector of wavemodes in h/Mpc at which the baryonic boost
                  will be computed
        :type k: array_like, optional

        :return: k_array, baryonic_boost, extrapolation_flags
        :rtype: tuple
        :param k_array: Sorted array of valid triangle configurations (k1, k2, k3), which also check for k1+k2>=k3.
        :type k_array: ndarray
        :param baryonic_boost: Predicted baryonic boost values from the emulator.
        :type baryonic_boost: ndarray
        :param extrapolation_flags: Flags indicating if each triangle is in the extrapolation regime.
        :type extrapolation_flags: list of bool
        """

        # Pack all arguments into kwargs for emulator
        _kwargs = locals()
        kwargs = {key: _kwargs[key]
                  for key in set(_kwargs.keys()) - set(['self'])}

        emulator = self.emulator['baryon']
        coords, pp, grid = self._get_parameters(kwargs, 'baryon')

        # Build and validate triangle configurations
        k_array = jnp.asarray([kwargs['k1'], kwargs['k2'], kwargs['k3']], dtype=jnp.float32).T
        k_array = jnp.sort(k_array, axis=1)  # Ensure k1 <= k2 <= k3
        mask = (k_array[:, 0] + k_array[:, 1]) >= k_array[:, 2]  # Triangle inequality
        k_array = k_array[mask]
        N_k = k_array.shape[0]

        # Determine extrapolation flags per configuration
        extrapolation_flags = []
        if(check_k_extrapolation):
            extrapolation_flags = jnp.any((k_array < emulator['k_range'][0]) | (k_array > emulator['k_range'][1]), axis=1)
            # Verbose output if any extrapolation is happening
            if self.verbose and any(extrapolation_flags):
                print(f"Warning: Some triangle configurations are extrapolated (k < {emulator['k_range'][0]} or k > {emulator['k_range'][1]}).")


        if grid is not None:
            N_parameter = len(grid[list(grid.keys())[0]])
            missing_params = set(emulator['keys'])-set(grid.keys())
            for name in missing_params:
                grid[name] = np.array([kwargs[name]] *  N_parameter)

            # Repeat each cosmology parameter for every triangle configuration
            para_jax = {}
            for name, trained_name in zip(emulator['keys'], emulator['trained_keys']):
                param_vals = jnp.asarray(grid[name])
                # Repeat each parameter N_k times (cosmo1 with all ks, cosmo2 with all ks, etc.)
                para_jax[trained_name] = jnp.tile(param_vals[:, None], (1, N_k)).reshape(-1)

            # Tile the k-array (same triangle configurations repeated for each cosmology)
            para_jax['k1'] = jnp.tile(k_array[:, 0], N_parameter)
            para_jax['k2'] = jnp.tile(k_array[:, 1], N_parameter)
            para_jax['k3'] = jnp.tile(k_array[:, 2], N_parameter)

            # Predict the baryonic boost using the emulator
            baryonic_boost = emulator['model'](para_jax).reshape(N_parameter,N_k)

        else:
            # Prepare parameters for emulator input
            para_jax = {trained_name: jnp.asarray([coords[name].item()] * N_k, dtype=jnp.float32)
                            for (name, trained_name) in zip(emulator['keys'], emulator['trained_keys'])
                                        if name in emulator['keys']}
            para_jax['k1'] = jnp.asarray(k_array[:, 0], dtype=jnp.float32)
            para_jax['k2'] = jnp.asarray(k_array[:, 1], dtype=jnp.float32)
            para_jax['k3'] = jnp.asarray(k_array[:, 2], dtype=jnp.float32)

            # Predict the baryonic boost using the emulator
            baryonic_boost = emulator['model'](para_jax)


        return k_array, baryonic_boost, extrapolation_flags


