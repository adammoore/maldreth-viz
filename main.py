import os
from dash import Dash, html, dcc, Input, Output, dash_table, State, callback_context
import dash_cytoscape as cyto
import sqlite3
import pandas as pd
import dash_bootstrap_components as dbc

# Database setup
DB_FILE = 'research_data_lifecycle.db'
CSV_FILE = 'research_data_lifecycle.csv'


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
        cursor.execute("INSERT OR REPLACE INTO LifeCycle (stage, stagedesc) VALUES (?, ?)", (stage, ''))

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
        cursor.execute("""
        INSERT OR REPLACE INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage) VALUES (?, ?, '', '', ?)
        """, (row['EXAMPLES'], row['DESCRIPTION (1 SENTENCE)'], row['RESEARCH DATA LIFECYCLE STAGE']))

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
    return pd.DataFrame()


def fetch_edges():
    """Fetch the edges for the cytoscape graph."""
    query = "SELECT * FROM CycleConnects"
    return fetch_data(query)


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("Research Data Lifecycle Management", className="text-center"),
    dbc.Row([
        dbc.Col([
            html.H3("Lifecycle Stages"),
            dcc.Dropdown(
                id="stage-dropdown",
                options=[{"label": stage, "value": stage} for stage in fetch_data("SELECT stage FROM LifeCycle").stage],
                value="ANALYSE",
                clearable=False
            ),
            html.H3("Lifecycle Graph"),
            cyto.Cytoscape(
                id='lifecycle-graph',
                style={'width': '100%', 'height': '400px'},
                layout={'name': 'circle'},
                elements=[]
            )
        ], width=3, style={"background-color": "#fff", "padding": "20px", "box-shadow": "0 0 10px rgba(0, 0, 0, 0.1)",
                           "margin-right": "20px"}),
        dbc.Col([
            html.H3("Substages"),
            dash_table.DataTable(
                id='substage-table',
                columns=[
                    {"name": "Substage Name", "id": "substagename"},
                    {"name": "Description", "id": "substagedesc"},
                    {"name": "Exemplar", "id": "exemplar"}
                ],
                data=[],
                editable=True,
                row_deletable=True,
                style_table={'margin-bottom': '20px'},
                style_cell={'textAlign': 'left', 'padding': '8px', 'border': '1px solid #ddd'},
                style_header={'backgroundColor': '#f2f2f2'}
            ),
            dbc.Button("Add Substage", color="primary", id="add-substage-btn", style={"margin-bottom": "20px"}),
            html.H3("Tools"),
            dash_table.DataTable(
                id='tools-table',
                columns=[
                    {"name": "Tool Name", "id": "ToolName"},
                    {"name": "Description", "id": "ToolDesc"},
                    {"name": "Link", "id": "ToolLink"},
                    {"name": "Provider", "id": "ToolProvider"}
                ],
                data=[],
                editable=True,
                row_deletable=True,
                style_table={'margin-bottom': '20px'},
                style_cell={'textAlign': 'left', 'padding': '8px', 'border': '1px solid #ddd'},
                style_header={'backgroundColor': '#f2f2f2'}
            ),
            dbc.Button("Add Tool", color="primary", id="add-tool-btn")
        ], width=9, style={"background-color": "#fff", "padding": "20px", "box-shadow": "0 0 10px rgba(0, 0, 0, 0.1)"})
    ])
], fluid=True)


@app.callback(
    Output('substage-table', 'data'),
    Output('tools-table', 'data'),
    Output('lifecycle-graph', 'elements'),
    Input('stage-dropdown', 'value'),
    Input('lifecycle-graph', 'tapNode')
)
def update_content(selected_stage, tapped_node):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'lifecycle-graph':
        selected_stage = tapped_node['data']['id'] if tapped_node else selected_stage

    substages_query = f"SELECT substagename, substagedesc, exemplar FROM SubStage WHERE stage = '{selected_stage}'"
    substages_data = fetch_data(substages_query).to_dict('records')
    tools_query = f"SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = '{selected_stage}'"
    tools_data = fetch_data(tools_query).to_dict('records')

    nodes_query = "SELECT stage FROM LifeCycle"
    nodes = fetch_data(nodes_query).to_dict('records')
    edges = fetch_edges().to_dict('records')

    elements = [{'data': {'id': node['stage'], 'label': node['stage']}} for node in nodes]
    elements.extend([{'data': {'source': edge['source'], 'target': edge['target']}} for edge in edges])

    return substages_data, tools_data, elements


@app.callback(
    Output('stage-dropdown', 'value'),
    Input('lifecycle-graph', 'tapNode')
)
def update_stage_dropdown(tapped_node):
    if tapped_node:
        return tapped_node['data']['id']
    return dash.no_update


if __name__ == '__main__':
    conn = create_connection()
    if conn:
        initialize_database(conn)
        if not os.path.exists(DB_FILE):
            populate_data_from_csv(conn, CSV_FILE)
        conn.close()
    app.run_server(debug=True)
