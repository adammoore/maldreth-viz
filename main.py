import os
import logging
from dash import Dash, html, dcc, Input, Output, State, callback_context, no_update, dash_table
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
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])

# Color palette
COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'background': '#43a40',
    'text': '#f8a94a'
}

# Define layout with improved UI/UX and STEM-oriented styling
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
                        layout={'name': 'dagre', 'padding': 50},
                        elements=[],
                        stylesheet=[
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'text-valign': 'center',
                                    'text-halign': 'center',
                                    'background-color': COLORS['primary'],
                                    'color': COLORS['text'],
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
                                    'line-color': COLORS['danger'],
                                    'target-arrow-color': COLORS['danger']
                                }
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'background-color': COLORS['success'],
                                    'line-color': COLORS['success'],
                                    'target-arrow-color': COLORS['success'],
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
                    html.H4(id='stage-name', className="mb-3"),
                    html.P(id='stage-description', className="mb-3"),
                    cyto.Cytoscape(
                        id='stage-details-graph',
                        style={'width': '100%', 'height': '400px'},
                        elements=[],
                        stylesheet=[
                            {
                                'selector': 'node',
                                'style': {
                                    'content': 'data(label)',
                                    'text-valign': 'center',
                                    'text-halign': 'center',
                                    'background-color': COLORS['secondary'],
                                    'color': COLORS['text'],
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
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'background-color': COLORS['success'],
                                    'line-color': COLORS['success'],
                                    'target-arrow-color': COLORS['success'],
                                    'transition-property': 'background-color, line-color, target-arrow-color',
                                    'transition-duration': '0.5s'
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
                            'color': COLORS['text'],
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['secondary']}
                        ],
                    )
                ], label="Substages"),
                dbc.Tab([
                    dash_table.DataTable(
                        id='tools-table',
                        columns=[
                            {"name": "Tool Name", "id": "ToolName"},
                            {"name": "Description", "id": "ToolDesc"},
                            {"name": "Link", "id": "ToolLink", "presentation": "markdown"},
                            {"name": "Provider", "id": "ToolProvider"}
                        ],
                        data=[],
                        editable=True,
                        row_deletable=True,
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
                            'color': COLORS['text'],
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['secondary']}
                        ]
                    ),
                    dbc.Button("Add Tool", color="success", id="add-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Update Tool", color="primary", id="update-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Delete Tool", color="danger", id="delete-tool-btn", className="mt-3")
                ], label="Tools")
            ])
        ], width=12),
    ])
], fluid=True, style={'backgroundColor': COLORS['background'], 'color': COLORS['text'], 'minHeight': '100vh'})

@app.callback(
    Output('lifecycle-graph', 'elements'),
    Input('lifecycle-graph', 'tapNodeData')
)
def update_graph_elements(tapped_node):
    conn = create_connection(DB_FILE)
    if not conn:
        return []

    try:
        stages = get_lifecycle_stages(conn)
        connections = get_cycle_connections(conn)

        # Create node elements
        elements = [{'data': {'id': row['stage'], 'label': row['stage'], 'title': row['stagedesc']}} for _, row in stages.iterrows()]

        # Create edge elements, ensuring both source and target nodes exist
        for _, row in connections.iterrows():
            source = row['start']
            target = row['end']
            if source in stages['stage'].values and target in stages['stage'].values:
                elements.append({'data': {'source': source, 'target': target, 'type': row['type']}})
            else:
                logging.warning(f"Skipping edge {source} -> {target} due to missing node(s)")

        if tapped_node:
            for element in elements:
                if element['data']['label'] == tapped_node['label']:
                    element['classes'] = 'highlighted'

        return elements
    except pd.errors.DatabaseError as e:
        logging.error(f"Error querying database: {e}")
        return []
    finally:
        conn.close()

@app.callback(
    Output('stage-name', 'children'),
    Output('stage-description', 'children'),
    Output('substage-table', 'data'),
    Output('tools-table', 'data'),
    Output('stage-details-graph', 'elements'),
    Input('lifecycle-graph', 'tapNodeData')
)
def update_substage_and_tools(tapped_node):
    conn = create_connection(DB_FILE)
    if not conn:
        return '', '', [], [], []

    try:
        if tapped_node:
            stage = tapped_node['label']
            stage_info = get_stage_info(conn, stage)
            stage_name = stage_info['stage']
            stage_description = stage_info['description']

            substages = get_substages(conn, stage)
            tools = get_tools(conn, stage)

            substage_data = substages.to_dict('records')
            tools_data = tools.to_dict('records')

            # Create stage details graph elements
            stage_details_elements = [
                {"data": {"id": stage, "label": stage}, "classes": "highlighted"}
            ]
            for _, row in substages.iterrows():
                sub_id = f"sub_{row['substagename']}"
                stage_details_elements.append({"data": {"id": sub_id, "label": row['substagename']}, "classes": "highlighted"})
                stage_details_elements.append({"data": {"source": stage, "target": sub_id}})
            for _, row in tools.iterrows():
                tool_id = f"tool_{row['ToolName']}"
                stage_details_elements.append({"data": {"id": tool_id, "label": row['ToolName']}, "classes": "highlighted"})
                stage_details_elements.append({"data": {"source": stage, "target": tool_id}})

            return stage_name, stage_description, substage_data, tools_data, stage_details_elements
        else:
            return '', '', [], [], []
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return '', '', [], [], []
    finally:
        conn.close()

def get_stage_info(conn, stage):
    query = "SELECT stage, stagedesc FROM LifeCycle WHERE stage = ?"
    result = pd.read_sql_query(query, conn, params=(stage,)).iloc[0]
    return {'stage': result['stage'], 'description': result['stagedesc']}

def get_substages(conn, stage):
    query = "SELECT substagename, substagedesc, exemplar FROM SubStage WHERE stage = ?"
    return pd.read_sql_query(query, conn, params=(stage,))

def get_tools(conn, stage):
    query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
    return pd.read_sql_query(query, conn, params=(stage,))

def get_lifecycle_stages(conn):
    query = "SELECT stage, stagedesc FROM LifeCycle"
    return pd.read_sql_query(query, conn)

def get_cycle_connections(conn):
    query = "SELECT start, end, type FROM CycleConnects"
    return pd.read_sql_query(query, conn)

if __name__ == '__main__':
    app.run_server(debug=True)