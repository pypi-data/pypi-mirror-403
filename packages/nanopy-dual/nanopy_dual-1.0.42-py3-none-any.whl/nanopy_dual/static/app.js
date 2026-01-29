// NanoPy Dual - Frontend JavaScript

// ========== NAVIGATION ==========
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        // Remove active class from all
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

        // Add active to clicked
        item.classList.add('active');
        const sectionId = item.dataset.section;
        document.getElementById(sectionId).classList.add('active');

        // Load section data
        if (sectionId === 'patterns') loadPatterns();
        if (sectionId === 'cracked') loadCracked();
        if (sectionId === 'learn') loadAIStats();
        if (sectionId === 'tracking') loadTargets();
        if (sectionId === 'smart') loadCategories();
        if (sectionId === 'stats') loadStats();
    });
});

// ========== API HELPERS ==========
async function api(endpoint, options = {}) {
    try {
        const resp = await fetch(`/api${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        return await resp.json();
    } catch (err) {
        console.error('API Error:', err);
        return { error: err.message };
    }
}

async function apiPost(endpoint, data) {
    return api(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// ========== STATUS ==========
let statusInterval = null;

async function checkStatus() {
    const data = await api('/status');

    // Hashcat status
    const hcDot = document.getElementById('hashcatDot');
    const hcStatus = document.getElementById('hashcatStatus');
    if (data.hashcat_available) {
        hcDot.className = 'status-dot';
        hcStatus.textContent = 'Hashcat Ready';
    } else {
        hcDot.className = 'status-dot offline';
        hcStatus.textContent = 'Hashcat N/A';
    }

    // Loop status
    const loopDot = document.getElementById('loopDot');
    const loopStatusEl = document.getElementById('loopStatus');
    if (data.loop_running) {
        loopDot.className = 'status-dot running';
        loopStatusEl.textContent = 'Running';
    } else {
        loopDot.className = 'status-dot';
        loopStatusEl.textContent = 'Idle';
    }

    // If loop is running, get detailed status
    if (data.loop_running) {
        updateLoopStatus();
    }
}

async function updateLoopStatus() {
    const data = await api('/loop/status');

    // Update phase
    const phaseEl = document.getElementById('loopPhase');
    phaseEl.textContent = data.phase.toUpperCase();
    phaseEl.className = 'loop-phase ' + data.phase;

    // Update panel
    const panel = document.getElementById('loopPanel');
    if (data.running) {
        panel.classList.add('running');
        panel.classList.remove('cracked');
    } else if (data.result) {
        panel.classList.remove('running');
        panel.classList.add('cracked');
    } else {
        panel.classList.remove('running', 'cracked');
    }

    // Update stats - ALL fields from backend
    document.getElementById('loopCount').textContent = data.loop_count || 0;
    document.getElementById('patternsGen').textContent = data.patterns_generated || 0;
    document.getElementById('patternsLearned').textContent = data.patterns_learned || 0;
    document.getElementById('masksTried').textContent = data.patterns_tried || 0;
    document.getElementById('existingUsed').textContent = data.existing_patterns_used || 0;

    // Current length display with progress
    const lenText = data.current_length ?
        `${data.current_length} (${data.min_length}-${data.max_length})` : '-';
    document.getElementById('currentLen').textContent = lenText;

    // Current masks being tested
    const masksCurrentEl = document.getElementById('masksCurrent');
    if (masksCurrentEl) {
        masksCurrentEl.textContent = data.masks_current || 0;
    }

    // Batch mode info bar - show when running with meaningful data
    const batchInfo = document.getElementById('batchInfo');
    if (batchInfo) {
        if (data.running && (data.batch_count > 0 || data.masks_current > 0 || data.current_category)) {
            let info = [];
            if (data.current_category) info.push(`Category: ${data.current_category}`);
            if (data.batch_count > 0) info.push(`Batch #${data.batch_count}`);
            if (data.masks_current > 0) info.push(`${data.masks_current} masks`);
            if (data.exhaustion_progress > 0) info.push(`${data.exhaustion_progress}% exhausted`);
            if (data.sequential_mode) info.push('SEQ');
            if (data.max_keyspace) info.push(`max ${(data.max_keyspace / 1000000).toFixed(0)}M`);

            batchInfo.textContent = info.join(' | ');
            batchInfo.style.display = 'block';
        } else {
            batchInfo.style.display = 'none';
        }
    }

    // Smart mode status
    const smartModeEl = document.getElementById('smartModeStatus');
    if (smartModeEl && data.smart_mode !== undefined) {
        smartModeEl.textContent = data.smart_mode ? 'ON' : 'OFF';
        smartModeEl.style.color = data.smart_mode ? 'var(--accent-green)' : 'var(--text-dim)';
    }

    // Current category
    const categoryEl = document.getElementById('currentCategory');
    if (categoryEl) {
        if (data.current_category) {
            categoryEl.textContent = data.current_category;
            categoryEl.style.color = 'var(--accent-yellow)';
        } else {
            categoryEl.textContent = data.smart_mode ? 'Auto' : 'Brute';
            categoryEl.style.color = 'var(--text-dim)';
        }
    }

    // Result
    const resultBox = document.getElementById('resultBox');
    if (data.result) {
        resultBox.style.display = 'block';
        document.getElementById('resultPassword').textContent = data.result;
    } else {
        resultBox.style.display = 'none';
    }

    // Update buttons
    document.getElementById('startBtn').disabled = data.running;
    document.getElementById('stopBtn').disabled = !data.running;

    // Update loop status in header
    const loopDot = document.getElementById('loopDot');
    const loopStatusEl = document.getElementById('loopStatus');
    if (data.running) {
        loopDot.className = 'status-dot running';
        loopStatusEl.textContent = data.phase.charAt(0).toUpperCase() + data.phase.slice(1);
    } else if (data.result) {
        loopDot.className = 'status-dot';
        loopStatusEl.textContent = 'Cracked!';
    } else {
        loopDot.className = 'status-dot';
        loopStatusEl.textContent = 'Idle';
    }
}

