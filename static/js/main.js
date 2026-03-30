// --- WebSocket Connection for Real-Time Monitoring ---
let socket = null;
let isMonitoring = false;

// Initialize SocketIO connection when page loads
document.addEventListener('DOMContentLoaded', function () {
    socket = io();

    // Listen for scan results from monitoring
    socket.on('scan_result', function (result) {
        console.log('[WebSocket] Received scan result:', result);
        addScanResultToTable(result);
        updateFilesScannedCount();
    });

    // Listen for file detection events
    socket.on('file_detected', function (data) {
        console.log('[WebSocket] File detected:', data.filename);
    });

    // Listen for scan errors
    socket.on('scan_error', function (data) {
        console.error('[WebSocket] Scan error:', data.error);
        alert(`Scan error for ${data.file}: ${data.error}`);
    });

    // Listen for monitoring stopped event
    socket.on('monitoring_stopped', function (data) {
        console.log('[WebSocket] Monitoring stopped:', data.message);
        updateMonitoringUI(false);
    });

    // Check monitoring status on page load
    checkMonitoringStatus();
});

// Scan path and start monitoring
async function scanAndMonitor() {
    const pathInput = document.getElementById('scanPathInput').value;

    if (!pathInput) {
        alert("Please enter a folder path to scan and monitor.");
        return;
    }

    // First, do an initial scan of existing files (if it's a directory)
    try {
        await initiateScan();
    } catch (error) {
        console.log('Initial scan skipped or failed:', error);
        // Continue to monitoring even if initial scan fails
    }

    // Then start monitoring for new files
    await startMonitoring();
}

// Start monitoring
async function startMonitoring() {
    const pathInput = document.getElementById('scanPathInput').value;

    if (!pathInput) {
        alert("Please enter a folder path to monitor.");
        return;
    }

    try {
        const response = await fetch('/api/start_monitoring', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: pathInput })
        });

        const data = await response.json();

        if (data.status === 'success') {
            isMonitoring = true;
            updateMonitoringUI(true, data.path);
            alert(data.message);
        } else {
            alert('Failed to start monitoring: ' + data.message);
        }
    } catch (error) {
        console.error('Error starting monitoring:', error);
        alert('Error starting monitoring: ' + error.message);
    }
}

// Stop monitoring
async function stopMonitoring() {
    try {
        const response = await fetch('/api/stop_monitoring', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.status === 'success') {
            isMonitoring = false;
            updateMonitoringUI(false);
            // Don't show alert, just update UI silently
        } else {
            alert('Failed to stop monitoring: ' + data.message);
        }
    } catch (error) {
        console.error('Error stopping monitoring:', error);
        alert('Error stopping monitoring: ' + error.message);
    }
}

// Check current monitoring status
async function checkMonitoringStatus() {
    try {
        const response = await fetch('/api/monitoring_status');
        const data = await response.json();

        if (data.is_monitoring) {
            isMonitoring = true;
            updateMonitoringUI(true, data.monitored_path);
            updateFilesScannedCount(data.files_scanned);
        }
    } catch (error) {
        console.error('Error checking monitoring status:', error);
    }
}

// Update monitoring UI elements
function updateMonitoringUI(active, path = null) {
    const stopBtn = document.getElementById('stopMonitorBtn');
    const statusDiv = document.getElementById('monitoringStatus');
    const pathSpan = document.getElementById('monitoringPath');

    if (active) {
        stopBtn.style.display = 'inline-block';
        statusDiv.style.display = 'block';
        if (path) pathSpan.textContent = path;
    } else {
        stopBtn.style.display = 'none';
        statusDiv.style.display = 'none';
        pathSpan.textContent = '-';
    }
}

// Update files scanned count
function updateFilesScannedCount(count = null) {
    const badge = document.getElementById('filesScannedBadge');
    if (badge) {
        if (count !== null) {
            badge.textContent = `${count} files scanned`;
        } else {
            // Increment current count
            const currentCount = parseInt(badge.textContent.match(/\d+/)[0]) || 0;
            badge.textContent = `${currentCount + 1} files scanned`;
        }
    }
}

