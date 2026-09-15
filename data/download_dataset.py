"""
CIC-IDS2017 Real Dataset Downloader & Validator.

Downloads genuine network traffic CSVs from the Canadian Institute for Cybersecurity (CIC)
mirror repositories (University of New Brunswick / Hugging Face mirror) and validates schema.
"""

import os
import sys
import urllib.request
import argparse
import pandas as pd

MIRROR_URLS = {
    "web_attacks": "https://huggingface.co/datasets/c01dsnap/CIC-IDS2017/resolve/main/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "portscan": "https://huggingface.co/datasets/c01dsnap/CIC-IDS2017/resolve/main/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv"
}

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")


def ensure_data_dir():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)


def download_file(url: str, dest_path: str, chunk_size: int = 1024 * 1024, max_bytes: int = None):
    """Downloads a file with streaming progress, optional byte limit for quick sampling."""
    print(f"Connecting to: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    with urllib.request.urlopen(req) as response:
        total_size = response.headers.get("Content-Length")
        if total_size:
            total_size = int(total_size)
            print(f"Total remote file size: {total_size / (1024 * 1024):.2f} MB")
        
        bytes_downloaded = 0
        with open(dest_path, "wb") as out_file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                bytes_downloaded += len(chunk)
                if total_size:
                    pct = (bytes_downloaded / total_size) * 100
                    print(f"\rDownloaded: {bytes_downloaded / (1024*1024):.2f} MB ({pct:.1f}%)", end="", flush=True)
                else:
                    print(f"\rDownloaded: {bytes_downloaded / (1024*1024):.2f} MB", end="", flush=True)
                
                if max_bytes and bytes_downloaded >= max_bytes:
                    print(f"\nReached configured download limit of {max_bytes / (1024*1024):.2f} MB for sample.")
                    break
        print(f"\nSaved to: {dest_path}")


def validate_and_sample_dataset(raw_csv_path: str, sample_csv_path: str, sample_size: int = 10000):
    """
    Validates the downloaded CIC-IDS2017 CSV, cleans incomplete final lines if sampled,
    and extracts a balanced stratified sample for quick demonstration if requested.
    """
    print(f"\nValidating downloaded CSV: {raw_csv_path}...")
    try:
        # Read with on_bad_lines='skip' in case stream was cut midway
        df = pd.read_csv(raw_csv_path, encoding="utf-8", low_memory=False, on_bad_lines="skip")
    except UnicodeDecodeError:
        df = pd.read_csv(raw_csv_path, encoding="latin1", low_memory=False, on_bad_lines="skip")
    
    # Clean column names (CIC-IDS2017 columns have leading spaces)
    df.columns = df.columns.str.strip()
    
    if "Label" not in df.columns:
        raise ValueError(f"'Label' column not found in {df.columns.tolist()[:10]}")
    
    # Sanitize label column to avoid Windows cp1252 print errors
    df["Label"] = df["Label"].astype(str).str.replace(r"[^\x00-\x7F]+", "-", regex=True).str.strip()
    
    print(f"Dataset successfully loaded: {len(df):,} records, {len(df.columns)} features.")
    print("Class distribution in downloaded file:")
    print(df["Label"].value_counts().to_string())
    
    if sample_size and len(df) > sample_size:
        # Stratified sampling to maintain all attack classes
        print(f"\nExtracting stratified sample of {sample_size:,} records for fast, authentic evaluation...")
        stratified_groups = []
        for label, group in df.groupby("Label"):
            ratio = len(group) / len(df)
            n_samples = max(20, int(sample_size * ratio))
            if len(group) < n_samples:
                stratified_groups.append(group)
            else:
                stratified_groups.append(group.sample(n_samples, random_state=42))
        
        sample_df = pd.concat(stratified_groups).sample(frac=1.0, random_state=42).reset_index(drop=True)
        # Cap to exact sample_size if needed
        if len(sample_df) > sample_size:
            sample_df = sample_df.head(sample_size)
        
        sample_df.to_csv(sample_csv_path, index=False)
        print(f"Stratified sample saved to {sample_csv_path} ({len(sample_df):,} records).")
        print("Sample class distribution:")
        print(sample_df["Label"].value_counts().to_string())
    else:
        df.to_csv(sample_csv_path, index=False)
        print(f"Complete dataset saved to {sample_csv_path} ({len(df):,} records).")


def main():
    parser = argparse.ArgumentParser(description="Download authentic CIC-IDS2017 dataset.")
    parser.add_argument("--type", choices=["web_attacks", "portscan"], default="web_attacks",
                        help="Attack category to download (default: web_attacks)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick download mode (~15 MB chunk of real data for immediate demonstration)")
    parser.add_argument("--sample-size", type=int, default=10000,
                        help="Number of records to extract for training sample (default: 10,000)")
    args = parser.parse_args()

    ensure_data_dir()
    url = MIRROR_URLS[args.type]
    raw_filename = f"raw_{args.type}.csv"
    sample_filename = f"cic_ids2017_{args.type}.csv"
    
    raw_path = os.path.join(RAW_DATA_DIR, raw_filename)
    sample_path = os.path.join(RAW_DATA_DIR, sample_filename)
    
    max_bytes = 15 * 1024 * 1024 if args.quick else None
    
    if not os.path.exists(raw_path):
        download_file(url, raw_path, max_bytes=max_bytes)
    else:
        print(f"Found existing raw file: {raw_path}")
        
    validate_and_sample_dataset(raw_path, sample_path, sample_size=args.sample_size)


if __name__ == "__main__":
    main()