// ========== LOOP CRACKER ==========
async function startLoop() {
    const hash = document.getElementById('targetHash').value.trim();
    const hashType = document.getElementById('hashType').value;
    const minLen = parseInt(document.getElementById('pwdMinLen').value) || 6;
    const maxLen = parseInt(document.getElementById('pwdMaxLen').value) || 10;
    const smartMode = document.getElementById('smartModeToggle').checked;

    if (!hash) {
        alert('Please enter a target hash');
        return;
    }

    const data = await apiPost('/loop/start', { hash, hash_type: hashType, min_length: minLen, max_length: maxLen, smart_mode: smartMode });

    if (data.already_cracked) {
        alert('Already cracked! Password: ' + data.password);
        document.getElementById('resultBox').style.display = 'block';
        document.getElementById('resultPassword').textContent = data.password;
        return;
    }

    if (data.error) {
        alert('Error: ' + data.error);
        return;
    }

    // Start polling
    if (statusInterval) clearInterval(statusInterval);
    statusInterval = setInterval(updateLoopStatus, 1000);

    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').disabled = false;
}

async function stopLoop() {
    await apiPost('/loop/stop', {});

    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }

    document.getElementById('startBtn').disabled = false;
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('loopPhase').textContent = 'STOPPED';

    updateLoopStatus();
}

async function generateTestHash() {
    const password = document.getElementById('testPassword').value.trim() || 'NVIDIA';
    const hashType = document.getElementById('hashType').value;

    // Use Web Crypto API
    const encoder = new TextEncoder();
    const data = encoder.encode(password);

    let hashBuffer;
    if (hashType === 'sha256') {
        hashBuffer = await crypto.subtle.digest('SHA-256', data);
    } else if (hashType === 'sha1') {
        hashBuffer = await crypto.subtle.digest('SHA-1', data);
    } else if (hashType === 'sha512') {
        hashBuffer = await crypto.subtle.digest('SHA-512', data);
    } else {
        // MD5 not supported in Web Crypto, use SHA256
        hashBuffer = await crypto.subtle.digest('SHA-256', data);
        if (hashType === 'md5') {
            alert('MD5 not supported in browser, using SHA256');
        }
    }

    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    document.getElementById('targetHash').value = hash;
    document.getElementById('testPassword').placeholder = `"${password}" hashed`;
}

// ========== PATTERNS ==========
let patternsPage = 1;
const patternsPerPage = 50;
let allPatterns = [];
let filteredPatterns = [];

