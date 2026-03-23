from mne.preprocessing import ICA
from mne_icalabel import label_components

class Preprocessor:

    @classmethod
    def preprocessing(cls, raw):
        raw = cls.__prerequisite_preprocess(raw)
        raw = cls.__artifact_filter(raw)
        raw = cls.__finalize_preprocess(raw)

        return raw

    @staticmethod
    def __prerequisite_preprocess(raw):
        raw.filter(l_freq=1, h_freq=100, verbose=False)
        raw.set_montage('standard_1020', match_case=False, verbose=False)
        raw.set_eeg_reference('average', projection=False, verbose=False)
        
        return raw
    
    @staticmethod
    def __artifact_filter(raw):
        ica = ICA(
            n_components=None, 
            max_iter='auto', 
            random_state=97, 
            method='infomax',
            fit_params=dict(extended=True),
        )
        
        ica.fit(raw, verbose=False)

        labels = label_components(raw, ica, method='iclabel')
        
        exclude = []
        artifact_categories = [
            'eye', 
            'heart', 
            'muscle', 
            'line noise', 
            'channel noise'
        ]
        
        category_map = {
            'brain': 0, 
            'muscle': 1, 
            'eye': 2, 
            'heart': 3, 
            'line noise': 4, 
            'channel noise': 5, 
            'other': 6
        }

        for i, label in enumerate(labels['labels']):
            probs_raw = labels['y_pred_proba'][i]
            
            if hasattr(probs_raw, "__len__"):
                target_idx = category_map[label]
                prob = probs_raw[target_idx]
            else:
                prob = probs_raw

            if label in artifact_categories and prob > 0.50:
                exclude.append(i)
        
        ica.exclude = exclude

        raw_clean = ica.apply(raw.copy(), verbose=False)
        
        return raw_clean
    
    @staticmethod
    def __finalize_preprocess(raw):
        raw.resample(250, verbose=False)
        raw.filter(l_freq=1, h_freq=48, verbose=False)
        data = raw.get_data()
        max_val = abs(data).max()

        if max_val < 1e-3:
            raw.apply_function(lambda x: x * 1e6, verbose=False)

        return raw