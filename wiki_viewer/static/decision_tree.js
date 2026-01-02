/**
 * Decision Tree Visualizer - Interactive SVG Rendering & Path Tracing
 *
 * Features:
 * - SVG-based tree rendering with different node shapes
 * - Live path tracing with animation
 * - Vendor selection with parameter resolution
 * - Test input simulation
 */

class DecisionTreeVisualizer {
    constructor() {
        // Get tree data from embedded script
        this.treeData = window.DECISION_TREE_DATA || {};
        this.currentVendor = null;
        this.resolvedLabels = {};
        this.currentPath = [];
        this.currentEdges = [];

        // SVG elements
        this.svg = document.getElementById('decision-tree-svg');
        this.nodesLayer = document.getElementById('nodes-layer');
        this.edgesLayer = document.getElementById('edges-layer');
        this.labelsLayer = document.getElementById('labels-layer');

        // UI elements
        this.vendorSelect = document.getElementById('vendor-select');
        this.rulesSection = document.getElementById('rules-section');
        this.rulesTable = document.getElementById('rules-table');
        this.inputsSection = document.getElementById('inputs-section');
        this.resultSection = document.getElementById('result-section');
        this.resultDisplay = document.getElementById('result-display');
        this.emptyState = document.getElementById('empty-state');
        this.canvasLabel = document.getElementById('canvas-label');

        // Inputs
        this.inputQuantity = document.getElementById('input-quantity');
        this.inputPurchased = document.getElementById('input-purchased');
        this.calcYIS = document.getElementById('calc-yis');
        this.calcDays = document.getElementById('calc-days');
        this.btnEvaluate = document.getElementById('btn-evaluate');

        // Toolbar
        this.btnZoomIn = document.getElementById('btn-zoom-in');
        this.btnZoomOut = document.getElementById('btn-zoom-out');
        this.btnResetView = document.getElementById('btn-reset-view');
        this.btnFitView = document.getElementById('btn-fit-view');

        // Node detail panel
        this.detailPanel = document.getElementById('node-detail-panel');
        this.detailTitle = document.getElementById('detail-title');
        this.detailDescription = document.getElementById('detail-description');
        this.detailCondition = document.getElementById('detail-condition');
        this.closeDetail = document.getElementById('close-detail');

        // Zoom/pan state
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.isPanning = false;
        this.panStart = { x: 0, y: 0 };

        // Initialize
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateYISDisplay();
    }

