"""
Quantum-Inspired Digital Signature Security Engine.
Connects network intrusion detection telemetry to operational digital-signature security threats
and simulates a genuine Quantum Digital Signature (QDS) verification protocol based on Bell-state entanglement.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class DigitalSignatureThreatMapper:
    """
    Translates network-level intrusion detection events into digital signature security impacts.
    
    SCIENTIFIC DISTINCTION:
    The underlying CIC-IDS2017 dataset measures network packet flow statistics.
    In enterprise PKI and cloud e-signature architectures, signing endpoints, OCSP responders,
    and certificate directories are exposed as web APIs. This mapper translates network attacks
    into their corresponding PKI / Digital Signature vulnerability vectors.
    """
    
    THREAT_TAXONOMY = {
        "BENIGN": {
            "category": "Legitimate Signature Operation",
            "threat_type": "None (Authorized)",
            "impact": "Normal signing / verification request via authorized PKI channel.",
            "severity": "Informational",
            "base_disturbance": 0.01
        },
        "Web Attack - Brute Force": {
            "category": "Credential Theft & Impersonation",
            "threat_type": "Adversarial Impersonation Attack",
            "impact": "Brute-force credential cracking on signing portal to forge unauthorized digital signatures.",
            "severity": "Critical",
            "base_disturbance": 0.65
        },
        "Web Attack - Sql Injection": {
            "category": "Key Store & Trust Manipulation",
            "threat_type": "Signature Key Forgery & Certificate Store Corruption",
            "impact": "SQL payload targeting database holding public-key certificates or signature audit logs.",
            "severity": "Critical",
            "base_disturbance": 0.80
        },
        "Web Attack - XSS": {
            "category": "Session Hijacking",
            "threat_type": "Unauthorized Signing & Client Hijacking",
            "impact": "Cross-site script injection capturing signing tokens or silently executing approval workflows.",
            "severity": "High",
            "base_disturbance": 0.55
        },
        "PortScan": {
            "category": "PKI Infrastructure Reconnaissance",
            "threat_type": "Reconnaissance against OCSP/CA Responders",
            "impact": "Port scanning probing Certificate Revocation and Timestamping servers for vulnerabilities.",
            "severity": "Medium",
            "base_disturbance": 0.40
        }
    }

    @classmethod
    def map_threat(cls, is_threat: int, confidence: float, raw_attack_label: Optional[str] = None) -> Dict[str, Any]:
        """Maps model prediction and flow context to digital signature security implications."""
        if not is_threat:
            profile = cls.THREAT_TAXONOMY["BENIGN"].copy()
            disturbance = profile["base_disturbance"] * (1.0 - confidence)
        else:
            label_match = None
            if raw_attack_label:
                lbl_lower = raw_attack_label.lower()
                if "sql" in lbl_lower:
                    label_match = "Web Attack - Sql Injection"
                elif "xss" in lbl_lower:
                    label_match = "Web Attack - XSS"
                elif "port" in lbl_lower:
                    label_match = "PortScan"
                elif "brute" in lbl_lower or "attack" in lbl_lower:
                    label_match = "Web Attack - Brute Force"
            
            profile = (cls.THREAT_TAXONOMY.get(label_match) or cls.THREAT_TAXONOMY["Web Attack - Brute Force"]).copy()
            disturbance = min(0.95, profile["base_disturbance"] * confidence)
            
        profile["estimated_channel_disturbance"] = round(float(disturbance), 4)
        profile["confidence"] = round(float(confidence), 4)
        return profile


class QuantumDigitalSignatureProtocol:
    """
    Quantum-Inspired Digital Signature (QDS) Verification Simulator.
    
    Implements a Bell-state entanglement verification protocol:
    1. Signer and Verifier share entangled photon pairs: |Phi+> = (|00> + |11>) / sqrt(2).
    2. Anomaly disturbance (induced by detected cyber threats) injects depolarizing Pauli noise.
    3. Calculates genuine State Fidelity F(rho, sigma) and Quantum Bit Error Rate (QBER).
    4. Evaluates against an anomaly security threshold (default 0.85).
    """

    def __init__(self, threshold_fidelity: float = 0.85):
        self.threshold_fidelity = threshold_fidelity
        
        # Exact density matrix for ideal Bell state |Phi+><Phi+|
        bell_state = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
        self.rho_ideal = np.outer(bell_state, bell_state.conj())
        
        # Pauli matrices (2x2)
        self.I = np.eye(2, dtype=np.complex128)
        self.X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
        self.Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
        self.Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)

    def simulate_transmission(self, disturbance_level: float) -> Dict[str, Any]:
        """
        Simulates quantum state transmission across an adversarial quantum channel.
        Applies depolarizing channel: rho' = (1 - p)*rho + (p/3)*(X*rho*X + Y*rho*Y + Z*rho*Z).
        """
        p = np.clip(disturbance_level, 0.0, 1.0)
        
        # Single-qubit noise acting on qubit 1 (simulating interception or key eavesdropping)
        term_X = np.kron(self.X, self.I) @ self.rho_ideal @ np.kron(self.X, self.I)
        term_Y = np.kron(self.Y, self.I) @ self.rho_ideal @ np.kron(self.Y, self.I)
        term_Z = np.kron(self.Z, self.I) @ self.rho_ideal @ np.kron(self.Z, self.I)
        
        rho_noisy = (1.0 - p) * self.rho_ideal + (p / 3.0) * (term_X + term_Y + term_Z)
        
        # Quantum state fidelity: F = <Phi+| rho_noisy |Phi+>
        bell_state = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
        fidelity = float(np.real(bell_state.conj() @ rho_noisy @ bell_state))
        
        # Estimated Quantum Bit Error Rate (QBER): QBER ≈ (1 - Fidelity)
        qber = float(np.clip(1.0 - fidelity, 0.0, 1.0))
        
        # Decision logic
        is_verified = bool(fidelity >= self.threshold_fidelity)
        
        # Pauli measurement probabilities in computational basis |00>, |01>, |10>, |11>
        diag_probs = np.real(np.diag(rho_noisy))
        
        return {
            "disturbance_parameter": round(float(p), 4),
            "state_fidelity": round(float(fidelity), 4),
            "qber_percent": round(float(qber * 100), 2),
            "fidelity_threshold": self.threshold_fidelity,
            "signature_status": "VERIFIED_AUTHENTIC" if is_verified else "REJECTED_TAMPERED",
            "anomaly_detected": not is_verified,
            "computational_basis_probs": {
                "|00>": round(float(diag_probs[0]), 4),
                "|01>": round(float(diag_probs[1]), 4),
                "|10>": round(float(diag_probs[2]), 4),
                "|11>": round(float(diag_probs[3]), 4)
            },
            "security_verdict": (
                "Signature verification succeeded with high quantum state fidelity."
                if is_verified else
                f"Quantum Bit Error Rate ({qber*100:.1f}%) exceeds safety threshold! "
                "Adversarial interception or key tampering detected. Digital signature rejected."
            )
        }

    @staticmethod
    def get_protocol_metadata() -> Dict[str, Any]:
        """Provides transparent architectural demarcation between implemented and future concepts."""
        return {
            "implemented_components": [
                "Bell-state (|Phi+>) entanglement density matrix generation",
                "Adversarial depolarizing noise channel simulation parameterized by threat score",
                "Exact quantum state fidelity F(rho_ideal, rho_noisy) computation",
                "Quantum Bit Error Rate (QBER) estimation and decision thresholding",
                "Mapping of CIC-IDS2017 network flow attacks to PKI digital signature vectors"
            ],
            "experimental_components": [
                "Coupling classical/quantum cyber threat confidence scores to quantum channel disturbance parameter",
                "Projective measurement probability estimation under adversarial degradation"
            ],
            "conceptual_future_components": [
                "Physical single-photon QKD / QDS fiber optic links",
                "Quantum memory repeaters for long-range signature distribution",
                "Byzantine agreement via multi-party quantum states (Gottesman-Chuang QDS protocol on hardware)"
            ]
        }


if __name__ == "__main__":
    protocol = QuantumDigitalSignatureProtocol(threshold_fidelity=0.85)
    print("Testing Quantum Digital Signature Protocol...")
    
    benign_res = protocol.simulate_transmission(disturbance_level=0.02)
    print("\n--- Benign Scenario (Disturbance = 0.02) ---")
    print(f"State Fidelity: {benign_res['state_fidelity']}")
    print(f"QBER: {benign_res['qber_percent']}%")
    print(f"Status: {benign_res['signature_status']}")
    print(f"Verdict: {benign_res['security_verdict']}")
    assert benign_res["signature_status"] == "VERIFIED_AUTHENTIC", "Benign signature should be verified!"
    
    attack_res = protocol.simulate_transmission(disturbance_level=0.75)
    print("\n--- Attack Scenario (Disturbance = 0.75) ---")
    print(f"State Fidelity: {attack_res['state_fidelity']}")
    print(f"QBER: {attack_res['qber_percent']}%")
    print(f"Status: {attack_res['signature_status']}")
    print(f"Verdict: {attack_res['security_verdict']}")
    assert attack_res["signature_status"] == "REJECTED_TAMPERED", "Attack signature should be rejected!"
    
    print("\nQuantum Digital Signature Protocol verification SUCCESS!")
