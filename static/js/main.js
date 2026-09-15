/**
 * Cyber Threat Detection & Quantum Signature Security Controller
 * Manages dynamic metrics, Chart.js visualizations, and live threat testing.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    setupPresetButtons();
    setupPacketPredictionForm();
    setupBenchmarkTrigger();
});

function initCharts() {
    // Check if comparison chart canvas exists
    const compCtx = document.getElementById('comparisonMetricsChart');
    if (compCtx && window.BENCHMARK_DATA) {
        const data = window.BENCHMARK_DATA;
        const cMetrics = data.classical ? data.classical.metrics : null;
        const qMetrics = data.quantum ? data.quantum.metrics : null;

        if (cMetrics && qMetrics) {
            new Chart(compCtx, {
                type: 'bar',
                data: {
                    labels: ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC'],
                    datasets: [
                        {
                            label: 'Classical (Random Forest)',
                            data: [
                                cMetrics.accuracy,
                                cMetrics.precision,
                                cMetrics.recall,
                                cMetrics.f1_score,
                                cMetrics.roc_auc || 0
                            ],
                            backgroundColor: 'rgba(0, 242, 254, 0.75)',
                            borderColor: '#00f2fe',
                            borderWidth: 1.5,
                            borderRadius: 6
                        },
                        {
                            label: 'Quantum (PennyLane QSVC)',
                            data: [
                                qMetrics.accuracy,
                                qMetrics.precision,
                                qMetrics.recall,
                                qMetrics.f1_score,
                                qMetrics.roc_auc || 0
                            ],
                            backgroundColor: 'rgba(168, 85, 247, 0.75)',
                            borderColor: '#a855f7',
                            borderWidth: 1.5,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#cbd5e1', font: { family: 'Outfit', size: 12 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `${ctx.dataset.label}: ${(ctx.raw * 100).toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: 0,
                            max: 1.0,
                            ticks: {
                                color: '#94a3b8',
                                callback: (val) => `${(val * 100).toFixed(0)}%`
                            },
                            grid: { color: 'rgba(255, 255, 255, 0.06)' }
                        },
                        x: {
                            ticks: { color: '#cbd5e1' },
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    // Latency Chart
    const latCtx = document.getElementById('latencyMetricsChart');
    if (latCtx && window.BENCHMARK_DATA) {
        const data = window.BENCHMARK_DATA;
        const cMetrics = data.classical ? data.classical.metrics : null;
        const qMetrics = data.quantum ? data.quantum.metrics : null;

        if (cMetrics && qMetrics) {
            new Chart(latCtx, {
                type: 'bar',
                data: {
                    labels: ['Training Duration (s)', 'Inference per Sample (ms)'],
                    datasets: [
                        {
                            label: 'Classical (Random Forest)',
                            data: [
                                cMetrics.training_time_seconds,
                                cMetrics.inference_time_ms_per_sample
                            ],
                            backgroundColor: 'rgba(0, 242, 254, 0.75)',
                            borderColor: '#00f2fe',
                            borderWidth: 1.5,
                            borderRadius: 6
                        },
                        {
                            label: 'Quantum Simulation (PennyLane)',
                            data: [
                                qMetrics.training_time_seconds,
                                qMetrics.inference_time_ms_per_sample
                            ],
                            backgroundColor: 'rgba(168, 85, 247, 0.75)',
                            borderColor: '#a855f7',
                            borderWidth: 1.5,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'logarithmic',
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255, 255, 255, 0.06)' }
                        },
                        x: {
                            ticks: { color: '#cbd5e1' },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#cbd5e1', font: { family: 'Outfit', size: 12 } }
                        }
                    }
                }
            });
        }
    }
}

// Preset test vector handlers
const PRESETS = {
    benign: {
        name: "Authentic CIC-IDS2017 Normal Flow (BENIGN)",
        label: "BENIGN",
        // Normalized standard flow features
        features: [80, 54820, 2, 0, 12, 0, 6, 6, 6.0, 0.0, 0, 0, 0.0, 0.0, 218.89, 36.48, 54820, 0, 54820, 54820, 0, 0, 0, 0, 0, 0, 0, 0, 40, 0, 36.48, 0.0, 6, 6, 6.0, 0.0, 0.0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 9.0, 6.0, 0.0, 40, 0, 0, 0, 0, 0, 0, 2, 12, 0, 0, 256, -1, 1, 20, 0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0]
    },
    bruteforce: {
        name: "Authentic Web Attack – Brute Force (Impersonation)",
        label: "Web Attack – Brute Force",
        features: [80, 5201111, 8, 5, 432, 11520, 432, 0, 54.0, 152.7, 4320, 0, 2304.0, 2038.5, 2297.9, 2.49, 433425.9, 1488734.0, 5201111, 3, 5199201, 1299800.2, 5198000, 3, 1910, 636.6, 1900, 3, 0, 0, 1.53, 0.96, 4320, 0, 919.3, 1693.4, 2867800.0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 996.0, 54.0, 2304.0, 172, 112, 8, 432, 5, 11520, 29200, 235, 3, 20, 0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0]
    },
    sqlinjection: {
        name: "Authentic Web Attack – SQL Injection (Key Forgery)",
        label: "Web Attack – Sql Injection",
        features: [80, 5006610, 4, 3, 439, 480, 439, 0, 109.75, 219.5, 480, 0, 160.0, 277.1, 183.56, 1.39, 834435.0, 2043689.8, 5006610, 3, 5006610, 1668870.0, 5006500, 3, 105, 52.5, 100, 3, 0, 0, 0.79, 0.59, 480, 0, 131.2, 232.8, 54228.0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 150.0, 109.75, 160.0, 92, 72, 4, 439, 3, 480, 29200, 235, 2, 20, 0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0]
    },
    portscan: {
        name: "Authentic PortScan (Revocation/OCSP Blackout)",
        label: "PortScan",
        features: [443, 48, 1, 1, 0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0.0, 41666.6, 48.0, 0.0, 48, 48, 0, 0.0, 0, 0, 0, 0.0, 0, 0, 0, 0, 20833.3, 20833.3, 0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0.0, 0.0, 0.0, 40, 20, 1, 0, 1, 0, 1024, 0, 0, 20, 0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0]
    }
};

function setupPresetButtons() {
    const presetSelect = document.getElementById('presetSelector');
    const featureInput = document.getElementById('featureVectorInput');
    const attackLabelInput = document.getElementById('attackLabelInput');
    const presetDesc = document.getElementById('presetDescription');

    if (presetSelect && featureInput) {
        presetSelect.addEventListener('change', (e) => {
            const key = e.target.value;
            if (PRESETS[key]) {
                featureInput.value = JSON.stringify(PRESETS[key].features);
                if (attackLabelInput) attackLabelInput.value = PRESETS[key].label;
                if (presetDesc) presetDesc.textContent = PRESETS[key].name;
            }
        });
        // Trigger initial preset
        if (presetSelect.value && PRESETS[presetSelect.value]) {
            featureInput.value = JSON.stringify(PRESETS[presetSelect.value].features);
            if (attackLabelInput) attackLabelInput.value = PRESETS[presetSelect.value].label;
            if (presetDesc) presetDesc.textContent = PRESETS[presetSelect.value].name;
        }
    }
}

function setupPacketPredictionForm() {
    const form = document.getElementById('packetPredictionForm');
    const resultsContainer = document.getElementById('predictionResultsBox');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const featureStr = document.getElementById('featureVectorInput').value.trim();
            const attackLabel = document.getElementById('attackLabelInput') ? document.getElementById('attackLabelInput').value : "BENIGN";

            let features;
            try {
                features = JSON.parse(featureStr);
                if (!Array.isArray(features)) throw new Error("Input must be a JSON array of numbers");
            } catch (err) {
                alert("Invalid input: Please provide a valid JSON array of numerical features, or pick a preset above.");
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⚡ Simulating Classical & Quantum Execution...';

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        features: features,
                        attack_label: attackLabel
                    })
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.detail || "Prediction failed");
                }

                renderPredictionResults(data);
            } catch (err) {
                alert(`Error executing prediction: ${err.message}`);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    }
}

function renderPredictionResults(data) {
    const box = document.getElementById('predictionResultsBox');
    if (!box) return;

    box.style.display = 'block';
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Classical Result
    const cVerdict = document.getElementById('classicalVerdict');
    const cConf = document.getElementById('classicalConfidence');
    const cBadge = document.getElementById('classicalBadge');
    if (cVerdict) {
        cVerdict.textContent = data.classical.is_threat ? "MALICIOUS CYBER THREAT" : "NORMAL NETWORK FLOW";
        cConf.textContent = `${(data.classical.confidence * 100).toFixed(1)}% Confidence`;
        cBadge.className = data.classical.is_threat ? 'badge badge-threat' : 'badge badge-safe';
        cBadge.textContent = data.classical.is_threat ? 'ATTACK DETECTED' : 'NORMAL';
    }

    // Quantum Result
    const qVerdict = document.getElementById('quantumVerdict');
    const qConf = document.getElementById('quantumConfidence');
    const qBadge = document.getElementById('quantumBadge');
    if (qVerdict) {
        qVerdict.textContent = data.quantum.is_threat ? "MALICIOUS CYBER THREAT" : "NORMAL NETWORK FLOW";
        qConf.textContent = `${(data.quantum.confidence * 100).toFixed(1)}% Quantum State Confidence`;
        qBadge.className = data.quantum.is_threat ? 'badge badge-threat' : 'badge badge-safe';
        qBadge.textContent = data.quantum.is_threat ? 'QUANTUM THREAT' : 'NORMAL';
    }

    // Digital Signature Security & Quantum Protocol Impact
    const sigStatus = document.getElementById('qdsSignatureStatus');
    const sigBadge = document.getElementById('qdsStatusBadge');
    const fidelityVal = document.getElementById('qdsFidelityValue');
    const qberVal = document.getElementById('qdsQberValue');
    const threatCategory = document.getElementById('qdsThreatCategory');
    const threatImpact = document.getElementById('qdsThreatImpact');
    const secVerdict = document.getElementById('qdsSecurityVerdict');

    const proto = data.digital_signature_protocol;
    const threat = data.threat_mapping;

    if (sigStatus) sigStatus.textContent = proto.signature_status;
    if (sigBadge) {
        sigBadge.className = proto.anomaly_detected ? 'badge badge-threat' : 'badge badge-safe';
        sigBadge.textContent = proto.anomaly_detected ? 'TAMPERED / FORGED' : 'VERIFIED AUTHENTIC';
    }
    if (fidelityVal) fidelityVal.textContent = `${(proto.state_fidelity * 100).toFixed(1)}%`;
    if (qberVal) qberVal.textContent = `${proto.qber_percent.toFixed(1)}%`;
    if (threatCategory) threatCategory.textContent = threat.category;
    if (threatImpact) threatImpact.textContent = threat.impact;
    if (secVerdict) secVerdict.textContent = proto.security_verdict;
}

function setupBenchmarkTrigger() {
    const btn = document.getElementById('runBenchmarkBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const sampleSize = document.getElementById('benchmarkSampleSize') ? parseInt(document.getElementById('benchmarkSampleSize').value) : 3000;
        const qubits = document.getElementById('benchmarkQubits') ? parseInt(document.getElementById('benchmarkQubits').value) : 4;

        if (!confirm(`Execute full experimental benchmark on ${sampleSize.toLocaleString()} real CIC records using ${qubits} simulated qubits? This will execute real PennyLane circuits.`)) {
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '⚙️ Executing Classical & Quantum Simulation Experiments...';

        try {
            const resp = await fetch('/api/run_benchmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sample_size: sampleSize, n_qubits: qubits })
            });

            const res = await resp.json();
            if (!resp.ok) throw new Error(res.detail || "Benchmark execution failed");

            alert("Benchmark completed successfully! Reloading dashboard results...");
            window.location.reload();
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '🚀 Re-Run Comparative Experiment';
        }
    });
}
