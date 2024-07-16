import os
from dash import Dash, html, dcc, Input, Output, dash_table, State
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
        INSERT OR REPLACE INTO SubStage (substagename, substagedesc, exemplar, stage)
        VALUES (?, ?, ?, ?)
        """, (row['TOOL CATEGORY TYPE'], row['DESCRIPTION (1 SENTENCE)'], row['EXAMPLES'],
              row['RESEARCH DATA LIFECYCLE STAGE']))

    # Populate Tools table (assuming Tools are the same as SubStages in this case)
    for _, row in substage_data.iterrows():
        cursor.execute("""
        INSERT OR REPLACE INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage)
        VALUES (?, ?, ?, ?, ?)
        """, (row['TOOL CATEGORY TYPE'], row['DESCRIPTION (1 SENTENCE)'], '', '', row['RESEARCH DATA LIFECYCLE STAGE']))

    conn.commit()


def get_lifecycle_stages(conn):
    """Fetch the list of lifecycle stages from the database."""
    query = "SELECT stage, stagedesc FROM LifeCycle"
    return pd.read_sql_query(query, conn)


def get_substages(conn, stage):
    """Fetch the substages for a given lifecycle stage."""
    query = "SELECT substagename, substagedesc, exemplar FROM SubStage WHERE stage = ?"
    return pd.read_sql_query(query, conn, params=(stage,))


def get_tools(conn, stage):
    """Fetch the tools for a given lifecycle stage."""
    query = "SELECT ToolName, ToolDesc, ToolLink, ToolProvider FROM Tools WHERE stage = ?"
    return pd.read_sql_query(query, conn, params=(stage,))


# Color scheme
COLORS = {
    'primary': '#3498db',
    'secondary': '#2c3e50',
    'accent': '#e74c3c',
    'background': '#ecf0f1',
    'text': '#2c3e50',
}


def create_layout(lifecycle_stages):
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Research Data Lifecycle Management", className="text-center mb-4",
                            style={'color': COLORS['primary']}), width=12)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Lifecycle Stages"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            id='stage-dropdown',
                            options=[{'label': row['stage'], 'value': row['stage']} for _, row in
                                     lifecycle_stages.iterrows()],
                            value=lifecycle_stages.iloc[0]['stage'] if not lifecycle_stages.empty else None,
                            clearable=False,
                            style={'width': '100%'}
                        )
                    ])
                ], className="mb-4"),
                dbc.Card([
                    dbc.CardHeader("Lifecycle Graph"),
                    dbc.CardBody([
                        cyto.Cytoscape(
                            id='lifecycle-graph',
                            layout={'name': 'concentric', 'minNodeSpacing': 50},
                            style={'width': '100%', 'height': '400px'},
                            elements=[]
                        )
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Substages"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='substages-table',
                            columns=[{'name': i, 'id': i} for i in ['substagename', 'substagedesc', 'exemplar']],
                            data=[],
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'whiteSpace': 'normal'},
                            style_header={
                                'backgroundColor': COLORS['primary'],
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': COLORS['background']
                                }
                            ]
                        )
                    ])
                ], className="mb-4"),
                dbc.Card([
                    dbc.CardHeader("Tools"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='tools-table',
                            columns=[{'name': i, 'id': i} for i in
                                     ['ToolName', 'ToolDesc', 'ToolLink', 'ToolProvider']],
                            data=[],
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'whiteSpace': 'normal'},
                            style_header={
                                'backgroundColor': COLORS['primary'],
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': COLORS['background']
                                }
                            ]
                        )
                    ])
                ])
            ], width=6)
        ])
    ], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh'})


# Initialize the Dash app with a modern Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize database connection
conn = create_connection()
initialize_database(conn)

# Populate database if it's empty
if pd.read_sql_query("SELECT * FROM LifeCycle", conn).empty:
    populate_data_from_csv(conn, CSV_FILE)

# Fetch lifecycle stages for initial layout
lifecycle_stages = get_lifecycle_stages(conn)

# Set the app layout
app.layout = create_layout(lifecycle_stages)


@app.callback(
    [Output('substages-table', 'data'),
     Output('tools-table', 'data'),
     Output('lifecycle-graph', 'elements')],
    [Input('stage-dropdown', 'value')]
)
def update_dashboard(selected_stage):
    """Update the dashboard based on the selected stage."""
    substages = get_substages(conn, selected_stage)
    tools = get_tools(conn, selected_stage)

    # Create graph elements
    graph_elements = [{'data': {'id': selected_stage, 'label': selected_stage}, 'classes': 'lifecycle-stage'}]

    for _, row in substages.iterrows():
        sub_id = f"sub_{row['substagename']}"
        graph_elements.append({'data': {'id': sub_id, 'label': row['substagename']}, 'classes': 'substage'})
        graph_elements.append({'data': {'source': selected_stage, 'target': sub_id}})

    for _, row in tools.iterrows():
        tool_id = f"tool_{row['ToolName']}"
        graph_elements.append({'data': {'id': tool_id, 'label': row['ToolName']}, 'classes': 'tool'})
        graph_elements.append({'data': {'source': selected_stage, 'target': tool_id}})

    return substages.to_dict('records'), tools.to_dict('records'), graph_elements


if __name__ == '__main__':
    app.run_server(debug=True)