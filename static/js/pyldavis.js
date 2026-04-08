/**
 * pyLDAvis Visualization Module
 * Handles the rendering and interaction of pyLDAvis topic visualization
 */

// Current pyLDAvis data
let pyldavisData = null;
let currentProjectId = null;

// API endpoints
const API_ENDPOINTS = {
    current: '/api/kdd/pyldavis',
    project: (id) => `/api/projects/${id}/pyldavis`
};

/**
 * Initialize pyLDAvis visualization
 * @param {number|null} projectId - Optional project ID to load specific project
 */
async function initPyLDAvis(projectId = null) {
    currentProjectId = projectId;

    const container = document.getElementById('pyldavis-container');
    if (!container) {
        console.warn('pyLDAvis container not found');
        return;
    }

    // Show loading state
    container.innerHTML = '<div class="pyldavis-loading">Loading visualization...</div>';

    try {
        // Fetch pyLDAvis data
        const endpoint = projectId
            ? API_ENDPOINTS.project(projectId)
            : API_ENDPOINTS.current;

        const response = await fetch(endpoint);
        const result = await response.json();

        if (!result.success) {
            showError(result.message || 'Failed to load pyLDAvis data');
            return;
        }

        pyldavisData = result.data;
        renderPyLDAvis(pyldavisData);

    } catch (error) {
        console.error('Error loading pyLDAvis data:', error);
        showError('Failed to connect to server. Please try again.');
    }
}

/**
 * Render pyLDAvis visualization
 * @param {Object} data - pyLDAvis data object
 */
function renderPyLDAvis(data) {
    const container = document.getElementById('pyldavis-container');
    if (!container) return;

    try {
        // Clear container
        container.innerHTML = '';

        // Create the visualization structure
        const vizWrapper = document.createElement('div');
        vizWrapper.id = 'ldavis-container';
        vizWrapper.style.cssText = `
            width: 100%;
            min-height: 600px;
            display: flex;
            gap: 20px;
        `;

        // Left panel: Intertopic Distance Map
        const leftPanel = createLeftPanel(data);
        vizWrapper.appendChild(leftPanel);

        // Right panel: Top terms panel
        const rightPanel = createRightPanel(data);
        vizWrapper.appendChild(rightPanel);

        container.appendChild(vizWrapper);

        // Initialize the visualization
        initializeVisualization(data);

    } catch (error) {
        console.error('Error rendering pyLDAvis:', error);
        showError('Error rendering visualization. Please try again.');
    }
}

/**
 * Create left panel with topic distance map
 * @param {Object} data - pyLDAvis data
 * @returns {HTMLElement} Left panel element
 */
function createLeftPanel(data) {
    const panel = document.createElement('div');
    panel.id = 'left-panel';
    panel.style.cssText = `
        flex: 1;
        min-width: 0;
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    `;

    const title = document.createElement('h3');
    title.textContent = 'Intertopic Distance Map';
    title.style.cssText = 'margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #333;';
    panel.appendChild(title);

    const svgContainer = document.createElement('div');
    svgContainer.id = 'topic-distance-map';
    svgContainer.style.cssText = `
        width: 100%;
        height: 500px;
        position: relative;
    `;
    panel.appendChild(svgContainer);

    const subtitle = document.createElement('p');
    subtitle.textContent = '(Size represents topic prevalence)';
    subtitle.style.cssText = 'margin: 8px 0 0 0; font-size: 12px; color: #666; text-align: center;';
    panel.appendChild(subtitle);

    return panel;
}

/**
 * Create right panel with top terms
 * @param {Object} data - pyLDAvis data
 * @returns {HTMLElement} Right panel element
 */
function createRightPanel(data) {
    const panel = document.createElement('div');
    panel.id = 'right-panel';
    panel.style.cssText = `
        flex: 0 0 300px;
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    `;

    const title = document.createElement('h3');
    title.textContent = 'Top Terms';
    title.style.cssText = 'margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #333;';
    panel.appendChild(title);

    // Lambda slider
    const sliderContainer = createLambdaSlider();
    panel.appendChild(sliderContainer);

    // Topic info
    const topicInfo = document.createElement('div');
    topicInfo.id = 'topic-info';
    topicInfo.style.cssText = 'margin-top: 16px;';
    panel.appendChild(topicInfo);

    const subtitle = document.createElement('p');
    subtitle.textContent = '(Click on a topic bubble to see its terms)';
    subtitle.style.cssText = 'margin: 16px 0 0 0; font-size: 11px; color: #666; text-align: center;';
    panel.appendChild(subtitle);

    return panel;
}

/**
 * Create lambda slider for term relevance adjustment
 * @returns {HTMLElement} Slider container element
 */
