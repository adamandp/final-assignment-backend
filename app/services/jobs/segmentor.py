import mne

class Segmentor:
    def segmentor(raw):
        epoch = mne.make_fixed_length_epochs(
            raw, 
            duration=10.0, 
            preload=True,
            verbose=False
        )
        
        return epoch