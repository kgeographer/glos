// TMI Browse Module - handles hierarchical TMI navigation
// static/js/tmi-browse.js

class TMIBrowser {
    constructor() {
        this.currentPath = []; // Track navigation path
        this.navigationHistory = []; // For back button
    }

    // Initialize TMI categories
    loadTMICategories() {
        console.log("Loading TMI categories...");
        const hierarchyDiv = document.getElementById('tmiHierarchy');
        
        if (!hierarchyDiv) {
            console.error("tmiHierarchy element not found");
            return;
        }

        hierarchyDiv.innerHTML = '<p class="text-muted">Loading TMI categories...</p>';

        fetch('/get_tmi_categories')
            .then(response => response.json())
            .then(data => {
                console.log('TMI categories received:', data.length, 'categories');
                this.displayCategories(data);
            })
            .catch(error => {
                console.error('Error loading TMI categories:', error);
                hierarchyDiv.innerHTML = '<p class="text-danger">Error loading motif categories</p>';
            });
    }

    // Display top-level categories
    displayCategories(categories) {
        const hierarchyDiv = document.getElementById('tmiHierarchy');
        
        let html = '<div class="tmi-navigation">';
        // html += '<h6>TMI Categories</h6>';
        html += '<div class="list-group">';

        categories.forEach(category => {
            html += `
                <div class="motif-category-item list-group-item d-flex justify-content-between align-items-center"
                     onclick="tmiBrowser.navigateToNode('${category.category}', '${category.description}')">
                    <div>
                        <strong>${category.category}:</strong> ${category.description}
                    </div>
                    <span class="badge bg-primary rounded-pill">${category.connected_count} of ${category.total_count}</span>
                </div>`;
        });

        html += '</div></div>';
        hierarchyDiv.innerHTML = html;
        
        // Clear results when at category level
        this.clearResults();
        this.currentPath = [];
    }


    // Navigate to any TMI node with smart path management
    navigateToNode(nodeId, nodeLabel) {
        console.log(`Navigating to node: ${nodeId} (${nodeLabel})`);
        console.log(`Current path before navigation:`, this.currentPath.map(p => p.nodeId));

        // Smart path cleanup based on navigation target
        const existingIndex = this.currentPath.findIndex(p => p.nodeId === nodeId);

        if (existingIndex !== -1) {
            // We're navigating to a node already in our path - truncate to that point
            console.log(`Node ${nodeId} found at index ${existingIndex}, truncating path`);
            this.currentPath = this.currentPath.slice(0, existingIndex + 1);
        } else {
            // New node - determine if it's a child of current location or a sibling/cousin
            if (this.currentPath.length > 0) {
                const currentNode = this.currentPath[this.currentPath.length - 1];

                // Check if target is a direct child of current node
                if (this.isDirectChild(nodeId, currentNode.nodeId)) {
                    // It's a child - safe to add to current path
                    console.log(`${nodeId} is a child of ${currentNode.nodeId}, adding to path`);
                    this.currentPath.push({ nodeId: nodeId, nodeLabel: nodeLabel });
                } else {
                    // It's not a direct child - might be a sibling or cousin
                    // Find the appropriate level to truncate to
                    const appropriateLevel = this.findAppropriatePathLevel(nodeId);
                    this.currentPath = this.currentPath.slice(0, appropriateLevel);
                    this.currentPath.push({ nodeId: nodeId, nodeLabel: nodeLabel });
                    console.log(`${nodeId} is not a direct child, truncated path and added`);
                }
            } else {
                // Empty path - this is our first navigation
                this.currentPath.push({ nodeId: nodeId, nodeLabel: nodeLabel });
            }
        }

        console.log(`Current path after navigation:`, this.currentPath.map(p => p.nodeId));

        // Add to history (keeping existing logic)
        this.navigationHistory.push({
            nodeId: nodeId,
            nodeLabel: nodeLabel,
            path: [...this.currentPath]
        });

        // Load children of this node
        this.loadNodeChildren(nodeId, nodeLabel);
    }

    // Helper method to determine if nodeB is a direct child of nodeA
    isDirectChild(childId, parentId) {
        // TMI hierarchy logic:
        // - A is parent of A0-A99, A100-A499, etc.
        // - A0-A99 is parent of A0, A10, A20, etc.
        // - A100-A499 is parent of A100, A200, A300, etc.

        if (parentId.length === 1 && childId.startsWith(parentId)) {
            // Category level: A -> A0-A99, A100-A499
            return childId.includes('-') && childId.startsWith(parentId);
        }

        if (parentId.includes('-')) {
            // Range level: A100-A499 -> A100, A200, A300
            const [rangeStart, rangeEnd] = parentId.split('-');
            const category = rangeStart[0];

            if (!childId.startsWith(category) || childId.includes('-')) {
                return false;
            }

            // Extract numeric part and check if it's in range
            const childNum = parseInt(childId.slice(1)) || 0;
            const startNum = parseInt(rangeStart.slice(1)) || 0;
            const endNum = parseInt(rangeEnd.slice(1)) || 0;

            return childNum >= startNum && childNum <= endNum;
        }

        // Default: not a direct child
        return false;
    }

