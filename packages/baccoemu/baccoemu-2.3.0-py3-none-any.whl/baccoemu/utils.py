import numpy as np
import copy
import progressbar
import hashlib
import jax.numpy as jnp
from jax import jacfwd
from jax.nn import sigmoid
from jax import jit
from functools import partial

class load_model:
    def __init__(self, fname):
        import h5py
        f = h5py.File(fname, 'r')
        self.params = []
        for key in f['model_weights'].attrs['layer_names']:
            self.params.append((f['model_weights'][key][key]['kernel:0'][:].astype(jnp.float32),
                                f['model_weights'][key][key]['bias:0'][:].astype(jnp.float32)))
        self.jac_predict = jacfwd(self.predict)

    def relu(self, x):
        return jnp.maximum(0, x)

    def predict(self, x):
        activations = x.astype(jnp.float32)
        for w, b in self.params[:-1]:
            outputs = jnp.matmul(activations, w)
            outputs = jnp.add(outputs, b)
            activations = self.relu(outputs)
        final_w, final_b = self.params[-1]
        logits = jnp.matmul(activations, final_w)
        logits = jnp.add(logits, final_b)
        return logits

    def __call__(self, x):
        return self.predict(x)

    def jacobian(self, x):
        return self.jac_predict(x)


class StandardScalerSimplified:
    def __init__(self, mean, std=None):
        self.mean = np.array(mean)
        self.std = std if std is None else np.array(std)

    def inverse_transform(self, x):
        X = copy.deepcopy(x)
        if self.std is None:
            return X + self.mean
        return X * self.std + self.mean


def _md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _transform_space(x, space_rotation=False, rotation=None, bounds=None):
    """Normalize coordinates to [0,1] intervals and if necessary apply a
    rotation

    :param x: coordinates in parameter space
    :type x: ndarray
    :param space_rotation: whether to apply the rotation matrix defined through
                           the rotation keyword, defaults to False
    :type space_rotation: bool, optional
    :param rotation: rotation matrix, defaults to None
    :type rotation: ndarray, optional
    :param bounds: ranges within which the emulator hypervolume is defined,
                   defaults to None
    :type bounds: ndarray, optional
    :return: normalized and (if required) rotated coordinates
    :rtype: ndarray
    """
    if space_rotation:
        # Get x into the eigenbasis
        R = rotation['rotation_matrix'].T
        xR = copy.deepcopy(np.array([np.dot(R, xi)
                                     for xi in x]))
        xR = xR - rotation['rot_points_means']
        xR = xR/rotation['rot_points_stddevs']
        return xR
    else:
        return (x - bounds[:, 0])/(bounds[:, 1] - bounds[:, 0])


class MyProgressBar():
    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if not self.pbar:
            self.pbar = progressbar.ProgressBar(maxval=total_size)
            self.pbar.start()

        downloaded = block_num * block_size
        if downloaded < total_size:
            self.pbar.update(downloaded)
        else:
            self.pbar.finish()

