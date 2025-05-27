/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";

const { Component, onWillStart, onMounted, useRef, useState, onWillUpdateProps } = owl;

// State Flow Diagram Widget
export class StateFlowDiagramWidget extends Component {
    static template = "state_flow_manager.StateFlowDiagram";
    static props = {
        ...standardFieldProps,
        processId: {
            type: Number,
            optional: true,
        },
        record: Object, // The current record
    };

    setup() {
        this.orm = useService("orm");
        this.diagramRef = useRef("diagramContainer"); // We'll add a t-ref in the template
        this.state = useState({
            mermaidGraph: "",
            isLoading: true,
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/mermaid/mermaid.esm.min.js"); // Path might vary based on Odoo version
        });

        onMounted(async () => {
            await this.loadAndRenderGraph();
        });

        onWillUpdateProps(async (nextProps) => {
            const oldProcessId = this.props.record.data.process_id ? this.props.record.data.process_id[0] : null;
            const newProcessId = nextProps.record.data.process_id ? nextProps.record.data.process_id[0] : null;
            const oldCurrentStateId = this.props.record.data.current_state_id ? this.props.record.data.current_state_id[0] : null;
            const newCurrentStateId = nextProps.record.data.current_state_id ? nextProps.record.data.current_state_id[0] : null;

            if (oldProcessId !== newProcessId || oldCurrentStateId !== newCurrentStateId) {
                 await this.loadAndRenderGraph(nextProps.record);
            }
        });
    }

