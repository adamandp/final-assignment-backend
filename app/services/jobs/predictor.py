import numpy as np
import os
import joblib
import logging

logger = logging.getLogger(__name__)

class Predictor:
    def __init__(self):
        self.classes = ["Alzheimer", "MCI", "Normal"]
        self.models = {}
        self._load_models()

    def _load_models(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(base_dir, "model", "pickles")
        
        logger.info(f"🧠 Loading ML models from {model_path}...")
        
        if not os.path.exists(model_path):
            logger.error(f"❌ Model path not found: {model_path}")
            return

        for file in os.listdir(model_path):
            if file.endswith(".pkl"):
                name = file.replace(".pkl", "").replace("model_", "")
                full_path = os.path.join(model_path, file)
                self.models[name] = joblib.load(full_path)
        
        logger.info(f"✅ Loaded {len(self.models)} models successfully!")

    def predict(self, df, df_con):
        all_probas = []

        for name, model in self.models.items():
            if name == 'con':
                X = df_con
            else:
                df_ch = df[df['ch_name'] == name]
                if df_ch.empty:
                    continue
                X = df_ch.drop(columns=['ch_name'])

            # Ambil probabilitas
            proba = model.predict_proba(X)
            avg_proba = np.mean(proba, axis=0)
            all_probas.append(avg_proba)

        if not all_probas:
            raise ValueError("No valid predictions found for any channel.")

        final_proba = np.mean(all_probas, axis=0)
        final_idx = int(np.argmax(final_proba))

        prob_map = {
            self.classes[i]: float(final_proba[i]) 
            for i in range(len(self.classes))
        }

        return {
            "prediction": self.classes[final_idx],
            "probabilities": prob_map
        }

predictor = Predictor()