function createLambdaSlider() {
    const container = document.createElement('div');
    container.style.cssText = 'margin-bottom: 16px;';

    const label = document.createElement('label');
    label.textContent = 'Relevance (λ): 0.60';
    label.id = 'lambda-label';
    label.style.cssText = 'display: block; margin-bottom: 8px; font-size: 14px; color: #333;';
    container.appendChild(label);

    const slider = document.createElement('input');
    slider.type = 'range';
    slider.id = 'lambda-slider';
    slider.min = '0';
    slider.max = '1';
    slider.step = '0.01';
    slider.value = '0.6';
    slider.style.cssText = 'width: 100%;';

    slider.addEventListener('input', (e) => {
        const lambda = parseFloat(e.target.value);
        document.getElementById('lambda-label').textContent = `Relevance (λ): ${lambda.toFixed(2)}`;
        updateTopicTerms(lambda);
    });

    container.appendChild(slider);

    const info = document.createElement('p');
    info.textContent = 'λ = 1: Term probability within topic | λ = 0: Term exclusivity to topic';
    info.style.cssText = 'font-size: 11px; color: #888; margin: 4px 0 0 0;';
    container.appendChild(info);

    return container;
}

/**
 * Initialize the D3.js visualization
 * @param {Object} data - pyLDAvis data
 */
function initializeVisualization(data) {
    try {
        // Check if D3 is available
        if (typeof d3 === 'undefined') {
            throw new Error('D3.js is not loaded');
        }

        const width = document.getElementById('topic-distance-map').clientWidth - 32;
        const height = 500;

        // Create SVG
        const svg = d3.select('#topic-distance-map')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Create scales
        const xExtent = d3.extent(data.topic_coordinates, d => d.x);
        const yExtent = d3.extent(data.topic_coordinates, d => d.y);

        const xScale = d3.scaleLinear()
            .domain(xExtent)
            .range([40, width - 40]);

        const yScale = d3.scaleLinear()
            .domain(yExtent)
            .range([height - 40, 40]);

        const sizeScale = d3.scaleSqrt()
            .domain(d3.extent(data.topic_coordinates, d => d.Freq))
            .range([30, 80]);

        const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

        // Create tooltip
        const tooltip = d3.select('body')
            .append('div')
            .attr('class', 'pyldavis-tooltip')
            .style('position', 'absolute')
            .style('padding', '8px 12px')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('opacity', '0')
            .style('z-index', '1000');

        // Add topic circles
        const circles = svg.selectAll('.topic-circle')
            .data(data.topic_coordinates)
            .enter()
            .append('circle')
            .attr('class', 'topic-circle')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', d => sizeScale(d.Freq))
            .attr('fill', (d, i) => colorScale(i))
            .attr('fill-opacity', 0.7)
            .attr('stroke', (d, i) => colorScale(i))
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('mouseover', function(event, d) {
                d3.select(this)
                    .attr('fill-opacity', 0.9)
                    .attr('stroke-width', 3);

                tooltip
                    .style('opacity', '1')
                    .html(`<strong>${d.topics}</strong><br/>Frequency: ${(d.Freq * 100).toFixed(1)}%`);
            })
            .on('mousemove', function(event) {
                tooltip
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            })
            .on('mouseout', function() {
                d3.select(this)
                    .attr('fill-opacity', 0.7)
                    .attr('stroke-width', 2);

                tooltip.style('opacity', '0');
            })
            .on('click', function(event, d) {
                // Update right panel with selected topic
                const topicIndex = data.topic_coordinates.indexOf(d);
                selectTopic(topicIndex);
            });

        // Add topic labels
        svg.selectAll('.topic-label')
            .data(data.topic_coordinates)
            .enter()
            .append('text')
            .attr('class', 'topic-label')
            .attr('x', d => xScale(d.x))
            .attr('y', d => yScale(d.y))
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('fill', 'white')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .style('pointer-events', 'none')
            .text((d, i) => i + 1);

        // Store for later updates
        window.pyldavisScales = { xScale, yScale, sizeScale, colorScale, svg };

        // Initialize with first topic
        if (data.topic_coordinates.length > 0) {
            selectTopic(0);
        }

    } catch (error) {
        console.error('Error initializing visualization:', error);
        showError('Error initializing D3 visualization. Please ensure D3.js is loaded.');
    }
}

/**
 * Select and display a topic's terms
 * @param {number} topicIndex - Index of the selected topic
 */
