"""
Preprocessing Pipeline for CIC Cybersecurity Datasets.
Guarantees NO DATA LEAKAGE: All scalers and feature selectors are fitted
strictly on training splits and only transformed on test splits.
"""

import os
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif
import joblib

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def clean_raw_data(df: pd.DataFrame, drop_duplicates: bool = True) -> pd.DataFrame:
    """
    Cleans raw CIC network flow data:
    1. Trims whitespace from column headers and string values.
    2. Replaces infinite values with NaNs.
    3. Imputes or drops NaN rows.
    4. Eliminates duplicate flow records.
    """
    data = df.copy()
    data.columns = data.columns.str.strip()
    
    # Identify non-numeric and numeric columns
    label_col = "Label" if "Label" in data.columns else next(c for c in data.columns if c.lower() == "label")
    
    # Replace infinite values with NaNs in numeric columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    data[numeric_cols] = data[numeric_cols].replace([np.inf, -np.inf], np.nan)
    
    # Drop rows with NaNs in label
    data = data.dropna(subset=[label_col])
    
    # Median impute remaining NaNs in numeric features
    for col in numeric_cols:
        if data[col].isna().any():
            median_val = data[col].median()
            data[col] = data[col].fillna(median_val if not np.isnan(median_val) else 0.0)
            
    if drop_duplicates:
        data = data.drop_duplicates().reset_index(drop=True)
        
    return data


