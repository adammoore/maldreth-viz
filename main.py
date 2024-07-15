import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash import dash_table
import sqlite3
import json
import os

# Initialize the Dash app with Bootstrap stylesheet
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def fetch_lifecycle_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('research_lifecycle.db')
    cursor = conn.cursor()

    # Fetch lifecycle data
    cursor.execute('SELECT stageID, stage, stagedesc FROM LifeCycle')
    data = cursor.fetchall()
    conn.close()

    return [{'id': row[0], 'name': row[1], 'description': row[2]} for row in data]

def fetch_tools(stage_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('research_lifecycle.db')
    cursor = conn.cursor()

    # Fetch tools data for the given stage ID
    cursor.execute('''
        SELECT ToolName, ToolDesc, ToolLink, ToolProvider
        FROM Tools
        WHERE stage = ?
    ''', (stage_id,))
    tools = cursor.fetchall()
    conn.close()

    return tools

def create_web3d_layout():
    data = fetch_lifecycle_data()
    nodes = [{"id": stage["id"], "label": stage["name"], "title": stage["description"]} for stage in data]
    edges = [{"from": data[i]["id"], "to": data[(i + 1) % len(data)]["id"]} for i in range(len(data))]

    return nodes, edges

nodes, edges = create_web3d_layout()

app.layout = dbc.Container([
    html.H1("The MaLDReTH Research Data Lifecycle", className='text-center my-4'),

    # Graph component to display the lifecycle diagram
    dcc.Graph(
        id='lifecycle-graph',
        figure={
            "data": [
                {
                    "type": "scatter3d",
                    "mode": "markers+text",
                    "x": [node["id"] for node in nodes],
                    "y": [0] * len(nodes),
                    "z": [0] * len(nodes),
                    "text": [node["label"] for node in nodes],
                    "customdata": [node["id"] for node in nodes],
                    "marker": {"size": 10}
                }
            ],
            "layout": {
                "title": "Research Data Lifecycle",
                "showlegend": False
            }
        }
    ),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H2(id='stage-name', className='mb-3'),
            html.Div(id='stage-description', className='mb-4', style={'maxWidth': '800px', 'margin': 'auto', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '5px'}),
            html.H3("Tool Categories:", className='mb-3'),
            dbc.Accordion(id='tool-categories')
        ])
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H3("Tool List", className='mb-3'),
            dcc.Dropdown(
                id='sort-dropdown',
                options=[
                    {'label': 'Sort by Name', 'value': 'name'},
                    {'label': 'Sort by Category', 'value': 'category'}
                ],
                value='name',
                className='mb-3'
            ),
            dash_table.DataTable(
                id='tool-table',
                columns=[
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Category', 'id': 'category'},
                    {'name': 'Description', 'id': 'description'},
                    {'name': 'Website', 'id': 'website'}
                ],
                style_cell={'textAlign': 'left'},
                style_data={'whiteSpace': 'normal', 'height': 'auto'},
                page_size=10,
                filter_action='native',
                sort_action='native',
                sort_mode='multi'
            )
        ])
    ])
])

@app.callback(
    [Output('stage-name', 'children'),
     Output('stage-description', 'children'),
     Output('tool-categories', 'children'),
     Output('tool-table', 'data')],
    [Input('lifecycle-graph', 'clickData'),
     Input('sort-dropdown', 'value')]
)
def update_stage_info(clickData, sort_value):
    if not clickData or 'points' not in clickData or not clickData['points']:
        return "Select a stage", "", [], []

    stage_id = clickData['points'][0]['customdata']
    conn = sqlite3.connect('research_lifecycle.db')
    cursor = conn.cursor()

    cursor.execute('SELECT stage, stagedesc FROM LifeCycle WHERE stageID = ?', (stage_id,))
    stage = cursor.fetchone()
    if not stage:
        return "Select a stage", "", [], []

    stage_name, stage_desc = stage

    tools = fetch_tools(stage_id)

    accordion_items = []
    all_tools = []
    for i, (tool_name, tool_desc, tool_link, tool_provider) in enumerate(tools):
        accordion_items.append(
            dbc.AccordionItem(
                [html.Ul([html.Li([
                    html.Strong(tool_name),
                    html.Span(f": {tool_desc}"),
                    html.A(" (Website)", href=tool_link, target="_blank")
                ])])],
                title=tool_provider,
                item_id=f"item-{i}"
            )
        )
        all_tools.append({
            'name': tool_name,
            'category': tool_provider,
            'description': tool_desc,
            'website': tool_link
        })

    if sort_value == 'name':
        all_tools.sort(key=lambda x: x['name'])
    else:
        all_tools.sort(key=lambda x: x['category'])

    conn.close()
    return stage_name, stage_desc, accordion_items, all_tools

if __name__ == '__main__':
    app.run_server(debug=True)
