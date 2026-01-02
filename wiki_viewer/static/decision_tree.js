/**
 * Decision Tree Visualizer - Production-Ready Implementation
 *
 * Features:
 * - Real Mermaid decision trees from wiki files
 * - Vendor card selection with live parameter display
 * - Slider inputs with live YIS calculation
 * - Live path tracing (auto-update on input change)
 * - Node feedback system with comments
 * - SVG-based tree rendering with proper node shapes
 * - Pan/zoom controls
 */

class DecisionTreeVisualizer {
    constructor() {
        // Data
        this.treeData = window.DECISION_TREE_DATA || {};
        this.feedbackCounts = window.FEEDBACK_COUNTS || {};
        this.currentTreeId = window.DEFAULT_TREE_ID;
        this.currentVendor = null;
        this.currentVendorId = null;
        this.vendorDetails = {};
        this.resolvedLabels = {};
        this.currentPath = [];
        this.currentEdges = [];
        this.currentResult = null;

        // SVG elements
        this.svg = document.getElementById('decision-tree-svg');
        this.nodesLayer = document.getElementById('nodes-layer');
        this.edgesLayer = document.getElementById('edges-layer');
        this.labelsLayer = document.getElementById('labels-layer');
        this.feedbackLayer = document.getElementById('feedback-layer');

        // State
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.isPanning = false;
        this.panStart = { x: 0, y: 0 };
        this.selectedNodeId = null;

        // Debounce timer for live updates
        this.updateTimer = null;

        // Initialize
        this.cacheElements();
        this.init();
    }

    cacheElements() {
        // Header
        this.treeSelect = document.getElementById('tree-select');

        // Sidebar sections
        this.vendorCards = document.getElementById('vendor-cards');
        this.vendorHint = document.getElementById('vendor-hint');
        this.rulesSection = document.getElementById('rules-section');
        this.rulesGrid = document.getElementById('rules-grid');
        this.inputsSection = document.getElementById('inputs-section');
        this.resultSection = document.getElementById('result-section');
        this.pathSection = document.getElementById('path-section');
        this.pathSummary = document.getElementById('path-summary');

        // Sliders
        this.quantitySlider = document.getElementById('input-quantity');
        this.purchasedSlider = document.getElementById('input-purchased');
        this.qtyValue = document.getElementById('qty-value');
        this.purchasedValue = document.getElementById('purchased-value');

        // Calculated values
        this.calcYIS = document.getElementById('calc-yis');
        this.calcDays = document.getElementById('calc-days');
        this.yisBar = document.getElementById('yis-bar');
        this.thresholdLow = document.getElementById('threshold-low');
        this.thresholdTarget = document.getElementById('threshold-target');

        // Result
        this.resultDisplay = document.getElementById('result-display');
        this.resultAction = document.getElementById('result-action');
        this.resultPriority = document.getElementById('result-priority');
        this.resultReorder = document.getElementById('result-reorder');
        this.reorderRow = document.getElementById('reorder-row');
        this.resultReason = document.getElementById('result-reason');

        // Canvas
        this.canvasLabel = document.getElementById('canvas-label');
        this.liveIndicator = document.getElementById('live-indicator');
        this.zoomDisplay = document.getElementById('zoom-display');
        this.emptyState = document.getElementById('empty-state');

        // Toolbar
        this.btnZoomIn = document.getElementById('btn-zoom-in');
        this.btnZoomOut = document.getElementById('btn-zoom-out');
        this.btnResetView = document.getElementById('btn-reset-view');
        this.btnFitView = document.getElementById('btn-fit-view');

        // Detail panel
        this.detailPanel = document.getElementById('node-detail-panel');
        this.detailTitle = document.getElementById('detail-title');
        this.detailDescription = document.getElementById('detail-description');
        this.detailCondition = document.getElementById('detail-condition');
        this.detailResult = document.getElementById('detail-result');
        this.closeDetail = document.getElementById('close-detail');

        // Feedback
        this.detailFeedbackCount = document.getElementById('detail-feedback-count');
        this.feedbackList = document.getElementById('detail-feedback-list');
        this.feedbackAuthor = document.getElementById('feedback-author');
        this.feedbackText = document.getElementById('feedback-text');
        this.btnAddFeedback = document.getElementById('btn-add-feedback');
    }

    async init() {
        await this.loadVendors();
        this.bindEvents();
        this.updateSliderDisplays();
        this.renderTree();
    }