    // Helper method to find appropriate path level for a node
    findAppropriatePathLevel(nodeId) {
        // Work backwards through currentPath to find where this node belongs
        for (let i = this.currentPath.length - 1; i >= 0; i--) {
            const pathNode = this.currentPath[i];
            if (this.isDirectChild(nodeId, pathNode.nodeId)) {
                return i + 1; // Truncate after this level
            }
        }

        // If no appropriate parent found, start fresh
        return 0;
    }

    // Load children of a specific node
    loadNodeChildren(nodeId, nodeLabel) {
        const hierarchyDiv = document.getElementById('tmiHierarchy');
        hierarchyDiv.innerHTML = '<p class="text-muted">Loading...</p>';

        // Build breadcrumb navigation
        let breadcrumbHtml = this.buildBreadcrumb();
        
        fetch(`/get_tmi_children/${nodeId}`)
            .then(response => response.json())
            .then(data => {
                console.log(`Found ${data.length} children for ${nodeId}`);
                
                if (data.length === 0) {
                    // No children - this is a leaf node, show motifs
                    this.displayNodeMotifs(nodeId, nodeLabel);
                } else {
                    // Has children - show them for further navigation
                    this.displayNodeChildren(data, nodeId, nodeLabel, breadcrumbHtml);
                }
            })
            .catch(error => {
                console.error('Error loading node children:', error);
                hierarchyDiv.innerHTML = breadcrumbHtml + '<p class="text-danger">Error loading content</p>';
            });
    }

    // Display children of a node
    displayNodeChildren(children, nodeId, nodeLabel, breadcrumbHtml) {
        const hierarchyDiv = document.getElementById('tmiHierarchy');
        
        let html = breadcrumbHtml;
        html += `<h6>${nodeLabel}</h6>`;
        html += '<div class="list-group">';

        children.forEach(child => {
            const iconClass = child.has_children ? 'folder' : 'file-text';
            const clickHandler = child.has_children ? 
                `tmiBrowser.navigateToNode('${child.child_id}', '${child.label.replace(/'/g, "\\'")}')` :
                `tmiBrowser.displayNodeMotifs('${child.child_id}', '${child.label.replace(/'/g, "\\'")}')`;

            html += `
                <div class="motif-category-item list-group-item d-flex justify-content-between align-items-center"
                     onclick="${clickHandler}">
                    <div>
                        <i class="fas fa-${iconClass} me-2"></i>
                        <strong>${child.child_id}:</strong> ${child.label}
                    </div>
                    <span class="badge ${child.connected_count > 0 ? 'bg-success' : 'bg-secondary'} rounded-pill">
                        ${child.connected_count} connected
                    </span>
                </div>`;
        });

        html += '</div>';
        hierarchyDiv.innerHTML = html;

        // Clear results when browsing hierarchy
        this.clearResults();
    }

    // Display motifs for a specific node
    displayNodeMotifs(nodeId, nodeLabel) {
        console.log(`Loading motifs for node: ${nodeId}`);
        
        // Update navigation if this is a direct call (not from hierarchy navigation)
        if (!this.currentPath.some(p => p.nodeId === nodeId)) {
            this.currentPath.push({ nodeId: nodeId, nodeLabel: nodeLabel });
        }

        const resultDiv = document.getElementById('browseResultContent');
        resultDiv.innerHTML = '<p class="text-muted">Loading motifs...</p>';

        fetch(`/get_motifs_for_node/${nodeId}?limit=100`)
            .then(response => response.json())
            .then(data => {
                console.log(`Found ${data.motifs.length} motifs for ${nodeId}`);
                this.displayMotifsResult(data, nodeId, nodeLabel);
            })
            .catch(error => {
                console.error('Error loading motifs:', error);
                resultDiv.innerHTML = '<p class="text-danger">Error loading motifs</p>';
            });
    }

    // Display motifs in the results panel
    displayMotifsResult(data, nodeId, nodeLabel) {
        const resultDiv = document.getElementById('browseResultContent');
        
        let html = `<h6>Motifs in ${nodeId}: ${nodeLabel}</h6>`;
        html += `<p class="text-muted">${data.total} motifs connected to ATU tale types</p>`;
        
        if (data.motifs.length === 0) {
            html += '<p></p>';
        } else {
            html += '<ul class="list-unstyled">';

            data.motifs.forEach(motif => {
                html += `<li class="mb-2">
                    <a href="#" onclick="tmiBrowser.loadMotifDetail('${motif.motif_id}')" class="text-decoration-none">
                        <strong>${motif.motif_id}</strong>: ${motif.text}
                        <span class="badge bg-primary ms-2">${motif.type_count} tale types</span>
                    </a>
                </li>`;
            });

            html += '</ul>';

            if (data.total > data.limit) {
                html += `<p class="text-muted">Showing first ${data.limit} of ${data.total} connected motifs</p>`;
            }
        }

        resultDiv.innerHTML = html;
    }

