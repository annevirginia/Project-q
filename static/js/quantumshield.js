/**
 * QuantumShield v2 — Frontend JavaScript
 * Post-Quantum Risk Simulation Platform
 * All data is synthetic. Educational simulation only.
 */

// ─── State ──────────────────────────────────────────────────────────────
let currentPage = 'overview';
let dashboardData = null;
let findingsData = [];
let assetsData = [];
let signaturesData = [];
let migrationData = [];
let ledgerData = [];
let chartsMap = {};

// ─── Page Navigation ────────────────────────────────────────────────────

function switchPage(page) {
    // Deactivate all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));

    // Activate target page
    const target = document.getElementById('page-' + page);
    if (target) target.classList.add('active');

    const navLink = document.querySelector(`[data-page="${page}"]`);
    if (navLink) navLink.classList.add('active');

    currentPage = page;

    // Load page data
    loadPageData(page);
}

function loadPageData(page) {
    switch (page) {
        case 'overview': loadOverview(); break;
        case 'inventory': loadInventory(); break;
        case 'risk': loadRiskAnalysis(); break;
        case 'lifecycle': loadLifecycleSelector(); break;
        case 'attack-surface': loadAttackSurface(); break;
        case 'signatures': loadSignatures(); break;
        case 'ledger': loadLedger(); break;
        case 'migration': loadMigration(); break;
        case 'explainable': loadExplainable(); break;
    }
}

// ─── Dataset Switching ──────────────────────────────────────────────────

async function switchDataset(profile) {
    showLoading(true);
    try {
        const resp = await fetch(`/api/datasets/${profile}/load`, { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'success') {
            document.getElementById('profile-name-header').textContent =
                { A: 'Legacy Enterprise', B: 'Mixed Transition', C: 'PQC Migration Program', D: 'Stress-Test Environment' }[profile] || profile;
            // Reload current page
            loadPageData(currentPage);
        }
    } catch (e) {
        console.error('Dataset switch failed:', e);
    }
    showLoading(false);
}

async function resetSimulation() {
    showLoading(true);
    try {
        await fetch('/api/reset', { method: 'POST' });
        document.getElementById('dataset-select').value = 'A';
        document.getElementById('profile-name-header').textContent = 'Legacy Enterprise';
        loadPageData(currentPage);
    } catch (e) {
        console.error('Reset failed:', e);
    }
    showLoading(false);
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
}

// ─── API Helpers ────────────────────────────────────────────────────────

const API_BASE = (window.location.protocol.startsWith('http') && window.location.port === '5000')
    ? ''
    : 'http://127.0.0.1:5000';

async function api(path) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const resp = await fetch(url);
    return resp.json();
}

async function apiPost(path, body = {}) {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    return resp.json();
}

// ─── Executive Overview ─────────────────────────────────────────────────

async function loadOverview() {
    try {
        const [report, riskSummary] = await Promise.all([
            api('/api/reports/executive'),
            api('/api/risk/summary'),
        ]);

        dashboardData = report;

        // Render dashboard cards
        renderDashboardCards(report.cards);

        // Render charts
        renderRiskDistribution(riskSummary.risk_distribution);
        renderQuantumStatus();
        renderAlgoDistribution(riskSummary.algorithm_risk);
        renderAgilityScore(riskSummary.agility_score);

    } catch (e) {
        console.error('Overview load failed:', e);
    }
}

function renderDashboardCards(cards) {
    const grid = document.getElementById('dashboard-cards');
    if (!grid) return;

    const cardDefs = [
        { key: 'total_assets', label: 'Total Assets', icon: '📦', cls: '' },
        { key: 'assets_scanned', label: 'Assets Scanned', icon: '🔍', cls: '' },
        { key: 'quantum_vulnerable', label: 'Quantum Vulnerable', icon: '⚠️', cls: 'danger' },
        { key: 'pqc_ready', label: 'PQC Ready', icon: '🛡️', cls: 'success' },
        { key: 'critical_findings', label: 'Critical Findings', icon: '🔴', cls: 'danger' },
        { key: 'hndl_exposure', label: 'HNDL Exposed', icon: '🎯', cls: 'warning' },
        { key: 'sigs_needing_migration', label: 'Sigs Needing Migration', icon: '✍️', cls: 'warning' },
        { key: 'agility_score', label: 'Agility Score', icon: '⚡', cls: 'purple' },
        { key: 'migration_completion_pct', label: 'Migration Complete', icon: '📈', cls: 'success', suffix: '%' },
        { key: 'evidence_gaps', label: 'Evidence Gaps', icon: '❓', cls: 'warning' },
        { key: 'pending_approvals', label: 'Pending Approvals', icon: '📋', cls: '' },
    ];

    grid.innerHTML = cardDefs.map(d => {
        let val = cards[d.key] ?? 0;
        if (typeof val === 'number' && val > 999) val = val.toLocaleString();
        return `
            <div class="stat-card ${d.cls}">
                <div class="stat-value">${val}${d.suffix || ''}</div>
                <div class="stat-label">${d.icon} ${d.label}</div>
            </div>
        `;
    }).join('');
}

function renderRiskDistribution(dist) {
    destroyChart('risk-distribution-chart');
    const ctx = document.getElementById('risk-distribution-chart');
    if (!ctx) return;

    chartsMap['risk-distribution-chart'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Moderate', 'High', 'Critical'],
            datasets: [{
                data: [dist.Low || 0, dist.Moderate || 0, dist.High || 0, dist.Critical || 0],
                backgroundColor: ['#22c55e', '#eab308', '#f97316', '#ef4444'],
                borderColor: '#0f1425',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#8b92a8', font: { family: 'Outfit', size: 10 }, boxWidth: 10, padding: 8 }
                }
            }
        }
    });
}

