"""
Research Data Lifecycle Tools Visualization

This Flask application uses Dash and Dash Bootstrap Components to visualize
the research data lifecycle stages and associated tools. Users can explore
the lifecycle stages, view details, and manage tools. Clicking on a lifecycle
stage shifts the focus to that stage in all views.

Modules:
    - os
    - logging
    - dash
    - dash_cytoscape
    - dash_bootstrap_components
    - pandas
    - sqlite3
    - dash.exceptions

Usage:
    Run this script to start the Flask application server.
"""

import os
import logging
from dash import Dash, html, dcc, Input, Output, State, dash_table
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
lifecycle_stages = lifecycle_stages_df.set_index('stage')['stagedesc'].to_dict()

# Fetch cycle connections
cycle_connects_df = get_dataframe_from_db("SELECT id, start, end, type FROM CycleConnects")

# Fetch substages
substages_df = get_dataframe_from_db("SELECT substagename AS substage, stage FROM SubStage")

# Fetch exemplars from the SubStage table
exemplars_df = get_dataframe_from_db(
    "SELECT substagename AS substage, exemplar AS exemplarname, substagedesc AS exemplardesc FROM SubStage")

# Fetch tools
tools_df = get_dataframe_from_db("SELECT ToolName, ToolDesc, ToolLink, ToolProvider, stage FROM Tools")


def create_full_lifecycle_elements():
    """Create nodes and edges for the full lifecycle graph."""
    # Create nodes for lifecycle stages
    nodes = [
        {
            'data': {'id': stage, 'label': stage},
            'style': {
                'shape': 'round-rectangle',
                'width': '150px',
                'height': '50px',
                'background-color': '#E6F3FF',
                'border-color': '#2E86C1',
                'border-width': 2
            },
            'tooltip': {'content': desc}  # Set tooltip for description
        }
        for stage, desc in lifecycle_stages.items()
    ]

    # Create edges for cycle connections
    edges = []
    for idx, row in cycle_connects_df.iterrows():
        if row['start'] not in lifecycle_stages or row['end'] not in lifecycle_stages:
            logger.warning(f"Skipping edge with non-existent source or target: {row['start']} -> {row['end']}")
            continue

        edge_style = {
            'line-style': 'dashed' if row['type'] == 'alternative' else 'solid',
            'target-arrow-shape': 'triangle',
            'line-color': '#2E86C1',
            'target-arrow-color': '#2E86C1'
        }

        edges.append({
            'data': {'source': row['start'], 'target': row['end'], 'label': row['type']},
            'style': edge_style
        })

    return nodes + edges


def create_focused_stage_elements(stage):
    """Create nodes and edges for the focused stage graph."""
    substages = substages_df[substages_df['stage'] == stage]['substage'].tolist()
    nodes = [
        {
            'data': {'id': substage, 'label': substage},
            'style': {
                'shape': 'round-rectangle',
                'width': '150px',
                'height': '50px',
                'background-color': '#E6F3FF',
                'border-color': '#2E86C1',
                'border-width': 2
            },
            'tooltip': {'content': f"Substage: {substage}"}
        }
        for substage in substages
    ]
    edges = [
        {
            'data': {'source': substages[i], 'target': substages[i + 1]},
            'style': {
                'target-arrow-shape': 'triangle',
                'line-color': '#2E86C1',
                'target-arrow-color': '#2E86C1'
            }
        }
        for i in range(len(substages) - 1)
    ]
    return nodes + edges


def get_tools_for_stage(stage):
    """Get tools for the specified stage."""
    return tools_df[tools_df['stage'] == stage]


# Updated app layout
app.layout = dbc.Container([
    html.H1("Research Data Lifecycle Tools", className="my-4"),
    html.P(
        "Explore the research data lifecycle stages and associated tools. Click on a stage to view details and manage tools."),
    dbc.Row([
        dbc.Col([
            html.H3("Full Lifecycle"),
            cyto.Cytoscape(
                id='full-lifecycle-graph',
                layout={'name': 'circle'},
                style={'width': '100%', 'height': '400px'},
                elements=create_full_lifecycle_elements(),
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'color': '#000',  # Set text color
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'line-color': '#2E86C1',
                            'target-arrow-color': '#2E86C1'
                        }
                    },
                    {
                        'selector': '.tooltip',
                        'style': {
                            'label': 'data(tooltip)',
                            'text-opacity': 0,
                            'text-background-color': '#fff',
                            'text-background-opacity': 0.8,
                            'text-background-shape': 'round-rectangle',
                            'text-border-color': '#ccc',
                            'text-border-width': 1,
                            'text-border-opacity': 0.8,
                            'text-margin-y': -10,
                            'text-margin-x': -10
                        }
                    }
                ]
            )
        ], width=6),
        dbc.Col([
            html.H3("Focused Stage"),
            dcc.Dropdown(
                id='stage-dropdown',
                options=[{'label': stage, 'value': stage} for stage in lifecycle_stages.keys()],
                value=list(lifecycle_stages.keys())[0] if lifecycle_stages else None
            ),
            cyto.Cytoscape(
                id='focused-stage-graph',
                layout={'name': 'grid'},
                style={'width': '100%', 'height': '350px'},
                elements=[],
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'color': '#000',  # Set text color
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'line-color': '#2E86C1',
                            'target-arrow-color': '#2E86C1'
                        }
                    },
                    {
                        'selector': '.tooltip',
                        'style': {
                            'label': 'data(tooltip)',
                            'text-opacity': 0,
                            'text-background-color': '#fff',
                            'text-background-opacity': 0.8,
                            'text-background-shape': 'round-rectangle',
                            'text-border-color': '#ccc',
                            'text-border-width': 1,
                            'text-border-opacity': 0.8,
                            'text-margin-y': -10,
                            'text-margin-x': -10
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
                    {"name": "Provider", "id": "ToolProvider"},
                    {"name": "Edit", "id": "edit", "presentation": "markdown"}
                ],
                data=[],
                editable=True,
                row_deletable=True,
                filter_action="native",
                sort_action="native",
                style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
                style_table={'overflowX': 'auto'}
            ),
            dbc.Button("Add Tool", id="add-tool-button", color="primary", className="mt-2"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Add or Edit Tool")),
                    dbc.ModalBody([
                        dbc.Form([
                            dbc.Label("Tool Name"),
                            dbc.Input(id="tool-name-input", placeholder="Enter tool name"),
                            dbc.Label("Description"),
                            dbc.Input(id="tool-desc-input", placeholder="Enter tool description"),
                            dbc.Label("Link"),
                            dbc.Input(id="tool-link-input", placeholder="Enter tool link"),
                            dbc.Label("Provider"),
                            dbc.Input(id="tool-provider-input", placeholder="Enter tool provider"),
                            dbc.Label("Stage"),
                            dcc.Dropdown(
                                id="tool-stage-dropdown",
                                options=[{'label': stage, 'value': stage} for stage in lifecycle_stages.keys()],
                                value=list(lifecycle_stages.keys())[0] if lifecycle_stages else None
                            )
                        ])
                    ]),
                    dbc.ModalFooter(
                        dbc.Button("Save", id="save-tool-button", className="ml-auto")
                    )
                ],
                id="tool-modal",
                is_open=False
            )
        ], width=6)
    ]),
    html.Div(id='dummy-output', style={'display': 'none'})
], fluid=True)


