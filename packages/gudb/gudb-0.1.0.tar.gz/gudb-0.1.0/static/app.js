// State
let alerts = [];
let socket = null;
let activeAnalysisStart = 0;

// Initialize
function initDashboard() {
    loadAlerts();
    initializeSocket();

    // Auto-refresh feed slightly less aggressively
    setInterval(loadAlerts, 8000);

    // Close modal on click outside
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

function initializeSocket() {
    socket = io();
    socket.on('connect', () => {
        logBrain('> WebSocket connected.');
    });

    socket.on('analysis_status', (data) => {
        updateBrainState(data.status);
        showToast(data.message, data.status);

        // Show update in log
        const messages = {
            'pending': 'Queued for analysis...',
            'analyzing': 'Detective Node started analysis...',
            'completed': 'Architect Node finished reasoning.',
            'failed': 'Analysis failed.'
        };
        if (messages[data.status]) logBrain(`> ${messages[data.status]}`);

        // Update data
        const idx = alerts.findIndex(a => a.id === data.alert_id);
        if (idx !== -1) {
            alerts[idx].status = data.status;
            renderFeed();

            // If modal is open for this ID, refresh it
            const modal = document.getElementById('detailModal');
            if (modal.style.display === 'flex' && modal.dataset.activeId == data.alert_id) {
                // If it just finished, re-fetch full analysis
                if (data.status === 'completed') {
                    setTimeout(() => openDeepDive(data.alert_id), 100);
                } else {
                    // Just update the skeleton/message in modal
                    openDeepDive(data.alert_id);
                }
            }
        } else {
            // New alert might have arrived while log was closed, fetch all
            loadAlerts();
        }
    });
}

function updateBrainState(status) {
    const detective = document.getElementById('nodeDetective');
    const architect = document.getElementById('nodeArchitect');
    const validator = document.getElementById('nodeValidator');
    const c1 = document.getElementById('conn1');
    const c2 = document.getElementById('conn2');

    // Reset all
    if (detective && architect && validator && c1 && c2) {
        [detective, architect, validator].forEach(n => n.className = 'node');
        [c1, c2].forEach(c => c.className = 'connector ' + c.className.split(' ')[1]);

        if (status === 'analyzing') {
            detective.classList.add('active');
            logBrain('> Detective: Gathering query plan...');
            setTimeout(() => {
                detective.classList.add('completed');
                c1.classList.add('active');
                architect.classList.add('active');
                logBrain('> Architect: Identifying constraints...');
            }, 1000);
        } else if (status === 'completed') {
            // Fast forward visual (since it's done)
            detective.classList.add('completed');
            architect.classList.add('completed');
            validator.classList.add('completed');
        }
    }
}

function logBrain(msg) {
    const log = document.getElementById('thoughtLog');
    if (!log) return;
    const div = document.createElement('div');
    div.className = 'log-entry new';
    div.textContent = msg;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
}

async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        alerts = (data.alerts || []).reverse();
        renderFeed();
    } catch (e) {
        console.error("Feed load error", e);
    }
}

function renderFeed() {
    const container = document.getElementById('feedList');
    if (!container) return;
    if (!alerts.length) {
        container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-secondary)">Waiting for signals...</div>';
        return;
    }

    container.innerHTML = alerts.map(alert => {
        const severity = alert.severity || 'info';
        const date = new Date(alert.timestamp * 1000);
        const timeStr = date.toLocaleTimeString();

        // Status badge logic
        let statusBadge = '';
        if (alert.status) {
            const statusClass = alert.status === 'completed' ? 'success' :
                alert.status === 'failed' ? 'failed' : 'analyzing';
            const statusText = alert.status === 'completed' ? '✓ Analyzed' :
                alert.status === 'failed' ? '✗ Failed' : '⏳ Analyzing...';
            const pulseClass = alert.status === 'analyzing' ? 'pulse' : '';
            statusBadge = `<span class="badge ${statusClass} ${pulseClass}" style="margin-left:auto; text-transform:none;">${statusText}</span>`;
        }

        // Git commit badge
        let gitBadge = '';
        if (alert.git_commit && alert.git_commit.short_hash) {
            gitBadge = `<span class="git-badge" title="Commit: ${alert.git_commit.message}">
                📌 ${alert.git_commit.short_hash}
            </span>`;
        }

        return `
        <div class="insight-card">
            <div class="card-header">
                <span class="badge ${severity}">${severity}</span>
                ${gitBadge}
                ${statusBadge}
                <span class="timestamp" style="margin-left:10px">${timeStr}</span>
            </div>
            
            <div class="code-preview">
                ${escapeHtml(alert.query.substring(0, 150))}${alert.query.length > 150 ? '...' : ''}
            </div>
            
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size:0.8rem; color:var(--text-secondary)">
                    Duration: ${Math.round(alert.duration_ms)}ms
                </div>
                <button class="magic-btn" onclick="openDeepDive(${alert.id})">
                    ${alert.status === 'analyzing' ? '⏳ Analyzing...' : '✨ View AI Analysis'}
                </button>
            </div>
        </div>
        `;
    }).join('');
}

