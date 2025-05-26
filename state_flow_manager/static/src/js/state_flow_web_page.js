/** @odoo-module **/

console.log("state_flow_web_page.js loaded");

document.addEventListener('DOMContentLoaded', async function() {
    const diagramContainer = document.getElementById("mermaid_diagram_container");
    
    if (!diagramContainer) {
        console.error("Diagram container #mermaid_diagram_container not found.");
        return;
    }

    const processDataJsonString = diagramContainer.dataset.processData;
    if (!processDataJsonString) {
        console.error("Process data not found in diagram container's data attributes.");
        diagramContainer.innerHTML = "<div class='alert alert-danger'>Error: Process data not available.</div>";
        return;
    }

    let processData;
    try {
        processData = JSON.parse(processDataJsonString);
    } catch (e) {
        console.error("Error parsing process data JSON:", e);
        diagramContainer.innerHTML = "<div class='alert alert-danger'>Error: Could not parse process data.</div>";
        return;
    }
    
    if (typeof mermaid === 'undefined') {
        console.error("Mermaid.js is not loaded.");
        diagramContainer.innerHTML = "<div class='alert alert-danger'>Error: Mermaid.js library not found. Please check assets.</div>";
        return;
    }

    let graphDefinition = "graph TD\n"; // TD for Top-Down

    if (processData && processData.nodes && processData.nodes.length > 0) {
        processData.nodes.forEach(node => {
            let nodeLabel = node.name ? node.name.replace(/"/g, '#quot;') : '(Unnamed State)';
            // Usar ( ) para círculos en Mermaid
            graphDefinition += `    ${node.key}("${nodeLabel}")\n`;
        });

        if (processData.edges) {
            processData.edges.forEach(edge => {
                let edgeLabel = edge.name ? edge.name.replace(/"/g, '#quot;') : '';
                graphDefinition += `    ${edge.from} -->|"${edgeLabel}"| ${edge.to}\n`;
            });
        }
    } else {
        graphDefinition += "    A((No process data available or process is empty))";
    }
    
    diagramContainer.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><i class="fa fa-spinner fa-spin fa-3x text-muted"></i> Rendering...</div>';

    try {
        mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'loose' });
        // Ensure unique ID for render to avoid clashes if multiple diagrams are on a page or re-renders occur
        const svgId = 'stateFlowMermaidSvgPage_' + Date.now() + Math.random().toString(36).substring(2, 15);
        const { svg } = await mermaid.render(svgId, graphDefinition);
        diagramContainer.innerHTML = svg;
    } catch (e) {
        console.error("Mermaid rendering error:", e);
        diagramContainer.innerHTML = "<div class='alert alert-danger'>Error rendering diagram. " + e.message + "</div><pre class='mt-2'>" + graphDefinition.replace(/</g, '&lt;').replace(/>/g, '&gt;') + "</pre>";
    }
    // --- CREACIÓN DE TRANSICIÓN POR CLICK DIRECTO EN NODOS ---
    // (Eliminado: ya no se permite crear transiciones haciendo clic en los nodos)
});