    // Load detailed view of a specific motif
    loadMotifDetail(motifId) {
        console.log(`Loading detail for motif: ${motifId}`);
        
        const resultDiv = document.getElementById('browseResultContent');
        resultDiv.innerHTML = '<p class="text-muted">Loading motif details...</p>';

        Promise.all([
            fetch(`/get_motif_details/${motifId}`).then(r => r.json()),
            fetch(`/get_types_for_motif/${motifId}`).then(r => r.json())
        ]).then(([motifDetails, types]) => {
            this.displayMotifResult(motifId, motifDetails, types);
        }).catch(error => {
            console.error('Error loading motif details:', error);
            resultDiv.innerHTML = '<p class="text-danger">Error loading motif details</p>';
        });
    }

    // Display detailed motif result
    displayMotifResult(motifId, details, types) {
        let culturalRefs = '';
        if (details.ref_terms && details.ref_terms.length > 0) {
            const terms = details.ref_terms.slice(0, 5);
            const remaining = details.ref_terms.length - 5;
            culturalRefs = `<span class="cultural-refs">[${terms.join(', ')}${remaining > 0 ? `, ...${remaining} more` : ''}]</span>`;
        }

        let html = `
            <div class="result-item">
                <h5>TMI ${motifId}: ${details.text} ${culturalRefs}</h5>

                <div class="motif-list">
                    <h6>Tale Types (${types.length}):</h6>
        `;

        types.forEach(type => {
            let typeCulturalRefs = '';
            if (type.ref_terms && type.ref_terms.trim()) {
                typeCulturalRefs = ` <span class="cultural-refs">[${type.ref_terms}]</span>`;
            }
            html += `<div class="motif-item">
                       <a href="#" onclick="loadBrowseTaleType('${type.type_id}')" class="text-decoration-none">
                         <strong>ATU ${type.type_id}</strong> – ${type.label}${typeCulturalRefs}
                       </a>
                     </div>`;
        });

        html += '</div></div>';
        document.getElementById('browseResultContent').innerHTML = html;
    }

    // Build breadcrumb navigation
    buildBreadcrumb() {
        if (this.currentPath.length === 0) {
            return '';
        }

        let breadcrumbHtml = '<div class="mb-3 tmi-breadcrumb">';
        breadcrumbHtml += '<nav aria-label="breadcrumb"><ol class="breadcrumb">';
        
        // Home/Categories link
        breadcrumbHtml += '<li class="breadcrumb-item">';
        breadcrumbHtml += '<a href="#" onclick="tmiBrowser.loadTMICategories()">Categories</a>';
        breadcrumbHtml += '</li>';

        // Path items (except the last one)
        for (let i = 0; i < this.currentPath.length - 1; i++) {
            const item = this.currentPath[i];
            breadcrumbHtml += '<li class="breadcrumb-item">';
            breadcrumbHtml += `<a href="#" onclick="tmiBrowser.navigateToNode('${item.nodeId}', '${item.nodeLabel.replace(/'/g, "\\'")}')">`;
            breadcrumbHtml += item.nodeId;
            breadcrumbHtml += '</a></li>';
        }

        // Current item (not clickable)
        if (this.currentPath.length > 0) {
            const current = this.currentPath[this.currentPath.length - 1];
            breadcrumbHtml += `<li class="breadcrumb-item active">${current.nodeId}</li>`;
        }

        breadcrumbHtml += '</ol></nav></div>';
        return breadcrumbHtml;
    }

    // Clear results panel
    clearResults() {
        const resultDiv = document.getElementById('browseResultContent');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="browse-explanation">
                    <p class="text-muted mb-2">Displaying only motifs that have been cross-referenced in the ATU index.</p>
                    <p class="text-muted">Select a category to begin browsing...</p>
                    <img src="/static/images/TMI_cover.jpg" alt="TMI Browse" height="300">
                </div>
            `;
        }
    }
    // Go back one level
    goBack() {
        if (this.navigationHistory.length > 1) {
            // Remove current
            this.navigationHistory.pop();

            // Get previous
            const previous = this.navigationHistory[this.navigationHistory.length - 1];
            this.currentPath = [...previous.path];
            
            if (previous.nodeId === 'categories') {
                this.loadTMICategories();
            } else {
                this.loadNodeChildren(previous.nodeId, previous.nodeLabel);
            }
        } else {
            this.loadTMICategories();
        }
    }
}

// Create global instance
const tmiBrowser = new TMIBrowser();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TMIBrowser;
}