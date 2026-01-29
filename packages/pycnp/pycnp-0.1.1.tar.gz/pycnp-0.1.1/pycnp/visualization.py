"""
Graph visualization module.

Provides the :func:`visualize_graph` function for generating interactive
HTML visualizations of graphs with critical nodes highlighted.

This module uses the ``pyvis`` library to create network visualizations
that can be opened in a web browser. The visualization includes features
for highlighting critical nodes, searching for nodes, and viewing connected
component information.

Requirements
------------
This module requires the ``pyvis`` package. Install with:
``pip install pyvis``

Functions
---------
visualize_graph
    Generates an interactive HTML visualization of a graph.
"""

# ruff: noqa: E501 (HTML/JS templates are intentionally not line-wrapped)

from __future__ import annotations

import json
import logging
import os
import webbrowser
from typing import TYPE_CHECKING, Dict, List, Set, Union

from .constants import PACKAGE_LOGGER_NAME

if TYPE_CHECKING:
    from ._pycnp import ProblemData

logger = logging.getLogger(PACKAGE_LOGGER_NAME)

# Node styling constants
DEFAULT_NODE_SIZE = 25
DEFAULT_NODE_FONT_SIZE = 14
HIGHLIGHT_DURATION_MS = 3000
NETWORK_HEIGHT = "95vh"
NETWORK_WIDTH = "100%"

# Color constants
DEFAULT_NODE_COLOR = "#97c2fc"
CRITICAL_NODE_COLOR = "#ff6961"
COMPONENT_COLORS = [
    "#57C7E5",
    "#E557C7",
    "#C7E557",
    "#E58C57",
    "#57E58C",
    "#8C57E5",
    "#E5B857",
    "#57A3E5",
    "#E5578C",
    "#8CE557",
]

try:
    from pyvis.network import Network  # type: ignore[import-untyped]

    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False


