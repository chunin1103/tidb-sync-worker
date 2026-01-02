/**
 * Decision Tree Visualizer - Clean Minimal Design
 * Matches the React prototype interaction
 */

class DecisionTreeApp {
    constructor() {
        // Data from global window objects
        this.masterLogic = window.MASTER_LOGIC || { nodes: [], edges: [] };
        this.vendors = window.VENDORS || {};

        // State
        this.currentVendor = null;
        this.currentVendorId = null;
        this.simData = {
            yearsInStock: 0.15,
            hasLargerSheets: true
        };
        this.activePath = new Set();

        // Cache elements
        this.cacheElements();

        // Initialize editors with data
        this.initEditors();

        // Bind events
        this.bindEvents();

        // Render initial tree
        this.renderTree();
    }

    cacheElements() {
        // Mode tabs
        this.modeTabs = document.querySelectorAll('.mode-tab');
        this.views = {
            simulation: document.getElementById('simulation-view'),
            logic_editor: document.getElementById('logic-view'),
            vendor_editor: document.getElementById('vendor-view')
        };

        // Vendor grid
        this.vendorGrid = document.getElementById('vendor-grid');
        this.vendorBtns = document.querySelectorAll('.vendor-btn');

        // Rules section
        this.rulesSection = document.getElementById('rules-section');
        this.activeVendorName = document.getElementById('active-vendor-name');
        this.ruleThreshold = document.getElementById('rule-threshold');
        this.ruleCascade = document.getElementById('rule-cascade');

        // Inputs section
        this.inputsSection = document.getElementById('inputs-section');
        this.yisSlider = document.getElementById('yis-slider');
        this.yisValue = document.getElementById('yis-value');
        this.cascadeToggle = document.getElementById('cascade-toggle');

        // SVG
        this.treeSvg = document.getElementById('tree-svg');
        this.edgesLayer = document.getElementById('edges-layer');
        this.nodesLayer = document.getElementById('nodes-layer');

        // Editors
        this.logicEditor = document.getElementById('logic-editor');
        this.vendorEditor = document.getElementById('vendor-editor');
        this.btnApplyLogic = document.getElementById('btn-apply-logic');
        this.btnApplyVendors = document.getElementById('btn-apply-vendors');
        this.logicError = document.getElementById('logic-error');
        this.vendorError = document.getElementById('vendor-error');
    }

    initEditors() {
        if (this.logicEditor) {
            this.logicEditor.value = JSON.stringify(this.masterLogic, null, 2);
        }
        if (this.vendorEditor) {
            this.vendorEditor.value = JSON.stringify(this.vendors, null, 2);
        }
    }