async function renderQuantumStatus() {
    try {
        const data = await api('/api/assets');
        assetsData = data.assets;

        const statusCounts = {};
        data.assets.forEach(a => {
            const s = a.quantum_status || 'unknown';
            statusCounts[s] = (statusCounts[s] || 0) + 1;
        });

        destroyChart('quantum-status-chart');
        const ctx = document.getElementById('quantum-status-chart');
        if (!ctx) return;

        const labels = Object.keys(statusCounts);
        const colors = labels.map(l => ({
            'quantum-broken': '#ef4444',
            'quantum-weakened': '#f97316',
            'classically-broken': '#eab308',
            'quantum-resilient': '#22c55e',
        })[l] || '#6b7280');

        chartsMap['quantum-status-chart'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.map(l => l.replace('-', ' ').replace(/\b\w/g, c => c.toUpperCase())),
                datasets: [{
                    label: 'Assets',
                    data: Object.values(statusCounts),
                    backgroundColor: colors,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: '#8b92a8', font: { size: 9 } }, grid: { display: false } },
                    y: { ticks: { color: '#8b92a8', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    } catch (e) { console.error(e); }
}

function renderAlgoDistribution(algoRisk) {
    destroyChart('algo-distribution-chart');
    const ctx = document.getElementById('algo-distribution-chart');
    if (!ctx) return;

    const labels = Object.keys(algoRisk).slice(0, 12);
    const scores = labels.map(l => algoRisk[l].avg_score);
    const counts = labels.map(l => algoRisk[l].count);

    chartsMap['algo-distribution-chart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Avg Risk Score',
                    data: scores,
                    backgroundColor: scores.map(s => s >= 75 ? '#ef4444' : s >= 50 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'),
                    borderRadius: 3,
                    yAxisID: 'y',
                },
                {
                    label: 'Asset Count',
                    data: counts,
                    type: 'line',
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0,212,255,0.1)',
                    pointBackgroundColor: '#00d4ff',
                    pointRadius: 2,
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#8b92a8', font: { size: 9 }, boxWidth: 10, padding: 6 } }
            },
            scales: {
                x: { ticks: { color: '#8b92a8', font: { size: 8 }, maxRotation: 35 }, grid: { display: false } },
                y: { position: 'left', ticks: { color: '#8b92a8', font: { size: 8 } }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Risk Score', color: '#8b92a8', font: { size: 8 } } },
                y1: { position: 'right', ticks: { color: '#00d4ff', font: { size: 8 } }, grid: { display: false }, title: { display: true, text: 'Count', color: '#00d4ff', font: { size: 8 } } }
            }
        }
    });
}

function renderAgilityScore(agility) {
    if (!agility) return;

    // Gauge using Plotly
    const gaugeDiv = document.getElementById('agility-gauge');
    if (gaugeDiv) {
        Plotly.newPlot(gaugeDiv, [{
            type: 'indicator',
            mode: 'gauge+number',
            value: agility.score,
            gauge: {
                axis: { range: [0, 100], tickcolor: '#8b92a8', tickfont: { size: 9 } },
                bar: { color: agility.score >= 70 ? '#22c55e' : agility.score >= 40 ? '#eab308' : '#ef4444', thickness: 0.25 },
                bgcolor: '#1e2545',
                bordercolor: 'rgba(255,255,255,0.06)',
                steps: [
                    { range: [0, 33], color: 'rgba(239,68,68,0.1)' },
                    { range: [33, 66], color: 'rgba(234,179,8,0.1)' },
                    { range: [66, 100], color: 'rgba(34,197,94,0.1)' },
                ],
            },
            number: { font: { color: '#e8eaf0', family: 'JetBrains Mono', size: 22 } },
        }], {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 8, b: 8, l: 20, r: 20 },
            height: 125,
            font: { color: '#8b92a8' },
        }, { responsive: true, displayModeBar: false });
    }

    // Factor list
    const factorsDiv = document.getElementById('agility-factors');
    if (factorsDiv && agility.factors) {
        factorsDiv.innerHTML = Object.entries(agility.factors).map(([key, val]) => {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            const color = val >= 70 ? 'green' : val >= 40 ? 'orange' : 'red';
            return `
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:3px;">
                        <span style="color:var(--text-secondary)">${label}</span>
                        <span style="color:var(--accent-cyan);font-family:var(--font-mono)">${val}%</span>
                    </div>
                    <div class="progress-bar"><div class="progress-fill ${color}" style="width:${val}%"></div></div>
                </div>
            `;
        }).join('');
    }
}

// ─── Crypto Inventory ───────────────────────────────────────────────────

async function loadInventory() {
    try {
        const data = await api('/api/findings');
        findingsData = data.findings;
        renderInventoryTable(findingsData);
    } catch (e) { console.error(e); }
}

