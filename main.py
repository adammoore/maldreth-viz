import os
import logging
import math
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
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Color palette
COLORS = {
    'primary': '#3498db',
    'secondary': '#2c3e50',
    'accent': '#e74c3c',
    'background': '#ecf0f1',
    'text': '#34495e'
}

# Define layout with improved UI/UX and responsive design
app.layout = dbc.Container([
    html.H1("MaLDReTH Research Data Lifecycle", className="text-center my-4", style={'color': COLORS['primary']}),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    cyto.Cytoscape(
                        id='lifecycle-graph',
                        style={'width': '100%', 'height': '600px'},
                        layout={
                            'name': 'circle',
                            'radius': 250
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
                                    'color': COLORS['background'],
                                    'shape': 'round-rectangle',
                                    'width': '120px',
                                    'height': '60px',
                                    'font-size': '14px',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '100px',
                                    'transition-property': 'background-color',
                                    'transition-duration': '0.3s'
                                }
                            },
                            {
                                'selector': 'edge',
                                'style': {
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle',
                                    'line-color': COLORS['secondary'],
                                    'target-arrow-color': COLORS['secondary'],
                                    'width': 2
                                }
                            },
                            {
                                'selector': '.highlighted',
                                'style': {
                                    'background-color': COLORS['accent'],
                                    'border-color': COLORS['accent'],
                                    'border-width': '3px',
                                    'transition-property': 'background-color, border-color, border-width',
                                    'transition-duration': '0.3s'
                                }
                            }
                        ]
                    )
                ])
            ], className="mb-4 shadow")
        ], width=12, lg=8),
        dbc.Col([
            html.H3("Stage Details", className="mb-3", style={'color': COLORS['secondary']}),
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='stage-details', className="mb-3"),
                    html.H4("Substages", className="mb-2", style={'color': COLORS['secondary']}),
                    dash_table.DataTable(
                        id='substage-table',
                        columns=[
                            {"name": "Substage", "id": "substagename"},
                            {"name": "Description", "id": "substagedesc"}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                        },
                        style_header={
                            'backgroundColor': COLORS['primary'],
                            'color': COLORS['background'],
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['background']}
                        ],
                    )
                ])
            ], className="mb-4 shadow")
        ], width=12, lg=4),
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Tools", className="mb-3", style={'color': COLORS['secondary']}),
            dbc.Card([
                dbc.CardBody([
                    dash_table.DataTable(
                        id='tools-table',
                        columns=[
                            {"name": "Tool Name", "id": "ToolName"},
                            {"name": "Description", "id": "ToolDesc"},
                            {"name": "Link", "id": "ToolLink", "presentation": "markdown"},
                            {"name": "Provider", "id": "ToolProvider"}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                        },
                        style_header={
                            'backgroundColor': COLORS['primary'],
                            'color': COLORS['background'],
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['background']}
                        ],
                        sort_action='native',
                        filter_action='native',
                        page_action='native',
                        page_size=5,
                    ),
                    dbc.Button("Add Tool", color="success", id="add-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Update Tool", color="info", id="update-tool-btn", className="mt-3 me-2"),
                    dbc.Button("Delete Tool", color="danger", id="delete-tool-btn", className="mt-3")
                ])
            ], className="mb-4 shadow")
        ], width=12)
    ])
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})


@app.callback(
    Output('lifecycle-graph', 'elements'),
    Input('lifecycle-graph', 'id')
)
def update_lifecycle_graph(_):
    conn = create_connection(DB_FILE)
    if not conn:
        return []

    try:
        # Fetch stages with their IDs
        stages_query = "SELECT rowid, stage, stagedesc FROM LifeCycle"
        stages = pd.read_sql_query(stages_query, conn)

        # Fetch connections
        edges_query = "SELECT start, end FROM CycleConnects"
        edges = pd.read_sql_query(edges_query, conn)

        # Create nodes
        elements = [
            {
                'data': {
                    'id': str(row['rowid']),
                    'label': row['stage'],
                    'title': row['stagedesc']
                }
            } for _, row in stages.iterrows()
        ]

        # Create a mapping of stage rowids to their positions in the elements list
        id_to_index = {str(row['rowid']): i for i, row in stages.iterrows()}

        # Add edges
        for _, edge in edges.iterrows():
            start_id = str(edge['start'])
            end_id = str(edge['end'])
            if start_id in id_to_index and end_id in id_to_index:
                elements.append({
                    'data': {
                        'source': start_id,
                        'target': end_id,
                        'id': f"{start_id}-{end_id}"
                    }
                })

        return elements
    except pd.errors.DatabaseError as e:
        logging.error(f"Error querying database: {e}")
        return []
    finally:
        conn.close()


@app.callback(
    [Output('stage-details', 'children'),
     Output('substage-table', 'data'),
     Output('tools-table', 'data'),
     Output('lifecycle-graph', 'stylesheet')],
    [Input('lifecycle-graph', 'tapNodeData')]
)
def update_stage_details(node_data):
    if not node_data:
        raise PreventUpdate

    conn = create_connection(DB_FILE)
    if not conn:
        return html.Div("Database connection error"), [], [], []

    try:
        # Fetch stage details
        stage_query = "SELECT stage, stagedesc FROM LifeCycle WHERE rowid = ?"
        stage_details = pd.read_sql_query(stage_query, conn, params=(node_data['id'],))

        # Handle case where no stage details are found
        if stage_details.empty:
            stage_name = "Unknown Stage"
            stage_desc = "No description available"
        else:
            stage_name = stage_details.iloc[0]['stage']
            stage_desc = stage_details.iloc[0]['stagedesc']

        # Fetch substages
        substages_query = "SELECT substagename, substagedesc FROM SubStage WHERE stage = ?"
        substages = pd.read_sql_query(substages_query, conn, params=(stage_name,))

        # Fetch tools
        tools_query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
        tools = pd.read_sql_query(tools_query, conn, params=(stage_name,))

        # Update stylesheet to highlight selected node
        stylesheet = [
            {
                'selector': 'node',
                'style': {
                    'content': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': COLORS['primary'],
                    'color': COLORS['background'],
                    'shape': 'round-rectangle',
                    'width': '120px',
                    'height': '60px',
                    'font-size': '14px',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'transition-property': 'background-color',
                    'transition-duration': '0.3s'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'line-color': COLORS['secondary'],
                    'target-arrow-color': COLORS['secondary'],
                    'width': 2
                }
            },
            {
                'selector': f'node[id = "{node_data["id"]}"]',
                'style': {
                    'background-color': COLORS['accent'],
                    'border-color': COLORS['accent'],
                    'border-width': '3px',
                }
            }
        ]

        return (
            html.Div([
                html.H4(stage_name, style={'color': COLORS['primary']}),
                html.P(stage_desc)
            ]),
            substages.to_dict('records'),
            tools.to_dict('records'),
            stylesheet
        )
    except pd.errors.DatabaseError as e:
        logging.error(f"Error querying database: {e}")
        return html.Div("Error fetching data"), [], [], []
    finally:
        conn.close()


# Add callbacks for adding, updating, and deleting tools here

if __name__ == '__main__':
    app.run_server(debug=True)