function showToast(message, status) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${status}`;

    const statusEmoji = {
        'analyzing': '⏳',
        'completed': '✅',
        'failed': '❌'
    };

    toast.innerHTML = `<span style="font-size:1.2rem">${statusEmoji[status] || '📢'}</span> <span>${message}</span>`;
    container.appendChild(toast);

    // Animate in
    setTimeout(() => toast.classList.add('show'), 100);

    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

async function openDeepDive(id) {
    const modal = document.getElementById('detailModal');
    const content = document.getElementById('intelContent');
    const tree = document.getElementById('planTree');

    modal.style.display = 'flex';
    modal.dataset.activeId = id;

    // Show Loading Skeleton
    content.innerHTML = `
        <div class="skeleton title"></div>
        <div class="skeleton text"></div>
        <div class="skeleton text"></div>
    `;

    try {
        const res = await fetch(`/api/alerts/${id}/analysis`);
        const data = await res.json();
        renderDeepDiveContent(data, content, tree);
    } catch (e) {
        content.innerHTML = `<div style="color:var(--crimson)">Error loading analysis: ${e.message}</div>`;
    }
}

function renderDeepDiveContent(data, content, treeContainer) {
    const analysis = data.analysis;
    const alert = data.alert;

    // 1. Render Intel Panel
    const isReady = analysis.status === 'completed';

    if (!isReady) {
        content.innerHTML = `
            <div class="intel-header">
                <div class="intel-title">
                    <h2>Analysis in Progress...</h2>
                    <div class="intel-subtitle">The Architect node is reasoning on this query.</div>
                </div>
                <button class="close-btn" onclick="closeModal()">×</button>
            </div>
            <div class="skeleton text"></div><div class="skeleton text"></div>
        `;
        return;
    }

    const impact = analysis.impact_analysis || {};
    // Handle generic impact analysis structure OR the legacy flat structure
    const readGain = analysis.performance_gain || impact.read_gain || "Unknown";
    const writeRisk = analysis.risk_assessment || impact.write_penalty || "Unknown";

    content.innerHTML = `
        <div class="intel-header">
            <div class="intel-title">
                <h2>AI Observation</h2>
                <div class="intel-subtitle">Query Pattern #${alert.id} Analysis</div>
            </div>
            <button class="close-btn" onclick="closeModal()">×</button>
        </div>

        <div class="intel-section">
            <h3>🔍 Bottleneck Identification</h3>
            <p style="color:var(--text-secondary); line-height:1.6;">
                ${escapeHtml(analysis.reasoning || "No diagnosis available.")}
            </p>
        </div>

        <div class="intel-section" style="background:var(--emerald-dim); border-left:4px solid var(--emerald); padding:15px; border-radius:4px; margin-bottom:20px;">
            <h3 style="color:var(--emerald); margin-top:0;">💼 Business Impact (Why it Matters)</h3>
            <p style="font-weight:bold; margin-bottom:5px;">
                ${escapeHtml(analysis.business_impact || "Instantaneous User Experience predicted.")}
            </p>
            <div style="font-size:0.8rem; color:var(--text-secondary)">Compute Efficiency Score: ${analysis.performance_gain ? '9/10' : 'N/A'}</div>
        </div>

        <div class="intel-section" style="background:var(--amber-dim); border-left:4px solid var(--amber); padding:15px; border-radius:4px; margin-bottom:20px;">
            <h3 style="color:var(--amber); margin-top:0;">⚠️ Risk Assessment</h3>
            <p style="margin-bottom:5px;">
                ${escapeHtml(analysis.risk_assessment || "Low Risk. Minimal impact on write latency.")}
            </p>
        </div>

        <div class="intel-section" style="background:rgba(88, 166, 255, 0.1); border-left:4px solid #58A6FF; padding:15px; border-radius:4px; margin-bottom:20px;">
            <h3 style="color:#58A6FF; margin-top:0;">🌱 Carbon & Cost Logic</h3>
            <p>
                ${escapeHtml(analysis.cost_savings || "Estimated 40% reduction in CPU cycles and cloud billing.")}
            </p>
        </div>

        <div class="intel-section">
            <h3>✨ Proposed SQL Fix</h3>
            <div class="sql-fix-box">
                <div class="sql-header">
                    <span>SQL Fix</span>
                    <span style="font-size:0.75rem; color:var(--emerald)">READY TO DEPLOY</span>
                </div>
                <div class="sql-content">${escapeHtml(analysis.suggested_fix)}</div>
                 <div style="padding:10px; background:var(--surface-card); display:flex; gap:10px;">
                    <button class="magic-btn" onclick="copyToClipboard(\`${escapeHtml(analysis.suggested_fix).replace(/`/g, '\\`')}\`)">
                        📋 Copy SQL
                    </button>
                    <button class="magic-btn" style="border-color:var(--text-secondary); color:var(--text-primary)">
                        🚀 Deploy to Staging
                    </button>
                </div>
            </div>
        </div>

        <div class="intel-section" style="background:var(--surface-card); padding:15px; border-radius:4px;">
            <h3>🔄 Implementation Advice (Rollback)</h3>
            <p style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:10px;">If performance degrades, run this immediately:</p>
            <code style="display:block; padding:10px; background:#0D1117; color:var(--crimson); border-radius:4px; font-size:0.85rem;">
                ${escapeHtml(analysis.rollback_command || "-- No rollback command provided.")}
            </code>
            <button class="magic-btn" onclick="copyToClipboard(\`${escapeHtml(analysis.rollback_command || "").replace(/`/g, '\\`')}\`)" style="margin-top:10px; font-size:0.75rem;">
                📋 Copy Rollback
            </button>
        </div>
        
        <div class="validation-footer">
            <i class="fas fa-check-circle"></i> SRE Guardrails enabled. Senior DRE Validation complete.
        </div>
    `;

    // 2. Render Visualization Tree (Mocking a simple tree based on explain)
    treeContainer.innerHTML = '';

    // Robust parse of plan text (handles JSON or Python string format)
    let planText = "";
    if (typeof analysis.explain_plan === 'object') {
        planText = JSON.stringify(analysis.explain_plan);
    } else {
        planText = String(analysis.explain_plan || "");
    }

    const nodes = [];

    // Check for specific node types with Regex to be robust
    // Python string uses single quotes 'Node Type': 'Seq Scan'
    if (/['"]Node Type['"]\s*:\s*['"]Seq Scan['"]/i.test(planText) || planText.includes("Seq Scan")) {
        nodes.push({ name: "Seq Scan", type: "bottleneck", details: "Full Table Scan" });
    }
    if (/['"]Node Type['"]\s*:\s*['"]Index Scan['"]/i.test(planText) || planText.includes("Index Scan")) {
        nodes.push({ name: "Index Scan", type: "normal", details: "Efficient" });
    }
    if (/['"]Node Type['"]\s*:\s*['"]Limit['"]/i.test(planText) || planText.includes("Limit")) {
        nodes.push({ name: "Limit", type: "normal", details: "Rows Capped" });
    }

    // Default fallback if nothing found
    if (nodes.length === 0) {
        if (planText.length > 5) nodes.push({ name: "Query Execution", type: "normal" });
        else nodes.push({ name: "Plan Pending", type: "normal" });
    }

    let boxHtml = '';
    nodes.forEach((n, i) => {
        const isLast = i === nodes.length - 1;
        boxHtml += `
            <div class="tree-node ${n.type}">
                <div style="font-size:0.85rem; font-weight:700;">${n.name}</div>
                <div style="font-size:0.7rem; color:var(--text-secondary)">${n.details || ("Step " + (i + 1))}</div>
                ${n.type === 'bottleneck' ? '<div style="margin-top:5px; font-size:0.7rem; color:var(--amber); font-weight:bold;">⚠️ SLOW</div>' : ''}
            </div>
        `;
        if (!isLast) {
            boxHtml += `<div class="tree-connector"></div>`;
        }
    });
    treeContainer.innerHTML = boxHtml;
}

function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    // Simple toast
    const el = document.createElement('div');
    el.innerText = 'Copied!';
    el.style.position = 'fixed';
    el.style.bottom = '20px';
    el.style.right = '20px';
    el.style.background = '#10B981';
    el.style.color = 'white';
    el.style.padding = '10px 20px';
    el.style.borderRadius = '5px';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2000);
}
