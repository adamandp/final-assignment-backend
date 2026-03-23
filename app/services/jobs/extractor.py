import numpy as np
import pandas as pd
import antropy as ant
import pywt
from scipy import stats
import mne
from mne_connectivity import spectral_connectivity_epochs

class Extractor:
    __bands = {
        'delta': (1, 4),
        'theta': (5, 8),
        'alpha': (9, 13),
        'beta':  (14, 30),
        'gamma': (31, 48)
    }

    @classmethod
    def extractor(cls, epochs):
        all_features = []
        ch_names = epochs.ch_names
        epochs_arr = epochs.get_data()
        
        # frequency domain
        spectrum = cls.__get_spectrum(epochs)
        g_psb = cls.__get_power_spectral_band(spectrum, cls.__bands)
        g_dfreq = cls.__get_dominant_frequency(spectrum, cls.__bands)
        g_ss = cls.__get_spectral_shape(spectrum)

        # time domain
        g_hp = cls.__get_hjorth_params(epochs_arr)
        g_entrop = cls.__get_entropies(epochs_arr)
        g_we = cls.__get_wavelet_energy(epochs_arr)
        g_wpe = cls.__get_wavelet_packet_energy(epochs_arr)
        g_temp = cls.__get_temporal(epochs_arr)

        for i in range(len(epochs)):            
            for ch_idx, ch_name in enumerate(ch_names):

                # frequency domain
                psb = {k: v[i][ch_idx] for k, v in g_psb.items()}
                dfreq = {k: v[i][ch_idx] for k, v in g_dfreq.items()}
                ss = {k: v[i][ch_idx] for k, v in g_ss.items()}
                
                # time domain
                hp = {k: v[i][ch_idx] for k, v in g_hp.items()}
                entropies = {k: v[i][ch_idx] for k, v in g_entrop.items()}
                we = {k: v[i][ch_idx] for k, v in g_we.items()}
                wpe = {k: v[i][ch_idx] for k, v in g_wpe.items()}
                temp = {k: v[i][ch_idx] for k, v in g_temp.items()}


                epoch_features = {
                    **psb,
                    "theta/alpha": psb['theta'] / psb['alpha'],
                    "theta/beta": psb['theta'] / psb['beta'],
                    "gamma/alpha": psb['gamma'] / psb['alpha'],
                    **hp,
                    **dfreq,
                    **entropies,
                    **we,
                    **wpe,
                    **ss,
                    **temp,
                    
                    "ch_name": ch_name,
                }
                    
                all_features.append(epoch_features)

        return pd.DataFrame(all_features)
    
    def feature_extraction_connectivity(epoch):
        indices = np.triu_indices(19, k=1)
        standard_channels = [
            'Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 
            'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz'
        ]
        
        mapping = {'T7': 'T3', 'T8': 'T4', 'P7': 'T5', 'P8': 'T6'}
        for old_name, new_name in mapping.items():
            if old_name in epoch.ch_names:
                mne.rename_channels(epoch.info, {old_name: new_name})

        epoch.pick_channels(standard_channels, ordered=True)
        
        con = spectral_connectivity_epochs(
            epoch,
            method="ppc",
            indices=indices,
            mode="multitaper",
            sfreq=250,
            fmin=1,
            fmax=4,
            faverage=True,
            n_jobs=1,
            verbose=False
        )
        
        con_values = con.get_data().squeeze()    
        
        column_names = [
            f"{standard_channels[i]}-{standard_channels[j]}" for i, j in zip(indices[0], indices[1])
        ]

        return pd.DataFrame([con_values], columns=column_names)

    @staticmethod
    def __get_spectrum(epochs):
        spectrum = epochs.compute_psd(
            method='welch', 
            fmin=1, 
            fmax=48, 
            verbose=False
        )

        return spectrum
    
    @staticmethod
    def __get_power_spectral_band(spectrum, bands):
        return {
            name: np.mean(spectrum.get_data(fmin=low, fmax=high), axis=-1)
            for name, (low, high) in bands.items()
        }
    
    @staticmethod
    def __get_hjorth_params(epoch):
        activity = np.var(epoch, axis=-1)
        
        d1 = np.diff(epoch, axis=-1)
        d2 = np.diff(d1, axis=-1)
        
        var_d1 = np.var(d1, axis=-1)
        var_d2 = np.var(d2, axis=-1)
        
        mobility = np.sqrt(var_d1 / (activity + 1e-10))
        complexity = np.sqrt(var_d2 / (var_d1 + 1e-10)) / (mobility + 1e-10)
        
        return {
            "hjorth_activity": activity,
            "hjorth_mobility": mobility,
            "hjorth_complexity": complexity,
        }
    
    @staticmethod
    def __get_dominant_frequency(spectrum, bands):
        return {
            name: freqs[np.argmax(psd, axis=-1)]
            for name, (low, high) in bands.items()
            for psd, freqs in [
                spectrum.get_data(return_freqs=True, fmin=low, fmax=high)
            ]
        }
    
    @staticmethod
    def __get_entropies(epoch):
        funcs = {
            "se": ant.sample_entropy,
            "ae": ant.app_entropy,
            "pe": lambda x: ant.perm_entropy(x, normalize=True),
            "svd_e": lambda x: ant.svd_entropy(x, normalize=True),
        }

        return {
            name: np.apply_along_axis(func, axis=-1, arr=epoch)
            for name, func in funcs.items()
        }
    
    @staticmethod
    def __get_wavelet_energy(epochs_arr):
        wavelet='db4'
        level=4
        
        def _compute(signal):
            coeffs = pywt.wavedec(signal, wavelet, level=level)
            energies = np.array([np.sum(c**2) for c in coeffs])

            return np.array([
                energies[0],
                energies[1:].mean(),
                energies[0] / (energies.sum() + 1e-10)
            ])

        all_feats = np.apply_along_axis(_compute, axis=-1, arr=epochs_arr)

        names = [
            "approximate_wavelet_energy",
            "detailed_wavelet_energy",
            "relative_wavelet_energy"
        ]

        return {name: all_feats[:, :, i] for i, name in enumerate(names)}
    
    @staticmethod
    def __get_wavelet_packet_energy(epochs_arr):
        wavelet='db4'
        level=4

        def _compute(signal):
            wp = pywt.WaveletPacket(signal, wavelet=wavelet, mode='symmetric', maxlevel=level)
            energies = np.array([np.sum(n.data**2) for n in wp.get_level(level, 'freq')])

            return np.array([
                energies[0],
                energies[1:].mean(),
                energies[0] / (energies.sum() + 1e-10)
            ])

        all_feats = np.apply_along_axis(_compute, axis=-1, arr=epochs_arr)

        names = [
            "approximate_wavelet_packet_energy",
            "detailed_wavelet_packet_energy",
            "relative_wavelet_packet_energy"
        ]

        return {name: all_feats[:, :, i] for i, name in enumerate(names)}
    
    @staticmethod
    def __get_spectral_shape(spectrum):
        psds = spectrum.get_data()
        freqs = spectrum.freqs

        psd_norm = psds / (psds.sum(axis=-1, keepdims=True) + 1e-10)

        centroid = (psd_norm * freqs).sum(axis=-1)

        freq_diff = freqs - centroid[..., None]
        spread = np.sqrt((psd_norm * freq_diff**2).sum(axis=-1))

        skew = (psd_norm * freq_diff**3).sum(axis=-1) / (spread**3 + 1e-10)
        kurt = (psd_norm * freq_diff**4).sum(axis=-1) / (spread**4 + 1e-10)

        flux = np.diff(psds, axis=-1)**2
        flux = flux.sum(axis=-1)

        def rolloff_1d(psd):
            cum = np.cumsum(psd)
            idx = np.searchsorted(cum, 0.85 * cum[-1])
            return freqs[idx]

        rolloff = np.apply_along_axis(rolloff_1d, axis=-1, arr=psds)

        return {
            "spectral_centroid": centroid,
            "spectral_spread": spread,
            "spectral_skewness": skew,
            "spectral_kurtosis": kurt,
            "spectral_flux": flux,
            "spectral_rolloff": rolloff,
        }
    
    @staticmethod
    def __get_temporal(epochs_arr):
        x = epochs_arr
        
        skewness = stats.skew(x, axis=-1)
        kurt = stats.kurtosis(x, axis=-1)
        peak = np.max(np.abs(x), axis=-1)
        
        rms = np.sqrt(np.mean(x**2, axis=-1))
        mean_abs = np.mean(np.abs(x), axis=-1)
        smr = (np.mean(np.sqrt(np.abs(x)), axis=-1))**2
        
        shape_factor = rms / (mean_abs + 1e-10)
        impulse_factor = peak / (mean_abs + 1e-10)
        crest_factor = peak / (rms + 1e-10)
        clearance_factor = peak / (smr + 1e-10)
        
        diff_x = np.abs(np.diff(x, axis=-1))
        wamp = np.sum(diff_x > 1e-5, axis=-1)
        
        zcr = np.sum(np.diff(np.sign(x), axis=-1) != 0, axis=-1)
        
        return {
            "skewness": skewness,
            "kurtosis": kurt,
            "shape_factor": shape_factor,
            "peak_amplitude": peak,
            "impulse_factor": impulse_factor,
            "crest_factor": crest_factor,
            "clearance_factor": clearance_factor,
            "willison_amplitude": wamp,
            "zero_crossing": zcr,
        }