    async loadVendors() {
        try {
            const res = await fetch('/wiki/decision-tree/api/vendors');
            const data = await res.json();
            if (data.success) {
                this.vendorDetails = data.vendor_details || {};
            }
        } catch (e) {
            console.error('Failed to load vendors:', e);
        }
    }

    bindEvents() {
        // Tree selector
        if (this.treeSelect) {
            this.treeSelect.addEventListener('change', () => this.onTreeChange());
        }

        // Vendor cards
        if (this.vendorCards) {
            this.vendorCards.querySelectorAll('.vendor-card').forEach(card => {
                card.addEventListener('click', () => this.onVendorSelect(card));
            });
        }

        // Slider inputs - live update
        if (this.quantitySlider) {
            this.quantitySlider.addEventListener('input', () => this.onSliderChange());
        }
        if (this.purchasedSlider) {
            this.purchasedSlider.addEventListener('input', () => this.onSliderChange());
        }

        // Toolbar
        if (this.btnZoomIn) this.btnZoomIn.addEventListener('click', () => this.zoom(1.2));
        if (this.btnZoomOut) this.btnZoomOut.addEventListener('click', () => this.zoom(0.8));
        if (this.btnResetView) this.btnResetView.addEventListener('click', () => this.resetView());
        if (this.btnFitView) this.btnFitView.addEventListener('click', () => this.fitToView());

        // Detail panel
        if (this.closeDetail) {
            this.closeDetail.addEventListener('click', () => this.hideDetailPanel());
        }
        if (this.btnAddFeedback) {
            this.btnAddFeedback.addEventListener('click', () => this.addFeedback());
        }

        // Pan/zoom
        if (this.svg) {
            this.svg.addEventListener('mousedown', (e) => this.startPan(e));
            this.svg.addEventListener('mousemove', (e) => this.pan(e));
            this.svg.addEventListener('mouseup', () => this.endPan());
            this.svg.addEventListener('mouseleave', () => this.endPan());
            this.svg.addEventListener('wheel', (e) => this.handleWheel(e));
        }

        // Keyboard
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.hideDetailPanel();
        });
    }

    // ========================================================================
    // TREE SELECTION
    // ========================================================================

    async onTreeChange() {
        const treeId = this.treeSelect.value;
        if (!treeId) return;

        try {
            const res = await fetch(`/wiki/decision-tree/api/tree/${treeId}`);
            const data = await res.json();
            if (data.success) {
                this.treeData = data.tree;
                this.currentTreeId = treeId;
                this.clearPath();
                this.renderTree();
            }
        } catch (e) {
            console.error('Failed to load tree:', e);
        }
    }

    // ========================================================================
    // VENDOR SELECTION
    // ========================================================================

    async onVendorSelect(card) {
        // Update UI
        this.vendorCards.querySelectorAll('.vendor-card').forEach(c => {
            c.classList.remove('active');
        });
        card.classList.add('active');

        const vendorId = card.dataset.vendorId;
        this.currentVendorId = vendorId;
        this.currentVendor = this.vendorDetails[vendorId];

        // Hide hint
        if (this.vendorHint) this.vendorHint.style.display = 'none';

        // Display rules
        this.displayVendorRules();

        // Show inputs
        if (this.inputsSection) this.inputsSection.style.display = 'block';
        if (this.resultSection) this.resultSection.style.display = 'block';
        if (this.pathSection) this.pathSection.style.display = 'block';

        // Update thresholds
        this.updateThresholdMarkers();

        // Hide empty state, show live indicator
        if (this.emptyState) this.emptyState.classList.add('hidden');
        if (this.liveIndicator) this.liveIndicator.style.display = 'flex';

        // Update canvas label
        if (this.canvasLabel && this.currentVendor) {
            this.canvasLabel.textContent = this.currentVendor.name || vendorId;
        }

        // Resolve labels and render
        await this.resolveLabels();
        this.renderTree();

        // Trigger live evaluation
        this.evaluatePath();
    }

    displayVendorRules() {
        if (!this.currentVendor || !this.rulesGrid) return;

        const params = this.currentVendor.parameters || {};
        this.rulesGrid.innerHTML = '';

        const paramConfig = {
            threshold_years: { label: 'Threshold', format: v => `${v} yr` },
            target_years: { label: 'Target', format: v => `${v} yr` },
            lean_threshold: { label: 'Lean Alert', format: v => `${v} yr` },
            allow_cascade: { label: 'Cascade', format: v => v ? 'Yes' : 'No', isBoolean: true },
            rounding_multiple: { label: 'Round To', format: v => `${v}` }
        };

        for (const [key, config] of Object.entries(paramConfig)) {
            if (params[key] === undefined) continue;

            const value = params[key];
            const item = document.createElement('div');
            item.className = 'rule-item';

            let valueClass = 'rule-value';
            if (config.isBoolean) {
                valueClass += value ? ' boolean-true' : ' boolean-false';
            }

            item.innerHTML = `
                <span class="rule-label">${config.label}</span>
                <span class="${valueClass}">${config.format(value)}</span>
            `;
            this.rulesGrid.appendChild(item);
        }

        if (this.rulesSection) this.rulesSection.style.display = 'block';
    }

    async resolveLabels() {
        if (!this.currentVendorId) return;

        try {
            const res = await fetch('/wiki/decision-tree/api/resolve-labels', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor_id: this.currentVendorId })
            });
            const data = await res.json();
            if (data.success) {
                this.resolvedLabels = data.labels || {};
            }
        } catch (e) {
            console.error('Failed to resolve labels:', e);
        }
    }

    // ========================================================================
    // SLIDER & YIS CALCULATION
    // ========================================================================

    onSliderChange() {
        this.updateSliderDisplays();

        // Debounced live update
        if (this.updateTimer) clearTimeout(this.updateTimer);
        this.updateTimer = setTimeout(() => {
            if (this.currentVendorId) {
                this.evaluatePath();
            }
        }, 150);
    }

    updateSliderDisplays() {
        const qty = parseFloat(this.quantitySlider?.value || 0);
        const purchased = parseFloat(this.purchasedSlider?.value || 0);

        if (this.qtyValue) this.qtyValue.textContent = qty;
        if (this.purchasedValue) this.purchasedValue.textContent = purchased;

        // Calculate YIS
        let yis = 0;
        let days = 0;
        if (purchased > 0) {
            yis = qty / purchased;
            days = Math.round(yis * 365);
        }

        if (this.calcYIS) this.calcYIS.textContent = yis.toFixed(2);
        if (this.calcDays) this.calcDays.textContent = `${days} days`;

        // Update YIS bar (max 1 year = 100%)
        const barWidth = Math.min(yis * 100, 100);
        if (this.yisBar) this.yisBar.style.width = `${barWidth}%`;
    }

    updateThresholdMarkers() {
        if (!this.currentVendor) return;

        const params = this.currentVendor.parameters || {};
        const threshold = params.threshold_years || 0.25;
        const target = params.target_years || 0.40;

        // Position markers (max 1 year = 100%)
        if (this.thresholdLow) {
            this.thresholdLow.style.left = `${threshold * 100}%`;
        }
        if (this.thresholdTarget) {
            this.thresholdTarget.style.left = `${target * 100}%`;
        }
    }

    // ========================================================================
    // PATH EVALUATION (LIVE)
    // ========================================================================

    async evaluatePath() {
        if (!this.currentVendorId) return;

        const qty = parseFloat(this.quantitySlider?.value || 0);
        const purchased = parseFloat(this.purchasedSlider?.value || 0);

        try {
            const res = await fetch('/wiki/decision-tree/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vendor_id: this.currentVendorId,
                    inputs: {
                        quantity_in_stock: qty,
                        purchased: purchased
                    }
                })
            });

            const data = await res.json();

            if (data.success) {
                this.currentPath = data.path || [];
                this.currentEdges = data.active_edges || [];
                this.currentResult = data.result;

                this.displayResult(data);
                this.displayPathSummary();
                this.highlightPath();
            }
        } catch (e) {
            console.error('Evaluation failed:', e);
        }
    }

    displayResult(data) {
        const result = data.result || {};
        const action = result.action || 'unknown';

        // Update result box class
        if (this.resultDisplay) {
            this.resultDisplay.className = 'result-box result-' + action;
        }

        // Action text
        if (this.resultAction) {
            const actionLabels = {
                none: 'No Order Needed',
                order: 'Order Required',
                review: 'Manual Review',
                cascade_review: 'Cascade Review',
                complete: 'Complete'
            };
            this.resultAction.textContent = actionLabels[action] || action;
        }

        // Priority
        if (this.resultPriority) {
            this.resultPriority.textContent = result.priority || '--';
        }

        // Reorder quantity
        if (data.reorder_quantity !== null && data.reorder_quantity !== undefined) {
            if (this.reorderRow) this.reorderRow.style.display = 'flex';
            if (this.resultReorder) this.resultReorder.textContent = data.reorder_quantity;
        } else {
            if (this.reorderRow) this.reorderRow.style.display = 'none';
        }

        // Reason
        if (this.resultReason) {
            this.resultReason.textContent = result.reason || 'Path traced successfully';
        }
    }

    displayPathSummary() {
        if (!this.pathSummary) return;

        this.pathSummary.innerHTML = '';

        this.currentPath.forEach((nodeId, idx) => {
            if (idx > 0) {
                const arrow = document.createElement('span');
                arrow.className = 'path-arrow';
                arrow.textContent = '→';
                this.pathSummary.appendChild(arrow);
            }

            const node = document.createElement('span');
            node.className = 'path-node active';
            if (idx === this.currentPath.length - 1) {
                node.classList.add('current');
            }
            node.textContent = nodeId;
            this.pathSummary.appendChild(node);
        });
    }

    highlightPath() {
        // Reset all nodes and edges
        this.nodesLayer.querySelectorAll('.node-group').forEach(g => {
            g.classList.remove('active', 'inactive');
        });
        this.edgesLayer.querySelectorAll('.edge-group').forEach(g => {
            g.classList.remove('active', 'inactive');
            const path = g.querySelector('.edge-path');
            if (path) {
                path.classList.remove('active', 'animated', 'inactive');
            }
        });

        // Mark active nodes
        this.currentPath.forEach(nodeId => {
            const nodeGroup = this.nodesLayer.querySelector(`[data-node-id="${nodeId}"]`);
            if (nodeGroup) {
                nodeGroup.classList.add('active');
            }
        });

        // Mark active edges
        this.currentEdges.forEach(edgeId => {
            const edgeGroup = this.edgesLayer.querySelector(`[data-edge-id="${edgeId}"]`);
            if (edgeGroup) {
                const path = edgeGroup.querySelector('.edge-path');
                if (path) {
                    path.classList.add('active', 'animated');
                }
            }
        });

        // Mark inactive nodes/edges
        this.nodesLayer.querySelectorAll('.node-group').forEach(g => {
            if (!g.classList.contains('active')) {
                g.classList.add('inactive');
            }
        });
        this.edgesLayer.querySelectorAll('.edge-group').forEach(g => {
            const path = g.querySelector('.edge-path');
            if (path && !path.classList.contains('active')) {
                path.classList.add('inactive');
            }
        });
    }

    clearPath() {
        this.currentPath = [];
        this.currentEdges = [];
        this.currentResult = null;

        if (this.pathSummary) this.pathSummary.innerHTML = '';
    }

    // ========================================================================
    // TREE RENDERING
    // ========================================================================

    renderTree() {
        if (!this.treeData || !this.treeData.tree) return;

        const tree = this.treeData.tree;
        const nodes = tree.nodes || {};
        const edges = tree.edges || [];

        // Clear layers
        this.nodesLayer.innerHTML = '';
        this.edgesLayer.innerHTML = '';
        this.labelsLayer.innerHTML = '';
        this.feedbackLayer.innerHTML = '';

        // Render edges first (below nodes)
        edges.forEach(edge => this.renderEdge(edge, nodes));

        // Render nodes
        Object.values(nodes).forEach(node => this.renderNode(node));

        // Render feedback indicators
        this.renderFeedbackIndicators(nodes);

        // Apply current path highlighting
        if (this.currentPath.length > 0) {
            this.highlightPath();
        }
    }

    renderNode(node) {
        const pos = node.position || { x: 100, y: 100 };
        const type = node.type || 'default';
        const label = this.resolvedLabels[node.id] || node.label || node.id;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', `node-group node-${type}`);
        g.setAttribute('data-node-id', node.id);
        g.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);

        // Create shape based on type
        let shape;
        const width = this.getNodeWidth(label);
        const height = 40;

        switch (type) {
            case 'start':
            case 'rounded':
                shape = this.createRoundedRect(-width/2, -height/2, width, height, 20, '#4caf50', '#e8f5e9');
                break;
            case 'decision':
                shape = this.createDiamond(0, 0, Math.max(width, 50), height + 10, '#3f51b5', '#e8eaf6');
                break;
            case 'calculation':
                shape = this.createRect(-width/2, -height/2, width, height, '#ff9800', '#fff3e0');
                break;
            case 'result':
                const resultColor = node.result?.color || '#616161';
                shape = this.createRoundedRect(-width/2, -height/2, width, height, 20, resultColor, this.lightenColor(resultColor));
                break;
            case 'action':
            default:
                shape = this.createRect(-width/2, -height/2, width, height, '#9e9e9e', '#f5f5f5');
                break;
        }

        g.appendChild(shape);

        // Add label
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-label');
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('y', 0);

        // Word wrap for long labels
        const words = label.split(' ');
        if (words.length > 3 && label.length > 20) {
            const mid = Math.ceil(words.length / 2);
            const line1 = words.slice(0, mid).join(' ');
            const line2 = words.slice(mid).join(' ');

            const tspan1 = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan1.setAttribute('x', 0);
            tspan1.setAttribute('dy', '-0.5em');
            tspan1.textContent = line1;

            const tspan2 = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan2.setAttribute('x', 0);
            tspan2.setAttribute('dy', '1.2em');
            tspan2.textContent = line2;

            text.appendChild(tspan1);
            text.appendChild(tspan2);
        } else {
            text.textContent = label.length > 30 ? label.substring(0, 27) + '...' : label;
        }

        g.appendChild(text);

        // Click handler
        g.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showNodeDetail(node);
        });

        this.nodesLayer.appendChild(g);
    }

    renderEdge(edge, nodes) {
        const fromNode = nodes[edge.from];
        const toNode = nodes[edge.to];

        if (!fromNode || !toNode) return;

        const fromPos = fromNode.position || { x: 0, y: 0 };
        const toPos = toNode.position || { x: 0, y: 0 };

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'edge-group');
        g.setAttribute('data-edge-id', edge.id);

        // Calculate path (simple straight line for now)
        const fromY = fromPos.y + 20; // Bottom of node
        const toY = toPos.y - 25; // Top of node

        // Create curved path
        const midY = (fromY + toY) / 2;
        const d = `M ${fromPos.x} ${fromY} C ${fromPos.x} ${midY}, ${toPos.x} ${midY}, ${toPos.x} ${toY}`;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('class', 'edge-path');
        path.setAttribute('d', d);
        path.setAttribute('marker-end', 'url(#arrowhead)');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#bdbdbd');
        path.setAttribute('stroke-width', '2');

        g.appendChild(path);

        // Add label if exists
        const label = this.resolvedLabels[edge.id] || edge.label;
        if (label) {
            const labelX = (fromPos.x + toPos.x) / 2;
            const labelY = midY;

            // Background
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('class', 'edge-label-bg');
            bg.setAttribute('x', labelX - 20);
            bg.setAttribute('y', labelY - 8);
            bg.setAttribute('width', 40);
            bg.setAttribute('height', 16);
            bg.setAttribute('rx', 3);
            bg.setAttribute('fill', 'white');

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'edge-label');
            text.setAttribute('x', labelX);
            text.setAttribute('y', labelY);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.textContent = label;

            g.appendChild(bg);
            g.appendChild(text);
        }

        this.edgesLayer.appendChild(g);
    }

    renderFeedbackIndicators(nodes) {
        for (const [nodeId, count] of Object.entries(this.feedbackCounts)) {
            const node = nodes[nodeId];
            if (!node || count === 0) continue;

            const pos = node.position || { x: 100, y: 100 };

            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'feedback-indicator');
            g.setAttribute('transform', `translate(${pos.x + 30}, ${pos.y - 15})`);

            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('class', 'feedback-dot');
            circle.setAttribute('r', '10');
            circle.setAttribute('cx', '0');
            circle.setAttribute('cy', '0');

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'feedback-count-text');
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.textContent = count > 9 ? '9+' : count;

            g.appendChild(circle);
            g.appendChild(text);

            g.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showNodeDetail(node);
            });

            this.feedbackLayer.appendChild(g);
        }
    }

    // Shape helpers
    createRoundedRect(x, y, width, height, radius, stroke, fill) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('class', 'node-shape');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('rx', radius);
        rect.setAttribute('fill', fill);
        rect.setAttribute('stroke', stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('filter', 'url(#shadow)');
        return rect;
    }

    createRect(x, y, width, height, stroke, fill) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('class', 'node-shape');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('fill', fill);
        rect.setAttribute('stroke', stroke);
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('filter', 'url(#shadow)');
        return rect;
    }

    createDiamond(cx, cy, width, height, stroke, fill) {
        const halfW = width / 2;
        const halfH = height / 2;
        const points = `${cx},${cy - halfH} ${cx + halfW},${cy} ${cx},${cy + halfH} ${cx - halfW},${cy}`;

        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('class', 'node-shape');
        polygon.setAttribute('points', points);
        polygon.setAttribute('fill', fill);
        polygon.setAttribute('stroke', stroke);
        polygon.setAttribute('stroke-width', '2');
        polygon.setAttribute('filter', 'url(#shadow)');
        return polygon;
    }

    getNodeWidth(label) {
        // Estimate width based on text length
        const minWidth = 80;
        const charWidth = 7;
        return Math.max(minWidth, Math.min(200, label.length * charWidth + 30));
    }

    lightenColor(hex) {
        // Simple color lightening
        const colors = {
            '#4caf50': '#e8f5e9',
            '#f44336': '#ffebee',
            '#ff9800': '#fff3e0',
            '#2196f3': '#e3f2fd',
            '#9c27b0': '#f3e5f5',
            '#616161': '#f5f5f5'
        };
        return colors[hex] || '#f5f5f5';
    }

    // ========================================================================
    // NODE DETAIL PANEL
    // ========================================================================

    async showNodeDetail(node) {
        this.selectedNodeId = node.id;

        if (this.detailTitle) {
            this.detailTitle.textContent = node.id;
        }

        if (this.detailDescription) {
            const label = this.resolvedLabels[node.id] || node.label || '';
            this.detailDescription.textContent = label;
        }

        // Show condition if decision node
        if (this.detailCondition) {
            if (node.condition) {
                const cond = node.condition;
                this.detailCondition.innerHTML = `
                    <strong>Condition:</strong>
                    <code>${cond.field} ${cond.operator} ${cond.value}</code>
                `;
                this.detailCondition.style.display = 'block';
            } else {
                this.detailCondition.style.display = 'none';
            }
        }

        // Show result if result node
        if (this.detailResult) {
            if (node.result) {
                const res = node.result;
                this.detailResult.innerHTML = `
                    <strong>Result:</strong> ${res.action || ''}
                    <span style="color: ${res.color || '#666'}">●</span>
                `;
                this.detailResult.style.display = 'block';
            } else {
                this.detailResult.style.display = 'none';
            }
        }

        // Load feedback
        await this.loadFeedback(node.id);

        if (this.detailPanel) {
            this.detailPanel.style.display = 'flex';
        }
    }

    hideDetailPanel() {
        if (this.detailPanel) {
            this.detailPanel.style.display = 'none';
        }
        this.selectedNodeId = null;
    }

    // ========================================================================
    // FEEDBACK SYSTEM
    // ========================================================================

    async loadFeedback(nodeId) {
        try {
            const res = await fetch(`/wiki/decision-tree/api/feedback/${nodeId}`);
            const data = await res.json();

            if (data.success) {
                this.displayFeedback(data.comments || []);
                if (this.detailFeedbackCount) {
                    this.detailFeedbackCount.textContent = data.comments?.length || 0;
                }
            }
        } catch (e) {
            console.error('Failed to load feedback:', e);
        }
    }

    displayFeedback(comments) {
        if (!this.feedbackList) return;

        this.feedbackList.innerHTML = '';

        if (comments.length === 0) {
            this.feedbackList.innerHTML = '<p style="color: #999; font-size: 0.8rem;">No comments yet</p>';
            return;
        }

        comments.forEach(comment => {
            const item = document.createElement('div');
            item.className = 'feedback-item' + (comment.resolved ? ' resolved' : '');

            const time = new Date(comment.created_at).toLocaleDateString();

            item.innerHTML = `
                <div class="feedback-item-header">
                    <span class="feedback-author">${comment.author}</span>
                    <span class="feedback-time">${time}</span>
                </div>
                <div class="feedback-item-text">${comment.text}</div>
                ${!comment.resolved ? `<button class="feedback-resolve-btn" data-id="${comment.id}">Mark resolved</button>` : ''}
            `;

            const resolveBtn = item.querySelector('.feedback-resolve-btn');
            if (resolveBtn) {
                resolveBtn.addEventListener('click', () => this.resolveFeedback(comment.id));
            }

            this.feedbackList.appendChild(item);
        });
    }

    async addFeedback() {
        if (!this.selectedNodeId) return;

        const author = this.feedbackAuthor?.value || 'Anonymous';
        const text = this.feedbackText?.value?.trim();

        if (!text) {
            alert('Please enter a comment');
            return;
        }

        try {
            const res = await fetch('/wiki/decision-tree/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    node_id: this.selectedNodeId,
                    author: author,
                    text: text
                })
            });

            const data = await res.json();
            if (data.success) {
                // Clear form
                if (this.feedbackText) this.feedbackText.value = '';

                // Reload feedback
                await this.loadFeedback(this.selectedNodeId);

                // Update feedback count
                this.feedbackCounts[this.selectedNodeId] = (this.feedbackCounts[this.selectedNodeId] || 0) + 1;

                // Re-render feedback indicators
                const tree = this.treeData.tree || {};
                this.feedbackLayer.innerHTML = '';
                this.renderFeedbackIndicators(tree.nodes || {});
            }
        } catch (e) {
            console.error('Failed to add feedback:', e);
            alert('Failed to save comment');
        }
    }

    async resolveFeedback(commentId) {
        if (!this.selectedNodeId) return;

        try {
            const res = await fetch(`/wiki/decision-tree/api/feedback/${this.selectedNodeId}/${commentId}/resolve`, {
                method: 'POST'
            });

            const data = await res.json();
            if (data.success) {
                await this.loadFeedback(this.selectedNodeId);

                // Update feedback count
                if (this.feedbackCounts[this.selectedNodeId] > 0) {
                    this.feedbackCounts[this.selectedNodeId]--;
                }

                // Re-render feedback indicators
                const tree = this.treeData.tree || {};
                this.feedbackLayer.innerHTML = '';
                this.renderFeedbackIndicators(tree.nodes || {});
            }
        } catch (e) {
            console.error('Failed to resolve feedback:', e);
        }
    }

    // ========================================================================
    // PAN/ZOOM
    // ========================================================================

    zoom(factor) {
        this.scale *= factor;
        this.scale = Math.max(0.3, Math.min(3, this.scale));
        this.updateTransform();
        this.updateZoomDisplay();
    }

    resetView() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
        this.updateZoomDisplay();
    }

    fitToView() {
        // Get bounding box of all nodes
        const nodes = this.nodesLayer.querySelectorAll('.node-group');
        if (nodes.length === 0) return;

        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

        nodes.forEach(node => {
            const transform = node.getAttribute('transform');
            const match = transform.match(/translate\(([^,]+),\s*([^)]+)\)/);
            if (match) {
                const x = parseFloat(match[1]);
                const y = parseFloat(match[2]);
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
            }
        });

        const width = maxX - minX + 200;
        const height = maxY - minY + 200;

        const container = document.getElementById('canvas-container');
        const containerWidth = container?.clientWidth || 800;
        const containerHeight = container?.clientHeight || 600;

        this.scale = Math.min(containerWidth / width, containerHeight / height, 1.5);
        this.translateX = (containerWidth - width * this.scale) / 2 - minX * this.scale + 100;
        this.translateY = (containerHeight - height * this.scale) / 2 - minY * this.scale + 100;

        this.updateTransform();
        this.updateZoomDisplay();
    }

    startPan(e) {
        if (e.button !== 0) return;
        this.isPanning = true;
        this.panStart = { x: e.clientX, y: e.clientY };
    }

    pan(e) {
        if (!this.isPanning) return;
        const dx = e.clientX - this.panStart.x;
        const dy = e.clientY - this.panStart.y;
        this.translateX += dx;
        this.translateY += dy;
        this.panStart = { x: e.clientX, y: e.clientY };
        this.updateTransform();
    }

    endPan() {
        this.isPanning = false;
    }

    handleWheel(e) {
        e.preventDefault();
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom(factor);
    }

    updateTransform() {
        const layers = [this.nodesLayer, this.edgesLayer, this.labelsLayer, this.feedbackLayer];
        layers.forEach(layer => {
            if (layer) {
                layer.setAttribute('transform', `translate(${this.translateX}, ${this.translateY}) scale(${this.scale})`);
            }
        });
    }

    updateZoomDisplay() {
        if (this.zoomDisplay) {
            this.zoomDisplay.textContent = `${Math.round(this.scale * 100)}%`;
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.visualizer = new DecisionTreeVisualizer();
});