    bindEvents() {
        // Vendor selection
        this.vendorSelect.addEventListener('change', () => this.onVendorChange());

        // Input changes
        this.inputQuantity.addEventListener('input', () => this.updateYISDisplay());
        this.inputPurchased.addEventListener('input', () => this.updateYISDisplay());

        // Evaluate button
        this.btnEvaluate.addEventListener('click', () => this.evaluatePath());

        // Toolbar buttons
        this.btnZoomIn.addEventListener('click', () => this.zoom(1.2));
        this.btnZoomOut.addEventListener('click', () => this.zoom(0.8));
        this.btnResetView.addEventListener('click', () => this.resetView());
        this.btnFitView.addEventListener('click', () => this.fitToView());

        // Close detail panel
        this.closeDetail.addEventListener('click', () => this.hideDetailPanel());

        // Pan/zoom on SVG
        this.svg.addEventListener('mousedown', (e) => this.startPan(e));
        this.svg.addEventListener('mousemove', (e) => this.pan(e));
        this.svg.addEventListener('mouseup', () => this.endPan());
        this.svg.addEventListener('mouseleave', () => this.endPan());
        this.svg.addEventListener('wheel', (e) => this.handleWheel(e));

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideDetailPanel();
            }
        });
    }

    // ========================================================================
    // VENDOR SELECTION
    // ========================================================================

    async onVendorChange() {
        const vendorId = this.vendorSelect.value;

        if (!vendorId) {
            this.hideAllSections();
            return;
        }

        try {
            // Fetch vendor details and resolved labels
            const [vendorsRes, labelsRes] = await Promise.all([
                fetch('/wiki/decision-tree/api/vendors'),
                fetch('/wiki/decision-tree/api/resolve-labels', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ vendor_id: vendorId })
                })
            ]);

            const vendorsData = await vendorsRes.json();
            const labelsData = await labelsRes.json();

            if (!vendorsData.success || !labelsData.success) {
                throw new Error('Failed to load vendor data');
            }

            this.currentVendor = vendorsData.vendor_details[vendorId];
            this.resolvedLabels = labelsData.labels;

            // Update UI
            this.displayVendorRules();
            this.showInputSection();
            this.renderTree();
            this.hideEmptyState();
            this.updateCanvasLabel();

        } catch (error) {
            console.error('Error loading vendor:', error);
            alert('Failed to load vendor configuration');
        }
    }

    displayVendorRules() {
        if (!this.currentVendor) return;

        const params = this.currentVendor.parameters || {};
        const tbody = this.rulesTable.querySelector('tbody');
        tbody.innerHTML = '';

        const paramLabels = {
            threshold_years: 'Order Threshold',
            target_years: 'Order Target',
            lean_threshold: 'Lean Alert',
            allow_cascade: 'Cascade Logic',
            rounding_multiple: 'Round To'
        };

        for (const [key, label] of Object.entries(paramLabels)) {
            if (params[key] === undefined) continue;

            const value = params[key];
            const tr = document.createElement('tr');

            let valueClass = 'rule-value';
            let displayValue = value;

            if (typeof value === 'boolean') {
                valueClass += value ? ' boolean-true' : ' boolean-false';
                displayValue = value ? 'Yes' : 'No';
            } else if (typeof value === 'number') {
                if (key.includes('years') || key.includes('threshold')) {
                    displayValue = `${value} years (${Math.round(value * 365)} days)`;
                }
            }

            tr.innerHTML = `
                <td>${label}</td>
                <td><span class="${valueClass}">${displayValue}</span></td>
            `;
            tbody.appendChild(tr);
        }

        this.rulesSection.style.display = 'block';
    }

    showInputSection() {
        this.inputsSection.style.display = 'block';
        this.resultSection.style.display = 'none';
    }

    hideAllSections() {
        this.rulesSection.style.display = 'none';
        this.inputsSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        this.clearTree();
        this.showEmptyState();
        this.canvasLabel.textContent = 'Select a vendor to begin';
    }

    hideEmptyState() {
        this.emptyState.classList.add('hidden');
    }

    showEmptyState() {
        this.emptyState.classList.remove('hidden');
    }

    updateCanvasLabel() {
        if (this.currentVendor) {
            this.canvasLabel.textContent = `${this.currentVendor.name} - Decision Tree`;
        }
    }

    // ========================================================================
    // YEARS IN STOCK CALCULATION
    // ========================================================================

    updateYISDisplay() {
        const quantity = parseFloat(this.inputQuantity.value) || 0;
        const purchased = parseFloat(this.inputPurchased.value) || 0;

        if (purchased > 0) {
            const yis = quantity / purchased;
            const days = Math.round(yis * 365);
            this.calcYIS.textContent = `${yis.toFixed(2)} years`;
            this.calcDays.textContent = `(${days} days)`;
        } else {
            this.calcYIS.textContent = '— years';
            this.calcDays.textContent = '(no sales)';
        }
    }

    // ========================================================================
    // PATH EVALUATION
    // ========================================================================

    async evaluatePath() {
        if (!this.currentVendor) {
            alert('Please select a vendor first');
            return;
        }

        const quantity = parseFloat(this.inputQuantity.value) || 0;
        const purchased = parseFloat(this.inputPurchased.value) || 0;

        this.btnEvaluate.disabled = true;
        this.btnEvaluate.innerHTML = '<span class="btn-icon">⏳</span> Evaluating...';

        try {
            const response = await fetch('/wiki/decision-tree/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vendor_id: this.vendorSelect.value,
                    inputs: {
                        quantity_in_stock: quantity,
                        purchased: purchased
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentPath = data.path || [];
                this.currentEdges = data.active_edges || [];
                this.highlightPath();
                this.displayResult(data);
            } else {
                throw new Error(data.error || 'Evaluation failed');
            }

        } catch (error) {
            console.error('Evaluation error:', error);
            alert('Failed to evaluate path: ' + error.message);
        } finally {
            this.btnEvaluate.disabled = false;
            this.btnEvaluate.innerHTML = '<span class="btn-icon">▶</span> Trace Path';
        }
    }

    displayResult(data) {
        this.resultSection.style.display = 'block';

        const result = data.result || {};
        const action = result.action || 'unknown';
        const quantity = data.reorder_quantity;

        this.resultDisplay.className = `result-box action-${action}`;

        let html = `
            <div class="result-action">${action.replace('_', ' ')}</div>
            <div class="result-title">${this.getActionTitle(action)}</div>
            <div class="result-reason">${result.reason || ''}</div>
        `;

        if (quantity !== null && quantity > 0) {
            html += `
                <div class="result-quantity">
                    <span class="result-quantity-label">Reorder Quantity:</span>
                    <span class="result-quantity-value">${quantity}</span>
                    <span class="result-quantity-unit">units</span>
                </div>
            `;
        }

        this.resultDisplay.innerHTML = html;

        // Scroll result into view
        this.resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    getActionTitle(action) {
        const titles = {
            none: 'No Reorder Needed',
            optional: 'Optional Reorder',
            order: 'Order Required',
            review: 'Manual Review',
            cascade_review: 'Check Cascade Options'
        };
        return titles[action] || action;
    }

    // ========================================================================
    // TREE RENDERING
    // ========================================================================

    renderTree() {
        this.clearTree();

        const tree = this.treeData.tree;
        if (!tree || !tree.nodes) return;

        // Render edges first (so they're behind nodes)
        for (const edge of (tree.edges || [])) {
            this.renderEdge(edge, tree.nodes);
        }

        // Render nodes
        for (const [nodeId, node] of Object.entries(tree.nodes)) {
            this.renderNode(nodeId, node);
        }
    }

    clearTree() {
        this.nodesLayer.innerHTML = '';
        this.edgesLayer.innerHTML = '';
        this.labelsLayer.innerHTML = '';
        this.currentPath = [];
        this.currentEdges = [];
    }

    renderNode(nodeId, node) {
        const { x, y } = node.position || { x: 400, y: 50 };
        const type = node.type || 'default';
        const label = this.resolvedLabels[nodeId] || node.label || nodeId;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', `node ${type}`);
        g.setAttribute('data-node-id', nodeId);
        g.setAttribute('transform', `translate(${x}, ${y})`);

        // Create shape based on type
        let shape;
        switch (type) {
            case 'start':
                shape = this.createRoundedRect(-60, -25, 120, 50, 25);
                break;
            case 'decision':
                shape = this.createDiamond(0, 0, 70, 45);
                break;
            case 'calculation':
                shape = this.createRect(-70, -25, 140, 50);
                break;
            case 'result':
                shape = this.createRoundedRect(-80, -30, 160, 60, 10);
                // Add result-specific class for coloring
                const action = node.result?.action || '';
                g.classList.add(`result-${action}`);
                break;
            default:
                shape = this.createRect(-60, -25, 120, 50);
        }

        shape.setAttribute('class', 'node-shape');
        shape.setAttribute('filter', 'url(#shadow)');
        g.appendChild(shape);

        // Add label
        const text = this.createNodeLabel(label, type);
        g.appendChild(text);

        // Add click handler
        g.addEventListener('click', () => this.showNodeDetail(nodeId, node));

        this.nodesLayer.appendChild(g);
    }

    createRect(x, y, width, height) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        return rect;
    }

    createRoundedRect(x, y, width, height, radius) {
        const rect = this.createRect(x, y, width, height);
        rect.setAttribute('rx', radius);
        rect.setAttribute('ry', radius);
        return rect;
    }

    createDiamond(cx, cy, width, height) {
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const points = [
            `${cx},${cy - height}`,
            `${cx + width},${cy}`,
            `${cx},${cy + height}`,
            `${cx - width},${cy}`
        ].join(' ');
        polygon.setAttribute('points', points);
        return polygon;
    }

    createNodeLabel(text, type) {
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('class', 'node-label');
        label.setAttribute('x', 0);
        label.setAttribute('y', 0);

        // Wrap long labels
        const maxChars = type === 'decision' ? 20 : 25;
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';

        for (const word of words) {
            const testLine = currentLine ? `${currentLine} ${word}` : word;
            if (testLine.length > maxChars && currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                currentLine = testLine;
            }
        }
        if (currentLine) lines.push(currentLine);

        // Create tspans for each line
        const lineHeight = 14;
        const startY = -((lines.length - 1) * lineHeight) / 2;

        lines.forEach((line, i) => {
            const tspan = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
            tspan.setAttribute('x', 0);
            tspan.setAttribute('dy', i === 0 ? startY : lineHeight);
            tspan.textContent = line;
            label.appendChild(tspan);
        });

        return label;
    }

    renderEdge(edge, nodes) {
        const fromNode = nodes[edge.from];
        const toNode = nodes[edge.to];
        if (!fromNode || !toNode) return;

        const fromPos = fromNode.position || { x: 400, y: 50 };
        const toPos = toNode.position || { x: 400, y: 150 };

        // Calculate control points for curved path
        const midY = (fromPos.y + toPos.y) / 2;

        // Adjust start/end points based on node type
        const fromOffset = this.getNodeOffset(fromNode.type, 'bottom');
        const toOffset = this.getNodeOffset(toNode.type, 'top');

        const startX = fromPos.x;
        const startY = fromPos.y + fromOffset;
        const endX = toPos.x;
        const endY = toPos.y - toOffset;

        // Create edge group
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'edge');
        g.setAttribute('data-edge-id', edge.id);

        // Create path
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = this.createEdgePath(startX, startY, endX, endY);
        path.setAttribute('d', d);
        path.setAttribute('class', 'edge-line');
        g.appendChild(path);

        // Add label if present
        const label = this.resolvedLabels[edge.id] || edge.label;
        if (label) {
            const labelX = (startX + endX) / 2;
            const labelY = (startY + endY) / 2 - 5;

            // Label background
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('class', 'edge-label-bg');

            // Label text
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'edge-label');
            text.setAttribute('x', labelX);
            text.setAttribute('y', labelY);
            text.textContent = label;

            g.appendChild(bg);
            g.appendChild(text);

            // Size background to text after render
            requestAnimationFrame(() => {
                const bbox = text.getBBox();
                bg.setAttribute('x', bbox.x - 4);
                bg.setAttribute('y', bbox.y - 2);
                bg.setAttribute('width', bbox.width + 8);
                bg.setAttribute('height', bbox.height + 4);
                bg.setAttribute('rx', 3);
            });
        }

        this.edgesLayer.appendChild(g);
    }

    getNodeOffset(type, direction) {
        const offsets = {
            start: { top: 25, bottom: 25 },
            decision: { top: 45, bottom: 45 },
            calculation: { top: 25, bottom: 25 },
            result: { top: 30, bottom: 30 }
        };
        return offsets[type]?.[direction] || 25;
    }

    createEdgePath(x1, y1, x2, y2) {
        // Simple vertical path with curve
        const midY = (y1 + y2) / 2;

        if (Math.abs(x1 - x2) < 10) {
            // Straight vertical line
            return `M ${x1} ${y1} L ${x2} ${y2}`;
        } else {
            // Curved path for non-vertical edges
            return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
        }
    }

    // ========================================================================
    // PATH HIGHLIGHTING
    // ========================================================================

    highlightPath() {
        // Reset all nodes and edges
        document.querySelectorAll('.node').forEach(node => {
            node.classList.remove('active', 'inactive');
            node.classList.add('inactive');
        });

        document.querySelectorAll('.edge').forEach(edge => {
            edge.classList.remove('active', 'inactive', 'animated');
            edge.classList.add('inactive');
        });

        // Highlight active nodes
        this.currentPath.forEach((nodeId, index) => {
            const node = document.querySelector(`.node[data-node-id="${nodeId}"]`);
            if (node) {
                node.classList.remove('inactive');
                node.classList.add('active');
            }
        });

        // Highlight active edges with animation
        this.currentEdges.forEach((edgeId, index) => {
            const edge = document.querySelector(`.edge[data-edge-id="${edgeId}"]`);
            if (edge) {
                edge.classList.remove('inactive');
                edge.classList.add('active', 'animated');
            }
        });
    }

    // ========================================================================
    // NODE DETAIL PANEL
    // ========================================================================

    showNodeDetail(nodeId, node) {
        const resolvedLabel = this.resolvedLabels[nodeId] || node.label;
        const resolvedDesc = this.resolvedLabels[`${nodeId}_desc`] || node.description;

        this.detailTitle.textContent = resolvedLabel;
        this.detailDescription.textContent = resolvedDesc;

        // Show condition if present
        if (node.condition) {
            const cond = node.condition;
            const field = cond.field;
            const operator = cond.operator;
            const value = this.resolveValue(cond.value);

            this.detailCondition.innerHTML = `
                <span class="condition-field">${field}</span>
                <span class="condition-operator">${operator}</span>
                <span class="condition-value">${value}</span>
            `;
            this.detailCondition.style.display = 'block';
        } else if (node.formula) {
            this.detailCondition.innerHTML = `
                <strong>Formula:</strong> ${node.formula}
            `;
            this.detailCondition.style.display = 'block';
        } else {
            this.detailCondition.style.display = 'none';
        }

        this.detailPanel.style.display = 'block';
    }

    hideDetailPanel() {
        this.detailPanel.style.display = 'none';
    }

    resolveValue(value) {
        if (typeof value === 'string' && value.startsWith('{') && value.endsWith('}')) {
            const key = value.slice(1, -1);
            if (this.currentVendor?.parameters?.[key] !== undefined) {
                return this.currentVendor.parameters[key];
            }
        }
        return value;
    }

    // ========================================================================
    // ZOOM & PAN
    // ========================================================================

    zoom(factor) {
        this.scale *= factor;
        this.scale = Math.max(0.3, Math.min(3, this.scale));
        this.updateTransform();
    }

    resetView() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }

    fitToView() {
        // Reset to fit entire tree
        this.scale = 0.9;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }

    updateTransform() {
        const transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
        this.nodesLayer.style.transform = transform;
        this.edgesLayer.style.transform = transform;
        this.labelsLayer.style.transform = transform;

        // Also update SVG viewBox for proper scaling
        const container = document.getElementById('canvas-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Adjust viewBox based on scale
        const vbWidth = 900 / this.scale;
        const vbHeight = 950 / this.scale;
        const vbX = (900 - vbWidth) / 2 - this.translateX / this.scale;
        const vbY = (950 - vbHeight) / 2 - this.translateY / this.scale;

        this.svg.setAttribute('viewBox', `${vbX} ${vbY} ${vbWidth} ${vbHeight}`);
    }

    startPan(e) {
        if (e.button !== 0) return; // Left click only
        this.isPanning = true;
        this.panStart = { x: e.clientX, y: e.clientY };
        this.svg.style.cursor = 'grabbing';
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
        this.svg.style.cursor = 'grab';
    }

    handleWheel(e) {
        e.preventDefault();
        const factor = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom(factor);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.decisionTreeVisualizer = new DecisionTreeVisualizer();
});