async function loadPatterns(page = 1) {
    patternsPage = page;
    const data = await api('/patterns?limit=10000');

    if (!data.patterns || data.patterns.length === 0) {
        document.getElementById('patternsTable').innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No patterns learned yet</td></tr>';
        document.getElementById('patternsPagination').innerHTML = '';
        document.getElementById('filterCount').textContent = '';
        return;
    }

    allPatterns = data.patterns;
    applyFilters();
}

function applyFilters() {
    const lengthFilter = document.getElementById('filterLength').value;
    const charsFilter = document.getElementById('filterChars').value;
    const searchFilter = document.getElementById('filterSearch').value.toUpperCase().trim();

    filteredPatterns = allPatterns.filter(p => {
        // Length filter
        if (lengthFilter && p.length !== parseInt(lengthFilter)) {
            return false;
        }

        // Character type filter
        if (charsFilter) {
            const mask = p.mask || '';
            const pattern = p.pattern || '';

            switch (charsFilter) {
                case 'has_special':
                    if (!mask.includes('?s') && !pattern.includes('S')) return false;
                    break;
                case 'no_special':
                    if (mask.includes('?s') || pattern.includes('S')) return false;
                    break;
                case 'has_upper':
                    if (!mask.includes('?u') && !pattern.includes('U')) return false;
                    break;
                case 'has_lower':
                    if (!mask.includes('?l') && !pattern.includes('L')) return false;
                    break;
                case 'has_digit':
                    if (!mask.includes('?d') && !pattern.includes('D')) return false;
                    break;
                case 'only_lower':
                    if (!/^(\?l)+$/.test(mask) && !/^L+$/.test(pattern)) return false;
                    break;
                case 'only_upper':
                    if (!/^(\?u)+$/.test(mask) && !/^U+$/.test(pattern)) return false;
                    break;
                case 'only_digit':
                    if (!/^(\?d)+$/.test(mask) && !/^D+$/.test(pattern)) return false;
                    break;
            }
        }

        // Search filter
        if (searchFilter && !p.pattern.toUpperCase().includes(searchFilter)) {
            return false;
        }

        return true;
    });

    // Update filter count
    document.getElementById('filterCount').textContent =
        `Showing ${filteredPatterns.length} of ${allPatterns.length} patterns`;

    renderPatterns(1);
}

function clearFilters() {
    document.getElementById('filterLength').value = '';
    document.getElementById('filterChars').value = '';
    document.getElementById('filterSearch').value = '';
    applyFilters();
}

function renderPatterns(page = 1) {
    patternsPage = page;
    const tbody = document.getElementById('patternsTable');

    if (filteredPatterns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No patterns match filters</td></tr>';
        document.getElementById('patternsPagination').innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(filteredPatterns.length / patternsPerPage);
    const start = (page - 1) * patternsPerPage;
    const end = start + patternsPerPage;
    const pagePatterns = filteredPatterns.slice(start, end);

    tbody.innerHTML = pagePatterns.map((p, i) => `
        <tr>
            <td>${start + i + 1}</td>
            <td class="mono">${p.pattern}</td>
            <td class="mono" style="color: var(--accent-green);">${p.mask}</td>
            <td>${p.count}</td>
            <td>${p.length}</td>
            <td><span class="badge badge-blue">${p.status}</span></td>
        </tr>
    `).join('');

    // Pagination
    let paginationHtml = `<div style="display: flex; gap: 8px; align-items: center; margin-top: 16px; flex-wrap: wrap;">
        <span style="color: var(--text-secondary);">Total: ${filteredPatterns.length} patterns</span>
        <span style="color: var(--text-dim);">|</span>`;

    if (page > 1) {
        paginationHtml += `<button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="renderPatterns(1)">« First</button>`;
        paginationHtml += `<button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="renderPatterns(${page - 1})">‹ Prev</button>`;
    }

    paginationHtml += `<span style="color: var(--text-primary); padding: 0 12px;">Page ${page} / ${totalPages}</span>`;

    if (page < totalPages) {
        paginationHtml += `<button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="renderPatterns(${page + 1})">Next ›</button>`;
        paginationHtml += `<button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="renderPatterns(${totalPages})">Last »</button>`;
    }

    paginationHtml += `</div>`;
    document.getElementById('patternsPagination').innerHTML = paginationHtml;
}

// ========== CRACKED ==========
async function loadCracked() {
    const data = await api('/cracked?limit=100');
    const tbody = document.getElementById('crackedTable');

    if (!data.cracked || data.cracked.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-dim);">No passwords cracked yet</td></tr>';
        return;
    }

    tbody.innerHTML = data.cracked.map(c => `
        <tr>
            <td class="mono" style="font-size: 11px;">${c.hash.substring(0, 24)}...</td>
            <td class="mono" style="color: var(--accent-green); font-weight: 600;">${c.password}</td>
            <td>${c.hash_type}</td>
            <td class="mono">${c.pattern || '-'}</td>
            <td>${c.method}</td>
        </tr>
    `).join('');
}