def visualize_graph(
    problem_data: "ProblemData",
    critical_nodes_set: Union[Set[int], List[int]],
    filename: str = "interactive_graph.html",
) -> str:
    """
    Generate interactive graph visualization HTML file and open it automatically.

    Parameters
    ----------
    problem_data : ProblemData
        ProblemData object containing graph nodes and edges information.
    critical_nodes_set : set or list
        Critical nodes set.
    filename : str, default="interactive_graph.html"
        Output HTML filename.

    Returns
    -------
    str
        Absolute path of the generated HTML file.

    Raises
    ------
    ImportError
        If the ``pyvis`` library is not installed.
    """
    if not PYVIS_AVAILABLE:
        raise ImportError(
            "This feature requires 'pyvis' library. Please run: pip install pyvis"
        )

    if not isinstance(critical_nodes_set, set):
        critical_nodes_set = set(critical_nodes_set)

    adj_list = problem_data.get_adj_list()
    nodes = set(range(len(adj_list)))

    active_nodes = {n for n in nodes if n not in critical_nodes_set}
    visited = set()
    components: List[List[int]] = []
    for node in active_nodes:
        if node not in visited:
            component: List[int] = []
            queue: List[int] = [node]
            visited.add(node)
            while queue:
                current = queue.pop(0)
                component.append(current)
                for neighbor in adj_list[current]:
                    if neighbor in active_nodes and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)

    node_to_component_color: Dict[int, str] = {}
    for idx, component in enumerate(components):
        color = COMPONENT_COLORS[idx % len(COMPONENT_COLORS)]
        for node_id in component:
            node_to_component_color[node_id] = color

    net = Network(
        height=NETWORK_HEIGHT,
        width=NETWORK_WIDTH,
        bgcolor="#ffffff",
        font_color="black",
        notebook=False,
    )

    for node_id in nodes:
        net.add_node(
            node_id,
            label=str(node_id),
            color=DEFAULT_NODE_COLOR,
            title=f"Node {node_id}",
            shape="circle",
            size=DEFAULT_NODE_SIZE,
            font={
                "size": DEFAULT_NODE_FONT_SIZE,
                "color": "black",
                "face": "Arial",
                "align": "center",
            },
        )

    for node_id, neighbors in enumerate(adj_list):
        for neighbor_id in neighbors:
            if node_id < neighbor_id:
                net.add_edge(node_id, neighbor_id)

    html_content = net.generate_html(notebook=False)

    critical_nodes_list = list(critical_nodes_set)

    node_info: Dict[int, Dict[str, str]] = {}
    for node_id in nodes:
        info = {
            "component_color": node_to_component_color.get(
                node_id, DEFAULT_NODE_COLOR
            )
        }
        node_info[node_id] = info

    components_data: List[Dict[str, Union[int, str, List[int]]]] = []
    for idx, component in enumerate(components):
        color = COMPONENT_COLORS[idx % len(COMPONENT_COLORS)]
        components_data.append(
            {
                "id": idx + 1,
                "nodes": sorted(component),
                "size": len(component),
                "color": color,
            }
        )

    components_data.sort(key=lambda x: x["size"], reverse=True)

    # Long HTML/JS template - intentionally not formatted for readability
    injection_html = f"""
<style>
    /* Control panel: light theme */
    #control-panel {{
        position: fixed;
        top: 10px;
        left: 10px;
        padding: 15px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #60a5fa;
        border-radius: 8px;
        z-index: 1000;
        color: #1e40af;
        font-family: sans-serif;
        width: 250px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    #control-panel button {{
        display: block;
        width: 100%;
        padding: 10px;
        margin-top: 8px;
        border: 1px solid #60a5fa;
        background-color: #93c5fd;
        color: #1e40af;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 13px;
        font-weight: 500;
    }}
    #control-panel button:hover {{
        background-color: #60a5fa;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}

    #search-container {{
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #60a5fa;
    }}

    #search-input {{
        width: 100%;
        padding: 8px;
        border: 1px solid #60a5fa;
        background-color: #ffffff;
        color: #1e40af;
        border-radius: 4px;
        font-size: 13px;
        margin-bottom: 8px;
    }}

    #search-input:focus {{
        outline: none;
        border-color: #4CAF50;
        box-shadow: 0 0 5px rgba(76, 175, 80, 0.3);
    }}

    .search-results {{
        max-height: 100px;
        overflow-y: auto;
        background-color: #ffffff;
        border: 1px solid #60a5fa;
        border-radius: 4px;
        margin-top: 5px;
    }}

    .search-result-item {{
        padding: 5px 8px;
        cursor: pointer;
        border-bottom: 1px solid #60a5fa;
        font-size: 12px;
        color: #1e40af;
    }}

    .search-result-item:hover {{
        background-color: #93c5fd;
    }}

    .search-result-item:last-child {{
        border-bottom: none;
    }}

    /* Right-hand components panel: light theme */
    #components-panel {{
        position: fixed;
        top: 10px;
        right: 10px;
        width: 280px;
        max-height: 90vh;
        padding: 15px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #60a5fa;
        border-radius: 8px;
        z-index: 1000;
        color: #1e40af;
        font-family: sans-serif;
        overflow-y: auto;
        display: none;
    }}

    .component-item {{
        margin-bottom: 15px;
        padding: 10px;
        border: 1px solid #60a5fa;
        border-radius: 6px;
        background-color: rgba(240, 248, 255, 0.8);
    }}

    .component-header {{
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        font-weight: bold;
    }}

    .component-color {{
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 10px;
        border: 2px solid #fff;
    }}

    .component-nodes {{
        font-size: 12px;
        line-height: 1.4;
        color: #1e40af;
        max-height: 100px;
        overflow-y: auto;
    }}

    .node-tag {{
        display: inline-block;
        background-color: #60a5fa;
        color: white;
        padding: 2px 6px;
        margin: 2px;
        border-radius: 3px;
        font-size: 13px;
        cursor: pointer;
    }}

    .node-tag:hover {{
        background-color: #3b82f6;
    }}

    .critical-nodes {{
        margin-top: 15px;
        padding: 10px;
        border: 2px solid #ff6961;
        border-radius: 6px;
        background-color: rgba(255, 105, 97, 0.1);
    }}

    .critical-header {{
        color: #ff6961;
        font-weight: bold;
        margin-bottom: 8px;
    }}

    /* Bottom statistics panel: light theme */
    #stats-panel {{
        position: fixed;
        bottom: 80px;
        left: 10px;
        width: 250px;
        padding: 15px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #60a5fa;
        border-radius: 8px;
        z-index: 1000;
        color: #1e40af;
        font-family: sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: none;
    }}

    .stats-item {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        padding: 5px 0;
        border-bottom: 1px solid #60a5fa;
    }}

    .stats-item:last-child {{
        border-bottom: none;
        margin-bottom: 0;
    }}

    .stats-label {{
        color: #1e40af;
        font-size: 13px;
    }}

    .stats-value {{
        color: #4CAF50;
        font-weight: bold;
        font-size: 13px;
    }}
</style>

<div id="control-panel">
    <strong style="font-size: 16px; margin-bottom: 10px; display: block;">
        Control Panel
    </strong>

    <div id="search-container">
        <input
            type="text"
            id="search-input"
            placeholder="Search nodes (e.g.: 1,2,3 or 1-5)"
        />
        <div id="search-results" class="search-results" style="display: none;"></div>
    </div>

    <button id="reset-btn">Reset Graph</button>
    <button id="highlight-btn">Highlight Critical Nodes</button>
    <button id="isolate-btn">Remove Critical Nodes</button>
    <button id="toggle-components-btn">Show/Hide Component Info</button>
    <button id="toggle-stats-btn">Show/Hide Statistics</button>
</div>

<div id="components-panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <strong style="font-size: 16px;">Connected Components Info</strong>
        <button id="close-components-btn" style="background: none; border: none; color: #1e40af; font-size: 18px; cursor: pointer; padding: 0; margin-left: auto;">
            &times;
        </button>
    </div>

    <div class="critical-nodes">
        <div class="critical-header">
            Critical Nodes (<span id="critical-nodes-count-display"></span>)
        </div>
        <div id="critical-nodes-list"></div>
    </div>

    <div style="margin-top: 15px; margin-bottom: 10px; font-weight: bold; color: #1e40af;">
        Connected Components
    </div>
    <div id="components-list"></div>
</div>

<div id="stats-panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <strong style="font-size: 16px;">Graph Statistics</strong>
        <button id="close-stats-btn" style="background: none; border: none; color: #1e40af; font-size: 18px; cursor: pointer; padding: 0;">
            &times;
        </button>
    </div>

    <div id="stats-content">
        <div class="stats-item">
            <span class="stats-label">Node Count:</span>
            <span class="stats-value" id="total-nodes">-</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">Edge Count:</span>
            <span class="stats-value" id="total-edges">-</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">Component Count:</span>
            <span class="stats-value" id="components-count">-</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">Largest Component Size:</span>
            <span class="stats-value" id="largest-component">-</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">Smallest Component Size:</span>
            <span class="stats-value" id="smallest-component">-</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">Average Degree:</span>
            <span class="stats-value" id="average-degree">-</span>
        </div>
    </div>
</div>

<script type="text/javascript">
    // Wait for the network to be fully rendered and stabilized
    network.on("stabilizationIterationsDone", function () {{
        // Data from Python
        const CRITICAL_NODES = {json.dumps(critical_nodes_list)};
        const NODE_INFO = {json.dumps(node_info)};
        const COMPONENTS_DATA = {json.dumps(components_data)};
        const CRITICAL_COLOR = "{CRITICAL_NODE_COLOR}";
        const DEFAULT_COLOR = "{DEFAULT_NODE_COLOR}";

        // Store the original full edge set and node set
        const allEdges = new vis.DataSet(network.body.data.edges.get());
        const allNodes = new vis.DataSet(network.body.data.nodes.get());

        const nodesDataSet = network.body.data.nodes;
        const edgesDataSet = network.body.data.edges;

        // Calculate graph statistics
        function calculateStats() {{
            const allNodes = nodesDataSet.get();
            const allEdges = edgesDataSet.get();

            const totalNodes = allNodes.length;
            const totalEdges = allEdges.length;
            const componentsCount = COMPONENTS_DATA.length;
            const largestComponent = COMPONENTS_DATA.length > 0
                ? Math.max(...COMPONENTS_DATA.map(c => c.size))
                : 0;
            const smallestComponent = COMPONENTS_DATA.length > 0
                ? Math.min(...COMPONENTS_DATA.map(c => c.size))
                : 0;
            const avgDegree = totalNodes > 0
                ? (2 * totalEdges / totalNodes).toFixed(2)
                : 0;

            return {{
                totalNodes,
                totalEdges,
                componentsCount,
                largestComponent,
                smallestComponent,
                avgDegree
            }};
        }}

        // Update statistics panel
        function updateStatsPanel() {{
            const stats = calculateStats();
            document.getElementById('total-nodes').textContent = stats.totalNodes;
            document.getElementById('total-edges').textContent = stats.totalEdges;
            document.getElementById('components-count').textContent = stats.componentsCount;
            document.getElementById('largest-component').textContent = stats.largestComponent;
            document.getElementById('smallest-component').textContent = stats.smallestComponent;
            document.getElementById('average-degree').textContent = stats.avgDegree;
        }}

        // Initialize connected components panel
        function initializeComponentsPanel() {{
            // Display critical nodes count
            document.getElementById('critical-nodes-count-display').textContent =
                CRITICAL_NODES.length;

            // Display critical nodes (sorted by node number)
            const criticalNodesList = document.getElementById('critical-nodes-list');
            if (CRITICAL_NODES.length > 0) {{
                const sortedCriticalNodes = [...CRITICAL_NODES].sort((a, b) => a - b);
                criticalNodesList.innerHTML = sortedCriticalNodes.map(node =>
                    `<span class="node-tag" onclick="focusOnNode(${{node}})">${{node}}</span>`
                ).join('');
            }} else {{
                criticalNodesList.innerHTML =
                    '<span style="color: #999;">No critical nodes</span>';
            }}

            // Display connected components (already sorted by size)
            const componentsList = document.getElementById('components-list');
            if (COMPONENTS_DATA.length > 0) {{
                componentsList.innerHTML = COMPONENTS_DATA.map((comp, index) => `
                    <div class="component-item">
                        <div class="component-header">
                            <div class="component-color"
                                style="background-color: ${{comp.color}};">
                            </div>
                            <span>Component ${{index + 1}} (${{comp.size}})</span>
                        </div>
                        <div class="component-nodes">
                            ${{comp.nodes.map(node =>
                                `<span class="node-tag"
                                    onclick="focusOnNode(${{node}})">${{node}}</span>`
                            ).join('')}}
                        </div>
                    </div>
                `).join('');
            }} else {{
                componentsList.innerHTML = '<div style="color: #999; text-align: center; padding: 20px;">' +
                    'Connected components will be shown after removing critical nodes' +
                    '</div>';
            }}
        }}

        // Node search functionality
        function initializeSearch() {{
            const searchInput = document.getElementById('search-input');
            const searchResults = document.getElementById('search-results');

            searchInput.addEventListener('input', function() {{
                const query = this.value.trim();
                if (query === '') {{
                    searchResults.style.display = 'none';
                    return;
                }}

                const results = searchNodes(query);
                displaySearchResults(results);
            }});

            searchInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    const query = this.value.trim();
                    const results = searchNodes(query);
                    if (results.length > 0) {{
                        focusOnNode(results[0]);
                        searchResults.style.display = 'none';
                    }}
                }}
            }});
        }}

        function searchNodes(query) {{
            const allNodes = nodesDataSet.get().map(n => n.id);
            const results = [];

            // Support single node search
            if (/^\\d+$/.test(query)) {{
                const nodeId = parseInt(query);
                if (allNodes.includes(nodeId)) {{
                    results.push(nodeId);
                }}
            }}
            // Support range search (e.g.: 1-5)
            else if (/^\\d+-\\d+$/.test(query)) {{
                const [start, end] = query.split('-').map(n => parseInt(n));
                for (let i = Math.min(start, end); i <= Math.max(start, end); i++) {{
                    if (allNodes.includes(i)) {{
                        results.push(i);
                    }}
                }}
            }}
            // Support comma-separated multiple nodes (e.g.: 1,3,5)
            else if (/^[\\d,\\s]+$/.test(query)) {{
                const nodeIds = query.split(',')
                    .map(n => parseInt(n.trim()))
                    .filter(n => !isNaN(n));
                nodeIds.forEach(nodeId => {{
                    if (allNodes.includes(nodeId)) {{
                        results.push(nodeId);
                    }}
                }});
            }}

            return results;
        }}

        function displaySearchResults(results) {{
            const searchResults = document.getElementById('search-results');

            if (results.length === 0) {{
                searchResults.innerHTML =
                    '<div class="search-result-item">No matching nodes found</div>';
            }} else {{
                searchResults.innerHTML = results.slice(0, 10).map(nodeId =>
                    `<div class="search-result-item"
                        onclick="focusOnNode(${{nodeId}});
                            document.getElementById('search-results').style.display='none';">
                        Node ${{nodeId}} ${{CRITICAL_NODES.includes(nodeId) ? '(Critical Node)' : ''}}
                    </div>`
                ).join('');

                if (results.length > 10) {{
                    searchResults.innerHTML +=
                        '<div class="search-result-item" style="color: #999;">' +
                        'Showing first 10 results...</div>';
                }}
            }}

            searchResults.style.display = 'block';
        }}

        // Focus on specific node
        function focusOnNode(nodeId) {{
            network.selectNodes([nodeId]);
            network.focus(nodeId, {{
                scale: 1.5,
                animation: {{
                    duration: 1000,
                    easingFunction: "easeInOutQuad"
                }}
            }});

            // Highlight node
            const updates = [];
            nodesDataSet.getIds().forEach(id => {{
                let color = id === nodeId
                    ? '#FFD700'
                    : (CRITICAL_NODES.includes(id) ? CRITICAL_COLOR : DEFAULT_COLOR);
                updates.push({{id: id, color: color}});
            }});
            nodesDataSet.update(updates);

            // Restore original color after 3 seconds
            setTimeout(() => {{
                const updates = [];
                nodesDataSet.getIds().forEach(id => {{
                    let color = CRITICAL_NODES.includes(id)
                        ? CRITICAL_COLOR : DEFAULT_COLOR;
                    updates.push({{id: id, color: color}});
                }});
                nodesDataSet.update(updates);
            }}, {HIGHLIGHT_DURATION_MS});
        }}

        function resetGraph() {{
            // Restore all original nodes
            nodesDataSet.clear();
            nodesDataSet.add(allNodes.get());

            // Restore all original edges
            edgesDataSet.clear();
            edgesDataSet.add(allEdges.get());

            // Reset all node colors to default color
            const updates = [];
            nodesDataSet.getIds().forEach(id => {{
                updates.push({{id: id, color: DEFAULT_COLOR}});
            }});
            nodesDataSet.update(updates);

            network.fit();
        }}

        function highlightNodes() {{
            const updates = [];
            nodesDataSet.getIds().forEach(id => {{
                let color = CRITICAL_NODES.includes(id) ? CRITICAL_COLOR : DEFAULT_COLOR;
                updates.push({{id: id, color: color}});
            }});
            nodesDataSet.update(updates);
        }}

        function isolateNodes() {{
            // Completely remove critical nodes
            const nodesToRemove = [];
            const edgesToRemove = [];

            // Collect critical nodes to remove
            nodesDataSet.get().forEach(node => {{
                if (CRITICAL_NODES.includes(node.id)) {{
                    nodesToRemove.push(node.id);
                }}
            }});

            // Collect edges connected to critical nodes
            edgesDataSet.get().forEach(edge => {{
                if (CRITICAL_NODES.includes(edge.from)
                        || CRITICAL_NODES.includes(edge.to)) {{
                    edgesToRemove.push(edge.id);
                }}
            }});

            // Remove edges and nodes
            edgesDataSet.remove(edgesToRemove);
            nodesDataSet.remove(nodesToRemove);

            // Update remaining nodes' colors to component colors
            const nodeUpdates = [];
            nodesDataSet.getIds().forEach(id => {{
                if (!CRITICAL_NODES.includes(id)) {{
                    let color = NODE_INFO[id].component_color;
                    nodeUpdates.push({{id: id, color: color}});
                }}
            }});
            nodesDataSet.update(nodeUpdates);
        }}

        // Toggle connected components panel display
        function toggleComponentsPanel() {{
            const panel = document.getElementById('components-panel');
            // Note: display:none set in CSS will not be reflected in panel.style.display
            const currentDisplay = window.getComputedStyle(panel).display;
            if (currentDisplay === 'none') {{
                panel.style.display = 'block';
            }} else {{
                panel.style.display = 'none';
            }}
        }}

        // Toggle statistics panel display
        function toggleStatsPanel() {{
            const panel = document.getElementById('stats-panel');
            const currentDisplay = window.getComputedStyle(panel).display;
            if (currentDisplay === 'none') {{
                panel.style.display = 'block';
                updateStatsPanel();
            }} else {{
                panel.style.display = 'none';
            }}
        }}

        // Close connected components panel
        function closeComponentsPanel() {{
            document.getElementById('components-panel').style.display = 'none';
        }}

        // Close statistics panel
        function closeStatsPanel() {{
            document.getElementById('stats-panel').style.display = 'none';
        }}

        // Initialize all features
        initializeComponentsPanel();
        initializeSearch();
        updateStatsPanel();

        // Attach event listeners
        document.getElementById('reset-btn').onclick = resetGraph;
        document.getElementById('highlight-btn').onclick = highlightNodes;
        document.getElementById('isolate-btn').onclick = isolateNodes;
        document.getElementById('toggle-components-btn').onclick = toggleComponentsPanel;
        document.getElementById('toggle-stats-btn').onclick = toggleStatsPanel;
        document.getElementById('close-components-btn').onclick = closeComponentsPanel;
        document.getElementById('close-stats-btn').onclick = closeStatsPanel;

        // Hide search results when clicking elsewhere
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('#search-container')) {{
                document.getElementById('search-results').style.display = 'none';
            }}
        }});

        console.log("Enhanced interactive controls initialized.");
        console.log("Components data:", COMPONENTS_DATA);
        console.log("Available features: Search, Statistics, Component Analysis");
    }});
</script>
"""

    final_html = html_content.replace("</body>", injection_html + "</body>")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_html)

    abs_path = os.path.abspath(filename)
    logger.info("Interactive graph visualization saved to: %s", abs_path)

    try:
        webbrowser.open(f"file://{abs_path}")
        logger.info("Visualization page opened in default browser")
    except OSError:
        logger.warning("Unable to automatically open browser")
        logger.info("Please manually open file: %s", abs_path)

    return abs_path
