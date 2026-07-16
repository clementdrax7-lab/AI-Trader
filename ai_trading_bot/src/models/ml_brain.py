import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import os

class OnlineMLBrain:
    """Incremental Learning engine featuring historical training dataset ingestion."""
    def __init__(self):
        self.model = SGDClassifier(loss='log_loss', alpha=0.01, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def _prepare_features(self, killzone: str, bias: int, entry: float, fvg_level: float) -> np.ndarray:
        killzone_map = {"ASIA_RANGE": 1, "LONDON_KILL": 2, "NY_AM_KILL": 3, "LONDON_CLOSE": 4, "NY_PM_KILL": 5}
        zone_encoded = killzone_map.get(killzone, 0)
        fvg_size = abs(entry - fvg_level) if fvg_level else 0.0
        return np.array([[zone_encoded, float(bias), float(fvg_size), float(entry)]])

    def train_on_csv(self, csv_path: str):
        """Ingests historical CSV metrics to optimize weights prior to live execution loops."""
        if not os.path.exists(csv_path):
            print(f"⚠️ Pre-training skipped: No history file found at {csv_path}. Starting clean.")
            return

        print(f"🧠 [ML PRE-TRAINING] Processing data from {csv_path}...")
        try:
            df = pd.read_csv(csv_path)
            # Require standard target labels inside your CSV sheets
            if not all(col in df.columns for col in ['bias', 'entry', 'fvg_level', 'target_win']):
                print("❌ CSV missing required structural columns: ['bias', 'entry', 'fvg_level', 'target_win']")
                return

            X_list = []
            for _, row in df.iterrows():
                feat = self._prepare_features("ALL_SESSIONS", row['bias'], row['entry'], row['fvg_level'])
                X_list.append(feat[0])

            X = np.array(X_list)
            y = df['target_win'].to_numpy()

            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Perform initial optimization fit
            self.model.partial_fit(X_scaled, y, classes=np.array([0, 1]))
            self.is_trained = True
            print(f"✅ Success! Ingested {len(df)} historical entries. ML Brain optimized.")
        except Exception as e:
            print(f"❌ Error during historical training: {e}")

    def predict_confidence(self, killzone: str, bias: int, entry: float, fvg_level: float) -> float:
        if not self.is_trained:
            return 0.75
        X = self._prepare_features(killzone, bias, entry, fvg_level)
        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)
        return float(probabilities[0][1])

    def learn_from_outcome(self, killzone: str, bias: int, entry: float, fvg_level: float, outcome: int):
        X = self._prepare_features(killzone, bias, entry, fvg_level)
        if not self.is_trained:
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            self.model.partial_fit(X_scaled, np.array([outcome]), classes=np.array([0, 1]))
            self.is_trained = True
        else:
            self.scaler.partial_fit(X)
            X_scaled = self.scaler.transform(X)
            self.model.partial_fit(X_scaled, np.array([outcome]))
        print(f"🧠 [LIVE UPDATED] Calculated feedback logged: {'WIN' if outcome == 1 else 'LOSS'}")