// ========== LEARN AI ==========
async function loadAIStats() {
    const data = await api('/ai/stats');

    document.getElementById('aiLearned').textContent = data.total_learned || 0;
    document.getElementById('aiPatterns').textContent = data.unique_patterns || 0;
    document.getElementById('aiGeneration').textContent = data.generation || 0;
}

async function learnPasswords() {
    const text = document.getElementById('learnPasswords').value.trim();
    if (!text) {
        alert('Enter some passwords to learn from');
        return;
    }

    const passwords = text.split('\n').map(p => p.trim()).filter(p => p);
    const data = await apiPost('/learn', { passwords });

    if (data.error) {
        alert('Error: ' + data.error);
        return;
    }

    alert(`Learned from ${data.learned} passwords. Total patterns: ${data.total_patterns}`);
    document.getElementById('learnPasswords').value = '';
    loadAIStats();
}

async function generatePasswords() {
    const count = parseInt(document.getElementById('genCount').value) || 10;
    const length = parseInt(document.getElementById('genLength').value) || 8;
    const method = document.getElementById('genMethod').value;

    const data = await apiPost('/generate', { count, length, method });

    if (!data.passwords) {
        document.getElementById('generatedList').innerHTML = '<p style="color: var(--accent-red);">Error generating</p>';
        return;
    }

    const html = data.passwords.map(p => `
        <div style="padding: 4px 0; font-family: monospace;">${p}</div>
    `).join('');

    document.getElementById('generatedList').innerHTML = `
        <div style="background: var(--bg-tertiary); padding: 12px; border-radius: 6px; max-height: 300px; overflow-y: auto;">
            ${html}
        </div>
    `;
}

// ========== TRAIN PATTERNS ==========
async function trainPatterns() {
    const minLen = parseInt(document.getElementById('pwdMinLen').value) || 4;
    const maxLen = parseInt(document.getElementById('pwdMaxLen').value) || 8;

    const trainBtn = document.getElementById('trainBtn');
    const trainResult = document.getElementById('trainResult');
    const loopPhase = document.getElementById('loopPhase');
    const loopPanel = document.getElementById('loopPanel');

    trainBtn.disabled = true;
    trainResult.style.display = 'block';
    trainResult.innerHTML = '<span style="color: var(--accent-yellow);">Training... generating ALL patterns for lengths ' + minLen + '-' + maxLen + '...</span>';

    // Update loop panel to show TRAINING
    loopPhase.textContent = 'TRAINING';
    loopPhase.className = 'loop-phase learning';
    loopPanel.classList.add('running');
    document.getElementById('currentLen').textContent = minLen + '-' + maxLen;

    try {
        const data = await apiPost('/train', { min_length: minLen, max_length: maxLen });

        if (data.ok) {
            // Build details by length
            let details = Object.entries(data.by_length)
                .map(([len, count]) => `L${len}: ${count}`)
                .join(', ');

            trainResult.innerHTML = `
                <div style="color: var(--accent-green);">
                    Generated <strong>${data.total_patterns}</strong> patterns
                </div>
                <div style="color: var(--text-secondary); margin-top: 4px; font-size: 12px;">
                    ${details}
                </div>
                <div style="color: var(--text-dim); margin-top: 4px; font-size: 12px;">
                    Total in DB: ${data.total_in_db} patterns
                </div>
            `;

            // Update stats
            document.getElementById('patternsLearned').textContent = data.total_in_db;
        } else {
            trainResult.innerHTML = '<span style="color: var(--accent-red);">Error: ' + (data.error || 'Unknown error') + '</span>';
        }
    } catch (err) {
        trainResult.innerHTML = '<span style="color: var(--accent-red);">Error: ' + err.message + '</span>';
    }

    // Reset panel
    loopPhase.textContent = 'IDLE';
    loopPhase.className = 'loop-phase';
    loopPanel.classList.remove('running');
    trainBtn.disabled = false;
}