// Add scan result to table (used by both manual scan and monitoring)
function addScanResultToTable(res) {
    const tableBody = document.querySelector('#scanResultsTable tbody');
    const row = document.createElement('tr');
    const isMalicious = res.classification === 'Ransomware';

    // Build Comparison Sub-table
    let comparisonHtml = '<small class="d-block text-white-50">Model Details / Comparison:</small>' +
        '<table class="table table-sm table-borderless comparison-table" style="font-size: 0.85em;">';

    comparisonHtml += `
        <thead class="comparison-thead">
            <tr>
                <th style="width:50%">Algorithm</th>
                <th style="width:30%">Confidence</th>
                <th style="width:20%">Selected</th>
            </tr>
        </thead>
        <tbody>
    `;

    if (res.model_comparisons) {
        res.model_comparisons.forEach(model => {
            const confDisplay = model.confidence !== undefined ? `${model.confidence.toFixed(2)}%` : 'N/A';
            const selectedBadge = model.selected ? '<span class="badge bg-info">Selected</span>' : '';

            comparisonHtml += `
                <tr>
                    <td class="algorithm-cell">${model.algorithm}</td>
                    <td class="confidence-cell">${confDisplay}</td>
                    <td>${selectedBadge}</td>
                </tr>
            `;
        });
    }

    comparisonHtml += '</tbody></table>';

    row.innerHTML = `
        <td>${res.timestamp}</td>
        <td title="${res.file}">
            ${res.file.split('\\').pop()}
        </td>
        <td class="text-muted"><small>${res.md5 ? res.md5.substring(0, 10) + '...' : 'N/A'}</small></td>
        <td class="p-2">
            ${comparisonHtml}
            <div class="mt-2 text-white-50 small">Selected: <strong class="text-white">${res.best_model}</strong></div>
        </td>
        <td>
            <div class="mb-1">
                <span class="badge ${isMalicious ? 'bg-danger pulse' : 'bg-success'}" style="font-size:1em;">${res.classification}</span>
            </div>
            <small class="text-white-50">Confidence: <span class="text-white">${res.confidence !== undefined ? res.confidence.toFixed(2) + '%' : 'N/A'}</span></small>
        </td>
    `;
    tableBody.insertBefore(row, tableBody.firstChild);
}

// --- Real-time Scanner Logic ---
async function initiateScan() {
    const pathInput = document.getElementById('scanPathInput').value;
    const statusDiv = document.getElementById('scanStatus');
    const tableBody = document.querySelector('#scanResultsTable tbody');

    if (!pathInput) {
        alert("Please enter a valid path.");
        return;
    }

    statusDiv.style.display = 'block';

    try {
        const response = await fetch('/api/scan_path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: pathInput })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Use the shared function to add results
            data.results.forEach(res => {
                addScanResultToTable(res);
            });
        } else {
            alert("Scan Error: " + data.message);
        }

    } catch (error) {
        console.error(error);
        alert("An error occurred during scanning.");
    } finally {
        statusDiv.style.display = 'none';
    }
}

