// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!checkAuth()) {
        window.location.href = '/login';
        return;
    }

    // Load current pipeline status
    loadPipelineStatus();
});

// Load pipeline status
async function loadPipelineStatus() {
    try {
        const response = await fetch('/api/kdd/status');
        const data = await response.json();

        if (data.success) {
            updatePipelineUI(data.status);
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

// Update pipeline UI based on status
function updatePipelineUI(status) {
    const steps = ['selection', 'preprocessing', 'transforming', 'datamining'];

    steps.forEach((step, index) => {
        const stepEl = document.getElementById(`step-${step}`);
        const statusEl = document.getElementById(`status-${step}`);
        const btnEl = document.getElementById(`btn-${step}`);

        // Update status badge
        statusEl.className = `status-badge ${status[step]}`;
        statusEl.textContent = getStatusText(status[step]);

        // Update step styling
        stepEl.classList.remove('active', 'completed');
        if (status[step] === 'completed') {
            stepEl.classList.add('completed');
        }

        // Enable/disable buttons based on previous step
        if (index === 0) {
            btnEl.disabled = status[step] === 'running';
        } else {
            const prevStep = steps[index - 1];
            btnEl.disabled = status[prevStep] !== 'completed' || status[step] === 'running';
        }
    });
}

// Get human-readable status text
function getStatusText(status) {
    const texts = {
        'pending': 'Menunggu',
        'running': 'Berjalan...',
        'completed': 'Selesai',
        'error': 'Error'
    };
    return texts[status] || status;
}

// Run Selection
async function runSelection() {
    await runStep('selection', '/api/kdd/selection');
}

// Run Preprocessing
async function runPreprocessing() {
    await runStep('preprocessing', '/api/kdd/preprocessing');
}

// Run Transforming
async function runTransforming() {
    await runStep('transforming', '/api/kdd/transforming');
}

// Run Data Mining
async function runDataMining() {
    const numTopics = parseInt(document.getElementById('num-topics').value) || 5;
    await runStep('datamining', '/api/kdd/datamining', { num_topics: numTopics });
}

// Generic step runner
async function runStep(stepName, endpoint, body = {}) {
    const btn = document.getElementById(`btn-${stepName}`);
    const statusEl = document.getElementById(`status-${stepName}`);
    const outputEl = document.getElementById(`output-${stepName}`);
    const stepEl = document.getElementById(`step-${stepName}`);
    const alertContainer = document.getElementById('alert-container');

    // Update UI to running state
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner"></div> <span>Processing...</span>';
    statusEl.className = 'status-badge running';
    statusEl.textContent = 'Berjalan...';
    stepEl.classList.add('active');
    outputEl.classList.remove('hidden');
    outputEl.innerHTML = '<p class="animate-pulse">Memproses data...</p>';
    alertContainer.innerHTML = '';

    try {
        const response = await apiRequest(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });

        if (response.success) {
            // Update to completed
            statusEl.className = 'status-badge completed';
            statusEl.textContent = 'Selesai';
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');

            // Show output
            outputEl.innerHTML = formatOutput(response.data);

            // Enable next button
            enableNextButton(stepName);

            alertContainer.innerHTML = `
                <div class="alert alert-success">
                    ✓ ${response.message}
                </div>
            `;
        } else {
            throw new Error(response.message);
        }
    } catch (error) {
        statusEl.className = 'status-badge error';
        statusEl.textContent = 'Error';
        stepEl.classList.remove('active');
        outputEl.innerHTML = `<p style="color: var(--error);">Error: ${error.message}</p>`;

        alertContainer.innerHTML = `
            <div class="alert alert-error">
                ✕ ${error.message}
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = getButtonContent(stepName);
    }
}

// Get button content based on step
function getButtonContent(stepName) {
    const contents = {
        'selection': '<span>📁 Jalankan Selection</span>',
        'preprocessing': '<span>🔧 Jalankan Preprocessing</span>',
        'transforming': '<span>🔄 Jalankan Transforming</span>',
        'datamining': '<span>⚙️ Jalankan Data Mining</span>'
    };
    return contents[stepName];
}

// Enable next button after completion
function enableNextButton(stepName) {
    const nextSteps = {
        'selection': 'preprocessing',
        'preprocessing': 'transforming',
        'transforming': 'datamining'
    };

    const nextStep = nextSteps[stepName];
    if (nextStep) {
        document.getElementById(`btn-${nextStep}`).disabled = false;
    }
}

// Format output data for display
function formatOutput(data) {
    if (!data) return '<p>No data</p>';

    let html = '<div>';

    if (data.total_documents !== undefined) {
        html += `<p>📄 Total dokumen: <strong>${data.total_documents}</strong></p>`;
    }

    if (data.dictionary_size !== undefined) {
        html += `<p>📚 Ukuran dictionary: <strong>${data.dictionary_size}</strong></p>`;
    }

    if (data.corpus_size !== undefined) {
        html += `<p>📦 Ukuran corpus: <strong>${data.corpus_size}</strong></p>`;
    }

    if (data.coherence_score !== undefined) {
        html += `<p>📊 Coherence score: <strong>${data.coherence_score}</strong></p>`;
    }

    if (data.num_topics !== undefined) {
        html += `<p>🏷️ Jumlah topik: <strong>${data.num_topics}</strong></p>`;
    }

    if (data.sample) {
        html += '<p style="margin-top: var(--space-2);">📋 Sample data:</p>';
        html += '<pre style="font-size: 0.8rem; overflow-x: auto;">' +
            JSON.stringify(data.sample, null, 2) + '</pre>';
    }

    if (data.topics) {
        html += '<p style="margin-top: var(--space-2);">🏷️ Topik ditemukan:</p>';
        data.topics.forEach(topic => {
            const words = topic.words.slice(0, 5).map(w => w.word).join(', ');
            html += `<p style="margin-left: var(--space-4);">• <strong>${topic.topic_name}:</strong> ${words}</p>`;
        });
    }

    html += '</div>';
    return html;
}

// Reset Pipeline
async function resetPipeline() {
    if (!confirm('Apakah Anda yakin ingin mereset seluruh pipeline?')) {
        return;
    }

    const alertContainer = document.getElementById('alert-container');

    try {
        const response = await apiRequest('/api/kdd/reset', {
            method: 'POST'
        });

        if (response.success) {
            alertContainer.innerHTML = `
                <div class="alert alert-success">
                    ✓ ${response.message}
                </div>
            `;

            // Reload page to reset UI
            setTimeout(() => location.reload(), 1000);
        }
    } catch (error) {
        alertContainer.innerHTML = `
            <div class="alert alert-error">
                ✕ Gagal mereset pipeline: ${error.message}
            </div>
        `;
    }
}
