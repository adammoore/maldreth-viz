"""
Research Data Lifecycle Tools Visualization Application

This application provides a visual representation of the research data lifecycle
and associated tools. It allows users to explore different stages of the lifecycle,
view and manage tools associated with each stage, and visualize the connections
between different stages and substages.

The application uses Dash for the web interface, Cytoscape for graph visualization,
and SQLite for data storage. It includes features such as:
- Interactive lifecycle graph visualization
- Focused view on selected stages and substages
- Tool management (viewing, adding, editing, and deleting tools)
- Dynamic updates based on user interactions

Author: [Your Name]
Date: [Current Date]
Version: 2.2
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
server = app.server  # Expose the Flask server for deployment
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
    """
    Fetch data from the SQLite database and return as a pandas DataFrame.

    Args:
        query (str): SQL query to execute
        params (tuple): Parameters for the SQL query

    Returns:
        pd.DataFrame: Result of the query as a DataFrame
    """
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except (sqlite3.Error, pd.io.sql.DatabaseError) as e:
        logger.error(f"Error executing query: {e}")
        return pd.DataFrame()

# Fetch lifecycle stages
lifecycle_stages_df = get_dataframe_from_db("SELECT stage FROM LifeCycle")
lifecycle_stages = lifecycle_stages_df['stage'].tolist()

# Fetch cycle connections
cycle_connects_df = get_dataframe_from_db("SELECT start, end, type FROM CycleConnects")

# Fetch substages
substages_df = get_dataframe_from_db("SELECT stage, substagename AS substage FROM SubStage")

# Initialize the app layout
app.layout = dbc.Container([
    html.H1("Research Data Lifecycle Tools"),
    dbc.Row([
        # Full lifecycle graph
        dbc.Col([
            html.H3("Full Lifecycle"),
            cyto.Cytoscape(
                id='full-lifecycle-graph',
                layout={'name': 'circle'},
                style={'width': '100%', 'height': '400px'}
            )
        ], width=6),
        # Focused stage graph
        dbc.Col([
            html.H3("Focused Stage"),
            dcc.Dropdown(id='stage-dropdown', options=[{'label': stage, 'value': stage} for stage in lifecycle_stages], value=lifecycle_stages[0]),
            cyto.Cytoscape(
                id='focused-stage-graph',
                layout={'name': 'grid'},
                style={'width': '100%', 'height': '350px'}
            )
        ], width=6)
    ]),
    dbc.Row([
        # Substage information
        dbc.Col([
            html.H3("Substage Information"),
            html.Div(id='substage-info')
        ], width=6),
        # Tools list and CRUD operations
        dbc.Col([
            html.H3("Tools"),
            dash_table.DataTable(
                id='tools-table',
                columns=[
                    {"name": "Tool Name", "id": "ToolName"},
                    {"name": "Tool Description", "id": "ToolDesc"}
                ],
                data=[],
                editable=True,
                row_deletable=True
            ),
            dbc.Button("Add Tool", id="add-tool-btn", color="primary", className="mt-3"),
            dbc.Modal([
                dbc.ModalHeader("Add Tool"),
                dbc.ModalBody([
                    dbc.Input(id="add-tool-name", placeholder="Tool Name"),
                    dbc.Input(id="add-tool-desc", placeholder="Tool Description"),
                    dbc.Input(id="add-tool-link", placeholder="Tool Link"),
                    dbc.Input(id="add-tool-provider", placeholder="Tool Provider"),
                    dcc.Dropdown(id='add-tool-stage', options=[{'label': stage, 'value': stage} for stage in lifecycle_stages], value=lifecycle_stages[0])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Add", id="confirm-add-tool", color="primary"),
                    dbc.Button("Close", id="close-add-tool", className="ml-auto")
                ]),
            ], id="add-tool-modal", is_open=False),
        ], width=6)
    ])
])

def create_full_lifecycle_elements():
    """
    Create nodes and edges for the full lifecycle graph.

    Returns:
        list: List of dictionaries representing nodes and edges for Cytoscape
    """
    # Create a set of all unique stages
    all_stages = set(lifecycle_stages_df['stage'])
    all_stages.update(cycle_connects_df['start'])
    all_stages.update(cycle_connects_df['end'])

    # Create nodes for all stages
    nodes = [{'data': {'id': stage, 'label': stage}} for stage in all_stages]

    # Create edges only for existing nodes
    edges = []
    for _, row in cycle_connects_df.iterrows():
        if row['start'] in all_stages and row['end'] in all_stages:
            edges.append({
                'data': {
                    'source': row['start'],
                    'target': row['end'],
                    'label': row['type']
                }
            })
        else:
            logger.warning(f"Skipping edge {row['start']} -> {row['end']} due to missing node")

    return nodes + edges

def create_focused_stage_elements(stage):
    """
    Create nodes and edges for the focused stage graph.

    Args:
        stage (str): The selected stage to focus on

    Returns:
        list: List of dictionaries representing nodes and edges for Cytoscape
    """
    substages = substages_df[substages_df['stage'] == stage]['substage'].tolist()
    nodes = [{'data': {'id': substage, 'label': substage}} for substage in substages]
    edges = [{'data': {'source': substages[i], 'target': substages[i+1]}} for i in range(len(substages)-1)]
    return nodes + edges

@app.callback(
    Output('full-lifecycle-graph', 'elements'),
    Input('full-lifecycle-graph', 'id')
)
def update_full_lifecycle_graph(_):
    """
    Update the full lifecycle graph.

    Returns:
        list: Updated list of elements for the Cytoscape graph
    """
    elements = create_full_lifecycle_elements()
    logger.info(f"Created {len(elements)} elements for full lifecycle graph")
    return elements

@app.callback(
    Output('focused-stage-graph', 'elements'),
    Input('stage-dropdown', 'value')
)
def update_focused_stage_graph(selected_stage):
    """
    Update the focused stage graph based on the selected stage.

    Args:
        selected_stage (str): The stage selected in the dropdown

    Returns:
        list: Updated list of elements for the Cytoscape graph
    """
    return create_focused_stage_elements(selected_stage)

@app.callback(
    Output('substage-info', 'children'),
    [Input('focused-stage-graph', 'tapNodeData'),
     Input('stage-dropdown', 'value')]
)
def update_substage_info(node_data, selected_stage):
    """
    Update the substage information based on the selected node in the focused graph.

    Args:
        node_data (dict): Data of the tapped node
        selected_stage (str): The stage selected in the dropdown

    Returns:
        html.Div: Updated substage information
    """
    if node_data:
        substage = node_data['id']
        # Fetch substage information from the database
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
     Input('tools-table', 'data_timestamp')],
    [State('add-tool-name', 'value'),
     State('add-tool-desc', 'value'),
     State('add-tool-link', 'value'),
     State('add-tool-provider', 'value'),
     State('add-tool-stage', 'value'),
     State('tools-table', 'data')]
)
def update_tools(selected_stage, add_clicks, edit_timestamp,
                 tool_name, tool_desc, tool_link, tool_provider, tool_stage, current_data):
    """
    Handle all tool-related actions: fetching, adding, editing, and deleting tools.

    Args:
        selected_stage (str): The stage selected in the dropdown
        add_clicks (int): Number of clicks on the add tool button
        edit_timestamp (int): Timestamp of the last edit in the tools table
        tool_name (str): Name of the tool to be added
        tool_desc (str): Description of the tool to be added
        tool_link (str): Link of the tool to be added
        tool_provider (str): Provider of the tool to be added
        tool_stage (str): Stage of the tool to be added
        current_data (list): Current state of the tools table

    Returns:
        list: Updated list of tools as dictionaries
    """
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not ctx.triggered:
        raise PreventUpdate

    if trigger_id == 'stage-dropdown' or not current_data:
        # Fetch tools for the selected stage
        query = "SELECT ToolName, ToolDesc FROM Tools WHERE stage = ?"
        tools_df = get_dataframe_from_db(query, (selected_stage,))
        return tools_df.to_dict('records')

    elif trigger_id == 'confirm-add-tool':
        # Add new tool
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage)
                VALUES (?, ?, ?, ?, ?)
            """, (tool_name, tool_desc, tool_link, tool_provider, tool_stage))
            conn.commit()

    elif trigger_id == 'tools-table':
        # Handle edits and deletions
        with get_db_connection() as conn:
            # First, delete all tools for this stage (to handle deletions)
            conn.execute("DELETE FROM Tools WHERE stage = ?", (selected_stage,))
            # Then, insert all current tools (handles both edits and additions)
            for row in current_data:
                conn.execute("""
                    INSERT INTO Tools (ToolName, ToolDesc, stage)
                    VALUES (?, ?, ?)
                """, (row['ToolName'], row['ToolDesc'], selected_stage))
            conn.commit()

    # Fetch and return updated tools
    query = "SELECT ToolName, ToolDesc FROM Tools WHERE stage = ?"
    tools_df = get_dataframe_from_db(query, (selected_stage,))
    return tools_df.to_dict('records')

@app.callback(
    Output("add-tool-modal", "is_open"),
    [Input("add-tool-btn", "n_clicks"), Input("confirm-add-tool", "n_clicks"), Input("close-add-tool", "n_clicks")],
    [State("add-tool-modal", "is_open")]
)
def toggle_add_tool_modal(n1, n2, n3, is_open):
    """
    Toggle the visibility of the add tool modal.

    Args:
        n1 (int): Number of clicks on add tool button
        n2 (int): Number of clicks on confirm add tool button
        n3 (int): Number of clicks on close add tool button
        is_open (bool): Current state of the modal

    Returns:
        bool: New state of the modal
    """
    if n1 or n2 or n3:
        return not is_open
    return is_open

# Main entry point
if __name__ == '__main__':
    print("Starting the application...")
    # Check if running on Azure
    if 'WEBSITE_HOSTNAME' in os.environ:
        print("Running on Azure...")
        # Running on Azure, use production settings
        app.run_server(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    else:
        print("Running locally in debug mode...")
        # Running locally, use development settings
        app.run_server(debug=True)