    async loadAndRenderGraph(record = this.props.record) {
        this.state.isLoading = true;
        const processId = record.data.process_id ? record.data.process_id[0] : null;
        const currentStateId = record.data.current_state_id ? record.data.current_state_id[0] : null;

        if (!processId) {
            this.state.mermaidGraph = "graph TD\n    A[No Process Selected]";
            this.state.isLoading = false;
            this._renderMermaid();
            return;
        }

        try {
            const processData = await this.orm.call(
                "state.flow.process",
                "get_process_graph_data",
                [processId, currentStateId]
            );

            if (processData && processData.nodes && processData.edges) {
                let graphDefinition = "graph LR\n"; // Change to LR (Left-Right) for better visualization
                
                // Fetch all state details in one batch for better performance
                const stateIds = processData.nodes.map(node => node.id);
                const statesDetails = await this.orm.call(
                    'state.flow.state',
                    'read',
                    [stateIds, ['icon_class', 'name']],
                    {}
                );
                
                // Create a map for quick lookup
                const stateDetailsMap = {};
                statesDetails.forEach(state => {
                    stateDetailsMap[state.id] = state;
                });
                
                // Define states (nodes)
                for (const node of processData.nodes) {
                    let nodeLabel = node.name.replace(/"/g, '#quot;'); // Sanitize label
                    const stateDetail = stateDetailsMap[node.id];
                    
                    // Add icon prefix based on icon_class if available
                    if (stateDetail && stateDetail.icon_class) {
                        const iconClass = stateDetail.icon_class.trim();
                        
                        // Map Font Awesome icons to similar Unicode symbols for Mermaid compatibility
                        if (iconClass.includes('check')) {
                            nodeLabel = "✓ " + nodeLabel;
                        } else if (iconClass.includes('flag')) {
                            nodeLabel = "⚑ " + nodeLabel;
                        } else if (iconClass.includes('clock')) {
                            nodeLabel = "⏱ " + nodeLabel;
                        } else if (iconClass.includes('play')) {
                            nodeLabel = "▶ " + nodeLabel;
                        } else if (iconClass.includes('stop')) {
                            nodeLabel = "⏹ " + nodeLabel;
                        } else if (iconClass.includes('pause')) {
                            nodeLabel = "⏸ " + nodeLabel;
                        } else if (iconClass.includes('circle')) {
                            nodeLabel = "⚫ " + nodeLabel;
                        } else if (iconClass.includes('star')) {
                            nodeLabel = "★ " + nodeLabel;
                        } else if (iconClass.includes('alert') || iconClass.includes('exclamation')) {
                            nodeLabel = "⚠ " + nodeLabel;
                        } else if (iconClass.includes('times')) {
                            nodeLabel = "✗ " + nodeLabel;
                        } else if (iconClass.includes('cog') || iconClass.includes('gear')) {
                            nodeLabel = "⚙ " + nodeLabel;
                        } else if (iconClass.includes('arrow-right')) {
                            nodeLabel = "→ " + nodeLabel;
                        } else if (iconClass.includes('arrow-left')) {
                            nodeLabel = "← " + nodeLabel;
                        } else if (iconClass.includes('arrow-up')) {
                            nodeLabel = "↑ " + nodeLabel;
                        } else if (iconClass.includes('arrow-down')) {
                            nodeLabel = "↓ " + nodeLabel;
                        } else if (iconClass.includes('lock')) {
                            nodeLabel = "🔒 " + nodeLabel;
                        } else if (iconClass.includes('unlock')) {
                            nodeLabel = "🔓 " + nodeLabel;
                        } else if (iconClass.includes('user')) {
                            nodeLabel = "👤 " + nodeLabel;
                        } else if (iconClass.includes('users')) {
                            nodeLabel = "👥 " + nodeLabel;
                        } else if (iconClass.includes('home')) {
                            nodeLabel = "🏠 " + nodeLabel;
                        } else if (iconClass.includes('envelope') || iconClass.includes('mail')) {
                            nodeLabel = "✉ " + nodeLabel;
                        } else if (iconClass.includes('heart')) {
                            nodeLabel = "❤ " + nodeLabel;
                        } else {
                            nodeLabel = "• " + nodeLabel; // Default bullet
                        }
                    }
                    
                    if (node.is_current) {
                        // Style for current state - make it larger and use a different style
                        graphDefinition += `    ${node.key}["${nodeLabel}"]:::currentState\n`;
                    } else {
                        graphDefinition += `    ${node.key}["${nodeLabel}"]\n`;
                    }
                }

                // Define transitions (edges)
                processData.edges.forEach(edge => {
                    let edgeLabel = edge.name.replace(/"/g, '#quot;'); // Sanitize label
                    graphDefinition += `    ${edge.from} -->|"${edgeLabel}"| ${edge.to}\n`;
                });

                // Define styles for the states
                graphDefinition += "    classDef currentState fill:#4CAF50,stroke:#333,stroke-width:3px,color:white,font-weight:bold,font-size:16px\n";
                graphDefinition += "    classDef default fill:#f5f5f5,stroke:#999,stroke-width:1px,color:#333,font-size:14px\n";

                this.state.mermaidGraph = graphDefinition;
            } else {
                this.state.mermaidGraph = "graph LR\n    B[Error loading process data or no data]";
            }
        } catch (error) {
            console.error("Error loading or rendering state flow diagram:", error);
            this.state.mermaidGraph = "graph LR\n    C[Error fetching data]";
        }
        this.state.isLoading = false;
        this._renderMermaid();
    }

    _renderMermaid() {
        if (this.diagramRef.el && this.state.mermaidGraph) {
            // Configure mermaid with enhanced styling
            mermaid.initialize({ 
                startOnLoad: false, 
                theme: 'neutral',
                flowchart: {
                    htmlLabels: true,
                    curve: 'basis',
                    nodeSpacing: 50,
                    rankSpacing: 100,
                    padding: 15
                }
            });
            
            try {
                mermaid.render("stateFlowMermaidSvg", this.state.mermaidGraph, (svgCode) => {
                    if (this.diagramRef.el) { // Check if element still exists
                         this.diagramRef.el.innerHTML = svgCode;
                         
                         // Additional styling for the rendered SVG to make it larger
                         const svg = this.diagramRef.el.querySelector('svg');
                         if (svg) {
                             svg.style.width = '100%';
                             svg.style.maxWidth = '100%';
                             svg.style.height = 'auto';
                             svg.style.minHeight = '350px';
                         }
                    }
                });
            } catch (e) {
                 console.error("Mermaid rendering error:", e);
                 if (this.diagramRef.el) { 
                    this.diagramRef.el.innerHTML = "<p>Error rendering diagram. Check console.</p>";
                 }
            }
        }
    }
}

// Register the diagram widget
registry.category("fields").add("state_flow_diagram", {
    component: StateFlowDiagramWidget,
    // supportedTypes: [], // Optionally add if needed, e.g. for a dummy char field this widget might attach to.
}); 