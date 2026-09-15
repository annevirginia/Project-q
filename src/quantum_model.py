"""
Genuine Quantum Machine Learning & Simulation Engine.
Implements Variational Quantum Classifier (VQC) and Quantum Kernel Classifier (QSVC)
using PennyLane ('default.qubit' statevector simulator) and Qiskit.
Guarantees actual circuit execution, genuine statevector computation, and circuit visualization.
"""

import os
import sys
import time
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

# Ensure Windows terminal doesn't crash on quantum Unicode box drawing characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import joblib

# Pennylane quantum framework
import pennylane as qml
from pennylane import numpy as pnp

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


class QuantumThreatClassifier:
    """
    Genuine Quantum Classifier for Cyber Threat Detection.
    Utilizes PennyLane's statevector simulator ('default.qubit').
    Operates on n_qubits (default 4) angle-encoded features.
    
    Supports:
    1. Quantum Kernel Estimator (QSVC): Calculates Hilbert space state overlap
       K(x, x') = |<psi(x) | psi(x')>|^2.
    2. Variational Quantum Circuit (VQC): Parameterized ansatz with CNOT entanglement
       and Pauli-Z measurements.
    """
    def __init__(self, n_qubits: int = 4, n_layers: int = 2, method: str = "quantum_kernel", random_state: int = 42):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.method = method # 'quantum_kernel' or 'vqc'
        self.random_state = random_state
        
        self.backend_type = "PennyLane 'default.qubit' Statevector Simulator (Classical CPU)"
        self.is_trained: bool = False
        self.training_time: float = 0.0
        self.inference_time_per_sample: float = 0.0
        
        # Initialize quantum device
        self.dev = qml.device("default.qubit", wires=self.n_qubits)
        
        # Setup PennyLane QNodes
        self._setup_quantum_nodes()
        
        # Model state
        self.svc_model: Optional[SVC] = None
        self.X_train_ref: Optional[np.ndarray] = None
        self.vqc_weights: Optional[np.ndarray] = None
        self.vqc_bias: float = 0.0

    def _setup_quantum_nodes(self):
        """Builds PennyLane quantum nodes for feature encoding and kernel overlap."""
        n_q = self.n_qubits
        dev = self.dev

        # --- Feature Map Circuit ---
        def feature_map(x):
            for i in range(n_q):
                qml.RY(x[i], wires=i)
            # Entangling layer (Linear CNOT chain)
            for i in range(n_q - 1):
                qml.CNOT(wires=[i, i + 1])
            if n_q > 2:
                qml.CNOT(wires=[n_q - 1, 0])
            for i in range(n_q):
                qml.RZ(x[i], wires=i)

        # --- Quantum Kernel Overlap QNode ---
        @qml.qnode(dev)
        def kernel_circuit(x1, x2):
            feature_map(x1)
            qml.adjoint(feature_map)(x2)
            return qml.probs(wires=range(n_q))

        self._kernel_circuit = kernel_circuit

        # --- VQC Parameterized QNode ---
        @qml.qnode(dev)
        def vqc_circuit(weights, x):
            # Angle Embedding
            for i in range(n_q):
                qml.RY(x[i], wires=i)
            # Strongly Entangling Variational Layers
            for layer in range(weights.shape[0]):
                for i in range(n_q):
                    qml.Rot(weights[layer, i, 0], weights[layer, i, 1], weights[layer, i, 2], wires=i)
                for i in range(n_q - 1):
                    qml.CNOT(wires=[i, i + 1])
                if n_q > 2:
                    qml.CNOT(wires=[n_q - 1, 0])
            # Expectation of Pauli-Z on first qubit
            return qml.expval(qml.PauliZ(0))

        self._vqc_circuit = vqc_circuit

    def compute_quantum_kernel_matrix(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        Computes the Gram matrix of quantum state overlaps:
        K_ij = |<psi(x_i) | psi(x_j)>|^2.
        Calculated directly via the PennyLane quantum circuit on default.qubit.
        """
        n1 = len(X1)
        n2 = len(X2)
        gram = np.zeros((n1, n2), dtype=np.float64)
        
        is_symmetric = (X1 is X2) or (n1 == n2 and np.allclose(X1, X2))
        
        for i in range(n1):
            start_j = i if is_symmetric else 0
            for j in range(start_j, n2):
                probs = self._kernel_circuit(X1[i], X2[j])
                # |<psi_i | psi_j>|^2 is the probability of measuring all-zeros state |00...0>
                overlap = float(probs[0])
                gram[i, j] = overlap
                if is_symmetric:
                    gram[j, i] = overlap
                    
        return gram

    def train_kernel(self, X_train: np.ndarray, y_train: np.ndarray, max_train_samples: int = 500) -> Dict[str, Any]:
        """
        Trains the Quantum Support Vector Classifier (QSVC) using the quantum kernel matrix.
        Subsamples if train set is large to avoid O(N^2) quantum simulation bottleneck.
        """
        start_time = time.perf_counter()
        
        # Subsample for quantum simulation feasibility if needed
        if len(X_train) > max_train_samples:
            from sklearn.model_selection import train_test_split
            try:
                _, X_sub, _, y_sub = train_test_split(
                    X_train, y_train,
                    test_size=max_train_samples,
                    stratify=y_train,
                    random_state=self.random_state
                )
            except Exception:
                indices = np.random.RandomState(self.random_state).choice(len(X_train), max_train_samples, replace=False)
                X_sub = X_train[indices]
                y_sub = y_train[indices]
        else:
            X_sub = X_train
            y_sub = y_train
            
        self.X_train_ref = X_sub
        
        print(f"Computing Quantum Kernel Gram matrix ({len(X_sub)} x {len(X_sub)}) on {self.n_qubits} qubits...")
        K_train = self.compute_quantum_kernel_matrix(X_sub, X_sub)
        
        self.svc_model = SVC(kernel="precomputed", probability=True, class_weight="balanced", random_state=self.random_state)
        self.svc_model.fit(K_train, y_sub)
        
        self.training_time = time.perf_counter() - start_time
        self.is_trained = True
        
        train_preds = self.svc_model.predict(K_train)
        acc = accuracy_score(y_sub, train_preds)
        
        return {
            "method": "Quantum Kernel Classifier (QSVC)",
            "n_qubits": self.n_qubits,
            "training_samples_used": len(X_sub),
            "training_time_seconds": round(self.training_time, 4),
            "train_accuracy": round(float(acc), 4),
            "backend": self.backend_type
        }

    def train_vqc(self, X_train: np.ndarray, y_train: np.ndarray, epochs: int = 25, batch_size: int = 32) -> Dict[str, Any]:
        """
        Trains the Variational Quantum Classifier (VQC) via gradient descent.
        """
        start_time = time.perf_counter()
        rng = np.random.RandomState(self.random_state)
        
        # Subsample training data for fast VQC demonstration
        sample_limit = min(300, len(X_train))
        idx = rng.choice(len(X_train), sample_limit, replace=False)
        X_sub = X_train[idx]
        y_sub = np.where(y_train[idx] == 0, -1.0, 1.0) # Map to {-1, +1} for Pauli-Z
        
        # Initialize variational weights (layers, qubits, 3 angles)
        weights_init = 0.01 * rng.randn(self.n_layers, self.n_qubits, 3)
        self.vqc_weights = pnp.array(weights_init, requires_grad=True)
        self.vqc_bias = 0.0
        
        opt = qml.AdamOptimizer(stepsize=0.1)
        
        # Loss function: Mean squared error
        def cost_fn(weights, bias, x_batch, y_batch):
            loss = 0.0
            for x_i, y_i in zip(x_batch, y_batch):
                pred = self._vqc_circuit(weights, x_i) + bias
                loss += (pred - y_i) ** 2
            return loss / len(x_batch)

        print(f"Training VQC for {epochs} epochs on {self.n_qubits} qubits...")
        for epoch in range(epochs):
            batch_idx = rng.choice(len(X_sub), min(batch_size, len(X_sub)), replace=False)
            x_b = X_sub[batch_idx]
            y_b = y_sub[batch_idx]
            self.vqc_weights, self.vqc_bias = opt.step(
                lambda w, b: cost_fn(w, b, x_b, y_b), self.vqc_weights, self.vqc_bias
            )

        self.training_time = time.perf_counter() - start_time
        self.is_trained = True
        
        # Evaluate on train batch
        preds = []
        for x in X_sub:
            val = float(self._vqc_circuit(self.vqc_weights, x) + self.vqc_bias)
            preds.append(1 if val >= 0 else 0)
        acc = accuracy_score(y_train[idx], preds)

        return {
            "method": "Variational Quantum Classifier (VQC)",
            "n_qubits": self.n_qubits,
            "training_samples_used": len(X_sub),
            "training_time_seconds": round(self.training_time, 4),
            "train_accuracy": round(float(acc), 4),
            "backend": self.backend_type
        }

    def train(self, X_train: np.ndarray, y_train: np.ndarray, **kwargs) -> Dict[str, Any]:
        """Routes training to selected quantum method."""
        if self.method == "quantum_kernel":
            return self.train_kernel(X_train, y_train, **kwargs)
        else:
            return self.train_vqc(X_train, y_train, **kwargs)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Executes quantum circuit predictions on query points."""
        if not self.is_trained:
            raise ValueError("Quantum model must be trained before predicting.")
        
        if self.method == "quantum_kernel":
            K_test = self.compute_quantum_kernel_matrix(X, self.X_train_ref)
            return self.svc_model.predict(K_test)
        else:
            preds = []
            for x in X:
                val = float(self._vqc_circuit(self.vqc_weights, x) + self.vqc_bias)
                preds.append(1 if val >= 0 else 0)
            return np.array(preds)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Computes prediction probabilities from the quantum classifier."""
        if not self.is_trained:
            raise ValueError("Quantum model must be trained before predicting probabilities.")
            
        if self.method == "quantum_kernel":
            K_test = self.compute_quantum_kernel_matrix(X, self.X_train_ref)
            return self.svc_model.predict_proba(K_test)
        else:
            probs = []
            for x in X:
                val = float(self._vqc_circuit(self.vqc_weights, x) + self.vqc_bias)
                # Sigmoid mapping from Pauli expectation to probability
                prob_threat = 1.0 / (1.0 + np.exp(-val * 2.0))
                probs.append([1.0 - prob_threat, prob_threat])
            return np.array(probs)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray, max_eval_samples: int = 150) -> Dict[str, Any]:
        """
        Evaluates quantum classifier on test data and returns actual metrics.
        Limits test sample size if necessary to respect simulation latency.
        """
        if not self.is_trained:
            raise ValueError("Quantum model must be trained before evaluation.")
            
        if len(X_test) > max_eval_samples:
            from sklearn.model_selection import train_test_split
            try:
                _, X_eval, _, y_eval = train_test_split(
                    X_test, y_test,
                    test_size=max_eval_samples,
                    stratify=y_test,
                    random_state=self.random_state
                )
            except Exception:
                idx = np.random.RandomState(self.random_state).choice(len(X_test), max_eval_samples, replace=False)
                X_eval = X_test[idx]
                y_eval = y_test[idx]
        else:
            X_eval = X_test
            y_eval = y_test
            
        start_inf = time.perf_counter()
        y_pred = self.predict(X_eval)
        total_inf_time = time.perf_counter() - start_inf
        self.inference_time_per_sample = total_inf_time / len(X_eval) if len(X_eval) > 0 else 0.0
        
        try:
            y_proba = self.predict_proba(X_eval)[:, 1]
            auc = round(float(roc_auc_score(y_eval, y_proba)), 4)
        except Exception:
            auc = None
            
        acc = round(float(accuracy_score(y_eval, y_pred)), 4)
        prec = round(float(precision_score(y_eval, y_pred, zero_division=0)), 4)
        rec = round(float(recall_score(y_eval, y_pred, zero_division=0)), 4)
        f1 = round(float(f1_score(y_eval, y_pred, zero_division=0)), 4)
        
        cm = confusion_matrix(y_eval, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        return {
            "method": self.method,
            "backend": self.backend_type,
            "n_qubits": self.n_qubits,
            "test_samples_evaluated": len(X_eval),
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "roc_auc": auc,
            "training_time_seconds": round(self.training_time, 4),
            "total_inference_seconds": round(total_inf_time, 5),
            "inference_time_ms_per_sample": round(self.inference_time_per_sample * 1000, 4),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
                "matrix": cm.tolist()
            },
            "classification_report": classification_report(y_eval, y_pred, target_names=["Normal", "Threat"], output_dict=True, zero_division=0)
        }

    def get_circuit_ascii(self) -> str:
        """Returns the ASCII string representation of the actual quantum circuit."""
        dummy_x = np.array([0.5] * self.n_qubits)
        if self.method == "quantum_kernel":
            return qml.draw(self._kernel_circuit)(dummy_x, dummy_x)
        else:
            w = np.zeros((self.n_layers, self.n_qubits, 3))
            return qml.draw(self._vqc_circuit)(w, dummy_x)

    def render_circuit_diagram(self, output_path: Optional[str] = None) -> str:
        """
        Renders and saves the genuine quantum circuit diagram as an image using PIL.
        """
        from PIL import Image, ImageDraw
        
        if output_path is None:
            os.makedirs(RESULTS_DIR, exist_ok=True)
            output_path = os.path.join(RESULTS_DIR, "quantum_circuit.png")
            
        circuit_text = self.get_circuit_ascii()
        lines = circuit_text.splitlines()
        
        width = 860
        height = max(260, 70 + len(lines) * 34)
        img = Image.new("RGB", (width, height), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        
        # Header banner
        draw.rectangle([0, 0, width, 45], fill=(30, 41, 59))
        draw.text((25, 14), f"PennyLane Quantum Feature Map & Adjoint Kernel ({self.n_qubits} Qubits)", fill=(56, 189, 248))
        draw.text((640, 14), "default.qubit simulator", fill=(148, 163, 184))
        
        # Draw circuit lines
        y = 65
        colors = [(244, 114, 182), (56, 189, 248), (52, 211, 153), (251, 191, 36)]
        for idx, line in enumerate(lines):
            c = colors[idx % len(colors)]
            draw.text((25, y), line, fill=c)
            y += 28
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        
        # Also copy to static/img/ for frontend access
        static_img_dir = os.path.join(os.path.dirname(RESULTS_DIR), "static", "img")
        os.makedirs(static_img_dir, exist_ok=True)
        img.save(os.path.join(static_img_dir, "quantum_circuit.png"))
        
        return output_path

    def save(self, filepath: Optional[str] = None):
        """Serializes the trained quantum classifier."""
        if filepath is None:
            os.makedirs(MODELS_DIR, exist_ok=True)
            filepath = os.path.join(MODELS_DIR, f"quantum_{self.method}.joblib")
        # Save necessary state (excluding non-picklable qnodes)
        state = {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "method": self.method,
            "random_state": self.random_state,
            "backend_type": self.backend_type,
            "is_trained": self.is_trained,
            "training_time": self.training_time,
            "svc_model": self.svc_model,
            "X_train_ref": self.X_train_ref,
            "vqc_weights": self.vqc_weights,
            "vqc_bias": self.vqc_bias
        }
        joblib.dump(state, filepath)
        print(f"Quantum model state saved to {filepath}")

    @classmethod
    def load(cls, filepath: Optional[str] = None, method: str = "quantum_kernel") -> "QuantumThreatClassifier":
        """Loads a serialized quantum classifier."""
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, f"quantum_{method}.joblib")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Quantum model file not found at {filepath}")
        state = joblib.load(filepath)
        instance = cls(
            n_qubits=state["n_qubits"],
            n_layers=state["n_layers"],
            method=state["method"],
            random_state=state["random_state"]
        )
        instance.is_trained = state["is_trained"]
        instance.training_time = state["training_time"]
        instance.svc_model = state["svc_model"]
        instance.X_train_ref = state["X_train_ref"]
        instance.vqc_weights = state["vqc_weights"]
        instance.vqc_bias = state["vqc_bias"]
        return instance


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.data_loader import find_default_dataset, load_dataset
    from src.preprocessing import ThreatDataPreprocessor

    dataset_path = find_default_dataset()
    print(f"Loading dataset from: {dataset_path}")
    df = load_dataset(dataset_path)
    
    preprocessor = ThreatDataPreprocessor(n_quantum_features=4)
    data_splits = preprocessor.prepare_dataset(df)
    
    print("\n--- Initializing PennyLane Quantum Threat Classifier (4 Qubits) ---")
    q_clf = QuantumThreatClassifier(n_qubits=4, method="quantum_kernel")
    
    print("\n--- ASCII Circuit Diagram ---")
    print(q_clf.get_circuit_ascii())
    
    print("\n--- Training Quantum Model on 150 stratified samples ---")
    train_res = q_clf.train(data_splits["X_train_quantum"], data_splits["y_train"], max_train_samples=150)
    print(f"Quantum Training Time: {train_res['training_time_seconds']}s, Train Acc: {train_res['train_accuracy']*100:.2f}%")
    
    print("\n--- Evaluating on 100 stratified test quantum states ---")
    eval_res = q_clf.evaluate(data_splits["X_test_quantum"], data_splits["y_test"], max_eval_samples=100)
    print(f"Quantum Test Accuracy: {eval_res['accuracy']*100:.2f}%")
    print(f"Quantum Precision: {eval_res['precision']*100:.2f}%")
    print(f"Quantum Recall: {eval_res['recall']*100:.2f}%")
    print(f"Quantum F1-Score: {eval_res['f1_score']:.4f}")
    print(f"Quantum Latency: {eval_res['inference_time_ms_per_sample']} ms/sample")
    print("Confusion Matrix:", eval_res['confusion_matrix'])
    
    q_clf.save()
    img_path = q_clf.render_circuit_diagram()
    print(f"Rendered circuit diagram saved to {img_path}")
    print("Quantum Model execution and evaluation SUCCESS!")
