"""
Research Data Lifecycle Management Application

This application visualizes and manages the Research Data Lifecycle. It provides an interactive
graph representation of the lifecycle stages, along with detailed information about substages,
tools, and exemplars for each stage.

The application uses a SQLite database to store and retrieve data about the research data lifecycle,
including lifecycle stages, substages, tools, and connections between stages.

Key components:
1. Database setup and initialization
2. Data population from CSV
3. Dash layout definition
4. Callback functions for interactivity

The main layout consists of:
- A Cytoscape graph representing the lifecycle stages
- Tables for substages and tools
- A section for displaying exemplars

Callbacks enable dynamic updates of content based on user interactions with the graph and tables.
"""

import os
from dash import Dash, html, dcc, Input, Output, dash_table, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto
import sqlite3
import pandas as pd
import dash_bootstrap_components as dbc

# Database setup
DB_FILE = 'research_data_lifecycle.db'
CSV_FILE = 'research_data_lifecycle.csv'

STAGE_DEFINITIONS = {
    "CONCEPTUALISE": "To formulate the initial research idea or hypothesis, and define the scope of the research project and the data component/requirements of that project.",
    "PLAN": "To establish a structured strategic framework for management of the research project, outlining aims, objectives, methodologies, and resources required for data collection, management and analysis. Data management plans (DMP) should be established for this phase of the lifecycle.",
    "FUND": "To identify and acquire financial resources to support the research project, including data collection, management, analysis, sharing, publishing and preservation.",
    "COLLECT": "To use predefined procedures, methodologies and instruments to acquire and store data that is reliable, fit for purpose and of sufficient quality to test the research hypothesis.",
    "PROCESS": "To make new and existing data analysis-ready. This may involve standardised pre-processing, cleaning, reformatting, structuring, filtering, and performing quality control checks on data. It may also involve the creation and definition of metadata for use during analysis, such as acquiring provenance from instruments and tools used during data collection.",
    "ANALYSE": "To derive insights, knowledge, and understanding from processed data. Data analysis involves iterative exploration and interpretation of experimental or computational results, often utilising mathematical models and formulae to investigate relationships between experimental variables. Distinct data analysis techniques and methodologies are applied according to the data type (quantitative vs qualitative).",
    "STORE": "To record data using technological media appropriate for processing and analysis whilst maintaining data integrity and security.",
    "PUBLISH": "To release research data in published form for use by others with appropriate metadata for citation (including a unique persistent identifier) based on FAIR principles.",
    "PRESERVE": "To ensure the safety, integrity, and accessibility of data for as long as necessary so that data is as FAIR as possible. Data preservation is more than data storage and backup, since data can be stored and backed up without being preserved. Preservation should include curation activities such as data cleaning, validation, assigning preservation metadata, assigning representation information, and ensuring acceptable data structures and file formats. At a minimum, data and associated metadata should be published in a trustworthy digital repository and clearly cited in the accompanying journal article unless this is not possible (e.g. due to the privacy or safety concerns).",
    "SHARE": "To make data available and accessible to humans and/or machines. Data may be shared with project collaborators or published to share it with the wider research community and society at large. Data sharing is not limited to open data or public data, and can be done during various stages of the research data lifecycle. At a minimum, data and associated metadata should be published in a trustworthy digital repository and clearly cited in the accompanying journal article.",
    "ACCESS": "To control and manage data access by designated users and reusers. This may be in the form of publicly available published information. Necessary access control and authentication methods are applied.",
    "TRANSFORM": "To create new data from the original, for example: (i) by migration into a different format; (ii) by creating a subset, by selection or query, to create newly derived results, perhaps for publication; or, iii) combining or appending with other data"
}


def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn


def initialize_database(conn):
    """Create tables in the database if they don't exist."""
    try:
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS LifeCycle (
                stage TEXT PRIMARY KEY,
                stagedesc TEXT
            );
            CREATE TABLE IF NOT EXISTS SubStage (
                substagename TEXT,
                substagedesc TEXT,
                exemplar TEXT,
                stage TEXT,
                FOREIGN KEY (stage) REFERENCES LifeCycle(stage)
            );
            CREATE TABLE IF NOT EXISTS Tools (
                ToolName TEXT,
                ToolDesc TEXT,
                ToolLink TEXT,
                ToolProvider TEXT,
                stage TEXT,
                FOREIGN KEY (stage) REFERENCES LifeCycle(stage)
            );
            CREATE TABLE IF NOT EXISTS CycleConnects (
                source TEXT,
                target TEXT,
                FOREIGN KEY (source) REFERENCES LifeCycle(stage),
                FOREIGN KEY (target) REFERENCES LifeCycle(stage)
            );
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")


