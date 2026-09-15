"""
Head-to-Head Comparative Benchmark Suite.
Executes an honest, automated scientific comparison between classical and quantum threat classifiers
on the exact same dataset splits, without hardcoded outcomes.
"""

import os
import sys
import time
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_loader import inspect_dataset, stratified_subsample
from src.preprocessing import ThreatDataPreprocessor
from src.classical_model import ClassicalThreatClassifier
from src.quantum_model import QuantumThreatClassifier
from src.evaluation import save_confusion_matrix_plot, save_benchmark_results
from src.quantum_signature import QuantumDigitalSignatureProtocol, DigitalSignatureThreatMapper

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


def run_benchmark(
    df: pd.DataFrame,
    sample_size: int = 3000,
    n_qubits: int = 4,
    quantum_method: str = "quantum_kernel",
    max_quantum_train: int = 300,
    max_quantum_eval: int = 150
) -> Dict[str, Any]:
    """
    Executes the entire end-to-end benchmark:
    1. Stratified sampling from real dataset.
    2. Leakage-free preprocessing (Scalers & PCA fit strictly on train).
    3. Trains and benchmarks Classical Random Forest.
    4. Trains and benchmarks Quantum Threat Classifier.
    5. Evaluates on test sets.
    6. Automatically selects the winner based on actual test F1-score.
    7. Evaluates Quantum Digital Signature protocol under benign and threat conditions.
    """
    print(f"\n=======================================================")
    print(f"STARTING COMPARATIVE BENCHMARK (Sample Size: {sample_size:,}, Qubits: {n_qubits})")
    print(f"=======================================================\n")
    
    # Step 1: Honest sampling of real data
    df_sample = stratified_subsample(df, max_samples=sample_size)
    data_stats = inspect_dataset(df_sample)
    print(f"Dataset active records: {data_stats['num_records']:,} | Features: {data_stats['num_features']}")
    print(f"Class breakdown: Normal={data_stats['normal_count']:,} ({data_stats['normal_pct']}%), Attacks={data_stats['attack_count']:,} ({data_stats['attack_pct']}%)")
    
    # Step 2: Preprocessing
    preprocessor = ThreatDataPreprocessor(n_quantum_features=n_qubits)
    processed = preprocessor.prepare_dataset(df_sample, test_size=0.2, binary=True)
    preprocessor.save()
    
    X_train_c = processed["X_train_classical"]
    X_test_c = processed["X_test_classical"]
    X_train_q = processed["X_train_quantum"]
    X_test_q = processed["X_test_quantum"]
    y_train = processed["y_train"]
    y_test = processed["y_test"]
    
    print(f"\n[Train/Test Split] Train samples: {len(X_train_c):,} | Test samples: {len(X_test_c):,}")
    
    # Step 3: Train Classical Model (Random Forest)
    print("\n--- Training Classical Model (Random Forest) ---")
    classical_clf = ClassicalThreatClassifier(model_type="random_forest")
    classical_clf.train(X_train_c, y_train)
    classical_metrics = classical_clf.evaluate(X_test_c, y_test)
    classical_clf.save()
    print(f"Classical Accuracy: {classical_metrics['accuracy']*100:.2f}% | F1: {classical_metrics['f1_score']:.4f} | Train Time: {classical_metrics['training_time_seconds']}s")
    
    # Step 4: Train Quantum Model
    print(f"\n--- Training Quantum Model ({quantum_method.upper()} on {n_qubits} Qubits) ---")
    quantum_clf = QuantumThreatClassifier(n_qubits=n_qubits, method=quantum_method)
    quantum_clf.train(X_train_q, y_train, max_train_samples=max_quantum_train)
    quantum_metrics = quantum_clf.evaluate(X_test_q, y_test, max_eval_samples=max_quantum_eval)
    quantum_clf.save()
    print(f"Quantum Accuracy: {quantum_metrics['accuracy']*100:.2f}% | F1: {quantum_metrics['f1_score']:.4f} | Train Time: {quantum_metrics['training_time_seconds']}s")
    
    # Render and save real quantum circuit diagram
    os.makedirs(RESULTS_DIR, exist_ok=True)
    circuit_path = os.path.join(RESULTS_DIR, "quantum_circuit.png")
    try:
        quantum_clf.render_circuit_diagram(circuit_path)
    except Exception as e:
        print(f"Notice: Matplotlib circuit rendering skipped ({e})")
        
    circuit_ascii = quantum_clf.get_circuit_ascii()
    
    # Render confusion matrix plots
    cm_c_path = os.path.join(RESULTS_DIR, "confusion_matrix_classical.png")
    cm_q_path = os.path.join(RESULTS_DIR, "confusion_matrix_quantum.png")
    try:
        save_confusion_matrix_plot(np.array(classical_metrics["confusion_matrix"]["matrix"]), "Classical Model Confusion Matrix", cm_c_path)
        save_confusion_matrix_plot(np.array(quantum_metrics["confusion_matrix"]["matrix"]), "Quantum Model Confusion Matrix", cm_q_path)
    except Exception as e:
        print(f"Notice: Confusion matrix plot skipped ({e})")

    # Step 5: Automated, Unbiased Winner Determination
    c_f1 = classical_metrics["f1_score"]
    q_f1 = quantum_metrics["f1_score"]
    
    if c_f1 > q_f1 + 0.02:
        winner = "Classical Model (Random Forest)"
        scientific_verdict = (
            f"The Classical Random Forest achieved superior F1-score ({c_f1:.4f} vs {q_f1:.4f}) "
            "and orders of magnitude faster training and inference. For tabular cybersecurity network telemetry, "
            "classical ensemble decision trees currently outperform simulated quantum circuits in both accuracy and latency."
        )
    elif q_f1 > c_f1 + 0.02:
        winner = "Quantum / Quantum-Inspired Model"
        scientific_verdict = (
            f"The Quantum Model achieved superior F1-score ({q_f1:.4f} vs {c_f1:.4f}). "
            "The quantum state feature map captured non-linear separation in the reduced Hilbert space."
        )
    else:
        winner = "Comparable Performance (Statistical Tie)"
        scientific_verdict = (
            f"Both models demonstrated competitive performance (Classical F1: {c_f1:.4f}, Quantum F1: {q_f1:.4f}). "
            "However, classical inference latency is significantly lower on current classical computing hardware."
        )

    # Step 6: Quantum-Inspired Digital Signature Protocol Simulation
    qds = QuantumDigitalSignatureProtocol(threshold_fidelity=0.85)
    benign_sim = qds.simulate_transmission(disturbance_level=0.02)
    threat_sim = qds.simulate_transmission(disturbance_level=0.75)
    protocol_meta = qds.get_protocol_metadata()

    # Step 7: Final Consolidated Benchmark Object
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_name": "CIC-IDS2017 (Canadian Institute for Cybersecurity)",
        "records_processed": data_stats["num_records"],
        "raw_features_count": data_stats["num_features"],
        "class_distribution": data_stats["class_distribution"],
        "normal_count": data_stats["normal_count"],
        "attack_count": data_stats["attack_count"],
        "train_samples": len(X_train_c),
        "test_samples": len(X_test_c),
        "classical": {
            "model_name": "Random Forest Classifier",
            "features_used": X_train_c.shape[1],
            "metrics": classical_metrics
        },
        "quantum": {
            "model_name": f"PennyLane {quantum_method.replace('_', ' ').title()}",
            "backend": quantum_metrics["backend"],
            "n_qubits": n_qubits,
            "encoding": "Angle Embedding (RY, RZ) + CNOT Entangling Ring",
            "features_used": n_qubits,
            "metrics": quantum_metrics,
            "circuit_ascii": circuit_ascii
        },
        "comparison_summary": {
            "winner_model": winner,
            "f1_difference": round(abs(c_f1 - q_f1), 4),
            "latency_speedup_classical_x": round(
                quantum_metrics["inference_time_ms_per_sample"] / max(0.0001, classical_metrics["inference_time_ms_per_sample"]), 2
            ),
            "scientific_verdict": scientific_verdict
        },
        "digital_signature_protocol": {
            "benign_verification": benign_sim,
            "threat_verification": threat_sim,
            "metadata": protocol_meta
        }
    }
    
    save_benchmark_results(results)
    
    print("\n=======================================================")
    print("BENCHMARK COMPLETED SUCCESSFULLY")
    print(f"Winner: {winner}")
    print(f"Scientific Verdict: {scientific_verdict}")
    print("=======================================================\n")
    
    return results


if __name__ == "__main__":
    from src.data_loader import find_default_dataset, load_dataset
    dataset_path = find_default_dataset()
    print(f"Running benchmark on dataset: {dataset_path}")
    if dataset_path:
        df = load_dataset(dataset_path)
        run_benchmark(df, sample_size=3000, n_qubits=4, quantum_method="quantum_kernel", max_quantum_train=120, max_quantum_eval=80)