function selectTopic(topicIndex) {
    if (!pyldavisData || !pyldavisData.topic_info) return;

    // Update selected state in circles
    if (window.pyldavisScales) {
        d3.selectAll('.topic-circle')
            .attr('stroke-width', (d, i) => i === topicIndex ? 4 : 2)
            .attr('fill-opacity', (d, i) => i === topicIndex ? 0.9 : 0.5);
    }

    updateTopicTerms(0.6, topicIndex);
}

/**
 * Update the topic terms display based on lambda value
 * @param {number} lambda - Relevance parameter (0-1)
 * @param {number} topicIndex - Topic index (uses current if not specified)
 */
function updateTopicTerms(lambda, topicIndex = null) {
    if (!pyldavisData || !pyldavisData.topic_info) return;

    // If no topic specified, use the currently selected one (from highlighted circle)
    if (topicIndex === null) {
        const highlightedCircle = d3.selectAll('.topic-circle').filter(function() {
            return d3.select(this).attr('fill-opacity') === '0.9';
        });
        if (!highlightedCircle.empty()) {
            const circles = d3.selectAll('.topic-circle').nodes();
            topicIndex = circles.indexOf(highlightedCircle.node());
        }
        if (topicIndex === null || topicIndex < 0) topicIndex = 0;
    }

    const topicInfo = pyldavisData.topic_info.filter(d => d.Category === `Topic ${topicIndex + 1}`);

    if (!topicInfo.length) return;

    // Calculate relevance
    const terms = topicInfo.map(d => {
        const logLift = d.loglift || 0;
        const logProb = d.logprob || 0;
        const relevance = lambda * logLift + (1 - lambda) * logProb;
        return {
            term: d.Term,
            frequency: d.Freq,
            total: d.Total,
            relevance: relevance
        };
    }).sort((a, b) => b.relevance - a.relevance).slice(0, 30);

    // Render terms list
    const container = document.getElementById('topic-info');
    if (!container) return;

    const maxRelevance = Math.max(...terms.map(t => t.relevance));
    const minRelevance = Math.min(...terms.map(t => t.relevance));

    container.innerHTML = `
        <h4 style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #6366f1;">
            Topic ${topicIndex + 1} - Top 30 Terms
        </h4>
        <div style="max-height: 400px; overflow-y: auto;">
            ${terms.map((t, i) => {
                const barWidth = maxRelevance > minRelevance
                    ? ((t.relevance - minRelevance) / (maxRelevance - minRelevance)) * 100
                    : 50;

                return `
                    <div style="
                        display: flex;
                        align-items: center;
                        padding: 4px 0;
                        border-bottom: 1px solid #eee;
                    ">
                        <span style="
                            width: 24px;
                            height: 24px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background: #6366f1;
                            color: white;
                            border-radius: 50%;
                            font-size: 10px;
                            font-weight: bold;
                            flex-shrink: 0;
                        ">${i + 1}</span>
                        <span style="
                            flex: 1;
                            margin-left: 8px;
                            font-size: 13px;
                            color: #333;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                        ">${t.term}</span>
                        <div style="
                            width: ${barWidth}%;
                            height: 4px;
                            background: linear-gradient(90deg, #6366f1, #818cf8);
                            border-radius: 2px;
                            flex-shrink: 0;
                        "></div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Show error message in container
 * @param {string} message - Error message
 */
function showError(message) {
    const container = document.getElementById('pyldavis-container');
    if (container) {
        container.innerHTML = `<div class="error">${message}</div>`;
    }
}

/**
 * Show pyLDAvis view
 */
function showPyLDAvisView() {
    // Hide all views
    document.getElementById('overall-view').classList.add('hidden');
    document.getElementById('topic-view').classList.add('hidden');

    // Show pyLDAvis view
    document.getElementById('pyldavis-view').classList.remove('hidden');

    // Update active button
    document.getElementById('overall-mode').classList.remove('active');
    document.getElementById('topic-mode').classList.remove('active');
    document.getElementById('pyldavis-mode').classList.add('active');

    // Initialize visualization if not already loaded
    if (!pyldavisData) {
        initPyLDAvis(currentProjectId);
    }
}

/**
 * Refresh pyLDAvis data
 */
function refreshPyLDAvis() {
    pyldavisData = null;
    initPyLDAvis(currentProjectId);
}

// Export functions for use in other scripts
window.pyldavis = {
    init: initPyLDAvis,
    show: showPyLDAvisView,
    refresh: refreshPyLDAvis,
    selectTopic: selectTopic
};

// Auto-initialize when pyLDAvis view is shown
document.addEventListener('DOMContentLoaded', () => {
    // Check if pyLDAvis button exists
    const pyldavisBtn = document.getElementById('pyldavis-mode');
    if (pyldavisBtn) {
        pyldavisBtn.addEventListener('click', showPyLDAvisView);
    }
});