// ========== TARGET TRACKING ==========
async function loadTargets() {
    const data = await api('/targets');
    const tbody = document.getElementById('targetsTable');
    const select = document.getElementById('trackTargetSelect');

    if (!data.targets || data.targets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-dim);">No targets tracked yet</td></tr>';
        select.innerHTML = '<option value="">No targets yet...</option>';
        return;
    }

    // Update table
    tbody.innerHTML = data.targets.map(t => `
        <tr>
            <td class="mono">${t.target_id}</td>
            <td>${t.name || '-'}</td>
            <td><span class="badge badge-blue">${t.crack_count}</span></td>
            <td style="font-size: 12px;">${t.last_seen || '-'}</td>
            <td>
                <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="viewTargetDetails('${t.target_id}')">
                    View
                </button>
            </td>
        </tr>
    `).join('');

    // Update select dropdown
    select.innerHTML = '<option value="">Select target...</option>' +
        data.targets.map(t => `<option value="${t.target_id}">${t.name || t.target_id}</option>`).join('');
}

async function addTarget() {
    const targetId = document.getElementById('targetIdInput').value.trim();
    const name = document.getElementById('targetNameInput').value.trim();

    if (!targetId) {
        alert('Please enter a Target ID');
        return;
    }

    await apiPost('/targets', { target_id: targetId, name: name });
    document.getElementById('targetIdInput').value = '';
    document.getElementById('targetNameInput').value = '';
    loadTargets();
}

async function trackPassword() {
    const targetId = document.getElementById('trackTargetSelect').value;
    const hash = document.getElementById('trackHashInput').value.trim();
    const password = document.getElementById('trackPasswordInput').value.trim();
    const resultDiv = document.getElementById('trackResult');

    if (!targetId || !hash || !password) {
        alert('Please fill all fields');
        return;
    }

    const data = await apiPost(`/targets/${encodeURIComponent(targetId)}/track`, { hash, password });

    if (data.ok) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div style="color: var(--accent-green);">✓ Tracked successfully</div>
            <div style="margin-top: 8px;">
                <strong>Pattern:</strong> <span class="mono">${data.pattern}</span>
            </div>
            ${data.prediction.predictions && data.prediction.predictions.length > 0 ? `
                <div style="margin-top: 8px;">
                    <strong>Next predicted patterns:</strong>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                        ${data.prediction.predictions.slice(0, 5).map(p => `
                            <span class="badge badge-green" title="${p.reason}">${p.pattern}</span>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;

        // Clear inputs
        document.getElementById('trackHashInput').value = '';
        document.getElementById('trackPasswordInput').value = '';

        // Refresh targets
        loadTargets();

        // Show details
        viewTargetDetails(targetId);
    } else {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<span style="color: var(--accent-red);">Error: ${data.error}</span>`;
    }
}

async function viewTargetDetails(targetId) {
    const detailsCard = document.getElementById('targetDetailsCard');
    detailsCard.style.display = 'block';
    document.getElementById('targetDetailsId').textContent = targetId;

    // Get history and predictions
    const [historyData, predictData] = await Promise.all([
        api(`/targets/${encodeURIComponent(targetId)}/history`),
        api(`/targets/${encodeURIComponent(targetId)}/predict`)
    ]);

    // Render predictions
    const predictionsBox = document.getElementById('predictionsBox');
    if (predictData.predictions && predictData.predictions.length > 0) {
        predictionsBox.innerHTML = predictData.predictions.map(p => `
            <div style="background: var(--bg-tertiary); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--accent-green);">
                <div class="mono" style="font-size: 14px; color: var(--accent-green);">${p.pattern}</div>
                <div style="font-size: 11px; color: var(--text-dim);">${p.reason}</div>
            </div>
        `).join('');
    } else {
        predictionsBox.innerHTML = '<span style="color: var(--text-dim);">No predictions yet. Track more passwords!</span>';
    }

    // Render history timeline
    const timeline = document.getElementById('historyTimeline');
    if (historyData.history && historyData.history.length > 0) {
        timeline.innerHTML = historyData.history.map((h, i) => `
            <div style="display: flex; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--bg-tertiary);">
                <div style="width: 30px; text-align: center; color: var(--text-dim);">#${i + 1}</div>
                <div style="flex: 1;">
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <span class="mono" style="color: var(--accent-yellow); font-size: 14px;">${h.password}</span>
                        <span style="color: var(--text-dim);">→</span>
                        <span class="mono" style="color: var(--accent-blue);">${h.pattern}</span>
                    </div>
                    <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">
                        Length: ${h.length} |
                        ${h.has_upper ? '✓Upper ' : ''}
                        ${h.has_lower ? '✓Lower ' : ''}
                        ${h.has_digit ? '✓Digit ' : ''}
                        ${h.has_special ? '✓Special ' : ''}
                        | ${h.cracked_at}
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        timeline.innerHTML = '<div style="color: var(--text-dim);">No history yet</div>';
    }
}

