"""
Data Loader and Inspector for Canadian Institute for Cybersecurity (CIC) Datasets.
Provides genuine ingestion, validation, metadata extraction, and stratified sampling.
"""

import os
import glob
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")


def find_default_dataset() -> Optional[str]:
    """Discovers an available authentic CIC-IDS2017 CSV file in data/raw/."""
    if not os.path.exists(DEFAULT_DATA_DIR):
        return None
    
    preferred = [
        "cic_ids2017_web_attacks.csv",
        "cic_ids2017_webattacks.csv",
        "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
        "cic_ids2017_portscan.csv",
        "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
        "raw_web_attacks.csv"
    ]
    for filename in preferred:
        path = os.path.join(DEFAULT_DATA_DIR, filename)
        if os.path.exists(path) and os.path.getsize(path) > 1024:
            return path
    
    csv_files = glob.glob(os.path.join(DEFAULT_DATA_DIR, "*.csv"))
    if csv_files:
        return csv_files[0]
    return None


def load_dataset(file_path: str, nrows: Optional[int] = None) -> pd.DataFrame:
    """
    Loads raw CSV dataset safely, handling encoding, leading column whitespace,
    and irregular lines without data fabrication.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding="utf-8", nrows=nrows, low_memory=False, on_bad_lines="skip")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin1", nrows=nrows, low_memory=False, on_bad_lines="skip")
    
    # Strip whitespace from column headers (characteristic of CIC-IDS2017)
    df.columns = df.columns.str.strip()
    
    if "Label" not in df.columns:
        # Case insensitive check for label column
        label_col = next((c for c in df.columns if c.lower() == "label"), None)
        if label_col:
            df.rename(columns={label_col: "Label"}, inplace=True)
        else:
            raise ValueError(f"Dataset does not contain a 'Label' column. Available columns: {list(df.columns)[:8]}...")
    
    # Sanitize label column to avoid Windows cp1252 print errors & normalize en-dashes
    df["Label"] = df["Label"].astype(str).str.replace(r"[^\x00-\x7F]+", "-", regex=True).str.strip()
            
    return df


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspects raw dataset and extracts authentic statistical profiles.
    Does NOT fabricate any numbers.
    """
    total_records = len(df)
    total_features = len(df.columns) - 1 # excluding Label
    
    # Analyze classes
    label_series = df["Label"].astype(str).str.strip()
    class_counts = label_series.value_counts().to_dict()
    
    # Determine Normal vs Attack breakdown
    normal_count = sum(count for label, count in class_counts.items() if label.upper() == "BENIGN")
    attack_count = total_records - normal_count
    normal_pct = (normal_count / total_records * 100) if total_records > 0 else 0
    attack_pct = (attack_count / total_records * 100) if total_records > 0 else 0
    
    # Numerical and categorical inspection
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if "Label" in num_cols:
        num_cols.remove("Label")
    
    # Count NaNs and Infs accurately
    nan_count = int(df.isna().sum().sum())
    
    # Count infinite values across numeric columns
    inf_count = 0
    for col in num_cols:
        inf_count += int(np.isinf(df[col]).sum())
        
    duplicate_count = int(df.duplicated().sum())
    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    
    return {
        "num_records": total_records,
        "num_features": total_features,
        "numeric_features": len(num_cols),
        "class_distribution": class_counts,
        "normal_count": normal_count,
        "attack_count": attack_count,
        "normal_pct": round(normal_pct, 2),
        "attack_pct": round(attack_pct, 2),
        "missing_values": nan_count,
        "infinite_values": inf_count,
        "duplicate_rows": duplicate_count,
        "memory_mb": memory_mb,
        "feature_names": [c for c in df.columns if c != "Label"]
    }


def stratified_subsample(df: pd.DataFrame, max_samples: int = 10000, random_state: int = 42) -> pd.DataFrame:
    """
    Extracts a statistically representative, stratified subset of the real dataset
    when full dataset exceeds computational simulation feasibility.
    Preserves minority attack classes.
    """
    if len(df) <= max_samples:
        return df.copy()
    
    label_col = "Label"
    groups = []
    total = len(df)
    
    for _, group in df.groupby(label_col):
        fraction = len(group) / total
        n_group = max(20, int(max_samples * fraction))
        if len(group) <= n_group:
            groups.append(group)
        else:
            groups.append(group.sample(n=n_group, random_state=random_state))
            
    sampled = pd.concat(groups).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    if len(sampled) > max_samples:
        sampled = sampled.head(max_samples)
        
    return sampled
