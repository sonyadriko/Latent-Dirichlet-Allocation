// Visualization page JavaScript

let ldaResults = null;
let topicDistributionChart = null;
let topicWordsChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadVisualizationData();
});

// Load visualization data
async function loadVisualizationData() {
    const loadingState = document.getElementById('loading-state');
    const noDataState = document.getElementById('no-data-state');
    const vizContent = document.getElementById('viz-content');
    const alertContainer = document.getElementById('alert-container');

    try {
        const response = await fetch('/api/kdd/results');
        const data = await response.json();

        loadingState.classList.add('hidden');

        if (data.success && data.data) {
            ldaResults = data.data;
            vizContent.classList.remove('hidden');
            renderVisualization();
        } else {
            noDataState.classList.remove('hidden');
        }
    } catch (error) {
        loadingState.classList.add('hidden');
        alertContainer.innerHTML = `
            <div class="alert alert-error">
                ✕ Gagal memuat data: ${error.message}
            </div>
        `;
        noDataState.classList.remove('hidden');
    }
}

// Render all visualizations
function renderVisualization() {
    if (!ldaResults) return;

    // Update stats
    document.getElementById('stat-documents').textContent = ldaResults.documents?.length || 0;
    document.getElementById('stat-topics').textContent = ldaResults.num_topics || 0;
    document.getElementById('stat-coherence').textContent = ldaResults.coherence_score || 0;

    // Render charts
    renderTopicDistributionChart();
    renderTopicsList();
    renderDocumentTopicTable();
    populateTopicSelect();
    renderTopicWordsChart(0);
}

// Render topic distribution chart
function renderTopicDistributionChart() {
    const ctx = document.getElementById('topic-distribution-chart').getContext('2d');

    const distribution = ldaResults.topic_distribution || {};
    const labels = Object.keys(distribution).map(id => `Topik ${parseInt(id) + 1}`);
    const values = Object.values(distribution);

    // Generate gradient colors
    const colors = generateColors(labels.length);

    if (topicDistributionChart) {
        topicDistributionChart.destroy();
    }

    topicDistributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: 'rgba(15, 23, 42, 0.8)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#94a3b8',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    callbacks: {
                        label: function (context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.raw} dokumen (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Populate topic select dropdown
function populateTopicSelect() {
    const select = document.getElementById('topic-select');
    select.innerHTML = '';

    (ldaResults.topics || []).forEach((topic, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = topic.topic_name;
        select.appendChild(option);
    });
}

// Update topic words chart when topic is selected
function updateTopicWordsChart() {
    const select = document.getElementById('topic-select');
    renderTopicWordsChart(parseInt(select.value));
}

// Render topic words chart
function renderTopicWordsChart(topicIndex) {
    const ctx = document.getElementById('topic-words-chart').getContext('2d');

    const topics = ldaResults.topics || [];
    if (topics.length === 0 || !topics[topicIndex]) return;

    const topic = topics[topicIndex];
    const words = topic.words || [];
    const labels = words.map(w => w.word);
    const values = words.map(w => w.weight);

    if (topicWordsChart) {
        topicWordsChart.destroy();
    }

    topicWordsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Bobot Kata',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.7)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8'
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#64748b'
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// Render topics list
function renderTopicsList() {
    const container = document.getElementById('topics-list');
    container.innerHTML = '';

    (ldaResults.topics || []).forEach(topic => {
        const li = document.createElement('li');
        li.className = 'topic-item';

        const wordsHtml = topic.words.map(w =>
            `<span class="word-tag">${w.word}<span class="weight">${w.weight}</span></span>`
        ).join('');

        li.innerHTML = `
            <div class="topic-header">
                <span class="topic-name">${topic.topic_name}</span>
                <span class="text-muted">${topic.words.length} kata</span>
            </div>
            <div class="topic-words">
                ${wordsHtml}
            </div>
        `;

        container.appendChild(li);
    });
}

// Render document-topic table
function renderDocumentTopicTable() {
    const container = document.getElementById('doc-topic-table');
    container.innerHTML = '';

    const docTopics = ldaResults.document_topics || [];
    const documents = ldaResults.documents || [];

    docTopics.forEach((dt, index) => {
        const doc = documents[index] || {};
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--border-color)';

        tr.innerHTML = `
            <td style="padding: var(--space-3);">${dt.doc_id + 1}</td>
            <td style="padding: var(--space-3);">${doc.title || '-'}</td>
            <td style="padding: var(--space-3);">
                <span class="status-badge completed">Topik ${dt.dominant_topic + 1}</span>
            </td>
            <td style="padding: var(--space-3);">${(dt.dominant_prob * 100).toFixed(1)}%</td>
        `;

        container.appendChild(tr);
    });
}

// Generate colors for charts
function generateColors(count) {
    const baseColors = [
        'rgba(99, 102, 241, 0.8)',   // Indigo
        'rgba(139, 92, 246, 0.8)',   // Purple
        'rgba(6, 182, 212, 0.8)',    // Cyan
        'rgba(16, 185, 129, 0.8)',   // Emerald
        'rgba(245, 158, 11, 0.8)',   // Amber
        'rgba(239, 68, 68, 0.8)',    // Red
        'rgba(236, 72, 153, 0.8)',   // Pink
        'rgba(59, 130, 246, 0.8)',   // Blue
        'rgba(34, 197, 94, 0.8)',    // Green
        'rgba(168, 85, 247, 0.8)'    // Violet
    ];

    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}
