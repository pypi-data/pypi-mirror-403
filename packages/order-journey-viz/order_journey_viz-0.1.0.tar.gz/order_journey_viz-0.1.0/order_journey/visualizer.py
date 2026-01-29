import pandas as pd
from collections import defaultdict
import json
from datetime import datetime, timedelta

class OrderJourneyVisualizer:
    """
    Visualize order status transitions from a dataset with Orders, Status, and Timestamp columns.
    Handles cyclic flows (orders going back and forth between statuses).
    """
    
    def __init__(self, df, order_col='order_id', status_col='status', timestamp_col='timestamp'):
        """
        Initialize the visualizer with a dataframe.
        
        Args:
            df: pandas DataFrame with order journey data
            order_col: name of the order ID column
            status_col: name of the status column
            timestamp_col: name of the timestamp column
        """
        self.df = df.copy()
        self.order_col = order_col
        self.status_col = status_col
        self.timestamp_col = timestamp_col
        
        # Sort by order and timestamp
        self.df = self.df.sort_values([order_col, timestamp_col])
        
        # Store computed graph data
        self.nodes = []
        self.edges = []
        self.stats = {}
        
    def build_graph(self):
        """
        Build the state transition graph from the order data.
        Calculates nodes (statuses) and edges (transitions).
        """
        # Track transitions and their frequencies
        transitions = defaultdict(int)
        node_counts = defaultdict(int)
        transition_times = defaultdict(list)
        
        # Group by order to track each order's journey
        for order_id, group in self.df.groupby(self.order_col):
            statuses = group[self.status_col].tolist()
            timestamps = pd.to_datetime(group[self.timestamp_col]).tolist()
            
            # Track each transition
            for i in range(len(statuses)):
                node_counts[statuses[i]] += 1
                
                if i < len(statuses) - 1:
                    from_status = statuses[i]
                    to_status = statuses[i + 1]
                    transition_key = (from_status, to_status)
                    transitions[transition_key] += 1
                    
                    # Calculate time spent in transition
                    time_diff = (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600  # hours
                    transition_times[transition_key].append(time_diff)
        
        # Create nodes
        for status, count in node_counts.items():
            self.nodes.append({
                'id': status,
                'label': status,
                'count': count
            })
        
        # Create edges with statistics
        for (from_status, to_status), count in transitions.items():
            avg_time = sum(transition_times[(from_status, to_status)]) / len(transition_times[(from_status, to_status)])
            
            self.edges.append({
                'source': from_status,
                'target': to_status,
                'count': count,
                'avg_time_hours': round(avg_time, 2),
                'label': f"{count} orders\n~{round(avg_time, 1)}h"
            })
        
        # Store statistics
        self.stats = {
            'total_orders': self.df[self.order_col].nunique(),
            'total_transitions': sum(transitions.values()),
            'unique_statuses': len(node_counts)
        }
        
        return self
    
    def generate_html(self, output_file='order_journey.html'):
        """
        Generate an interactive HTML visualization using Cytoscape.js
        """
        # Get all unique statuses and order IDs for filters
        all_statuses = sorted(list(set([node['id'] for node in self.nodes])))
        all_orders = sorted(self.df[self.order_col].unique().tolist())
        
        # Prepare data for Cytoscape
        cytoscape_elements = []
        
        # Add nodes with additional metadata
        for node in self.nodes:
            cytoscape_elements.append({
                'data': {
                    'id': node['id'],
                    'label': f"{node['label']}\n({node['count']} orders)",
                    'count': node['count']
                }
            })
        
        # Add edges with additional metadata
        for i, edge in enumerate(self.edges):
            cytoscape_elements.append({
                'data': {
                    'id': f"edge_{i}",
                    'source': edge['source'],
                    'target': edge['target'],
                    'label': edge['label'],
                    'weight': edge['count'],
                    'count': edge['count']
                }
            })
        
        # Get order-to-statuses mapping for filtering
        order_status_map = {}
        for order_id, group in self.df.groupby(self.order_col):
            order_status_map[order_id] = group[self.status_col].unique().tolist()
        
        # Create HTML with embedded Cytoscape.js
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Order Journey Visualizer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        .header {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat-item {{
            flex: 1;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .main-content {{
            display: flex;
            gap: 20px;
        }}
        
        .sidebar {{
            width: 300px;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: fit-content;
        }}
        
        .viz-container {{
            flex: 1;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        #cy {{
            width: 100%;
            height: 700px;
            background-color: #fafafa;
        }}
        
        .control-section {{
            margin-bottom: 25px;
        }}
        
        .control-section h3 {{
            margin: 0 0 12px 0;
            font-size: 16px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
        }}
        
        .filter-group {{
            margin-bottom: 15px;
        }}
        
        .filter-group label {{
            display: block;
            margin-bottom: 6px;
            font-size: 13px;
            font-weight: 600;
            color: #34495e;
        }}
        
        select, input[type="text"] {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }}
        
        select[multiple] {{
            height: 120px;
        }}
        
        button {{
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        .btn-primary {{
            background-color: #3498db;
            color: white;
        }}
        
        .btn-primary:hover {{
            background-color: #2980b9;
        }}
        
        .btn-secondary {{
            background-color: #95a5a6;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background-color: #7f8c8d;
        }}
        
        .btn-success {{
            background-color: #27ae60;
            color: white;
        }}
        
        .btn-success:hover {{
            background-color: #229954;
        }}
        
        .layout-btn {{
            padding: 8px;
            margin: 3px 0;
            font-size: 12px;
        }}
        
        .layout-btn.active {{
            background-color: #e74c3c;
        }}
        
        .hint {{
            font-size: 11px;
            color: #7f8c8d;
            margin-top: 5px;
            font-style: italic;
        }}
        
        .export-section {{
            margin-top: 10px;
        }}
        
        .legend {{
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .legend-item {{
            margin: 8px 0;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📦 Order Journey Visualizer</h1>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="total-orders">{self.stats['total_orders']}</div>
                    <div class="stat-label">Total Orders</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-transitions">{self.stats['total_transitions']}</div>
                    <div class="stat-label">Total Transitions</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="unique-statuses">{self.stats['unique_statuses']}</div>
                    <div class="stat-label">Unique Statuses</div>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <!-- Filters Section -->
                <div class="control-section">
                    <h3>🔍 Filters</h3>
                    
                    <div class="filter-group">
                        <label>Filter by Status:</label>
                        <select id="status-filter" multiple>
                            <option value="all" selected>All Statuses</option>
                            {"".join([f'<option value="{status}">{status}</option>' for status in all_statuses])}
                        </select>
                        <div class="hint">Hold Ctrl/Cmd to select multiple</div>
                    </div>
                    
                    <div class="filter-group">
                        <label>Filter by Order ID:</label>
                        <select id="order-filter" multiple>
                            <option value="all" selected>All Orders</option>
                            {"".join([f'<option value="{order}">{order}</option>' for order in all_orders])}
                        </select>
                        <div class="hint">Hold Ctrl/Cmd to select multiple</div>
                    </div>
                    
                    <button class="btn-primary" onclick="applyFilters()">Apply Filters</button>
                    <button class="btn-secondary" onclick="resetFilters()">Reset Filters</button>
                </div>
                
                <!-- Layout Section -->
                <div class="control-section">
                    <h3>🎨 Layout Style</h3>
                    <button class="layout-btn btn-primary" onclick="changeLayout('dagre')">Dagre (Flow)</button>
                    <button class="layout-btn btn-primary" onclick="changeLayout('breadthfirst')">Hierarchical</button>
                    <button class="layout-btn btn-primary active" onclick="changeLayout('circle')">Circle</button>
                    <button class="layout-btn btn-primary" onclick="changeLayout('grid')">Grid</button>
                    <button class="layout-btn btn-primary" onclick="changeLayout('concentric')">Concentric</button>
                </div>
                
                <!-- Export Section -->
                <div class="control-section">
                    <h3>💾 Export</h3>
                    <button class="btn-success" onclick="exportImage('png')">Export as PNG</button>
                    <button class="btn-success" onclick="exportImage('jpg')">Export as JPEG</button>
                </div>
            </div>
            
            <div class="viz-container">
                <div id="cy"></div>
            </div>
        </div>
        
        <div class="legend">
            <h3>💡 How to Use:</h3>
            <div class="legend-item">🔵 <strong>Nodes (circles)</strong> = Order statuses with total count</div>
            <div class="legend-item">➡️ <strong>Arrows</strong> = Transitions between statuses (thickness = frequency)</div>
            <div class="legend-item">📊 <strong>Edge labels</strong> = Number of orders + average time in transition</div>
            <div class="legend-item">🖱️ <strong>Drag nodes</strong> to rearrange, <strong>scroll to zoom</strong>, <strong>click</strong> for details</div>
            <div class="legend-item">🎯 Use filters to focus on specific statuses or orders</div>
        </div>
    </div>
    
    <script>
        // Store original data and order-status mapping
        const originalElements = {json.dumps(cytoscape_elements)};
        const orderStatusMap = {json.dumps(order_status_map)};
        let cy;
        
        // Initialize Cytoscape
        function initCytoscape(elements) {{
            if (cy) {{
                cy.destroy();
            }}
            
            cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'background-color': '#3498db',
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#fff',
                            'text-outline-color': '#3498db',
                            'text-outline-width': 2,
                            'font-size': '12px',
                            'width': 'mapData(count, 0, 100, 60, 120)',
                            'height': 'mapData(count, 0, 100, 60, 120)',
                            'font-weight': 'bold'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 'mapData(weight, 0, 100, 2, 10)',
                            'line-color': '#95a5a6',
                            'target-arrow-color': '#95a5a6',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(label)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10,
                            'color': '#2c3e50',
                            'text-background-color': '#fff',
                            'text-background-opacity': 0.9,
                            'text-background-padding': '3px',
                            'arrow-scale': 1.5
                        }}
                    }},
                    {{
                        selector: 'node:selected',
                        style: {{
                            'background-color': '#e74c3c',
                            'text-outline-color': '#e74c3c'
                        }}
                    }},
                    {{
                        selector: 'edge:selected',
                        style: {{
                            'line-color': '#e74c3c',
                            'target-arrow-color': '#e74c3c',
                            'width': 6
                        }}
                    }}
                ],
                layout: {{
                    name: 'circle',
                    padding: 50
                }}
            }});
            
            // Add click handlers
            cy.on('tap', 'node', function(evt) {{
                const node = evt.target;
                alert('Status: ' + node.data('id') + '\\nTotal Orders: ' + node.data('count'));
            }});
            
            cy.on('tap', 'edge', function(evt) {{
                const edge = evt.target;
                alert('Transition: ' + edge.data('source') + ' → ' + edge.data('target') + 
                      '\\nOrders: ' + edge.data('count'));
            }});
        }}
        
        // Initialize on page load
        initCytoscape(originalElements);
        
        // Filter functions
        function applyFilters() {{
            const statusSelect = document.getElementById('status-filter');
            const orderSelect = document.getElementById('order-filter');
            
            const selectedStatuses = Array.from(statusSelect.selectedOptions).map(opt => opt.value);
            const selectedOrders = Array.from(orderSelect.selectedOptions).map(opt => opt.value);
            
            // If "all" is selected or nothing is selected, include all
            const includeAllStatuses = selectedStatuses.includes('all') || selectedStatuses.length === 0;
            const includeAllOrders = selectedOrders.includes('all') || selectedOrders.length === 0;
            
            // Filter elements
            let filteredElements = originalElements.filter(ele => {{
                if (ele.data.id && !ele.data.source) {{
                    // This is a node
                    if (!includeAllStatuses && !selectedStatuses.includes(ele.data.id)) {{
                        return false;
                    }}
                    
                    // Check if this status belongs to any selected order
                    if (!includeAllOrders) {{
                        const statusInSelectedOrder = selectedOrders.some(orderId => 
                            orderStatusMap[orderId] && orderStatusMap[orderId].includes(ele.data.id)
                        );
                        if (!statusInSelectedOrder) return false;
                    }}
                    
                    return true;
                }} else if (ele.data.source && ele.data.target) {{
                    // This is an edge - include if both source and target nodes are included
                    return true; // Will be filtered automatically by Cytoscape if nodes are missing
                }}
                return true;
            }});
            
            // Get valid node IDs
            const validNodeIds = new Set(
                filteredElements
                    .filter(e => e.data.id && !e.data.source)
                    .map(e => e.data.id)
            );
            
            // Filter edges to only include those between valid nodes
            filteredElements = filteredElements.filter(ele => {{
                if (ele.data.source && ele.data.target) {{
                    return validNodeIds.has(ele.data.source) && validNodeIds.has(ele.data.target);
                }}
                return true;
            }});
            
            initCytoscape(filteredElements);
            
            // Update stats
            const nodes = filteredElements.filter(e => e.data.id && !e.data.source);
            const edges = filteredElements.filter(e => e.data.source);
            document.getElementById('unique-statuses').textContent = nodes.length;
            document.getElementById('total-transitions').textContent = edges.length;
        }}
        
        function resetFilters() {{
            document.getElementById('status-filter').selectedIndex = 0;
            document.getElementById('order-filter').selectedIndex = 0;
            initCytoscape(originalElements);
            document.getElementById('unique-statuses').textContent = {self.stats['unique_statuses']};
            document.getElementById('total-transitions').textContent = {self.stats['total_transitions']};
        }}
        
        // Layout functions
        function changeLayout(layoutName) {{
            // Remove active class from all buttons
            document.querySelectorAll('.layout-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Add active class to clicked button
            event.target.classList.add('active');
            
            let layoutOptions = {{}};
            
            switch(layoutName) {{
                case 'dagre':
                    layoutOptions = {{
                        name: 'dagre',
                        rankDir: 'LR',
                        nodeSep: 100,
                        rankSep: 150,
                        padding: 50
                    }};
                    break;
                case 'breadthfirst':
                    layoutOptions = {{
                        name: 'breadthfirst',
                        directed: true,
                        padding: 50,
                        spacingFactor: 1.5
                    }};
                    break;
                case 'circle':
                    layoutOptions = {{
                        name: 'circle',
                        padding: 50
                    }};
                    break;
                case 'grid':
                    layoutOptions = {{
                        name: 'grid',
                        padding: 50,
                        rows: undefined,
                        cols: undefined
                    }};
                    break;
                case 'concentric':
                    layoutOptions = {{
                        name: 'concentric',
                        padding: 50,
                        concentric: function(node) {{
                            return node.data('count');
                        }},
                        levelWidth: function() {{
                            return 2;
                        }}
                    }};
                    break;
            }}
            
            cy.layout(layoutOptions).run();
        }}
        
        // Export functions
        function exportImage(format) {{
            const options = {{
                output: 'blob',
                bg: 'white',
                full: true,
                scale: 3
            }};
            
            if (format === 'png') {{
                const blob = cy.png(options);
                downloadBlob(blob, 'order_journey.png');
            }} else if (format === 'jpg') {{
                const blob = cy.jpg(options);
                downloadBlob(blob, 'order_journey.jpg');
            }}
        }}
        
        function downloadBlob(blob, filename) {{
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Visualization saved to {output_file}")
        print(f"📊 Stats: {self.stats['total_orders']} orders, {self.stats['total_transitions']} transitions, {self.stats['unique_statuses']} unique statuses")
        return output_file


# Example usage with sample data
def create_sample_data():
    """Create sample order data with back-and-forth transitions"""
    data = []
    base_time = datetime(2024, 1, 1)
    
    # Order 1: Smooth journey
    data.extend([
        {'order_id': 'ORD001', 'status': 'Pending', 'timestamp': base_time},
        {'order_id': 'ORD001', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=2)},
        {'order_id': 'ORD001', 'status': 'Shipped', 'timestamp': base_time + timedelta(days=1)},
        {'order_id': 'ORD001', 'status': 'Delivered', 'timestamp': base_time + timedelta(days=3)},
    ])
    
    # Order 2: Has issues - goes back and forth
    data.extend([
        {'order_id': 'ORD002', 'status': 'Pending', 'timestamp': base_time + timedelta(hours=1)},
        {'order_id': 'ORD002', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=3)},
        {'order_id': 'ORD002', 'status': 'Failed', 'timestamp': base_time + timedelta(hours=5)},
        {'order_id': 'ORD002', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=8)},
        {'order_id': 'ORD002', 'status': 'Shipped', 'timestamp': base_time + timedelta(days=2)},
        {'order_id': 'ORD002', 'status': 'Delivered', 'timestamp': base_time + timedelta(days=4)},
    ])
    
    # Order 3: Cancelled journey
    data.extend([
        {'order_id': 'ORD003', 'status': 'Pending', 'timestamp': base_time + timedelta(hours=4)},
        {'order_id': 'ORD003', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=6)},
        {'order_id': 'ORD003', 'status': 'Cancelled', 'timestamp': base_time + timedelta(hours=7)},
    ])
    
    # Order 4: Another back-and-forth
    data.extend([
        {'order_id': 'ORD004', 'status': 'Pending', 'timestamp': base_time + timedelta(hours=2)},
        {'order_id': 'ORD004', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=4)},
        {'order_id': 'ORD004', 'status': 'Failed', 'timestamp': base_time + timedelta(hours=6)},
        {'order_id': 'ORD004', 'status': 'Pending', 'timestamp': base_time + timedelta(hours=10)},
        {'order_id': 'ORD004', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=12)},
        {'order_id': 'ORD004', 'status': 'Shipped', 'timestamp': base_time + timedelta(days=2)},
        {'order_id': 'ORD004', 'status': 'Delivered', 'timestamp': base_time + timedelta(days=5)},
    ])
    
    # Order 5: Smooth journey
    data.extend([
        {'order_id': 'ORD005', 'status': 'Pending', 'timestamp': base_time + timedelta(hours=3)},
        {'order_id': 'ORD005', 'status': 'Processing', 'timestamp': base_time + timedelta(hours=5)},
        {'order_id': 'ORD005', 'status': 'Shipped', 'timestamp': base_time + timedelta(days=1, hours=2)},
        {'order_id': 'ORD005', 'status': 'Delivered', 'timestamp': base_time + timedelta(days=3, hours=5)},
    ])
    
    return pd.DataFrame(data)


# if __name__ == "__main__":
#     # Create sample data
#     print("📦 Creating sample order data...")
#     df = create_sample_data()
#     print(f"Created {len(df)} status records for {df['order_id'].nunique()} orders")
#     print("\nSample data:")
#     print(df.head(10))
    
#     # Create visualizer
#     print("\n🔧 Building order journey graph...")
#     viz = OrderJourneyVisualizer(df)
#     viz.build_graph()
    
#     # Generate HTML
#     print("\n🎨 Generating interactive visualization...")
#     output_file = viz.generate_html('order_journey.html')
    
#     print(f"\n✨ Done! Open {output_file} in your browser to see the visualization.")
#     print("\nThe visualization shows:")
#     print("  - Nodes = Order statuses (size shows frequency)")
#     print("  - Arrows = Transitions (thickness shows how many orders took that path)")
#     print("  - Labels = Number of orders + average time spent in transition")
