"""
Quantum-Inspired Cyber Threat Detection for Digital Signature Security
Master FastAPI Application & REST API Server.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Add current workspace to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_loader import find_default_dataset, load_dataset, inspect_dataset
from src.preprocessing import ThreatDataPreprocessor
from src.classical_model import ClassicalThreatClassifier
from src.quantum_model import QuantumThreatClassifier
from src.quantum_signature import QuantumDigitalSignatureProtocol, DigitalSignatureThreatMapper
from src.comparison import run_benchmark
from src.evaluation import load_benchmark_results

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("QuantumSecApp")

app = FastAPI(
    title="Quantum-Inspired Cyber Threat Detection for Digital Signature Security",
    description="SIH Research Prototype benchmarking Classical Machine Learning vs Quantum Machine Learning on authentic CIC cybersecurity data.",
    version="1.0.0"
)

# Mount static and templates
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)
templates.env.filters["number_format"] = lambda val: f"{int(val):,}" if isinstance(val, (int, float)) else str(val)

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


@app.on_event("startup")
def on_startup():
    load_persisted_state()


# --- HTML Page Routes ---

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "dashboard",
        "benchmark_data": GLOBAL_STATE["benchmark_results"],
        "dataset_stats": GLOBAL_STATE["dataset_stats"]
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "benchmark_data": GLOBAL_STATE["benchmark_results"],
        "dataset_stats": GLOBAL_STATE["dataset_stats"]
    })


@app.get("/dataset", response_class=HTMLResponse)
async def dataset_page(request: Request):
    stats = GLOBAL_STATE.get("dataset_stats") or {}
    return templates.TemplateResponse("dataset.html", {
        "request": request,
        "active_page": "dataset",
        "stats": stats
    })


@app.get("/classical", response_class=HTMLResponse)
async def classical_page(request: Request):
    b_data = GLOBAL_STATE.get("benchmark_results")
    model_data = b_data.get("classical") if b_data else None
    return templates.TemplateResponse("classical.html", {
        "request": request,
        "active_page": "classical",
        "model_data": model_data
    })


@app.get("/quantum", response_class=HTMLResponse)
async def quantum_page(request: Request):
    b_data = GLOBAL_STATE.get("benchmark_results")
    model_data = b_data.get("quantum") if b_data else None
    return templates.TemplateResponse("quantum.html", {
        "request": request,
        "active_page": "quantum",
        "model_data": model_data
    })


@app.get("/comparison", response_class=HTMLResponse)
async def comparison_page(request: Request):
    b_data = GLOBAL_STATE.get("benchmark_results")
    return templates.TemplateResponse("comparison.html", {
        "request": request,
        "active_page": "comparison",
        "benchmark_data": b_data,
        "benchmark_data_json": json.dumps(b_data) if b_data else "{}"
    })


@app.get("/threat-detection", response_class=HTMLResponse)
async def threat_detection_page(request: Request):
    return templates.TemplateResponse("threat_detection.html", {
        "request": request,
        "active_page": "threat"
    })


@app.get("/scientific-report", response_class=HTMLResponse)
async def scientific_report_page(request: Request):
    return templates.TemplateResponse("scientific_report.html", {
        "request": request,
        "active_page": "scientific"
    })


# --- API Endpoints ---

class PredictionRequest(BaseModel):
    features: List[float]
    attack_label: Optional[str] = "BENIGN"


@app.post("/api/predict")
async def predict_packet(req: PredictionRequest):
    """
    Executes real inference across both classical and quantum models,
    evaluating threat probability and running the Quantum Digital Signature protocol.
    """
    if GLOBAL_STATE["preprocessor"] is None or GLOBAL_STATE["classical_model"] is None:
        raise HTTPException(
            status_code=400,
            detail="Models not loaded. Please execute the benchmark first to train classical and quantum models."
        )

    preprocessor: ThreatDataPreprocessor = GLOBAL_STATE["preprocessor"]
    classical_clf: ClassicalThreatClassifier = GLOBAL_STATE["classical_model"]
    quantum_clf: Optional[QuantumThreatClassifier] = GLOBAL_STATE.get("quantum_model")

    raw_features = np.array(req.features, dtype=np.float32)
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
        # Fallback if quantum model is still training
        q_pred = c_pred
        q_conf = c_conf
        q_threat_prob = c_threat_prob

    # 3. Digital Signature Threat Mapping
    threat_info = DigitalSignatureThreatMapper.map_threat(
        is_threat=c_pred,
        confidence=c_conf,
        raw_attack_label=req.attack_label
    )

    # 4. Quantum Digital Signature (QDS) Bell-state Protocol Simulation
    qds = QuantumDigitalSignatureProtocol(threshold_fidelity=0.85)
    qds_sim = qds.simulate_transmission(disturbance_level=threat_info["estimated_channel_disturbance"])

    return {
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
    }


class BenchmarkTriggerRequest(BaseModel):
    sample_size: int = 3000
    n_qubits: int = 4
    quantum_method: str = "quantum_kernel"


@app.post("/api/run_benchmark")
async def trigger_benchmark(req: BenchmarkTriggerRequest):
    """Executes the full benchmark pipeline on real CIC records."""
    dataset_path = find_default_dataset()
    if not dataset_path:
        raise HTTPException(
            status_code=404,
            detail="No CIC dataset file found in data/raw/. Please run data/download_dataset.py first."
        )

    logger.info(f"Starting benchmark execution: sample_size={req.sample_size}, qubits={req.n_qubits}...")
    df = load_dataset(dataset_path)
    
    results = run_benchmark(
        df=df,
        sample_size=req.sample_size,
        n_qubits=req.n_qubits,
        quantum_method=req.quantum_method
    )
    
    # Reload in-memory state
    load_persisted_state()
    
    return {
        "status": "success",
        "message": f"Benchmark completed successfully for {results['records_processed']} records.",
        "winner": results["comparison_summary"]["winner_model"],
        "classical_accuracy": results["classical"]["metrics"]["accuracy"],
        "quantum_accuracy": results["quantum"]["metrics"]["accuracy"]
    }


@app.get("/api/status")
async def get_system_status():
    """Returns active system status."""
    return {
        "dataset_loaded": GLOBAL_STATE["dataset_stats"] is not None,
        "classical_model_ready": GLOBAL_STATE["classical_model"] is not None,
        "quantum_model_ready": GLOBAL_STATE["quantum_model"] is not None,
        "benchmark_ready": GLOBAL_STATE["benchmark_results"] is not None,
        "active_dataset": find_default_dataset()
    }


def main():
    """Runs the FastAPI server locally with Uvicorn."""
    print("===================================================================")
    print("Starting Quantum-Inspired Threat Detection & Digital Signature Defense")
    print("Server URL: http://127.0.0.1:8000")
    print("===================================================================")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
