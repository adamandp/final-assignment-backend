import mne
import os

class Loader:

    @classmethod
    def load_raw(cls, file_path):
        extension = os.path.splitext(file_path)[1].lower()

        if file_path.endswith('.edf'):
            raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        elif file_path.endswith('.set'):
            raw = mne.io.read_raw_eeglab(file_path, preload=True, verbose=False)
        elif file_path.endswith('.fif'):
            raw = mne.io.read_raw_fif(file_path, preload=True, verbose=False)
        else:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )
        return raw