// ========== STATS ==========
async function loadStats() {
    const data = await api('/stats');

    if (data.storage) {
        document.getElementById('statPatterns').textContent = data.storage.patterns || 0;
        document.getElementById('statCracked').textContent = data.storage.cracked || 0;
        document.getElementById('statLearned').textContent = data.storage.total_learned || 0;
        document.getElementById('statLeveldb').textContent = data.storage.leveldb ? '✓' : '✗';
    }

    // Hashcat info
    const hcData = await api('/hashcat/status');
    document.getElementById('hcAvailable').textContent = hcData.available ? 'Yes' : 'No';
    document.getElementById('hcVersion').textContent = hcData.version || 'N/A';
}

// ========== SMART MODE / CATEGORIES ==========
async function loadCategories() {
    const minLen = parseInt(document.getElementById('smartMinLen').value) || 6;
    const maxLen = parseInt(document.getElementById('smartMaxLen').value) || 10;
    const data = await api(`/categories?length=${maxLen}`);

    if (!data.categories) {
        document.getElementById('categoriesContainer').innerHTML =
            '<p style="color: var(--accent-red);">Error loading categories</p>';
        return;
    }

    // Update stats
    document.getElementById('totalCategories').textContent = data.total_categories || 0;
    document.getElementById('sampleLength').textContent = `${minLen}-${maxLen}`;

    // Calculate total masks
    let totalMasks = 0;
    data.categories.forEach(c => totalMasks += c.mask_count || 0);
    document.getElementById('totalPriorityMasks').textContent = totalMasks;

    // Render categories
    const container = document.getElementById('categoriesContainer');
    container.innerHTML = data.categories.map(cat => `
        <div style="display: flex; align-items: center; gap: 16px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 8px; cursor: pointer;"
             onclick="loadCategoryMasks('${cat.name}')">
            <div style="background: ${getColorForPriority(cat.priority)}; color: #000; padding: 4px 10px; border-radius: 4px; font-weight: bold; min-width: 30px; text-align: center;">
                ${cat.priority}
            </div>
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="color: var(--accent-yellow); font-weight: 600;">${cat.name}</span>
                    <span style="color: var(--accent-green); font-size: 12px;">${cat.frequency}%</span>
                </div>
                <div style="color: var(--text-dim); font-size: 12px; margin-top: 4px;">${cat.description}</div>
            </div>
            <div style="text-align: right;">
                <div style="color: var(--accent-blue); font-size: 18px; font-weight: bold;">${cat.mask_count}</div>
                <div style="color: var(--text-dim); font-size: 11px;">masks</div>
            </div>
            <div style="color: var(--text-dim);">→</div>
        </div>
    `).join('');
}

function getColorForPriority(priority) {
    const colors = {
        1: 'var(--accent-green)',
        2: 'var(--accent-blue)',
        3: 'var(--accent-purple)',
        4: 'var(--accent-yellow)',
        5: 'var(--text-secondary)',
        6: 'var(--text-dim)',
        7: 'var(--text-dim)'
    };
    return colors[priority] || 'var(--text-dim)';
}