def pkmulti(kk, mu, pk2d, nmodes=None, mode='reimann_sum', nthreads=None, verbose=None, pmulti_interp='polyfit', return_ell6=False):
    import scipy

    if mode not in ['reimann_sum', 'gl_quad']:
        raise ValueError('Please, specify a mode between reimann_sum and gl_quad')
    mode = {'reimann_sum' : 0, 'gl_quad' : 1}[mode]

    if nmodes is None:
        nmodes = np.repeat(1,len(kk))



    if return_ell6:
        num_mult = 4
    else:
        num_mult = 3
    moments = np.zeros((num_mult, len(kk)))
    p2ds = np.zeros((len(mu), len(kk)))
    No = 8
    p16_roots = [
        0.09501251, 0.28160355, 0.45801678, 0.61787624,
        0.75540441, 0.8656312, 0.94457502, 0.98940093]

    p16_w = [
        0.189450610455069,
        0.182603415044924,
        0.169156519395003,
        0.149595988816577,
        0.124628971255534,
        0.095158511682493,
        0.062253523938648,
        0.027152459411754]

    for ik in range(len(kk)):
        if nmodes[ik]>0:
            mask = pk2d[:, ik] != 0.0
            know = kk[ik]
            npoints = sum(mask)
            if npoints > 1:
                deg = np.min((4,npoints))
                cc = np.polyfit(mu[mask], pk2d[:, ik][mask], deg=deg)
                pmu_lin_interp = scipy.interpolate.interp1d(
                    mu[mask], pk2d[:, ik][mask], kind='linear')

                def _p_at_mu(mui):
                    if pmulti_interp == 'linear':
                        return pmu_lin_interp(mui)
                    elif pmulti_interp == 'polyfit':
                        return np.sum([cc[i] * mui**(deg - i)
                                        for i in range(len(cc))], axis=0)
                    elif pmulti_interp == 'mix':
                        if know < 0.5 * knl:
                            return np.sum([cc[i] * mui**(deg - i)
                                            for i in range(len(cc))], axis=0)
                        else:
                            return pmu_lin_interp(mui)
                    else:
                        raise ValueError(
                            'Illegal choice for pmulti_interp: choose between linear, polyfit and mix')

                for ell in range(num_mult):
                    result = 0.0
                    for io in range(No):
                        result += p16_w[io] * \
                            p16_roots[io]**(2 * ell) * _p_at_mu(p16_roots[io])
                    moments[ell, ik] = result
                p2ds[:, ik] = _p_at_mu(mu)
            else:
                logger.info(
                    'pk multipoles at k {0} set to zero: it seems you have a lot of bins for this grid size'.format(know))


        multi = np.zeros((num_mult, len(kk)))
        multi[0, :] = moments[0, :]
        multi[1, :] = (5.0 / 2.0) * (3.0 * moments[1, :] - moments[0, :])
        multi[2, :] = (9.0 / 8.0) * (35 * moments[2, :] - 30.0 *
                                 moments[1, :] + 3.0 * moments[0, :])
        if return_ell6:
            multi[3, :] = (13.0 / 32.0) * (231 * moments[3, :] - 315.0 *
                                 moments[2, :] + 105.0 * moments[1, :] - 5.0 * moments[0, :])

    return multi, p2ds, moments

class coevolution_relations:
    """ Coevolution reltions from https://arxiv.org/abs/2110.05408
    """
    def halo_b1L_nu(nu):
        return -0.00951 * nu**3 + 0.4873 * nu**2 - 0.1395 * nu - 0.4383

    def halo_b2L_b1L(b1L):
        return -0.09143 * b1L**3 + 0.7093 * b1L**2 - 0.2607 * b1L - 0.3469

    def halo_bs2L_b1L(b1L):
        return 0.02278 * b1L**3 - 0.005503 * b1L**2 - 0.5904 * b1L - 0.1174

    def halo_blL_b1L(b1L):
        return -0.6971 * b1L**3 + 0.7892 * b1L**2 + 0.5882 * b1L - 0.1072

    def gal_b2L_b1L(b1L):
        return 0.01677 * b1L**3 - 0.005116 * b1L**2 + 0.4279 * b1L - 0.1635

    def gal_bs2L_b1L(b1L):
        return -0.3605 * b1L**3 + 0.5649 * b1L**2 - 0.1412 * b1L - 0.01318

    def gal_blL_b1L(b1L):
        return 0.2298 * b1L**3 - 2.096 * b1L**2 + 0.7816 * b1L - 0.1545




