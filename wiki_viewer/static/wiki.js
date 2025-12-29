/**
 * Wiki Viewer - Interactive Diagram-Text Linking
 *
 * Features:
 * - Bidirectional linking (Mermaid node ↔ text section)
 * - Color-coded highlighting
 * - Tooltip previews
 * - Admin mode for creating mappings
 */

class WikiViewer {
    constructor() {
        this.mappings = [];
        this.adminMode = false;
        this.selectedNode = null;
        this.selectedSection = null;
        this.currentTooltip = null;

        this.init();
    }

    init() {
        // Load mappings from embedded JSON
        const mappingsEl = document.getElementById('mappings-data');
        if (mappingsEl) {
            try {
                this.mappings = JSON.parse(mappingsEl.textContent);
            } catch (e) {
                console.error('Failed to parse mappings:', e);
                this.mappings = [];
            }
        }

        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }
        });

        // Wait for Mermaid to render, then apply mappings
        setTimeout(() => {
            this.applyMappings();
            this.attachEventHandlers();
        }, 500);

        // Admin mode toggle
        const adminToggle = document.getElementById('admin-mode-toggle');
        if (adminToggle) {
            adminToggle.addEventListener('change', (e) => {
                this.toggleAdminMode(e.target.checked);
            });
        }
    }

    // =========================================================================
    // MAPPING APPLICATION
    // =========================================================================

    applyMappings() {
        /**
         * Apply color highlighting to mapped nodes and sections
         */
        console.log(`Applying ${this.mappings.length} mappings...`);

        this.mappings.forEach(mapping => {
            // Highlight Mermaid node
            this.highlightNode(mapping);

            // Highlight text section
            this.highlightSection(mapping);
        });
    }

    highlightNode(mapping) {
        /**
         * Apply color to Mermaid node
         */
        // Try different selector patterns (Mermaid generates IDs in various formats)
        const selectors = [
            `g[id*="flowchart-${mapping.node_id}-"]`,
            `g[id*="${mapping.node_id}"]`,
            `g[id="flowchart-${mapping.node_id}"]`
        ];

        let nodeEl = null;
        for (const selector of selectors) {
            nodeEl = document.querySelector(selector);
            if (nodeEl) break;
        }

        if (nodeEl) {
            // Apply color to node shape (rect, circle, or polygon)
            const shapeEl = nodeEl.querySelector('rect, circle, polygon');
            if (shapeEl) {
                shapeEl.style.fill = mapping.color;
                shapeEl.style.fillOpacity = '0.3';
                shapeEl.style.cursor = 'pointer';

                // Add data attributes for linking
                nodeEl.setAttribute('data-mapping-id', mapping.id);
                nodeEl.setAttribute('data-section-id', mapping.section_id);
                nodeEl.setAttribute('data-color', mapping.color);
            }
        } else {
            console.warn(`Node not found: ${mapping.node_id}`);
        }
    }

    highlightSection(mapping) {
        /**
         * Apply colored border to text section
         */
        const sectionEl = document.getElementById(mapping.section_id);
        if (sectionEl) {
            sectionEl.style.borderLeft = `4px solid ${mapping.color}`;
            sectionEl.style.paddingLeft = '12px';
            sectionEl.style.cursor = 'pointer';

            // Add data attributes for reverse linking
            sectionEl.setAttribute('data-mapping-id', mapping.id);
            sectionEl.setAttribute('data-node-id', mapping.node_id);
            sectionEl.setAttribute('data-color', mapping.color);
        } else {
            console.warn(`Section not found: ${mapping.section_id}`);
        }
    }

    // =========================================================================
    // EVENT HANDLERS (Normal Mode)
    // =========================================================================

    attachEventHandlers() {
        /**
         * Attach click and hover handlers for bidirectional linking
         */
        this.mappings.forEach(mapping => {
            // Node clicks
            this.attachNodeHandlers(mapping);

            // Section clicks
            this.attachSectionHandlers(mapping);
        });
    }

    attachNodeHandlers(mapping) {
        /**
         * Attach click and hover handlers to Mermaid node
         */
        const selectors = [
            `g[id*="flowchart-${mapping.node_id}-"]`,
            `g[id*="${mapping.node_id}"]`
        ];

        let nodeEl = null;
        for (const selector of selectors) {
            nodeEl = document.querySelector(selector);
            if (nodeEl) break;
        }

        if (nodeEl) {
            // Click handler
            nodeEl.addEventListener('click', (e) => {
                if (!this.adminMode) {
                    e.stopPropagation();
                    this.handleNodeClick(mapping);
                }
            });

            // Hover tooltip
            nodeEl.addEventListener('mouseenter', (e) => {
                if (!this.adminMode) {
                    this.showTooltip(e, mapping);
                }
            });

            nodeEl.addEventListener('mouseleave', () => {
                if (!this.adminMode) {
                    this.hideTooltip();
                }
            });
        }
    }

    attachSectionHandlers(mapping) {
        /**
         * Attach click handler to text section
         */
        const sectionEl = document.getElementById(mapping.section_id);

        if (sectionEl) {
            sectionEl.addEventListener('click', (e) => {
                if (!this.adminMode) {
                    e.stopPropagation();
                    this.handleSectionClick(mapping);
                }
            });
        }
    }

    handleNodeClick(mapping) {
        /**
         * When user clicks Mermaid node:
         * 1. Scroll to corresponding text section
         * 2. Highlight section temporarily (pulse effect)
         * 3. Show persistent tooltip
         */
        const sectionEl = document.getElementById(mapping.section_id);
        if (!sectionEl) return;

        // Smooth scroll to section
        sectionEl.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        // Pulse animation
        sectionEl.classList.add('pulse-highlight');
        setTimeout(() => {
            sectionEl.classList.remove('pulse-highlight');
        }, 2000);

        // Show persistent tooltip
        this.showPersistentTooltip(sectionEl, mapping);
    }

    handleSectionClick(mapping) {
        /**
         * When user clicks text section:
         * 1. Scroll to corresponding Mermaid diagram
         * 2. Highlight node temporarily (pulse effect)
         */
        const selectors = [
            `g[id*="flowchart-${mapping.node_id}-"]`,
            `g[id*="${mapping.node_id}"]`
        ];

        let nodeEl = null;
        for (const selector of selectors) {
            nodeEl = document.querySelector(selector);
            if (nodeEl) break;
        }

        if (!nodeEl) return;

        // Scroll diagram into view
        const diagramContainer = nodeEl.closest('.mermaid');
        if (diagramContainer) {
            diagramContainer.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }

        // Pulse animation on node
        const shapeEl = nodeEl.querySelector('rect, circle, polygon');
        if (shapeEl) {
            // Store original fill
            const originalFill = shapeEl.style.fill;
            const originalOpacity = shapeEl.style.fillOpacity;

            // Animate
            shapeEl.style.fill = mapping.color;
            shapeEl.style.fillOpacity = '0.8';

            setTimeout(() => {
                shapeEl.style.fill = originalFill;
                shapeEl.style.fillOpacity = originalOpacity;
            }, 2000);
        }
    }

    // =========================================================================
    // TOOLTIP SYSTEM
    // =========================================================================

    showTooltip(event, mapping) {
        /**
         * Show hover tooltip with preview text
         */
        const tooltip = document.createElement('div');
        tooltip.className = 'wiki-tooltip';
        tooltip.innerHTML = `
            <strong>${mapping.label}</strong>
            <p>${mapping.preview_text}</p>
            <span class="tooltip-hint">Click to navigate →</span>
        `;

        // Position near cursor
        tooltip.style.left = `${event.pageX + 15}px`;
        tooltip.style.top = `${event.pageY + 15}px`;

        // Smart positioning (flip if near edge)
        document.body.appendChild(tooltip);

        const rect = tooltip.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            tooltip.style.left = `${event.pageX - rect.width - 15}px`;
        }
        if (rect.bottom > window.innerHeight) {
            tooltip.style.top = `${event.pageY - rect.height - 15}px`;
        }

        this.currentTooltip = tooltip;
    }

    hideTooltip() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    }

    showPersistentTooltip(anchorEl, mapping) {
        /**
         * Show tooltip that stays until user clicks elsewhere
         */
        // Remove any existing persistent tooltip
        const existing = document.querySelector('.wiki-tooltip-persistent');
        if (existing) existing.remove();

        const tooltip = document.createElement('div');
        tooltip.className = 'wiki-tooltip wiki-tooltip-persistent';
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <strong>${mapping.label}</strong>
                <button class="tooltip-close">&times;</button>
            </div>
            <p>${mapping.preview_text}</p>
        `;

        // Position below section heading
        const rect = anchorEl.getBoundingClientRect();
        tooltip.style.left = `${rect.left + window.scrollX}px`;
        tooltip.style.top = `${rect.bottom + window.scrollY + 10}px`;

        document.body.appendChild(tooltip);

        // Close button
        tooltip.querySelector('.tooltip-close').addEventListener('click', () => {
            tooltip.remove();
        });

        // Click outside to close
        setTimeout(() => {
            const closeOnClick = (e) => {
                if (!tooltip.contains(e.target) && e.target !== anchorEl) {
                    tooltip.remove();
                    document.removeEventListener('click', closeOnClick);
                }
            };
            document.addEventListener('click', closeOnClick);
        }, 100);
    }

    // =========================================================================
    // ADMIN MODE
    // =========================================================================

    toggleAdminMode(enabled) {
        this.adminMode = enabled;

        if (enabled) {
            document.body.classList.add('admin-mode-active');
            this.initAdminMode();
        } else {
            document.body.classList.remove('admin-mode-active');
            this.exitAdminMode();
        }
    }

    initAdminMode() {
        /**
         * Enter admin mode: Show banner and attach admin handlers
         */
        // Show instructions banner
        const banner = document.createElement('div');
        banner.className = 'admin-banner';
        banner.innerHTML = `
            <p><strong>Admin Mode Active</strong></p>
            <p id="admin-instruction">Step 1: Click a Mermaid node to select it</p>
            <button id="cancel-admin">Exit Admin Mode</button>
        `;
        document.body.insertBefore(banner, document.body.firstChild);

        document.getElementById('cancel-admin').addEventListener('click', () => {
            document.getElementById('admin-mode-toggle').checked = false;
            this.toggleAdminMode(false);
        });

        // Attach admin click handlers
        this.attachAdminHandlers();
    }

    attachAdminHandlers() {
        /**
         * Attach click handlers for mapping creation
         */
        // All Mermaid nodes
        const allNodes = document.querySelectorAll('.mermaid g[id]');
        allNodes.forEach(nodeEl => {
            // Remove normal mode handlers (stop propagation)
            const newNode = nodeEl.cloneNode(true);
            nodeEl.parentNode.replaceChild(newNode, nodeEl);

            newNode.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectNodeForMapping(newNode);
            });
        });

        // All section headings
        const allSections = document.querySelectorAll('h2[id], h3[id], h4[id]');
        allSections.forEach(sectionEl => {
            // Create new element to remove existing handlers
            const newSection = sectionEl.cloneNode(true);
            sectionEl.parentNode.replaceChild(newSection, sectionEl);

            newSection.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectSectionForMapping(newSection);
            });
        });
    }

    selectNodeForMapping(nodeEl) {
        /**
         * Step 1: User clicks Mermaid node in admin mode
         */
        // Clear previous selection
        const prevSelected = document.querySelector('.admin-selected-node');
        if (prevSelected) {
            prevSelected.classList.remove('admin-selected-node');
        }

        // Mark as selected
        nodeEl.classList.add('admin-selected-node');

        // Extract node ID from SVG element
        const nodeId = this.extractNodeId(nodeEl);

        // Find diagram ID
        const diagramEl = nodeEl.closest('.mermaid');
        const diagramId = diagramEl ? diagramEl.getAttribute('data-diagram-id') : 'diagram_0';

        this.selectedNode = {
            element: nodeEl,
            nodeId: nodeId,
            diagramId: diagramId
        };

        // Update banner
        const instruction = document.getElementById('admin-instruction');
        if (instruction) {
            instruction.innerHTML = `<strong>Step 2:</strong> Click a text section heading to link to node "<strong>${nodeId}</strong>"`;
        }

        console.log('Selected node:', nodeId);
    }

    selectSectionForMapping(sectionEl) {
        /**
         * Step 2: User clicks text section in admin mode
         */
        if (!this.selectedNode) {
            alert('Please select a Mermaid node first (Step 1)');
            return;
        }

        // Clear previous selection
        const prevSelected = document.querySelector('.admin-selected-section');
        if (prevSelected) {
            prevSelected.classList.remove('admin-selected-section');
        }

        // Mark as selected
        sectionEl.classList.add('admin-selected-section');

        this.selectedSection = {
            element: sectionEl,
            sectionId: sectionEl.getAttribute('id'),
            text: sectionEl.textContent
        };

        console.log('Selected section:', this.selectedSection.sectionId);

        // Show confirmation dialog
        this.showMappingConfirmation();
    }

    async showMappingConfirmation() {
        /**
         * Step 3: Show confirmation dialog for mapping creation
         */
        const filePath = document.querySelector('.wiki-content').getAttribute('data-file-path');

        // Suggest next color
        const response = await fetch(`/wiki/api/suggest-color?file=${encodeURIComponent(filePath)}`);
        const data = await response.json();
        const suggestedColor = data.color;

        const modal = document.createElement('div');
        modal.className = 'admin-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Create Mapping</h3>
                <table>
                    <tr>
                        <td><strong>Node:</strong></td>
                        <td>${this.selectedNode.nodeId}</td>
                    </tr>
                    <tr>
                        <td><strong>Section:</strong></td>
                        <td>${this.selectedSection.text}</td>
                    </tr>
                    <tr>
                        <td><strong>Color:</strong></td>
                        <td>
                            <input type="color" id="mapping-color" value="${suggestedColor}" />
                        </td>
                    </tr>
                    <tr>
                        <td><strong>Label:</strong></td>
                        <td>
                            <input type="text" id="mapping-label" value="${this.selectedSection.text}" maxlength="50" />
                        </td>
                    </tr>
                </table>
                <div class="modal-actions">
                    <button id="confirm-mapping" class="btn-primary">Create Mapping</button>
                    <button id="cancel-mapping" class="btn-secondary">Cancel</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Confirm button
        document.getElementById('confirm-mapping').addEventListener('click', async () => {
            await this.saveMappingAPI();
            modal.remove();
        });

        // Cancel button
        document.getElementById('cancel-mapping').addEventListener('click', () => {
            modal.remove();
            this.clearSelections();
        });
    }

    async saveMappingAPI() {
        /**
         * POST new mapping to backend API
         */
        const filePath = document.querySelector('.wiki-content').getAttribute('data-file-path');
        const color = document.getElementById('mapping-color').value;
        const label = document.getElementById('mapping-label').value;

        // Extract preview text from section (next paragraph after heading)
        let previewText = '';
        let nextEl = this.selectedSection.element.nextElementSibling;
        if (nextEl) {
            previewText = nextEl.textContent.substring(0, 200).trim();
            if (previewText.length === 200) {
                previewText += '...';
            }
        }

        const mapping = {
            diagram_id: this.selectedNode.diagramId,
            node_id: this.selectedNode.nodeId,
            section_id: this.selectedSection.sectionId,
            color: color,
            label: label,
            preview_text: previewText
        };

        try {
            const response = await fetch(`/wiki/api/mappings/${filePath}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(mapping)
            });

            const result = await response.json();

            if (result.success) {
                alert(`Mapping created successfully!\n\nMapping ID: ${result.mapping_id}\n\nRefresh the page to see the mapping in action.`);

                // Clear selections
                this.clearSelections();

                // Optionally reload page
                if (confirm('Reload page now to see the new mapping?')) {
                    window.location.reload();
                }
            } else {
                alert('Failed to create mapping: ' + result.error);
            }
        } catch (error) {
            alert('Error saving mapping: ' + error.message);
            console.error('Mapping save error:', error);
        }
    }

    extractNodeId(nodeEl) {
        /**
         * Extract node ID from SVG element ID
         * Example: "flowchart-B-123" → "B"
         */
        const id = nodeEl.getAttribute('id');

        // Try pattern: flowchart-XXX-123
        let match = id.match(/flowchart-([A-Za-z0-9]+)-/);
        if (match) return match[1];

        // Try pattern: XXX-123
        match = id.match(/^([A-Za-z0-9]+)-/);
        if (match) return match[1];

        // Fallback: return full ID
        return id;
    }

    clearSelections() {
        this.selectedNode = null;
        this.selectedSection = null;

        const selected = document.querySelectorAll('.admin-selected-node, .admin-selected-section');
        selected.forEach(el => {
            el.classList.remove('admin-selected-node', 'admin-selected-section');
        });

        // Reset instruction
        const instruction = document.getElementById('admin-instruction');
        if (instruction) {
            instruction.innerHTML = 'Step 1: Click a Mermaid node to select it';
        }
    }

    exitAdminMode() {
        // Remove banner
        const banner = document.querySelector('.admin-banner');
        if (banner) banner.remove();

        // Clear selections
        this.clearSelections();

        // Reattach normal mode handlers
        this.attachEventHandlers();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on a wiki file page (has markdown content)
    if (document.getElementById('markdown-content')) {
        window.wikiViewer = new WikiViewer();
        console.log('Wiki Viewer initialized');
    }
});