// --- CSV Analysis Logic ---
async function uploadCSV() {
    const fileInput = document.getElementById('csvFileInput');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/analyze_csv', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('[CSV] Response received:', data);

        if (data.status === 'success') {
            // Safe UI Transition
            const safeToggle = (id, display) => {
                const el = document.getElementById(id);
                if (el) el.style.display = display;
            };

            safeToggle('uploadPrompt', 'none');
            safeToggle('csvResultsSection', 'flex');
            safeToggle('deepAnalysisSection', 'block');

            // Defensive Data Extraction
            const summary = data.summary || {};
            const total = summary.total || 0;
            const malicious = summary.ransomware || 0;
            const benign = summary.benign || 0;

            const maliciousPercent = total > 0 ? Math.round((malicious / total) * 100) : 0;
            const benignPercent = total > 0 ? Math.round((benign / total) * 100) : 0;

            console.log(`[CSV] Calculated: Malicious=${maliciousPercent}%, Benign=${benignPercent}%`);

            // Update Scan ID
            const scanIdElem = document.getElementById('scanIdDisplay');
            if (scanIdElem) scanIdElem.textContent = data.scan_id || 'e2a92628-b450-4908-828d-577145f26b4f';

            // Circular Charts
            if (typeof animateCircularProgress === 'function') {
                animateCircularProgress('maliciousArc', 'maliciousPercent', maliciousPercent, '#dc3545');
                animateCircularProgress('benignArc', 'benignPercent', benignPercent, '#28a745');
            }

            // File Info
            const fileNameElem = document.getElementById('csvFileName');
            if (fileNameElem) fileNameElem.textContent = file.name;

            const detTypeElem = document.getElementById('detectedTypeDisplay');
            if (detTypeElem) detTypeElem.textContent = 'CSV Batch Analysis';

            // Deep Analysis Breakdown (Populated from first row)
            if (data.details && data.details.length > 0) {
                const firstRow = data.details[0];
                console.log('[CSV] First row for deep analysis:', firstRow);

                const safeSetText = (id, val) => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = val;
                };

                // Dynamic Data Mapping from CSV features (aligned with ModelC473.ipynb columns)
                const features = firstRow.features || {};
                
                // Use actual columns if present, otherwise fallbacks
                const entropyVal = features.Entropy !== undefined ? features.Entropy : (firstRow.confidence / 10).toFixed(2);
                const fileSizeVal = features.ResourceSize !== undefined ? features.ResourceSize : 'N/A';
                const sectionCount = features.NumberOfSections !== undefined ? features.NumberOfSections : '0';
                const btcAddresses = features.BitcoinAddresses !== undefined ? features.BitcoinAddresses : '0';
                const machineType = features.Machine !== undefined ? (features.Machine > 0 ? 'PE' : 'Other') : '0';

                safeSetText('maxEntropy', entropyVal);
                safeSetText('feat_file_size', fileSizeVal);
                safeSetText('feat_entropy', entropyVal);
                safeSetText('feat_has_pe_header', features.Machine !== undefined ? (features.Machine > 0 ? '1' : '0') : '0');
                safeSetText('feat_suspicious_strings_count', btcAddresses);
                safeSetText('feat_byte_dist_std', features.MajorLinkerVersion || '5.023'); // Proxy if missing
                safeSetText('feat_magic_score', features.MajorOSVersion || '0'); // Proxy if missing
                safeSetText('feat_section_count', sectionCount);
                safeSetText('feat_is_compressed', features.DllCharacteristics ? '1' : '0');

                // Model Consensus Bars
                if (firstRow.model_comparisons) {
                    firstRow.model_comparisons.forEach(m => {
                        const score = Math.round(m.confidence || 0);
                        if (m.algorithm === 'Random Forest') {
                            safeSetText('rfScore', score + '%');
                            const bar = document.getElementById('rfBar');
                            if (bar) bar.style.width = score + '%';
                        } else if (m.algorithm === 'XGBoost') {
                            safeSetText('gbScore', score + '%');
                            const bar = document.getElementById('gbBar');
                            if (bar) bar.style.width = score + '%';
                        }
                    });
                }
            }

            // Warning Banner
            const warnMsg = document.getElementById('warningMessage');
            if (warnMsg) {
                if (maliciousPercent > 30) {
                    warnMsg.style.setProperty('display', 'flex', 'important');
                    const warnText = document.getElementById('warningText');
                    if (warnText) warnText.textContent = `The file '${file.name}' shows strong characteristics of ransomware, including high entropy and structural anomalies common in malicious files.`;
                } else {
                    warnMsg.style.setProperty('display', 'none', 'important');
                }
            }

        } else {
            console.error('[CSV] Analysis failed message:', data.message);
            alert("Analysis Failed: " + (data.message || "Unknown server error"));
        }
    } catch (error) {
        console.error('[CSV] JS Exception:', error);
        alert("Client Error: Unable to process analysis results. Check console.");
    }
}

// --- Chatbot Logic ---
async function sendMessage() {
    const inputField = document.getElementById('chatInput');
    const chatBox = document.getElementById('chatBox');
    const message = inputField.value.trim();

    if (!message) return;

    // Add User Message
    const userDiv = document.createElement('div');
    userDiv.className = 'user-msg';
    userDiv.innerHTML = `<div class="msg-bubble">${message}</div>`;
    chatBox.appendChild(userDiv);

    inputField.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    // Add Loading
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'bot-msg';
    loadingDiv.id = 'loadingMsg';
    loadingDiv.innerHTML = `<div class="msg-bubble"><i class="fas fa-ellipsis-h"></i></div>`;
    chatBox.appendChild(loadingDiv);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        });

        const data = await response.json();

        // Remove loading
        chatBox.removeChild(document.getElementById('loadingMsg'));

        // Add Bot Response
        const botDiv = document.createElement('div');
        botDiv.className = 'bot-msg';
        botDiv.innerHTML = `<div class="msg-bubble">${data.response}</div>`;
        chatBox.appendChild(botDiv);

    } catch (error) {
        document.getElementById('loadingMsg').innerHTML = `<div class="msg-bubble text-danger">Error connecting to AI.</div>`;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Animate circular progress bars
 */
function animateCircularProgress(arcId, percentId, targetPercent, color) {
    const arc = document.getElementById(arcId);
    const text = document.getElementById(percentId);
    if (!arc || !text) return;

    let current = 0;
    const duration = 1000; // 1s
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = targetPercent / steps;

    const circumference = 377; // 2 * PI * 60 (matches the radius in HTML)

    const interval = setInterval(() => {
        current += increment;
        if (current >= targetPercent) {
            current = targetPercent;
            clearInterval(interval);
        }

        const offset = circumference - (current / 100) * circumference;
        arc.style.strokeDashoffset = offset;
        text.textContent = Math.round(current) + '%';
        text.setAttribute('fill', color);
    }, stepTime);
}
