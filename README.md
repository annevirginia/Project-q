# Quantum-Inspired Cyber Threat Detection for Digital Signature Security

A complete, end-to-end, reproducible research prototype built for the **Smart India Hackathon (SIH)**. This platform benchmarks **Classical Machine Learning (Random Forest)** against **Quantum Machine Learning (PennyLane Quantum Support Vector Classifier & Variational Quantum Classifier)** on authentic **Canadian Institute for Cybersecurity (CIC-IDS2017)** network flow data, establishing an application-layer bridge to **Quantum Digital Signature (QDS)** Bell-state entanglement security.

---

## 📌 Key Architectural Pillars

1. **Authentic Cybersecurity Telemetry**:
   - Ingests canonical CIC-IDS2017 CSV files (e.g. `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv` and `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv`).
   - Zero synthetic/fabricated data. Full data cleaning for infinite flow rates (`Flow Bytes/s`), missing values, and duplicate elimination.
2. **Zero Data Leakage Guarantee**:
   - Strictly stratified 80/20 train/test split.
   - All scaling (`RobustScaler`) and dimensionality reduction (`PCA` to $N$ qubits) are fitted strictly on `X_train` and applied to `X_test`.
3. **Genuine Quantum Circuit Simulation**:
   - Implemented via **PennyLane** (`default.qubit` statevector simulator) and **Qiskit**.
   - Angle embedding ($\bigotimes R_y(x_i)|0\rangle$) and circular CNOT entanglement ladder creating Bell/GHZ-style quantum state correlations.
   - Evaluates real Hilbert space state overlaps $K(x, x') = |\langle \psi(x) | \psi(x') \rangle|^2$.
   - Explicitly demarcated as: **"Quantum Simulation on Classical CPU Backend"** (honest academic transparency).
4. **Digital Signature Security Bridge**:
   - Maps detected network intrusions to PKI digital signature vulnerabilities:
     - **Brute Force** $\to$ Credential cracking / unauthorized signer **Impersonation**.
     - **SQL Injection** $\to$ Database manipulation / public-key **Forgery** & certificate store tampering.
     - **XSS** $\to$ Session hijacking / **Unauthorized Signing** approvals.
     - **PortScan / DDoS** $\to$ Revocation blackout & **OCSP Denial-of-Service**.
   - Implements a simulated 3-party **Quantum Digital Signature (QDS)** protocol based on Bell states $|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$.
   - Measures **State Fidelity** $F(\rho, \sigma)$ and **Quantum Bit Error Rate (QBER)** under threat-induced depolarizing noise.
5. **Full-Stack Cyber Defense Dashboard**:
   - FastAPI + Vanilla CSS cyber-defense dark mode theme + Chart.js.
   - Interactive packet testing console, circuit visualizer, and side-by-side metric comparisons.

---

## 🛠️ Step-by-Step Setup & Execution Commands (Windows PowerShell)

### Step 1: Create and Activate Virtual Environment
Open PowerShell inside the project root folder:
```powershell
# Create virtual environment named 'venv'
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Project Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 3: Download Authentic CIC-IDS2017 Dataset
The automated downloader fetches canonical network flow captures directly from the mirror:
```powershell
# Quick mode: Downloads a ~15 MB authentic sample for fast setup & immediate evaluation
python data/download_dataset.py --quick --sample-size 10000

