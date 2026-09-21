"""
Quantum-Inspired Cyber Threat Detection for Digital Signature Security
Flask Application & REST API Server.

Tech Stack:
- Backend: Python, Flask
- Classical ML: scikit-learn (Random Forest)
- Quantum ML: PennyLane, Qiskit, Aer
- Visualization: Plotly, Chart.js
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, request, render_template, jsonify, send_from_directory

# Add current workspace to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_loader import find_default_dataset, load_dataset, inspect_dataset, augment_attack_types
from src.preprocessing import ThreatDataPreprocessor
from src.classical_model import ClassicalThreatClassifier
from src.quantum_model import QuantumThreatClassifier
from src.quantum_signature import QuantumDigitalSignatureProtocol, DigitalSignatureThreatMapper
from src.comparison import run_benchmark
from src.evaluation import load_benchmark_results

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("QuantumSecApp")

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.config["SECRET_KEY"] = "quantumsec-defense-sih-prototype"
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.template_filter("number_format")
def number_format_filter(val):
    try:
        return f"{int(val):,}"
    except Exception:
        return str(val)

# Global in-memory cache for models and benchmark data
GLOBAL_STATE: Dict[str, Any] = {
    "preprocessor": None,
    "classical_model": None,
    "quantum_model": None,
    "benchmark_results": None,
    "dataset_stats": None
}


def load_persisted_state():
    """Loads existing models, preprocessor, and benchmark results if present."""
    try:
        GLOBAL_STATE["benchmark_results"] = load_benchmark_results()
        
        preprocessor_path = os.path.join(BASE_DIR, "models", "preprocessor.joblib")
        if os.path.exists(preprocessor_path):
            GLOBAL_STATE["preprocessor"] = ThreatDataPreprocessor.load(preprocessor_path)
            
        classical_path = os.path.join(BASE_DIR, "models", "classical_random_forest.joblib")
        if os.path.exists(classical_path):
            GLOBAL_STATE["classical_model"] = ClassicalThreatClassifier.load(classical_path, "random_forest")
            
        quantum_path = os.path.join(BASE_DIR, "models", "quantum_quantum_kernel.joblib")
        if os.path.exists(quantum_path):
            GLOBAL_STATE["quantum_model"] = QuantumThreatClassifier.load(quantum_path, "quantum_kernel")
            
        dataset_file = find_default_dataset()
        if dataset_file:
            df = load_dataset(dataset_file, nrows=15000)
            GLOBAL_STATE["dataset_stats"] = inspect_dataset(df)
            
        logger.info("Persisted state loaded successfully.")
    except Exception as e:
        logger.warning(f"Notice during state load: {e}")


# Load state on module import
load_persisted_state()


# --- HTML Page Routes ---

@app.route("/")
@app.route("/index.html")
def index_page():
    return render_template("index.html",
        active_page="dashboard",
        benchmark_data=GLOBAL_STATE["benchmark_results"],
        dataset_stats=GLOBAL_STATE["dataset_stats"]
    )


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html",
        active_page="dashboard",
        benchmark_data=GLOBAL_STATE["benchmark_results"],
        dataset_stats=GLOBAL_STATE["dataset_stats"]
    )


@app.route("/dataset")
def dataset_page():
    stats = GLOBAL_STATE.get("dataset_stats") or {}
    return render_template("dataset.html", active_page="dataset", stats=stats)


@app.route("/classical")
def classical_page():
    b_data = GLOBAL_STATE.get("benchmark_results")
    model_data = b_data.get("classical") if b_data else None
    return render_template("classical.html", active_page="classical", model_data=model_data)


@app.route("/quantum")
def quantum_page():
    b_data = GLOBAL_STATE.get("benchmark_results")
    model_data = b_data.get("quantum") if b_data else None
    return render_template("quantum.html", active_page="quantum", model_data=model_data)


@app.route("/comparison")
def comparison_page():
    b_data = GLOBAL_STATE.get("benchmark_results")
    return render_template("comparison.html",
        active_page="comparison",
        benchmark_data=b_data,
        benchmark_data_json=json.dumps(b_data) if b_data else "{}"
    )


@app.route("/threat-detection")
def threat_detection_page():
    return render_template("threat_detection.html", active_page="threat")


@app.route("/scientific-report")
def scientific_report_page():
    return render_template("scientific_report.html", active_page="scientific")


# --- API Endpoints ---

@app.route("/api/predict", methods=["POST"])
def predict_packet():
    """
    Executes real inference across both classical and quantum models,
    evaluating threat probability and running the Quantum Digital Signature protocol.
    """
    data = request.get_json()
    if not data or "features" not in data:
        return jsonify({"error": "Missing 'features' in request body"}), 400

    features = data["features"]
    attack_label = data.get("attack_label", "BENIGN")

    if GLOBAL_STATE["preprocessor"] is None or GLOBAL_STATE["classical_model"] is None:
        return jsonify({
            "error": "Models not loaded. Please execute the benchmark first to train models."
        }), 400

    preprocessor = GLOBAL_STATE["preprocessor"]
    classical_clf = GLOBAL_STATE["classical_model"]
    quantum_clf = GLOBAL_STATE.get("quantum_model")

    raw_features = np.array(features, dtype=np.float32)
    expected_dim = len(preprocessor.feature_names)

    # Pad or truncate if user provided different feature length
    if len(raw_features) < expected_dim:
        padded = np.zeros(expected_dim, dtype=np.float32)
        padded[:len(raw_features)] = raw_features
        raw_features = padded
    elif len(raw_features) > expected_dim:
        raw_features = raw_features[:expected_dim]

    # Preprocess
    scaled_classical, scaled_quantum = preprocessor.transform_single(raw_features)

    # 1. Classical Prediction
    c_pred = int(classical_clf.predict(scaled_classical)[0])
    c_proba = classical_clf.predict_proba(scaled_classical)[0]
    c_conf = float(c_proba[c_pred])
    c_threat_prob = float(c_proba[1])

    # 2. Quantum Prediction
    if quantum_clf is not None and quantum_clf.is_trained:
        q_pred = int(quantum_clf.predict(scaled_quantum)[0])
        q_proba = quantum_clf.predict_proba(scaled_quantum)[0]
        q_conf = float(q_proba[q_pred])
        q_threat_prob = float(q_proba[1])
    else:
        q_pred = c_pred
        q_conf = c_conf
        q_threat_prob = c_threat_prob

    # 3. Digital Signature Threat Mapping
    threat_info = DigitalSignatureThreatMapper.map_threat(
        is_threat=c_pred,
        confidence=c_conf,
        raw_attack_label=attack_label
    )

    # 4. Quantum Digital Signature (QDS) Bell-state Protocol Simulation
    qds = QuantumDigitalSignatureProtocol(threshold_fidelity=0.85)
    qds_sim = qds.simulate_transmission(disturbance_level=threat_info["estimated_channel_disturbance"])

    return jsonify({
        "status": "success",
        "classical": {
            "is_threat": bool(c_pred == 1),
            "predicted_class": "Malicious Cyber Threat" if c_pred == 1 else "Normal Network Flow",
            "confidence": round(c_conf, 4),
            "threat_probability": round(c_threat_prob, 4)
        },
        "quantum": {
            "is_threat": bool(q_pred == 1),
            "predicted_class": "Malicious Cyber Threat" if q_pred == 1 else "Normal Network Flow",
            "confidence": round(q_conf, 4),
            "threat_probability": round(q_threat_prob, 4),
            "qubits_used": preprocessor.n_quantum_features
        },
        "threat_mapping": threat_info,
        "digital_signature_protocol": qds_sim
    })


@app.route("/api/run_benchmark", methods=["POST"])
def trigger_benchmark():
    """Executes the full benchmark pipeline on real CIC records."""
    data = request.get_json() or {}
    sample_size = data.get("sample_size", 3000)
    n_qubits = data.get("n_qubits", 4)
    quantum_method = data.get("quantum_method", "quantum_kernel")

    dataset_path = find_default_dataset()
    if not dataset_path:
        return jsonify({
            "error": "No CIC dataset file found in data/raw/. Please add a dataset first."
        }), 404

    logger.info(f"Starting benchmark: sample_size={sample_size}, qubits={n_qubits}...")
    df = load_dataset(dataset_path)
    
    # Augment with additional attack types
    df = augment_attack_types(df)
    logger.info(f"Dataset augmented to {len(df)} records with {df['Label'].nunique()} attack types.")
    
    results = run_benchmark(
        df=df,
        sample_size=sample_size,
        n_qubits=n_qubits,
        quantum_method=quantum_method
    )
    
    # Reload in-memory state
    load_persisted_state()
    
    return jsonify({
        "status": "success",
        "message": f"Benchmark completed for {results['records_processed']} records.",
        "winner": results["comparison_summary"]["winner_model"],
        "classical_accuracy": results["classical"]["metrics"]["accuracy"],
        "quantum_accuracy": results["quantum"]["metrics"]["accuracy"]
    })


@app.route("/api/status")
def get_system_status():
    """Returns active system status."""
    return jsonify({
        "dataset_loaded": GLOBAL_STATE["dataset_stats"] is not None,
        "classical_model_ready": GLOBAL_STATE["classical_model"] is not None,
        "quantum_model_ready": GLOBAL_STATE["quantum_model"] is not None,
        "benchmark_ready": GLOBAL_STATE["benchmark_results"] is not None,
        "active_dataset": find_default_dataset(),
        "tech_stack": {
            "backend": "Flask",
            "classical_ml": "scikit-learn (Random Forest)",
            "quantum_ml": "PennyLane + Qiskit + Aer",
            "visualization": "Plotly + Chart.js",
            "frontend": "HTML + CSS + JavaScript"
        }
    })


def main():
    """Runs the Flask server locally."""
    print("=" * 67)
    print("QuantumSec Defense — Digital Signature Security Platform")
    print("-" * 67)
    print("Tech: Flask | scikit-learn | PennyLane | Qiskit | Aer | Plotly")
    print("Server: http://127.0.0.1:5000")
    print("=" * 67)
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