def populate_data_from_csv(conn, csv_file):
    """Populate the database with data from the CSV file."""
    df = pd.read_csv(csv_file)
    df.columns = [col.strip().replace('\n', ' ').replace('  ', ' ') for col in df.columns]

    lifecycle_data = df['RESEARCH DATA LIFECYCLE STAGE'].unique()
    cursor = conn.cursor()

    # Populate LifeCycle table
    for stage in lifecycle_data:
        cursor.execute("INSERT OR REPLACE INTO LifeCycle (stage, stagedesc) VALUES (?, ?)",
                       (stage, STAGE_DEFINITIONS.get(stage, '')))

    # Populate SubStage table
    substage_data = df[['TOOL CATEGORY TYPE', 'DESCRIPTION (1 SENTENCE)', 'EXAMPLES', 'RESEARCH DATA LIFECYCLE STAGE']]
    for _, row in substage_data.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO SubStage (substagename, substagedesc, exemplar, stage) VALUES (?, ?, ?, ?)
        """, (row['TOOL CATEGORY TYPE'], row['DESCRIPTION (1 SENTENCE)'], row['EXAMPLES'],
              row['RESEARCH DATA LIFECYCLE STAGE']))

    # Populate Tools table
    tools_data = df[['EXAMPLES', 'DESCRIPTION (1 SENTENCE)', 'RESEARCH DATA LIFECYCLE STAGE']]
    for _, row in tools_data.iterrows():
        tools = row['EXAMPLES'].split(',')
        for tool in tools:
            cursor.execute("""
            INSERT OR REPLACE INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage) VALUES (?, ?, '', '', ?)
            """, (tool.strip(), row['DESCRIPTION (1 SENTENCE)'], row['RESEARCH DATA LIFECYCLE STAGE']))

    # Populate CycleConnects table (example connections, adjust as needed)
    connections = [
        ('CONCEPTUALISE', 'PLAN'),
        ('PLAN', 'FUND'),
        ('FUND', 'COLLECT'),
        ('COLLECT', 'PROCESS'),
        ('PROCESS', 'ANALYSE'),
        ('ANALYSE', 'STORE'),
        ('STORE', 'PUBLISH'),
        ('PUBLISH', 'PRESERVE'),
        ('PRESERVE', 'SHARE'),
        ('SHARE', 'ACCESS'),
        ('ACCESS', 'TRANSFORM'),
        ('TRANSFORM', 'CONCEPTUALISE')
    ]
    for source, target in connections:
        cursor.execute("INSERT OR REPLACE INTO CycleConnects (source, target) VALUES (?, ?)", (source, target))

    conn.commit()


def fetch_data(query):
    """Fetch data from the database based on the provided query."""
    conn = create_connection()
    if conn:
        try:
            df = pd.read_sql_query(query, conn)
            return df
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
        finally:
            conn.close()
    return pd.DataFrame()


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Research Data Lifecycle Management", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            html.H3("Lifecycle Graph"),
            cyto.Cytoscape(
                id='lifecycle-graph',
                style={'width': '100%', 'height': '600px'},
                layout={'name': 'circle'},
                elements=[],
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'background-color': '#BFD7B5',
                            'shape': 'round-rectangle',
                            'width': 'label',
                            'height': 'label',
                            'padding': '10px'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'line-color': '#A3C4BC',
                            'target-arrow-color': '#A3C4BC'
                        }
                    }
                ]
            )
        ], width=12, lg=12),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.H3("Substages", id="substages-title"),
            dash_table.DataTable(
                id='substage-table',
                columns=[
                    {"name": "Substage Name", "id": "substagename"},
                    {"name": "Description", "id": "substagedesc"},
                    {"name": "Exemplar", "id": "exemplar"}
                ],
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                ],
            ),
        ], width=12, lg=6, className="mb-4"),
        dbc.Col([
            html.H3("Tools", id="tools-title"),
            dash_table.DataTable(
                id='tools-table',
                columns=[
                    {"name": "Tool Name", "id": "ToolName"},
                    {"name": "Description", "id": "ToolDesc"}
                ],
                data=[],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'border': '1px solid #ddd',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
                ],
            ),
        ], width=12, lg=6, className="mb-4"),
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Exemplars", id="exemplars-title"),
            html.Div(id="exemplars-content")
        ], width=12)
    ])
], fluid=True)


@app.callback(
    Output('lifecycle-graph', 'elements'),
    Input('lifecycle-graph', 'id')
)
def update_graph_elements(_):
    """Update the lifecycle graph elements."""
    nodes_query = "SELECT stage, stagedesc FROM LifeCycle"
    nodes = fetch_data(nodes_query).to_dict('records')
    edges_query = "SELECT source, target FROM CycleConnects"
    edges = fetch_data(edges_query).to_dict('records')

    elements = [{'data': {'id': node['stage'], 'label': node['stage'], 'title': node['stagedesc']}} for node in nodes]
    elements.extend([{'data': {'source': edge['source'], 'target': edge['target']}} for edge in edges])

    return elements


@app.callback(
    Output('substages-title', 'children'),
    Output('substage-table', 'data'),
    Output('tools-title', 'children'),
    Output('tools-table', 'data'),
    Input('lifecycle-graph', 'tapNode')
)
def update_content(tapped_node):
    """Update content based on the selected node in the lifecycle graph."""
    if not tapped_node:
        raise PreventUpdate

    selected_stage = tapped_node['data']['id']

    substages_query = f"SELECT substagename, substagedesc, exemplar FROM SubStage WHERE stage = '{selected_stage}'"
    substages_data = fetch_data(substages_query).to_dict('records')

    tools_query = f"SELECT ToolName, ToolDesc FROM Tools WHERE stage = '{selected_stage}'"
    tools_data = fetch_data(tools_query).to_dict('records')

    return f"Substages for {selected_stage}", substages_data, f"Tools for {selected_stage}", tools_data


@app.callback(
    Output('exemplars-title', 'children'),
    Output('exemplars-content', 'children'),
    Input('substage-table', 'active_cell'),
    State('substage-table', 'data')
)
def update_exemplars(active_cell, substage_data):
    """Update exemplars based on the selected substage."""
    if not active_cell:
        raise PreventUpdate

    selected_row = substage_data[active_cell['row']]
    exemplars = selected_row['exemplar'].split(',')

    return f"Exemplars for {selected_row['substagename']}", [html.P(exemplar.strip()) for exemplar in exemplars]


if __name__ == '__main__':
    conn = create_connection()
    if conn:
        initialize_database(conn)
        if not os.path.exists(DB_FILE):
            populate_data_from_csv(conn, CSV_FILE)
        conn.close()
    app.run_server(debug=True)