function renderInventoryTable(findings) {
    const tbody = document.getElementById('inventory-tbody');
    if (!tbody) return;

    tbody.innerHTML = findings.map(f => {
        const bandClass = (f.risk_band || '').toLowerCase();
        const qsBadge = getQuantumBadge(f.algorithm);
        const hndlBadge = f.hndl_status?.includes('immediate') ? '<span class="badge badge-red">URGENT</span>'
            : f.hndl_status?.includes('hybrid') ? '<span class="badge badge-orange">HYBRID</span>'
            : f.hndl_status?.includes('monitoring') ? '<span class="badge badge-yellow">MONITOR</span>'
            : '<span class="badge badge-green">OK</span>';

        return `
            <tr>
                <td><span style="font-family:var(--font-mono);color:var(--accent-cyan)">#${f.priority}</span></td>
                <td>${getAssetName(f.asset_id)}</td>
                <td>${getAssetType(f.asset_id)}</td>
                <td><code style="color:var(--accent-purple)">${f.algorithm}</code></td>
                <td>${f.algorithm_role || '-'}</td>
                <td>${qsBadge}</td>
                <td>
                    <span class="badge badge-${bandClass}">${f.risk_score?.toFixed(1)} — ${f.risk_band}</span>
                </td>
                <td>${getAssetClassification(f.asset_id)}</td>
                <td>${hndlBadge}</td>
                <td><button class="btn-link" onclick="showFinding('${f.finding_id}')">Details</button></td>
            </tr>
        `;
    }).join('');
}

function filterInventory() {
    const qsFilter = document.getElementById('filter-quantum-status')?.value;
    const rbFilter = document.getElementById('filter-risk-band')?.value;
    const typeFilter = document.getElementById('filter-asset-type')?.value;
    const search = (document.getElementById('filter-search')?.value || '').toLowerCase();

    let filtered = findingsData;

    if (qsFilter) {
        filtered = filtered.filter(f => {
            const asset = assetsData.find(a => a.asset_id === f.asset_id);
            return asset && asset.quantum_status === qsFilter;
        });
    }
    if (rbFilter) {
        filtered = filtered.filter(f => f.risk_band === rbFilter);
    }
    if (typeFilter) {
        filtered = filtered.filter(f => {
            const asset = assetsData.find(a => a.asset_id === f.asset_id);
            return asset && asset.asset_type === typeFilter;
        });
    }
    if (search) {
        filtered = filtered.filter(f => {
            const name = getAssetName(f.asset_id).toLowerCase();
            return name.includes(search) || f.algorithm.toLowerCase().includes(search);
        });
    }

    renderInventoryTable(filtered);
}

function showFinding(findingId) {
    const finding = findingsData.find(f => f.finding_id === findingId);
    if (!finding) return;

    const content = document.getElementById('finding-detail-content');
    content.innerHTML = `
        <h3 style="color:var(--accent-cyan);margin-bottom:16px;">Finding: ${finding.finding_id}</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
            <div><strong>Asset:</strong> ${getAssetName(finding.asset_id)}</div>
            <div><strong>Algorithm:</strong> <code style="color:var(--accent-purple)">${finding.algorithm}</code></div>
            <div><strong>Role:</strong> ${finding.algorithm_role}</div>
            <div><strong>Risk Score:</strong> <span class="badge badge-${(finding.risk_band||'').toLowerCase()}">${finding.risk_score?.toFixed(1)} — ${finding.risk_band}</span></div>
            <div><strong>HNDL Status:</strong> ${finding.hndl_status}</div>
            <div><strong>Confidence:</strong> ${finding.confidence}</div>
        </div>

        <h4 style="color:var(--text-primary);margin-bottom:8px;">Risk Factor Breakdown</h4>
        <table class="data-table compact" style="margin-bottom:16px;">
            <thead><tr><th>Factor</th><th>Raw (0–100)</th><th>Weight</th><th>Contribution</th></tr></thead>
            <tbody>
                ${renderFactorRow('Algorithm Risk', finding.algorithm_risk, 0.25)}
                ${renderFactorRow('Data Sensitivity', finding.data_sensitivity, 0.20)}
                ${renderFactorRow('Data Lifetime', finding.data_lifetime, 0.15)}
                ${renderFactorRow('Asset Criticality', finding.asset_criticality, 0.15)}
                ${renderFactorRow('Internet Exposure', finding.internet_exposure, 0.10)}
                ${renderFactorRow('Migration Complexity', finding.migration_complexity_score, 0.10)}
                ${renderFactorRow('Inventory Uncertainty', finding.inventory_uncertainty, 0.05)}
            </tbody>
        </table>

        <h4 style="color:var(--text-primary);margin-bottom:8px;">Recommended Action</h4>
        <p style="color:var(--text-secondary);margin-bottom:12px;">${finding.recommended_action}</p>

        <h4 style="color:var(--text-primary);margin-bottom:8px;">Full Explanation</h4>
        <pre>${finding.explanation || 'No explanation available.'}</pre>
    `;

    document.getElementById('finding-modal').style.display = 'flex';
}

function renderFactorRow(label, raw, weight) {
    const contrib = (raw * weight).toFixed(1);
    const barColor = raw >= 75 ? 'red' : raw >= 50 ? 'orange' : raw >= 25 ? 'cyan' : 'green';
    return `
        <tr>
            <td>${label}</td>
            <td>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-family:var(--font-mono);width:35px">${raw}</span>
                    <div class="progress-bar" style="flex:1"><div class="progress-fill ${barColor}" style="width:${raw}%"></div></div>
                </div>
            </td>
            <td style="font-family:var(--font-mono)">${(weight * 100).toFixed(0)}%</td>
            <td style="font-family:var(--font-mono);color:var(--accent-cyan)">${contrib}</td>
        </tr>
    `;
}

// ─── Data Lifecycle ─────────────────────────────────────────────────────

