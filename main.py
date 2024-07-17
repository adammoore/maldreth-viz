import os
import logging
from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update, dash_table, dash
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
from dash.exceptions import PreventUpdate

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import the dagre layout for Cytoscape
cyto.load_extra_layouts()

# Database setup
DB_FILE = 'research_data_lifecycle.db'


def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
    return None


# Define Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

# Color palette
COLORS = {
    'primary': '#3498db',
    'secondary': '#2ecc71',
    'background': '#f8f9fa',
    'text': '#2c3e50'
}

# Define layout with improved UI/UX and subtle coloring
app.layout = dbc.Container([
    html.H1("MaLDReTH Research Data Lifecycle", className="text-center my-4", style={'color': COLORS['primary']}),
    dbc.Row([
        dbc.Col([
            html.H3("Lifecycle Graph", className="mb-3", style={'color': COLORS['secondary']}),
            dbc.Card([
                dbc.CardBody([
                    cyto.Cytoscape(
                        id='lifecycle-graph',
                        style={'width': '100%', 'height': '600px'},
                        layout={
                            'name': 'circle',
                            'padding': 50
                        },
                        elements=[],
                        stylesheet=[
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'text-valign': 'center',
                                    'text-halign': 'center',
                                    'background-color': COLORS['primary'],
                                    'color': '#ffffff',
                                    'shape': 'rectangle',
                                    'width': '120px',
                                    'height': '60px',
                                    'font-size': '14px',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '100px'
                                }
                            },
                            {
                                'selector': 'edge',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle',
                                    'line-color': COLORS['secondary'],
                                    'target-arrow-color': COLORS['secondary']
                                }
                            },
                            {
                                'selector': 'edge[type = "alternative"]',
                                'style': {
                                    'line-style': 'dashed',
                                    'line-dash-pattern': [6, 3],
                                    'line-color': '#999',
                                    'target-arrow-color': '#999'
                                }
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'background-color': '#FFD700',
                                    'line-color': '#FFD700',
                                    'target-arrow-color': '#FFD700',
                                    'transition-property': 'background-color, line-color, target-arrow-color',
                                    'transition-duration': '0.5s'
                                }
                            }
                        ]

                    )
                ])
            ], className="mb-4", style={'backgroundColor': COLORS['background']})
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Stage Details", className="mt-4 mb-3", style={'color': COLORS['secondary']}),
            dbc.Card([
                dbc.CardBody([
                    cyto.Cytoscape(
                        id='stage-details-graph',
                        style={'width': '100%', 'height': '400px'},
                        layout={'name': 'breadthfirst', 'roots': '#Access'},
                        elements=[],
                        stylesheet=[
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'text-valign': 'center',
                                    'text-halign': 'center',
                                    'background-color': COLORS['secondary'],
                                    'color': '#ffffff',
                                    'shape': 'round-rectangle',
                                    'width': '120px',
                                    'height': '40px',
                                    'font-size': '12px',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '100px'
                                }
                            },
                            {
                                'selector': 'edge',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle',
                                    'line-color': COLORS['primary'],
                                    'target-arrow-color': COLORS['primary']
                                }
                            }
                        ]
                    )
                ])
            ], style={'backgroundColor': COLORS['background']})
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Substages and Tools", className="mb-3", style={'color': COLORS['secondary']}),
            dbc.Tabs([
                dbc.Tab([
                    dash_table.DataTable(
                        id='substage-table',
                        columns=[
                            {"name": "Substage Name", "id": "substagename"},
                            {"name": "Description", "id": "substagedesc"},
                            {"name": "Exemplars", "id": "exemplar"}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'color': COLORS['text']
                        },
                        style_header={
                            'backgroundColor': COLORS['primary'],
                            'color': '#ffffff',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['background']}
                        ],
                    )
                ], label="Substages"),
                dbc.Tab([
                    dash_table.DataTable(
                        id='tools-table',
                        columns=[
                            {"name": "Tool Name", "id": "ToolName"},
                            {"name": "Description", "id": "ToolDesc"},
                            {"name": "Link", "id": "ToolLink"},
                            {"name": "Provider", "id": "ToolProvider"}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'color': COLORS['text']
                        },
                        style_header={
                            'backgroundColor': COLORS['primary'],
                            'color': '#ffffff',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['background']}
                        ],
                    ),
                    dbc.Button("Add Tool", color="primary", id="add-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Update Tool", color="secondary", id="update-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Delete Tool", color="danger", id="delete-tool-btn", className="mt-3")
                ], label="Tools")
            ])
        ], width=12),
    ])
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})