# Callbacks for updating focused stage graph and substage information
@app.callback(
    Output('focused-stage-graph', 'elements'),
    Input('stage-dropdown', 'value')
)
def update_focused_stage_graph(selected_stage):
    """Update the focused stage graph based on the selected stage."""
    if selected_stage:
        return create_focused_stage_elements(selected_stage)
    raise PreventUpdate


@app.callback(
    Output('substage-info', 'children'),
    Input('focused-stage-graph', 'tapNodeData')
)
def display_substage_info(node_data):
    """Display information about the selected substage."""
    if node_data:
        substage_name = node_data['id']
        filtered_df = exemplars_df[exemplars_df['substage'] == substage_name]
        if not filtered_df.empty:
            return [
                html.Div([
                    html.H4(substage_name),
                    html.P(f"Exemplar: {row['exemplarname']}"),
                    html.P(f"Description: {row['exemplardesc']}")
                ]) for idx, row in filtered_df.iterrows()
            ]
    return [html.P("Select a substage to view details.")]


@app.callback(
    Output('stage-dropdown', 'value'),
    Input('full-lifecycle-graph', 'tapNodeData')
)
def update_stage_dropdown(node_data):
    """Update the dropdown for focused stage based on clicked lifecycle stage."""
    if node_data:
        return node_data['id']
    raise PreventUpdate


@app.callback(
    Output('tools-table', 'data'),
    [Input('stage-dropdown', 'value'),
     Input('tool-sort-dropdown', 'value'),
     Input('save-tool-button', 'n_clicks')],
    [State('tool-name-input', 'value'),
     State('tool-desc-input', 'value'),
     State('tool-link-input', 'value'),
     State('tool-provider-input', 'value'),
     State('tool-stage-dropdown', 'value'),
     State('tools-table', 'data')]
)
def update_tools_table(selected_stage, sort_by, n_clicks, name, desc, link, provider, stage, data):
    """Update the tools table based on the selected stage, sorting option, and when a new tool is added."""
    if n_clicks and name and desc and link and provider and stage:
        new_tool = {
            "ToolName": name,
            "ToolDesc": desc,
            "ToolLink": f"[{link}]({link})" if link else "",
            "ToolProvider": provider,
            "stage": stage
        }
        data.append(new_tool)
        # Here you would also want to insert the new tool into the database
        # conn = get_db_connection()
        # conn.execute("INSERT INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage) VALUES (?, ?, ?, ?, ?)",
        #              (name, desc, link, provider, stage))
        # conn.commit()

    if selected_stage:
        tools_df_stage = get_tools_for_stage(selected_stage)
        tools_df_stage_sorted = tools_df_stage.sort_values(by=[sort_by])
        return tools_df_stage_sorted.to_dict('records')
    raise PreventUpdate


@app.callback(
    Output('tool-modal', 'is_open'),
    [Input('add-tool-button', 'n_clicks'),
     Input('tools-table', 'active_cell')],
    [State('tool-modal', 'is_open'),
     State('tools-table', 'data')]
)
def toggle_tool_modal(n1, active_cell, is_open, rows):
    """Toggle the modal for adding or editing a tool."""
    if n1 or active_cell:
        return not is_open
    return is_open


@app.callback(
    [Output('tool-name-input', 'value'),
     Output('tool-desc-input', 'value'),
     Output('tool-link-input', 'value'),
     Output('tool-provider-input', 'value'),
     Output('tool-stage-dropdown', 'value')],
    [Input('tools-table', 'active_cell')],
    [State('tools-table', 'data')]
)
def load_tool_data(active_cell, rows):
    """Load tool data into the modal for editing."""
    if active_cell:
        row = rows[active_cell['row']]
        return row['ToolName'], row['ToolDesc'], row['ToolLink'], row['ToolProvider'], row['stage']
    return "", "", "", "", ""


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