async function loadCategoryMasks(categoryName) {
    const maxLen = parseInt(document.getElementById('smartMaxLen').value) || 10;
    const data = await api(`/categories/${categoryName}/masks?length=${maxLen}`);

    if (data.error) {
        alert('Error: ' + data.error);
        return;
    }

    // Show the card
    const card = document.getElementById('categoryMasksCard');
    card.style.display = 'block';

    document.getElementById('selectedCategoryName').textContent = categoryName;
    document.getElementById('categoryMaskCount').textContent = `${data.count} masks for length ${maxLen}`;
    document.getElementById('categoryDescription').textContent = data.description;

    // Render masks
    const list = document.getElementById('categoryMasksList');
    if (data.masks && data.masks.length > 0) {
        list.innerHTML = data.masks.map(mask => `
            <span class="mono" style="background: var(--bg-secondary); padding: 6px 10px; border-radius: 4px; color: var(--accent-green); font-size: 12px;">
                ${mask}
            </span>
        `).join('');
    } else {
        list.innerHTML = '<span style="color: var(--text-dim);">No masks for this length</span>';
    }

    // Scroll to card
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function generateAllPatterns() {
    const minLen = parseInt(document.getElementById('smartMinLen').value) || 6;
    const maxLen = parseInt(document.getElementById('smartMaxLen').value) || 10;

    // Use the train endpoint with the range
    const data = await apiPost('/train', { min_length: minLen, max_length: maxLen });

    if (data.ok) {
        alert(`Generated ${data.total_patterns} patterns for lengths ${minLen}-${maxLen}.\nTotal in DB: ${data.total_in_db}`);
        loadCategories();
    } else {
        alert('Error: ' + (data.error || 'Unknown error'));
    }
}

// ========== CATEGORY SELECTION ==========
async function loadCategoryCheckboxes() {
    const data = await api('/categories');
    if (!data.categories) return;

    const container = document.getElementById('categoryCheckboxes');
    container.innerHTML = data.categories.map(cat => `
        <label style="display: flex; align-items: center; gap: 12px; padding: 10px; background: var(--bg-tertiary); border-radius: 8px; margin-bottom: 6px; cursor: pointer;">
            <input type="checkbox" id="cat_${cat.name}" value="${cat.name}" ${cat.enabled ? 'checked' : ''}
                   style="width: 18px; height: 18px; accent-color: var(--accent-green);">
            <div style="background: ${getColorForPriority(cat.priority)}; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; min-width: 24px; text-align: center;">
                ${cat.priority}
            </div>
            <div style="flex: 1;">
                <span style="color: var(--accent-yellow); font-weight: 600;">${cat.name}</span>
                <span style="color: var(--accent-green); font-size: 11px; margin-left: 8px;">${cat.frequency}%</span>
            </div>
            <span style="color: var(--text-dim); font-size: 12px;">${cat.description}</span>
        </label>
    `).join('');
}

function selectAllCategories() {
    document.querySelectorAll('#categoryCheckboxes input[type="checkbox"]').forEach(cb => cb.checked = true);
}

function selectNoneCategories() {
    document.querySelectorAll('#categoryCheckboxes input[type="checkbox"]').forEach(cb => cb.checked = false);
}

async function saveCategorySelection() {
    const enabled = [];
    document.querySelectorAll('#categoryCheckboxes input[type="checkbox"]:checked').forEach(cb => {
        enabled.push(cb.value);
    });

    const data = await apiPost('/categories', { enabled });
    if (data.ok) {
        alert(`Saved! Enabled categories: ${data.enabled.length > 0 ? data.enabled.join(', ') : 'ALL'}`);
    } else {
        alert('Error saving categories');
    }
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', async () => {
    checkStatus();
    setInterval(checkStatus, 5000);

    // Check if loop is already running and start polling if so
    const data = await api('/loop/status');
    if (data.running) {
        console.log('[UI] Loop already running, starting status polling');
        if (statusInterval) clearInterval(statusInterval);
        statusInterval = setInterval(updateLoopStatus, 1000);
    }
    updateLoopStatus();

    // Load category checkboxes for Smart Mode page
    loadCategoryCheckboxes();
});