@app.callback(
    Output('lifecycle-graph', 'elements'),
    Input('lifecycle-graph', 'tapNodeData')
)
def update_graph_elements(tapped_node):
    conn = create_connection(DB_FILE)
    if not conn:
        return []

    try:
        nodes_query = "SELECT stage, stagedesc FROM LifeCycle"
        nodes = pd.read_sql_query(nodes_query, conn)
        edges_query = "SELECT start, end, type FROM CycleConnects"
        edges = pd.read_sql_query(edges_query, conn)

        # Create a dictionary of nodes
        node_dict = {str(i+1): node['stage'] for i, node in enumerate(nodes.to_dict('records'))}

        # Create node elements
        elements = [{'data': {'id': str(i+1), 'label': node['stage'], 'title': node['stagedesc']}} for i, node in enumerate(nodes.to_dict('records'))]

        # Create edge elements, ensuring both source and target nodes exist
        for edge in edges.to_dict('records'):
            source = str(edge['start'])
            target = str(edge['end'])
            if source in node_dict and target in node_dict:
                elements.append({'data': {'source': source, 'target': target, 'type': edge['type']}})
            else:
                logging.warning(f"Skipping edge {source} -> {target} due to missing node(s)")

        if tapped_node:
            for element in elements:
                if element['data']['id'] == tapped_node['id']:
                    element['classes'] = 'highlighted'

        return elements
    except pd.errors.DatabaseError as e:
        logging.error(f"Error querying database: {e}")
        return []
    finally:
        conn.close()


@app.callback(
    Output('substage-table', 'data'),
    Output('tools-table', 'data'),
    Output('stage-details-graph', 'elements'),
    Input('lifecycle-graph', 'tapNodeData'),
    Input('add-tool-btn', 'n_clicks'),
    Input('update-tool-btn', 'n_clicks'),
    Input('delete-tool-btn', 'n_clicks'),
    State('tools-table', 'data'),
    State('tools-table', 'selected_rows')
)
def update_content(tapped_node, add_clicks, update_clicks, delete_clicks, tools_data, selected_rows):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    conn = create_connection(DB_FILE)
    if not conn:
        return [], [], []

    try:
        if tapped_node:
            selected_stage = pd.read_sql_query("SELECT stage FROM LifeCycle LIMIT 1 OFFSET ?", conn,
                                               params=(int(tapped_node['id']) - 1,)).iloc[0]['stage']
        else:
            selected_stage = None

        # Fetch substages data
        substages_query = """
        SELECT substagename, substagedesc, exemplar
        FROM SubStage
        WHERE stage = ? OR ? IS NULL
        """
        substages = pd.read_sql_query(substages_query, conn, params=(selected_stage, selected_stage))
        substage_data = substages.to_dict('records')

        # Fetch tools data
        tools_query = """
        SELECT ToolName, ToolDesc, ToolLink, ToolProvider
        FROM Tools
        WHERE stage = ? OR ? IS NULL
        """
        tools = pd.read_sql_query(tools_query, conn, params=(selected_stage, selected_stage))
        tools_data = tools.to_dict('records')

        # Create stage details graph elements
        stage_details_elements = [
            {'data': {'id': row['substagename'], 'label': row['substagename']}} for row in substage_data
        ]
        stage_details_elements.extend([
            {'data': {'id': row['ToolName'], 'label': row['ToolName']}} for row in tools_data
        ])
        stage_details_elements.extend([
            {'data': {'source': substage['substagename'], 'target': tool['ToolName']}}
            for substage in substage_data
            for tool in tools_data
        ])

        # Handle button clicks
        if button_id == 'add-tool-btn':
            new_tool = {
                'ToolName': 'New Tool',
                'ToolDesc': 'Description',
                'ToolLink': 'http://example.com',
                'ToolProvider': 'Provider',
                'stage': selected_stage
            }
            conn.execute("""
                INSERT INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage)
                VALUES (?, ?, ?, ?, ?)
            """, tuple(new_tool.values()))
            conn.commit()
            tools_data.append(new_tool)
        elif button_id == 'update-tool-btn' and selected_rows:
            selected_tool = tools_data[selected_rows[0]]
            conn.execute("""
                UPDATE Tools
                SET ToolDesc = ?, ToolLink = ?, ToolProvider = ?
                WHERE ToolName = ?
            """, (selected_tool['ToolDesc'], selected_tool['ToolLink'], selected_tool['ToolProvider'],
                  selected_tool['ToolName']))
            conn.commit()
        elif button_id == 'delete-tool-btn' and selected_rows:
            selected_tool = tools_data[selected_rows[0]]
            conn.execute("DELETE FROM Tools WHERE ToolName = ?", (selected_tool['ToolName'],))
            conn.commit()
            tools_data.pop(selected_rows[0])

        return substage_data, tools_data, stage_details_elements
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return [], [], []
    finally:
        conn.close()


if __name__ == '__main__':
    app.run_server(debug=True)