async function loadLifecycleSelector() {
    if (!assetsData.length) {
        const data = await api('/api/assets');
        assetsData = data.assets;
    }

    const select = document.getElementById('lifecycle-asset-select');
    if (select && select.options.length <= 1) {
        assetsData.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.asset_id;
            opt.textContent = `${a.asset_id} — ${a.asset_name} (${a.algorithm})`;
            select.appendChild(opt);
        });
    }
}

async function loadLifecycle(assetId) {
    if (!assetId) return;

    try {
        const data = await api(`/api/lifecycle/${assetId}`);
        renderTimeline(data.timeline);

        const analysisDiv = document.getElementById('lifecycle-analysis');
        const contentDiv = document.getElementById('lifecycle-analysis-content');
        if (analysisDiv && contentDiv) {
            analysisDiv.style.display = 'block';
            const a = data.analysis;
            contentDiv.innerHTML = `
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.85rem;">
                    <div>Required confidentiality: <strong>${data.data_lifetime_years} years</strong></div>
                    <div>Current encryption sufficient: <strong style="color:${a.current_encryption_sufficient ? 'var(--accent-green)' : 'var(--accent-red)'}">${a.current_encryption_sufficient ? 'Yes' : 'No'}</strong></div>
                    <div>Harvestable now: <strong style="color:${a.harvestable_now ? 'var(--accent-red)' : 'var(--accent-green)'}">${a.harvestable_now ? 'Yes' : 'No'}</strong></div>
                    <div>Future decryption risk: <strong style="color:${a.future_decryption_risk ? 'var(--accent-red)' : 'var(--accent-green)'}">${a.future_decryption_risk ? 'Yes' : 'No'}</strong></div>
                    <div>Re-encryption needed: <strong>${a.re_encryption_needed ? 'Yes' : 'No'}</strong></div>
                    <div>Signature longevity risk: <strong>${a.signature_longevity_risk ? 'Yes' : 'No'}</strong></div>
                </div>
                <p style="margin-top:12px;color:var(--text-secondary);font-size:0.85rem;">
                    <strong>Recommendation:</strong> ${data.recommended_action}
                </p>
                <p style="margin-top:6px;color:var(--text-secondary);font-size:0.82rem;">
                    Quantum exposure: <span class="badge badge-${data.quantum_exposure_classification === 'critical' ? 'red' : data.quantum_exposure_classification === 'high' ? 'orange' : data.quantum_exposure_classification === 'moderate' ? 'yellow' : 'green'}">${data.quantum_exposure_classification}</span>
                </p>
            `;
        }
    } catch (e) { console.error(e); }
}

function renderTimeline(events) {
    const container = document.getElementById('lifecycle-timeline');
    if (!container || !events) return;

    container.innerHTML = `
        <div class="timeline">
            ${events.map(e => `
                <div class="timeline-event risk-${e.risk_level}">
                    <div class="timeline-year">${e.year}${e.end_year ? ' → ' + e.end_year : ''}</div>
                    <div class="timeline-desc">${e.description}</div>
                    <span class="badge badge-${e.risk_level === 'critical' ? 'red' : e.risk_level === 'high' ? 'orange' : e.risk_level === 'moderate' ? 'yellow' : 'green'}">${e.risk_level} risk</span>
                </div>
            `).join('')}
        </div>
    `;
}

// ─── Risk Analysis ──────────────────────────────────────────────────────

async function loadRiskAnalysis() {
    try {
        const data = await api('/api/risk/summary');

        // Risk heatmap using Plotly
        renderRiskHeatmap(data.algorithm_risk);

        // Risk factor radar
        if (data.agility_score && data.agility_score.factors) {
            renderRiskRadar(data.agility_score.factors);
        }

        // Critical assets list
        renderCriticalAssets();

    } catch (e) { console.error(e); }
}

function renderRiskHeatmap(algoRisk) {
    const div = document.getElementById('risk-heatmap');
    if (!div) return;

    const algos = Object.keys(algoRisk);
    const scores = algos.map(a => algoRisk[a].avg_score);
    const counts = algos.map(a => algoRisk[a].count);
    const text = algos.map((a, i) => `${a}<br>Score: ${scores[i]}<br>Count: ${counts[i]}`);

    Plotly.newPlot(div, [{
        type: 'bar',
        x: algos,
        y: scores,
        marker: {
            color: scores.map(s => s >= 75 ? '#ef4444' : s >= 50 ? '#f97316' : s >= 25 ? '#eab308' : '#22c55e'),
        },
        text: counts.map(c => `n=${c}`),
        textposition: 'outside',
        textfont: { size: 8 },
        hovertext: text,
        hoverinfo: 'text',
    }], {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        margin: { t: 15, b: 60, l: 35, r: 15 },
        xaxis: { tickangle: -40, tickfont: { color: '#8b92a8', size: 8 } },
        yaxis: { title: 'Avg Risk', titlefont: { color: '#8b92a8', size: 9 }, tickfont: { color: '#8b92a8', size: 8 }, gridcolor: 'rgba(255,255,255,0.05)' },
        font: { color: '#8b92a8', family: 'Outfit' },
        height: 190,
    }, { responsive: true, displayModeBar: false });
}

