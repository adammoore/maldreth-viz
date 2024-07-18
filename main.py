"""
Research Data Lifecycle Tools Visualization Application

This application provides a visual representation of the research data lifecycle
and associated tools. It allows users to explore different stages of the lifecycle,
view and manage tools associated with each stage, and visualize the connections
between different stages and substages.

Author: Adam Vials Moore https://github.com/adammoore
Date: 2024-07-18
Version: 2.4
"""

import os
import logging
from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
from dash.exceptions import PreventUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "Research Data Lifecycle Tools Visualization"
app.config.suppress_callback_exceptions = True

# Database file
DB_FILE = 'research_data_lifecycle.db'

def get_db_connection():
    """Create a database connection."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_dataframe_from_db(query, params=()):
    """Fetch data from the SQLite database and return as a pandas DataFrame."""
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Error executing query: {e}")
        return pd.DataFrame()

# Fetch lifecycle stages
lifecycle_stages_df = get_dataframe_from_db("SELECT stage, stagedesc FROM LifeCycle")
lifecycle_stages = lifecycle_stages_df['stage'].tolist()

# Fetch cycle connections
cycle_connects_df = get_dataframe_from_db("SELECT start, end, type FROM CycleConnects")

# Fetch substages
substages_df = get_dataframe_from_db("SELECT stage, substagename AS substage FROM SubStage")

def create_full_lifecycle_elements():
    """Create nodes and edges for the full lifecycle graph."""
    # Create a mapping between numeric IDs and stage names
    stage_mapping = {i+1: stage for i, stage in enumerate(lifecycle_stages)}

    # Create nodes for all stages
    nodes = [
        {
            'data': {'id': stage, 'label': stage},
            'style': {'shape': 'rectangle', 'content': stage, 'background-color': '#E6F3FF', 'border-color': '#2E86C1', 'border-width': 2}
        }
        for stage in lifecycle_stages
    ]

    # Create edges based on cycle connections
    edges = []
    for _, row in cycle_connects_df.iterrows():
        start = stage_mapping.get(int(row['start']), row['start'])
        end = stage_mapping.get(int(row['end']), row['end'])
        if start in lifecycle_stages and end in lifecycle_stages:
            edges.append({
                'data': {
                    'source': start,
                    'target': end,
                    'label': row['type']
                },
                'style': {
                    'line-style': 'dashed' if row['type'] == 'optional' else 'solid',
                    'target-arrow-shape': 'triangle',
                    'line-color': '#2E86C1',
                    'target-arrow-color': '#2E86C1'
                }
            })
        else:
            logger.warning(f"Skipping edge {start} -> {end} due to missing node")

    return nodes + edges

def create_focused_stage_elements(stage):
    """Create nodes and edges for the focused stage graph."""
    substages = substages_df[substages_df['stage'] == stage]['substage'].tolist()
    nodes = [
        {
            'data': {'id': substage, 'label': substage},
            'style': {'shape': 'rectangle', 'content': substage, 'background-color': '#E6F3FF', 'border-color': '#2E86C1', 'border-width': 2}
        }
        for substage in substages
    ]
    edges = [
        {
            'data': {'source': substages[i], 'target': substages[i+1]},
            'style': {'target-arrow-shape': 'triangle', 'line-color': '#2E86C1', 'target-arrow-color': '#2E86C1'}
        }
        for i in range(len(substages)-1)
    ]
    return nodes + edges

# Updated app layout
app.layout = dbc.Container([
    html.H1("Research Data Lifecycle Tools", className="my-4"),
    dbc.Row([
        dbc.Col([
            html.H3("Full Lifecycle"),
            cyto.Cytoscape(
                id='full-lifecycle-graph',
                layout={'name': 'circle'},
                style={'width': '100%', 'height': '400px'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle'
                        }
                    }
                ]
            )
        ], width=6),
        dbc.Col([
            html.H3("Focused Stage"),
            dcc.Dropdown(
                id='stage-dropdown',
                options=[{'label': stage, 'value': stage} for stage in lifecycle_stages],
                value=lifecycle_stages[0] if lifecycle_stages else None
            ),
            cyto.Cytoscape(
                id='focused-stage-graph',
                layout={'name': 'grid'},
                style={'width': '100%', 'height': '350px'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle'
                        }
                    }
                ]
            )
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Substage Information"),
            html.Div(id='substage-info')
        ], width=6),
        dbc.Col([
            html.H3("Tools"),
            dcc.Dropdown(
                id='tool-sort-dropdown',
                options=[
                    {'label': 'Sort by Name', 'value': 'ToolName'},
                    {'label': 'Sort by Description', 'value': 'ToolDesc'},
                    {'label': 'Sort by Provider', 'value': 'ToolProvider'}
                ],
                value='ToolName'
            ),
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
                filter_action="native",
                sort_action="native",
                style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'ToolLink'},
                        'textDecoration': 'underline',
                        'cursor': 'pointer'
                    }
                ]
            ),
            dbc.Button("Add Tool", id="add-tool-btn", color="primary", className="mt-3"),
            dbc.Modal([
                dbc.ModalHeader("Add Tool"),
                dbc.ModalBody([
                    dbc.Input(id="add-tool-name", placeholder="Tool Name"),
                    dbc.Input(id="add-tool-desc", placeholder="Tool Description"),
                    dbc.Input(id="add-tool-link", placeholder="Tool Link"),
                    dbc.Input(id="add-tool-provider", placeholder="Tool Provider"),
                    dcc.Dropdown(id='add-tool-stage', options=[{'label': stage, 'value': stage} for stage in lifecycle_stages], value=lifecycle_stages[0] if lifecycle_stages else None)
                ]),
                dbc.ModalFooter([
                    dbc.Button("Add", id="confirm-add-tool", color="primary"),
                    dbc.Button("Close", id="close-add-tool", className="ml-auto")
                ]),
            ], id="add-tool-modal", is_open=False),
        ], width=6)
    ])
], fluid=True)

@app.callback(
    Output('full-lifecycle-graph', 'elements'),
    Input('full-lifecycle-graph', 'id')
)
def update_full_lifecycle_graph(_):
    """Update the full lifecycle graph."""
    elements = create_full_lifecycle_elements()
    logger.info(f"Created {len(elements)} elements for full lifecycle graph")
    return elements

@app.callback(
    Output('focused-stage-graph', 'elements'),
    Input('stage-dropdown', 'value')
)
def update_focused_stage_graph(selected_stage):
    """Update the focused stage graph based on the selected stage."""
    return create_focused_stage_elements(selected_stage)

@app.callback(
    Output('substage-info', 'children'),
    [Input('focused-stage-graph', 'tapNodeData'),
     Input('stage-dropdown', 'value')]
)
def update_substage_info(node_data, selected_stage):
    """Update the substage information based on the selected node in the focused graph."""
    if node_data:
        substage = node_data['id']
        query = "SELECT substagedesc AS info FROM SubStage WHERE stage = ? AND substagename = ?"
        df = get_dataframe_from_db(query, (selected_stage, substage))
        if not df.empty:
            return html.Div([
                html.H4(f"Substage: {substage}"),
                html.P(df.iloc[0]['info'])
            ])
    return html.Div("Select a substage to view information.")

@app.callback(
    Output('tools-table', 'data'),
    [Input('stage-dropdown', 'value'),
     Input('confirm-add-tool', 'n_clicks'),
     Input('tools-table', 'data_timestamp'),
     Input('tool-sort-dropdown', 'value')],
    [State('add-tool-name', 'value'),
     State('add-tool-desc', 'value'),
     State('add-tool-link', 'value'),
     State('add-tool-provider', 'value'),
     State('add-tool-stage', 'value'),
     State('tools-table', 'data')]
)
def update_tools(selected_stage, add_clicks, edit_timestamp, sort_by,
                 tool_name, tool_desc, tool_link, tool_provider, tool_stage, current_data):
    """Handle all tool-related actions: fetching, adding, editing, and deleting tools."""
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not ctx.triggered:
        raise PreventUpdate

    if trigger_id in ['stage-dropdown', 'tool-sort-dropdown'] or not current_data:
        query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
        tools_df = get_dataframe_from_db(query, (selected_stage,))
    elif trigger_id == 'confirm-add-tool':
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage)
                VALUES (?, ?, ?, ?, ?)
            """, (tool_name, tool_desc, tool_link, tool_provider, tool_stage))
            conn.commit()
        query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
        tools_df = get_dataframe_from_db(query, (selected_stage,))
    elif trigger_id == 'tools-table':
        with get_db_connection() as conn:
            conn.execute("DELETE FROM Tools WHERE stage = ?", (selected_stage,))
            for row in current_data:
                conn.execute("""
                    INSERT INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['ToolName'], row['ToolDesc'], row['ToolLink'], row['ToolProvider'], selected_stage))
            conn.commit()
        query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
        tools_df = get_dataframe_from_db(query, (selected_stage,))

    tools_df = tools_df.sort_values(by=sort_by)
    tools_df['ToolLink'] = tools_df['ToolLink'].apply(lambda x: f'[{x}]({x})' if pd.notnull(x) else '')

    return tools_df.to_dict('records')

@app.callback(
    Output("add-tool-modal", "is_open"),
    [Input("add-tool-btn", "n_clicks"), Input("confirm-add-tool", "n_clicks"), Input("close-add-tool", "n_clicks")],
    [State("add-tool-modal", "is_open")]
)
def toggle_add_tool_modal(n1, n2, n3, is_open):
    """Toggle the visibility of the add tool modal."""
    if n1 or n2 or n3:
        return not is_open
    return is_open

if __name__ == '__main__':
    logger.info("Starting the application...")
    if 'WEBSITE_HOSTNAME' in os.environ:
        logger.info("Running on Azure...")
        app.run_server(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    else:
        logger.info("Running locally in debug mode...")
        app.run_server(debug=True)