class EmulatorJAX:
    """General-purpose JAX-based emulator for predicting features from input parameters using a neural network.

    Supports loading pretrained networks stored in a specific npz format. Designed for rapid evaluation
    and differentiation of outputs with respect to inputs.

    This is an adapted version of CosmoPower Jax emulator (https://github.com/dpiras/cosmopower-jax), which is a JAX-based emulator for predicting power spectra from input parameters using a neural network.

    Parameters
    ----------
    filepath : string
        Full path to the .pkl file containing the pretrained model.
    verbose : bool, default=True
        Whether to print information during initialization.
    """
    def __init__(self, filepath=None, verbose=True):
        import pickle

        if verbose:
            print(filepath)

        # Load the pickle model file
        with open(filepath, 'rb') as f:
            loaded_variable_dict = pickle.load(f)

        if verbose:
            print(loaded_variable_dict.keys())

        # Extract relevant values from the loaded dictionary
        self.parameter_ranges = loaded_variable_dict['parameter_ranges']
        feature_dimensions = loaded_variable_dict['feature_dimensions']

        # Group activation hyperparameters and transpose weights to match JAX's convention
        hyper_params = np.array(loaded_variable_dict['hyper_params'])
        weights = []
        for i in range(len(list(loaded_variable_dict['weights'].keys()))):
            weights.append([np.array(loaded_variable_dict['weights'][f'layer_{i}']['w'], dtype=np.float32),
                            np.array(loaded_variable_dict['weights'][f'layer_{i}']['b'], dtype=np.float32)])

        # Store model components as attributes
        self.weights = weights
        self.hyper_params = hyper_params
        self.param_train_mean = np.array(loaded_variable_dict['param_train_mean'])
        self.param_train_std = np.array(loaded_variable_dict['param_train_std'])
        self.feature_train_mean = loaded_variable_dict['feature_train_mean']
        self.feature_train_std = loaded_variable_dict['feature_train_std']
        self.n_parameters = loaded_variable_dict['n_parameters']
        self.parameters = loaded_variable_dict['parameters']
        self.scaling_division = loaded_variable_dict['scaling_division']
        self.scaling_subtraction = loaded_variable_dict['scaling_subtraction']
        self.modes = jnp.arange(0, feature_dimensions)  # useful indexing range

    def _dict_to_ordered_arr_jax(self, input_dict):
        """Convert dictionary of input parameters to ordered array based on trained model."""
        if self.parameters is not None:
            return jnp.stack([input_dict[k] for k in self.parameters], axis=1)
        else:
            return jnp.stack([input_dict[k] for k in input_dict], axis=1)

    @partial(jit, static_argnums=0)
    def _activation(self, x, a, b):
        """Custom activation function as used in training.
        Parameters `a` and `b` control the nonlinearity.
        """
        return jnp.multiply(jnp.add(b, jnp.multiply(sigmoid(jnp.multiply(a, x)), jnp.subtract(1., b))), x)

    @partial(jit, static_argnums=0)
    def _predict(self, weights, hyper_params, param_train_mean, param_train_std,
                 feature_train_mean, feature_train_std, input_vec):
        """Forward pass through the neural network to produce feature predictions."""
        # Normalize input vector
        layer_out = [(input_vec - param_train_mean) / param_train_std]

        # Apply each hidden layer: linear -> activation
        for i in range(len(weights[:-1])):
            w, b = weights[i]
            alpha, beta = hyper_params[i]
            act = jnp.dot(layer_out[-1], w.T) + b  # Linear transformation
            layer_out.append(self._activation(act, alpha, beta))  # Apply activation

        # Final linear layer without activation
        w, b = weights[-1]
        preds = jnp.dot(layer_out[-1], w.T) + b

        # De-normalize predictions
        preds = preds * feature_train_std + feature_train_mean
        return preds.squeeze()

    @partial(jit, static_argnums=0)
    def predict(self, input_vec):
        """Predict features from input parameters using the emulator."""
        if isinstance(input_vec, dict):
            input_vec = self._dict_to_ordered_arr_jax(input_vec)

        # Ensure proper shape
        if len(input_vec.shape) == 1:
            input_vec = input_vec.reshape(-1, self.n_parameters)
        assert len(input_vec.shape) == 2

        return self._predict(self.weights, self.hyper_params, self.param_train_mean,
                             self.param_train_std, self.feature_train_mean, self.feature_train_std,
                             input_vec)

    @partial(jit, static_argnums=0)
    def rescaled_predict(self, input_vec):
        """Return emulator prediction scaled to match physical values."""
        return self.predict(input_vec) * self.scaling_division + self.scaling_subtraction