function renderRiskRadar(factors) {
    destroyChart('risk-factors-radar');
    const ctx = document.getElementById('risk-factors-radar');
    if (!ctx) return;

    const labels = Object.keys(factors).map(k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()));
    const values = Object.values(factors);

    chartsMap['risk-factors-radar'] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels,
            datasets: [{
                label: 'Agility Factors',
                data: values,
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0,212,255,0.15)',
                pointBackgroundColor: '#00d4ff',
                pointBorderColor: '#0f1425',
                pointRadius: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#5a6178', backdropColor: 'transparent', stepSize: 25, font: { size: 8 } },
                    grid: { color: 'rgba(255,255,255,0.08)' },
                    pointLabels: { color: '#8b92a8', font: { size: 8 } },
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderCriticalAssets() {
    const div = document.getElementById('critical-assets-list');
    if (!div || !findingsData.length) {
        if (div) div.innerHTML = '<p style="color:var(--text-muted)">Load findings from the Inventory page first.</p>';
        return;
    }

    const critical = findingsData.filter(f => f.risk_band === 'Critical' || f.risk_band === 'High').slice(0, 10);
    div.innerHTML = critical.map(f => `
        <div class="finding-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4>${getAssetName(f.asset_id)} <code style="font-size:0.75rem;color:var(--accent-purple)">${f.algorithm}</code></h4>
                <span class="badge badge-${(f.risk_band||'').toLowerCase()}">${f.risk_score?.toFixed(1)}</span>
            </div>
            <p style="font-size:0.82rem;color:var(--text-secondary);margin-top:6px;">${f.recommended_action}</p>
        </div>
    `).join('');
}

// ─── Attack Surface ─────────────────────────────────────────────────────

async function loadAttackSurface() {
    try {
        const data = await api('/api/attack-surface');
        renderAttackGraph(data);
    } catch (e) { console.error(e); }
}

function renderAttackGraph(data) {
    const div = document.getElementById('attack-surface-graph');
    if (!div) return;

    // Use Plotly network graph
    const nodeX = [];
    const nodeY = [];
    const nodeText = [];
    const nodeColors = [];
    const nodeSizes = [];

    // Position nodes in a circular layout
    const n = data.nodes.length;
    data.nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / n;
        const radius = 3 + (node.risk_score / 30);
        nodeX.push(Math.cos(angle) * radius);
        nodeY.push(Math.sin(angle) * radius);
        nodeText.push(`${node.label}<br>Algorithm: ${node.algorithm}<br>Risk: ${node.risk_band} (${node.risk_score?.toFixed(1)})<br>Status: ${node.quantum_status}`);
        nodeColors.push(node.color);
        nodeSizes.push(12 + (node.risk_score / 8));
    });

    // Edges
    const edgeX = [];
    const edgeY = [];
    data.edges.forEach(edge => {
        const src = data.nodes.findIndex(n => n.id === edge.source);
        const tgt = data.nodes.findIndex(n => n.id === edge.target);
        if (src >= 0 && tgt >= 0) {
            edgeX.push(nodeX[src], nodeX[tgt], null);
            edgeY.push(nodeY[src], nodeY[tgt], null);
        }
    });

    Plotly.newPlot(div, [
        {
            type: 'scatter',
            x: edgeX, y: edgeY,
            mode: 'lines',
            line: { color: 'rgba(255,255,255,0.1)', width: 1 },
            hoverinfo: 'none',
        },
        {
            type: 'scatter',
            x: nodeX, y: nodeY,
            mode: 'markers+text',
            marker: { color: nodeColors, size: nodeSizes.map(s => Math.round(s * 0.7)), line: { color: 'rgba(255,255,255,0.2)', width: 1 } },
            text: data.nodes.map(n => n.label.length > 12 ? n.label.substring(0, 12) + '…' : n.label),
            textposition: 'top center',
            textfont: { color: '#8b92a8', size: 8 },
            hovertext: nodeText,
            hoverinfo: 'text',
        }
    ], {
        paper_bgcolor: 'transparent',
        plot_bgcolor: '#0f1425',
        margin: { t: 8, b: 8, l: 8, r: 8 },
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        showlegend: false,
        height: 310,
    }, { responsive: true, displayModeBar: false });

    // Click handler for node details
    div.on('plotly_click', function(eventData) {
        if (eventData.points && eventData.points[0] && eventData.points[0].curveNumber === 1) {
            const idx = eventData.points[0].pointIndex;
            showNodeDetail(data.nodes[idx]);
        }
    });
}