    bindEvents() {
        // Mode tabs
        this.modeTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchMode(tab.dataset.mode));
        });

        // Vendor selection
        this.vendorBtns.forEach(btn => {
            btn.addEventListener('click', () => this.selectVendor(btn.dataset.vendorId));
        });

        // Slider
        if (this.yisSlider) {
            this.yisSlider.addEventListener('input', () => this.onSliderChange());
        }

        // Toggle
        if (this.cascadeToggle) {
            this.cascadeToggle.addEventListener('click', () => this.onToggleChange());
        }

        // Apply buttons
        if (this.btnApplyLogic) {
            this.btnApplyLogic.addEventListener('click', () => this.applyLogic());
        }
        if (this.btnApplyVendors) {
            this.btnApplyVendors.addEventListener('click', () => this.applyVendors());
        }
    }

    // ========================================================================
    // MODE SWITCHING
    // ========================================================================

    switchMode(mode) {
        // Update tabs
        this.modeTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.mode === mode);
        });

        // Show/hide views
        Object.entries(this.views).forEach(([key, view]) => {
            if (view) {
                view.classList.toggle('active', key === mode);
            }
        });
    }

    // ========================================================================
    // VENDOR SELECTION
    // ========================================================================

    selectVendor(vendorId) {
        // Update buttons
        this.vendorBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.vendorId === vendorId);
        });

        this.currentVendorId = vendorId;
        this.currentVendor = this.vendors[vendorId];

        if (!this.currentVendor) return;

        // Show rules section
        if (this.rulesSection) {
            this.rulesSection.style.display = 'block';
        }

        // Update rules display
        if (this.activeVendorName) {
            this.activeVendorName.textContent = this.currentVendor.name || vendorId;
        }
        if (this.ruleThreshold) {
            this.ruleThreshold.textContent = `${this.currentVendor.threshold_years} yrs`;
        }
        if (this.ruleCascade) {
            this.ruleCascade.textContent = this.currentVendor.allow_cascade ? 'YES' : 'NO';
            this.ruleCascade.className = 'rule-value ' + (this.currentVendor.allow_cascade ? 'success' : 'danger');
        }

        // Show inputs section
        if (this.inputsSection) {
            this.inputsSection.style.display = 'block';
        }

        // Recalculate path
        this.calculatePath();
        this.renderTree();
    }

    // ========================================================================
    // INPUT HANDLING
    // ========================================================================

    onSliderChange() {
        const value = parseFloat(this.yisSlider.value);
        this.simData.yearsInStock = value;

        // Update display
        if (this.yisValue) {
            this.yisValue.textContent = value.toFixed(2);
            // Color based on threshold
            if (this.currentVendor) {
                const isLow = value < this.currentVendor.threshold_years;
                this.yisValue.className = 'input-value' + (isLow ? ' warning' : '');
            }
        }

        // Recalculate
        this.calculatePath();
        this.renderTree();
    }

    onToggleChange() {
        this.simData.hasLargerSheets = !this.simData.hasLargerSheets;

        // Update UI
        if (this.cascadeToggle) {
            this.cascadeToggle.classList.toggle('active', this.simData.hasLargerSheets);
        }

        // Recalculate
        this.calculatePath();
        this.renderTree();
    }

    // ========================================================================
    // PATH CALCULATION
    // ========================================================================

    calculatePath() {
        this.activePath = new Set();

        if (!this.currentVendor) return;

        let currentNodeId = 'start';
        let steps = 0;

        while (currentNodeId && steps < 50) {
            this.activePath.add(currentNodeId);
            steps++;

            // Find matching edge
            const edge = this.masterLogic.edges.find(e =>
                e.from === currentNodeId && this.evaluateCondition(e.condition)
            );

            currentNodeId = edge ? edge.to : null;
        }
    }

    evaluateCondition(condition) {
        if (!condition) return true;

        // Complex logic handlers
        if (condition.complex_logic === 'cascade_check') {
            return this.currentVendor.allow_cascade && this.simData.hasLargerSheets;
        }
        if (condition.complex_logic === 'fallback') {
            return !this.currentVendor.allow_cascade || !this.simData.hasLargerSheets;
        }

        // Field comparison
        if (condition.field) {
            const val = this.simData[condition.field];
            let target = condition.value;

            // Resolve placeholder
            if (typeof target === 'string' && target.startsWith('{') && target.endsWith('}')) {
                const key = target.slice(1, -1);
                target = this.currentVendor[key];
            }

            switch (condition.operator) {
                case '>=': return val >= target;
                case '>': return val > target;
                case '<=': return val <= target;
                case '<': return val < target;
                case '==': return val == target;
                case '!=': return val != target;
            }
        }

        return false;
    }

    // ========================================================================
    // TREE RENDERING
    // ========================================================================

    renderTree() {
        // Clear
        this.edgesLayer.innerHTML = '';
        this.nodesLayer.innerHTML = '';

        // Render edges first
        this.masterLogic.edges.forEach(edge => this.renderEdge(edge));

        // Render nodes
        this.masterLogic.nodes.forEach(node => this.renderNode(node));
    }

    renderNode(node) {
        const x = (node.x / 100) * 800;
        const y = (node.y / 100) * 600;
        const isActive = this.activePath.has(node.id);

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'node-group');
        g.setAttribute('transform', `translate(${x}, ${y})`);

        // Icon background
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', '-24');
        rect.setAttribute('y', '-24');
        rect.setAttribute('width', '48');
        rect.setAttribute('height', '48');
        rect.setAttribute('rx', '12');
        rect.setAttribute('fill', isActive ? '#4f46e5' : 'white');
        rect.setAttribute('stroke', isActive ? '#4f46e5' : '#e2e8f0');
        rect.setAttribute('stroke-width', '2');

        // Icon
        const icon = this.getNodeIcon(node.type, isActive);

        // Label background
        const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const labelWidth = Math.min(node.label.length * 7 + 16, 160);
        labelBg.setAttribute('x', -labelWidth / 2);
        labelBg.setAttribute('y', '32');
        labelBg.setAttribute('width', labelWidth);
        labelBg.setAttribute('height', '24');
        labelBg.setAttribute('rx', '4');
        labelBg.setAttribute('fill', isActive ? 'white' : '#f8fafc');
        labelBg.setAttribute('stroke', isActive ? '#c7d2fe' : '#f1f5f9');

        // Label text
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('class', 'node-label-text' + (isActive ? ' active' : ''));
        label.setAttribute('y', '48');
        label.textContent = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;

        g.appendChild(rect);
        g.appendChild(icon);
        g.appendChild(labelBg);
        g.appendChild(label);

        this.nodesLayer.appendChild(g);
    }

    getNodeIcon(type, isActive) {
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', isActive ? 'white' : '#cbd5e1');
        icon.setAttribute('stroke-width', '2');
        icon.setAttribute('stroke-linecap', 'round');
        icon.setAttribute('stroke-linejoin', 'round');

        let path;
        switch (type) {
            case 'start':
                // Database icon
                path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', 'M-8 -8 L-8 8 M8 -8 L8 8 M-8 -8 Q0 -14 8 -8 M-8 8 Q0 14 8 8 M-8 0 Q0 6 8 0');
                break;
            case 'decision':
                // Activity icon
                path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', 'M-8 0 L-2 -8 L4 4 L10 -4');
                break;
            case 'end':
                // Check circle icon
                path = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', '0');
                circle.setAttribute('cy', '0');
                circle.setAttribute('r', '10');
                const check = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                check.setAttribute('d', 'M-4 0 L-1 3 L5 -3');
                path.appendChild(circle);
                path.appendChild(check);
                break;
            default:
                path = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                path.setAttribute('x', '-8');
                path.setAttribute('y', '-8');
                path.setAttribute('width', '16');
                path.setAttribute('height', '16');
                path.setAttribute('rx', '2');
        }

        icon.appendChild(path);
        return icon;
    }

    renderEdge(edge) {
        const fromNode = this.masterLogic.nodes.find(n => n.id === edge.from);
        const toNode = this.masterLogic.nodes.find(n => n.id === edge.to);

        if (!fromNode || !toNode) return;

        const fromX = (fromNode.x / 100) * 800;
        const fromY = (fromNode.y / 100) * 600;
        const toX = (toNode.x / 100) * 800;
        const toY = (toNode.y / 100) * 600;

        const isActive = this.activePath.has(edge.from) && this.activePath.has(edge.to);

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        // Line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('class', 'edge-line' + (isActive ? ' active' : ''));
        line.setAttribute('x1', fromX);
        line.setAttribute('y1', fromY + 24);
        line.setAttribute('x2', toX);
        line.setAttribute('y2', toY - 24);
        line.setAttribute('marker-end', isActive ? 'url(#arrow-active)' : 'url(#arrow-inactive)');

        g.appendChild(line);

        // Label
        if (edge.label) {
            const midX = (fromX + toX) / 2;
            const midY = (fromY + toY) / 2 + 10;

            // Resolve placeholders in label
            let labelText = edge.label;
            if (this.currentVendor && isActive) {
                labelText = labelText.replace('{threshold_years}', this.currentVendor.threshold_years);
            }

            const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            const textWidth = Math.min(labelText.length * 5 + 12, 200);
            labelBg.setAttribute('class', 'edge-label-bg');
            labelBg.setAttribute('x', midX - textWidth / 2);
            labelBg.setAttribute('y', midY - 8);
            labelBg.setAttribute('width', textWidth);
            labelBg.setAttribute('height', '16');
            labelBg.setAttribute('rx', '3');

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'edge-label-text' + (isActive ? ' active' : ''));
            text.setAttribute('x', midX);
            text.setAttribute('y', midY + 3);
            text.textContent = labelText.length > 30 ? labelText.slice(0, 28) + '...' : labelText;

            g.appendChild(labelBg);
            g.appendChild(text);
        }

        this.edgesLayer.appendChild(g);
    }

    // ========================================================================
    // EDITOR APPLY
    // ========================================================================

    applyLogic() {
        try {
            const newLogic = JSON.parse(this.logicEditor.value);
            this.masterLogic = newLogic;
            window.MASTER_LOGIC = newLogic;

            // Hide error
            if (this.logicError) this.logicError.style.display = 'none';

            // Recalculate and switch to simulation
            this.calculatePath();
            this.renderTree();
            this.switchMode('simulation');
        } catch (e) {
            if (this.logicError) {
                this.logicError.textContent = 'Invalid JSON: ' + e.message;
                this.logicError.style.display = 'flex';
            }
        }
    }

    applyVendors() {
        try {
            const newVendors = JSON.parse(this.vendorEditor.value);
            this.vendors = newVendors;
            window.VENDORS = newVendors;

            // Update current vendor if selected
            if (this.currentVendorId && this.vendors[this.currentVendorId]) {
                this.currentVendor = this.vendors[this.currentVendorId];
            }

            // Hide error
            if (this.vendorError) this.vendorError.style.display = 'none';

            // Recalculate and switch to simulation
            this.calculatePath();
            this.renderTree();
            this.switchMode('simulation');
        } catch (e) {
            if (this.vendorError) {
                this.vendorError.textContent = 'Invalid JSON: ' + e.message;
                this.vendorError.style.display = 'flex';
            }
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DecisionTreeApp();
});