# Full download mode (Optional: downloads complete ~50 MB raw Thursday capture)
python data/download_dataset.py --sample-size 20000
```
*The downloaded dataset is validated and stored in `data/raw/`.*

### Step 4 & 5: Train Both Classical and Quantum Models
Run the comparative benchmark engine. This executes data preprocessing, trains Random Forest on the full features, trains the PennyLane Quantum Kernel Classifier on 4 qubits, and generates real confusion matrices and circuit diagrams:
```powershell
# Run comparative benchmark on 3,000 real records with 4 qubits
python -c "from src.data_loader import load_dataset, find_default_dataset; from src.comparison import run_benchmark; df = load_dataset(find_default_dataset()); run_benchmark(df, sample_size=3000, n_qubits=4)"
```

### Step 6: Start the Interactive Web Application
```powershell
python app.py
```

### Step 7: Open the Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🔬 Live Demonstration Workflow for SIH Presentation

1. **Dashboard (`/`)**:
   - View active dataset records, real class distributions, and the latest benchmark winner automatically determined by test F1-score.
2. **Dataset Studio (`/dataset`)**:
   - Inspect authentic CICFlowMeter network flow features, missing value handling, and zero data leakage proof.
3. **Classical Model Studio (`/classical`)**:
   - Inspect Random Forest accuracy, precision, recall, F1, confusion matrix, and sub-millisecond inference latencies.
4. **Quantum Model Studio (`/quantum`)**:
   - View the **actual synthesized PennyLane quantum circuit diagram**, qubit registers, angle encoding rotations, and statevector simulation metrics.
5. **Comparative Benchmark (`/comparison`)**:
   - Review the side-by-side metrics table and Chart.js comparison charts.
   - Discuss the scientific verdict: why classical trees currently outperform simulated quantum circuits on classical hardware.
6. **Live Threat Detection & Signature Defense Console (`/threat-detection`)**:
   - Select preset network flow vectors (Normal Flow, Web Brute Force, SQL Injection, PortScan) or upload a custom flow vector.
   - Click **Execute Hybrid Cyber Defense Test**.
   - Observe real-time classification from both models, mapped PKI threat impact, and the Bell-state Quantum Digital Signature state fidelity & QBER calculation.
7. **Scientific Honesty & Hardware Roadmap (`/scientific-report`)**:
   - Present the 5-tier scientific disclosure separating what is implemented, what is simulated, and what represents future quantum hardware integration.

---

## 📊 Directory Structure

```
Project q/
│
├── app.py                         # FastAPI master web application & REST API server
├── requirements.txt               # Project dependencies
├── README.md                      # Reproduction guide and execution instructions
│
├── data/
│   ├── README.md                  # Dataset provenance, citations & taxonomy
│   ├── download_dataset.py        # Automated authentic CIC-IDS2017 downloader & sampler
│   └── raw/                       # Stored authentic CSV files
│
├── models/
│   ├── classical_random_forest.joblib # Fitted classical model
│   ├── quantum_quantum_kernel.joblib  # Fitted quantum parameters & Gram references
│   └── preprocessor.joblib            # Fitted RobustScaler and PCA transformers
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py             # CSV parsing, validation, and stratified sampling
│   ├── preprocessing.py           # Cleaning, inf handling, scaling, PCA angle mapping
│   ├── classical_model.py         # Random Forest, Logistic Regression, SVM trainers
│   ├── quantum_model.py           # PennyLane QSVC, VQC, circuit drawings, statevectors
│   ├── quantum_signature.py       # PKI threat mapper & Bell-state QDS protocol
│   ├── evaluation.py              # Metric calculation, confusion matrices, ROC plots
│   └── comparison.py              # End-to-end comparative benchmark runner
│
├── templates/
│   ├── base.html                  # Master HTML layout with modern navigation
│   ├── dashboard.html             # Overview & quick benchmark controls
│   ├── dataset.html               # Dataset inspection & preprocessing verification
│   ├── classical.html             # Classical model evaluation & confusion matrix
│   ├── quantum.html               # Quantum circuit viewer & simulation metrics
│   ├── comparison.html            # Head-to-head comparison table & Chart.js charts
│   ├── threat_detection.html      # Live packet test console & signature security impact
│   └── scientific_report.html     # Scientific analysis, limits & hardware roadmap
│
├── static/
│   ├── css/
│   │   └── style.css              # Cyber-defense dark mode design system
│   └── js/
│   │   └── main.js                # Frontend controller & Chart.js renderer
│
└── results/
    ├── benchmark_results.json     # Persisted experimental results
    ├── quantum_circuit.png        # Rendered circuit diagram
    └── confusion_matrix_*.png     # Rendered confusion matrices
```

---

## 📜 Scientific Citation & Dataset Credit

- **Canadian Institute for Cybersecurity (CIC)**:
  *Iman Sharafaldin, Arash Habibi Lashkari, and Ali A. Ghorbani, "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization", 4th International Conference on Information Systems Security and Privacy (ICISSP), Portugal, January 2018.*
- **PennyLane**:
  *Ville Bergholm et al., "PennyLane: Automatic differentiation and machine learning of quantum computations", arXiv:1811.04968.*