function showNodeDetail(node) {
    const panel = document.getElementById('node-detail-panel');
    const title = document.getElementById('node-detail-title');
    const content = document.getElementById('node-detail-content');
    if (!panel || !content) return;

    panel.style.display = 'block';
    title.textContent = node.label;
    content.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.85rem;">
            <div>Asset ID: <code>${node.id}</code></div>
            <div>Type: <strong>${node.type}</strong></div>
            <div>Algorithm: <code style="color:var(--accent-purple)">${node.algorithm}</code></div>
            <div>Quantum Status: ${getQuantumBadge(node.algorithm)}</div>
            <div>Risk: <span class="badge badge-${(node.risk_band||'').toLowerCase()}">${node.risk_score?.toFixed(1)} — ${node.risk_band}</span></div>
            <div>Classification: <strong>${node.classification}</strong></div>
            <div>Owner: ${node.owner}</div>
            <div>Migration: <strong>${node.migration_status}</strong></div>
            <div>Internet Exposed: <strong style="color:${node.internet_exposed ? 'var(--accent-red)' : 'var(--accent-green)'}">${node.internet_exposed ? 'Yes' : 'No'}</strong></div>
        </div>
    `;
}

// ─── Signatures ─────────────────────────────────────────────────────────

async function loadSignatures() {
    try {
        const data = await api('/api/signatures');
        signaturesData = data.signatures;
        renderSignaturesTable(signaturesData);
    } catch (e) { console.error(e); }
}

function renderSignaturesTable(sigs) {
    const tbody = document.getElementById('signatures-tbody');
    if (!tbody) return;

    tbody.innerHTML = sigs.map(s => {
        const statusBadge = {
            valid: '<span class="badge badge-green">Valid</span>',
            tampered: '<span class="badge badge-red">TAMPERED</span>',
            invalid: '<span class="badge badge-red">Invalid</span>',
            expired: '<span class="badge badge-yellow">Expired</span>',
        }[s.status] || '<span class="badge badge-gray">Unknown</span>';

        return `
            <tr>
                <td><code>${s.sig_id}</code></td>
                <td>${getAssetName(s.asset_id)}</td>
                <td><code style="color:var(--accent-purple)">${s.algorithm}</code></td>
                <td>${statusBadge}</td>
                <td>${s.certificate_status}</td>
                <td>${getQuantumBadge(s.algorithm)}</td>
                <td>${s.data_lifetime_years}</td>
                <td><button class="btn-link" onclick="verifySig('${s.sig_id}')">🔍 Verify</button></td>
            </tr>
        `;
    }).join('');
}

function filterSignatures() {
    const statusFilter = document.getElementById('sig-filter-status')?.value;
    const quantumFilter = document.getElementById('sig-filter-quantum')?.value;

    let filtered = signaturesData;
    if (statusFilter) filtered = filtered.filter(s => s.status === statusFilter);
    if (quantumFilter) filtered = filtered.filter(s => s.quantum_status === quantumFilter);

    renderSignaturesTable(filtered);
}

async function verifySig(sigId) {
    try {
        const data = await api(`/api/signatures/${sigId}/verify`);
        const v = data.verification;
        const s = data.signature;

        const content = document.getElementById('sig-verify-content');
        content.innerHTML = `
            <h3 style="color:${v.verified ? 'var(--accent-green)' : 'var(--accent-red)'}; margin-bottom:16px;">
                ${v.verified ? '✅' : '❌'} Signature Verification: ${v.status}
            </h3>
            <p style="margin-bottom:12px;">${v.message}</p>
            ${v.quantum_warning ? `<div class="card disclaimer-card" style="margin-bottom:12px;"><p style="color:var(--accent-yellow)">${v.quantum_detail || 'Quantum vulnerability detected.'}</p></div>` : ''}
            <table class="data-table compact">
                <tr><td>Signature ID</td><td><code>${s.sig_id}</code></td></tr>
                <tr><td>Algorithm</td><td><code style="color:var(--accent-purple)">${s.algorithm}</code></td></tr>
                <tr><td>Key ID</td><td><code>${s.key_id}</code></td></tr>
                <tr><td>Document Hash</td><td><code style="font-size:0.7rem">${s.document_hash?.substring(0, 32)}...</code></td></tr>
                <tr><td>Signature</td><td><code style="font-size:0.7rem">${s.signature_hex?.substring(0, 32)}...</code></td></tr>
                <tr><td>Recommended Action</td><td>${s.recommended_action}</td></tr>
            </table>
        `;
        document.getElementById('sig-verify-modal').style.display = 'flex';
    } catch (e) { console.error(e); }
}

// ─── Blockchain Ledger ──────────────────────────────────────────────────

async function loadLedger() {
    try {
        const data = await api('/api/ledger?per_page=50');
        ledgerData = data.transactions;
        renderLedgerTable(ledgerData);
        renderLedgerMigrationChart(ledgerData);
    } catch (e) { console.error(e); }
}

function renderLedgerTable(txs) {
    const tbody = document.getElementById('ledger-tbody');
    if (!tbody) return;

    tbody.innerHTML = txs.map(tx => {
        const sigBadge = tx.signature_status === 'valid'
            ? '<span class="badge badge-green">Valid</span>'
            : '<span class="badge badge-red">Invalid</span>';
        const migBadge = {
            legacy: '<span class="badge badge-red">Legacy</span>',
            hybrid: '<span class="badge badge-yellow">Hybrid</span>',
            'post-quantum': '<span class="badge badge-green">PQC</span>',
        }[tx.migration_status] || '';

        return `
            <tr style="${tx.is_tampered ? 'background:rgba(239,68,68,0.05)' : ''}">
                <td><code>${tx.tx_id}</code></td>
                <td>${tx.block_number}</td>
                <td>${tx.sender}</td>
                <td>${tx.receiver}</td>
                <td style="font-family:var(--font-mono)">${Number(tx.amount).toLocaleString()} SIM</td>
                <td><code style="color:var(--accent-purple)">${tx.signature_algorithm}</code></td>
                <td>${sigBadge}</td>
                <td>${migBadge}</td>
            </tr>
        `;
    }).join('');
}

function renderLedgerMigrationChart(txs) {
    const legacy = txs.filter(t => t.migration_status === 'legacy').length;
    const hybrid = txs.filter(t => t.migration_status === 'hybrid').length;
    const pqc = txs.filter(t => t.migration_status === 'post-quantum').length;

    destroyChart('ledger-migration-chart');
    const ctx = document.getElementById('ledger-migration-chart');
    if (!ctx) return;

    chartsMap['ledger-migration-chart'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Legacy', 'Hybrid', 'Post-Quantum'],
            datasets: [{
                data: [legacy, hybrid, pqc],
                backgroundColor: ['#ef4444', '#eab308', '#22c55e'],
                borderColor: '#0f1425',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#8b92a8', font: { family: 'Outfit', size: 10 }, boxWidth: 10, padding: 6 }
                }
            }
        }
    });
}

async function verifyLedger() {
    try {
        const data = await api('/api/ledger/verify');
        const div = document.getElementById('ledger-verification-result');
        div.style.display = 'block';
        div.innerHTML = `
            <h3 style="color:${data.chain_integrity ? 'var(--accent-green)' : 'var(--accent-red)'}">
                ${data.chain_integrity ? '✅ Chain Integrity Verified' : '❌ Chain Integrity Compromised'}
            </h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0;">
                <div class="stat-card"><div class="stat-value">${data.total_transactions}</div><div class="stat-label">Total TXs</div></div>
                <div class="stat-card success"><div class="stat-value">${data.valid_transactions}</div><div class="stat-label">Valid</div></div>
                <div class="stat-card danger"><div class="stat-value">${data.tampered_transactions}</div><div class="stat-label">Tampered</div></div>
                <div class="stat-card"><div class="stat-value">${data.signature_migration.pqc_pct}%</div><div class="stat-label">PQC Signed</div></div>
            </div>
            ${data.tampered_details.length > 0 ? `
                <h4 style="color:var(--accent-red);margin-bottom:8px;">⚠️ Tampered Transactions Detected</h4>
                ${data.tampered_details.map(t => `
                    <div class="finding-card" style="border-left:3px solid var(--accent-red);">
                        <code>${t.tx_id}</code> — ${t.sender} → ${t.receiver}: ${t.amount} SIM
                        <br><small>Algorithm: ${t.algorithm} | Block: ${t.block}</small>
                    </div>
                `).join('')}
            ` : ''}
            <p style="margin-top:12px;color:var(--text-secondary);font-size:0.85rem;">${data.recommendation}</p>
        `;
    } catch (e) { console.error(e); }
}

async function migrateLedger() {
    try {
        const data = await apiPost('/api/ledger/migrate', { target_algorithm: 'ML-DSA-65' });
        const div = document.getElementById('ledger-verification-result');
        div.style.display = 'block';
        div.innerHTML = `
            <h3 style="color:var(--accent-cyan)">🚀 Ledger Migration Simulation Complete</h3>
            <p style="margin:8px 0;color:var(--text-secondary)">Migrated ${data.migrated_count} transactions to ML-DSA-65</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0;">
                <div>
                    <h4>Before Migration</h4>
                    <p>Legacy: ${data.before.signature_migration.legacy} | PQC: ${data.before.signature_migration.post_quantum}</p>
                </div>
                <div>
                    <h4>After Migration</h4>
                    <p>Legacy: ${data.after.signature_migration.legacy} | PQC: ${data.after.signature_migration.post_quantum}</p>
                </div>
            </div>
        `;
    } catch (e) { console.error(e); }
}

// ─── Migration Planner ──────────────────────────────────────────────────

async function loadMigration() {
    try {
        const data = await api('/api/migration/tasks');
        migrationData = data.tasks;
        renderMigrationTable(migrationData);
        renderMigrationPhases(data.phase_summary);
    } catch (e) { console.error(e); }
}

function renderMigrationTable(tasks) {
    const tbody = document.getElementById('migration-tbody');
    if (!tbody) return;

    tbody.innerHTML = tasks.map(t => {
        const progressColor = t.progress_percent >= 80 ? 'green' : t.progress_percent >= 40 ? 'cyan' : 'orange';
        return `
            <tr>
                <td><code>${t.task_id}</code></td>
                <td>${getAssetName(t.asset_id)}</td>
                <td><code style="color:var(--accent-red)">${t.current_algorithm}</code></td>
                <td><code style="color:var(--accent-green)">${t.recommended_target}</code></td>
                <td>${t.migration_phase}. ${t.phase_name}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div class="progress-bar" style="width:80px"><div class="progress-fill ${progressColor}" style="width:${t.progress_percent}%"></div></div>
                        <span style="font-family:var(--font-mono);font-size:0.75rem">${t.progress_percent?.toFixed(0)}%</span>
                    </div>
                </td>
                <td style="font-family:var(--font-mono)">$${Number(t.estimated_cost).toLocaleString()}</td>
                <td><span class="badge badge-${t.approval_status === 'approved' ? 'green' : 'yellow'}">${t.approval_status}</span></td>
                <td><span class="badge badge-${t.validation_status === 'passed' ? 'green' : t.validation_status === 'in-progress' ? 'blue' : 'gray'}">${t.validation_status}</span></td>
            </tr>
        `;
    }).join('');
}

function renderMigrationPhases(summary) {
    destroyChart('migration-phases-chart');
    const ctx = document.getElementById('migration-phases-chart');
    if (!ctx || !summary) return;

    const labels = Object.keys(summary);
    const values = Object.values(summary);

    chartsMap['migration-phases-chart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Tasks in Phase',
                data: values,
                backgroundColor: values.map((_, i) => {
                    const hue = (i / labels.length) * 240;
                    return `hsla(${hue}, 70%, 55%, 0.8)`;
                }),
                borderRadius: 3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#8b92a8', font: { size: 9 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#8b92a8', font: { size: 8 } }, grid: { display: false } }
            }
        }
    });
}

// ─── What-If Simulator ──────────────────────────────────────────────────

function updateWhatIfLabel(input) {
    const id = input.id;
    const label = document.getElementById(id + '-label');
    if (label) {
        if (id === 'whatif-qubits') {
            label.textContent = Number(input.value).toLocaleString();
        } else {
            label.textContent = input.value + '%';
        }
    }
}

async function runWhatIf() {
    const params = {
        quantum_capability: parseInt(document.getElementById('whatif-quantum')?.value || 50) / 100,
        logical_qubits: parseInt(document.getElementById('whatif-qubits')?.value || 4000),
        error_correction_maturity: parseInt(document.getElementById('whatif-errorcorr')?.value || 50) / 100,
    };

    const lifetime = document.getElementById('whatif-lifetime')?.value;
    if (lifetime) params.data_lifetime_override = parseInt(lifetime);

    const budget = document.getElementById('whatif-budget')?.value;
    if (budget) params.migration_budget = parseFloat(budget);

    const rotation = document.getElementById('whatif-rotation')?.value;
    if (rotation) params.key_rotation_freq_days = parseInt(rotation);

    try {
        const data = await apiPost('/api/whatif', params);
        const r = data.results;

        const div = document.getElementById('whatif-results');
        div.style.display = 'block';
        document.getElementById('whatif-results-content').innerHTML = `
            <div class="cards-grid" style="margin-bottom:16px;">
                <div class="stat-card"><div class="stat-value">${r.average_risk_score}</div><div class="stat-label">Avg Risk Score</div></div>
                <div class="stat-card danger"><div class="stat-value">${r.critical_risk_assets}</div><div class="stat-label">Critical Assets</div></div>
                <div class="stat-card warning"><div class="stat-value">${r.vulnerable_signatures}</div><div class="stat-label">Vulnerable Sigs</div></div>
                <div class="stat-card"><div class="stat-value">${Number(r.exposed_data_records).toLocaleString()}</div><div class="stat-label">Exposed Records</div></div>
                <div class="stat-card purple"><div class="stat-value">$${Number(r.total_migration_cost).toLocaleString()}</div><div class="stat-label">Migration Cost</div></div>
                <div class="stat-card success"><div class="stat-value">${r.agility_score}</div><div class="stat-label">Agility Score</div></div>
                <div class="stat-card"><div class="stat-value">${r.budget_coverage}%</div><div class="stat-label">Budget Coverage</div></div>
                <div class="stat-card warning"><div class="stat-value">${r.expert_review_needed}</div><div class="stat-label">Expert Review Needed</div></div>
            </div>
        `;
    } catch (e) { console.error(e); }
}

// ─── Explainable AI ─────────────────────────────────────────────────────

async function loadExplainable() {
    if (!findingsData.length) {
        const data = await api('/api/findings');
        findingsData = data.findings;
    }

    const div = document.getElementById('explainable-findings');
    if (!div) return;

    const top = findingsData.slice(0, 8);
    div.innerHTML = top.map(f => `
        <div class="finding-card">
            <h4>${f.finding_id} — ${getAssetName(f.asset_id)}
                <span class="badge badge-${(f.risk_band||'').toLowerCase()}" style="margin-left:8px">${f.risk_score?.toFixed(1)}</span>
            </h4>
            <pre>${f.explanation || 'No explanation available.'}</pre>
        </div>
    `).join('');
}

// ─── Report Export ──────────────────────────────────────────────────────

async function exportJSON() {
    try {
        const data = await api('/api/reports/export');
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `quantumshield-report-${Date.now()}.json`);
    } catch (e) { console.error(e); }
}

function exportCSV() {
    if (!assetsData.length) {
        alert('Load data first by visiting the Executive Overview.');
        return;
    }

    const headers = ['asset_id', 'asset_name', 'asset_type', 'algorithm', 'algorithm_role', 'quantum_status',
        'data_classification', 'data_lifetime_years', 'business_criticality', 'migration_status', 'migration_target'];

    const rows = assetsData.map(a => headers.map(h => `"${(a[h] || '').toString().replace(/"/g, '""')}"`).join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `quantumshield-assets-${Date.now()}.csv`);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// ─── Helpers ────────────────────────────────────────────────────────────

function getAssetName(assetId) {
    const asset = assetsData.find(a => a.asset_id === assetId);
    return asset ? asset.asset_name : assetId;
}

function getAssetType(assetId) {
    const asset = assetsData.find(a => a.asset_id === assetId);
    return asset ? asset.asset_type : '-';
}

function getAssetClassification(assetId) {
    const asset = assetsData.find(a => a.asset_id === assetId);
    return asset ? asset.data_classification : '-';
}

function getQuantumBadge(algo) {
    const map = {
        'quantum-broken': '<span class="badge badge-red">Q-Broken</span>',
        'quantum-weakened': '<span class="badge badge-orange">Q-Weakened</span>',
        'classically-broken': '<span class="badge badge-yellow">C-Broken</span>',
        'quantum-resilient': '<span class="badge badge-green">Q-Resilient</span>',
    };

    // Look up from assets data
    const asset = assetsData.find(a => a.algorithm === algo);
    const status = asset ? asset.quantum_status : 'unknown';
    return map[status] || '<span class="badge badge-gray">Unknown</span>';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
}

function destroyChart(id) {
    if (chartsMap[id]) {
        chartsMap[id].destroy();
        delete chartsMap[id];
    }
}

// ─── Initialize ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
});

// Close modals on background click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});
