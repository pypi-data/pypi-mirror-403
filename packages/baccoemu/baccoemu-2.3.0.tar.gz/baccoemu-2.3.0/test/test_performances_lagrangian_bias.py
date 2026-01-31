import numpy as np
import baccoemu as baccoemu
import time
import copy

#Calling baccoemu to compute the Lagrangian bias power spectra

emulator = baccoemu.Lbias_expansion()

kk = np.logspace(-1,np.log10(0.5), 50)

for func_name in ['get_lpt_pk', 'get_nonlinear_pnn']:
    params = {
        'omega_cold'  :  0.315,
        'A_s'           :  2e-9,
        'omega_baryon'  :  0.05,
        'ns'            :  0.96,
        'hubble'        :  0.67,
        'neutrino_mass' :  0.0,
        'w0'            : -1.0,
        'wa'            :  0.0,
        'expfactor'     :  1,
    }

    params_sigma8 = copy.deepcopy(params)
    del params_sigma8['A_s']
    params_sigma8['sigma8_cold'] = 0.78

    t0 = time.time()
    k, plpt = getattr(emulator, func_name)(k=kk,**params) # this calls the emulator of the LPT-predicted 15 lagrangian bias expansion terms
    t1 = time.time()

    print("Performances of the Lagrangian bias emulator:")
    print("---------------------")
    print(f"15 LPT terms emulator: {t1-t0} (1 evaluation)")
    print("---------------------")

    aa = np.linspace(0.5,1,100)
    omm = np.linspace(0.3,0.35,100)
    vec_as = np.linspace(1.85e-9,2.15e-9,100)

    par_arr = []
    par_arr_s8 = []
    for i,a in enumerate(aa):
        pdict = copy.deepcopy(params)
        pdict['expfactor'] = a
        pdict['omega_cold'] = omm[i]
        pdict['A_s'] = vec_as[i]
        par_arr.append(pdict)

    t0 = time.time()
    pk = np.array([getattr(emulator, func_name)(k=kk,**par_arr[i])[1] for i,a in enumerate(aa)])
    t1 = time.time()

    pk = np.swapaxes(pk,0,1)

    print("---------------------")
    print(f"15 LPT terms emulator: {t1-t0} (100 evaluations)")
    print("---------------------")

    g_params = copy.deepcopy(params)
    g_params['expfactor'] = aa
    g_params['omega_cold'] = omm
    g_params['A_s'] = vec_as

    t0 = time.time()
    k, pk_grid = getattr(emulator, func_name)(k=kk,**g_params)
    t1 = time.time()

    print("---------------------")
    print("Using vectorization:")
    print(f"15 LPT terms emulator: {t1-t0} (100 evaluations)")
    print("---------------------")

    ratios = np.abs(pk/pk_grid-1.)
    message = f'Emulator with vectorization in disagreement at more than 0.1% ({np.amax(ratios)*100}%!)'
    assert np.all(ratios<=1e-3), message

print("All tests passed!")