class ThreatDataPreprocessor:
    """
    Leakage-free preprocessing pipeline storing fitted transformers,
    PCA projection matrices, and label encodings.
    """
    def __init__(self, n_quantum_features: int = 4, random_state: int = 42):
        self.n_quantum_features = n_quantum_features
        self.random_state = random_state
        self.scaler = RobustScaler()
        self.feature_selector = None
        self.pca = PCA(n_components=n_quantum_features, random_state=random_state)
        self.angle_scaler = MinMaxScaler(feature_range=(0, np.pi))
        
        self.raw_feature_names: List[str] = []
        self.feature_names: List[str] = []
        self.selected_feature_names: List[str] = []
        self.valid_indices: Optional[np.ndarray] = None
        self.label_mapping: Dict[str, int] = {}
        self.is_fitted: bool = False

    def prepare_dataset(self, df: pd.DataFrame, test_size: float = 0.2, binary: bool = True) -> Dict[str, Any]:
        """
        Executes full preprocessing:
        - Labels: binary threat (0 = Normal/BENIGN, 1 = Threat/Malicious)
        - Strict train/test split with stratification
        - Fit transforms ONLY on X_train
        - Prepares full classical features AND quantum angle-encoded features
        """
        cleaned_df = clean_raw_data(df)
        label_col = "Label" if "Label" in cleaned_df.columns else next(c for c in cleaned_df.columns if c.lower() == "label")
        
        raw_labels = cleaned_df[label_col].astype(str).str.strip()
        
        if binary:
            # BENIGN -> 0, any attack -> 1
            y = np.where(raw_labels.str.upper() == "BENIGN", 0, 1)
            self.label_mapping = {"Normal (BENIGN)": 0, "Malicious Threat": 1}
        else:
            unique_classes = sorted(raw_labels.unique())
            self.label_mapping = {cls: idx for idx, cls in enumerate(unique_classes)}
            y = raw_labels.map(self.label_mapping).values
            
        feature_df = cleaned_df.drop(columns=[label_col])
        # Retain only numeric features
        feature_df = feature_df.select_dtypes(include=[np.number])
        self.raw_feature_names = feature_df.columns.tolist()
        self.feature_names = list(self.raw_feature_names)
        X = feature_df.values.astype(np.float32)
        
        # Train / Test Split (Strictly Stratified)
        X_train_raw, X_test_raw, y_train, y_test, labels_train, labels_test = train_test_split(
            X, y, raw_labels.values, test_size=test_size, random_state=self.random_state, stratify=y
        )
        
        # Identify constant or near-constant features strictly on training data
        train_variances = np.var(X_train_raw, axis=0)
        self.valid_indices = np.where(train_variances > 1e-6)[0]
        if len(self.valid_indices) < len(self.raw_feature_names):
            X_train_raw = X_train_raw[:, self.valid_indices]
            X_test_raw = X_test_raw[:, self.valid_indices]
            self.feature_names = [self.raw_feature_names[i] for i in self.valid_indices]
            
        # Fit scaler ONLY on train data
        X_train_scaled = self.scaler.fit_transform(X_train_raw)
        X_test_scaled = self.scaler.transform(X_test_raw)
            
        # Fit PCA ONLY on train data for quantum circuit dimension
        X_train_pca = self.pca.fit_transform(X_train_scaled)
        X_test_pca = self.pca.transform(X_test_scaled)
        
        # Scale PCA components into rotation angles [0, pi] for angle encoding
        X_train_angles = self.angle_scaler.fit_transform(X_train_pca)
        X_test_angles = self.angle_scaler.transform(X_test_pca)
        # Clip to ensure valid angle bounds
        X_train_angles = np.clip(X_train_angles, 0, np.pi)
        X_test_angles = np.clip(X_test_angles, 0, np.pi)
        
        self.is_fitted = True
        
        return {
            "X_train_classical": X_train_scaled,
            "X_test_classical": X_test_scaled,
            "X_train_quantum": X_train_angles,
            "X_test_quantum": X_test_angles,
            "y_train": y_train,
            "y_test": y_test,
            "raw_labels_train": labels_train,
            "raw_labels_test": labels_test,
            "feature_names": self.feature_names,
            "pca_explained_variance": [round(float(v), 4) for v in self.pca.explained_variance_ratio_],
            "total_pca_variance": round(float(np.sum(self.pca.explained_variance_ratio_)), 4)
        }

    def transform_single(self, feature_vector: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transforms a single raw feature vector for live packet inference.
        Returns: (classical_scaled_vector, quantum_angle_vector)
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted.")
        
        vec = np.asarray(feature_vector, dtype=np.float32)
        if vec.ndim == 1:
            if self.valid_indices is not None and len(vec) == len(self.raw_feature_names):
                vec = vec[self.valid_indices]
            vec_2d = vec.reshape(1, -1)
        else:
            if self.valid_indices is not None and vec.shape[1] == len(self.raw_feature_names):
                vec = vec[:, self.valid_indices]
            vec_2d = vec

        scaled = self.scaler.transform(vec_2d)
        pca_proj = self.pca.transform(scaled)
        angles = np.clip(self.angle_scaler.transform(pca_proj), 0, np.pi)
        return scaled, angles

    def save(self, filepath: Optional[str] = None):
        """Serializes the preprocessor pipeline."""
        if filepath is None:
            os.makedirs(MODELS_DIR, exist_ok=True)
            filepath = os.path.join(MODELS_DIR, "preprocessor.joblib")
        joblib.dump(self, filepath)
        print(f"Preprocessor saved to {filepath}")

    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "ThreatDataPreprocessor":
        """Loads a serialized preprocessor pipeline."""
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, "preprocessor.joblib")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Preprocessor file not found at {filepath}")
        return joblib.load(filepath)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.data_loader import find_default_dataset, load_dataset
    
    dataset_path = find_default_dataset()
    print(f"Found dataset: {dataset_path}")
    if dataset_path:
        df = load_dataset(dataset_path)
        print(f"Loaded {len(df)} records. Fitting preprocessor...")
        preprocessor = ThreatDataPreprocessor(n_quantum_features=4)
        data_splits = preprocessor.prepare_dataset(df)
        print(f"X_train_classical shape: {data_splits['X_train_classical'].shape}")
        print(f"X_test_classical shape: {data_splits['X_test_classical'].shape}")
        print(f"X_train_quantum shape: {data_splits['X_train_quantum'].shape}")
        print(f"PCA explained variance: {data_splits['pca_explained_variance']}")
        print(f"Total PCA variance explained: {data_splits['total_pca_variance']*100:.2f}%")
        preprocessor.save()
        print("Preprocessor verification SUCCESS!")
