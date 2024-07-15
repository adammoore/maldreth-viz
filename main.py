import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import math

# Define the data (same as before)
data = [
    {"name": "Fund", "color": "#8dd3c7",
     "description": "To identify and acquire financial resources to support the research project, including data collection, management, analysis, sharing, publishing and preservation."},
    {"name": "Conceptualise", "color": "#ffffb3",
     "description": "To formulate the initial research idea or hypothesis, and define the scope of the research project and the data component/requirements of that project."},
    {"name": "Plan", "color": "#bebada",
     "description": "To establish a structured strategic framework for management of the research project, outlining aims, objectives, methodologies, and resources required for data collection, management and analysis. Data management plans (DMP) should be established for this phase of the lifecycle."},
    {"name": "Collect", "color": "#fb8072",
     "description": "To use predefined procedures, methodologies and instruments to acquire and store data that is reliable, fit for purpose and of sufficient quality to test the research hypothesis."},
    {"name": "Process", "color": "#80b1d3",
     "description": "To make new and existing data analysis-ready. This may involve standardised pre-processing, cleaning, reformatting, structuring, filtering, and performing quality control checks on data. It may also involve the creation and definition of metadata for use during analysis, such as acquiring provenance from instruments and tools used during data collection."},
    {"name": "Analyse", "color": "#fdb462",
     "description": "To derive insights, knowledge, and understanding from processed data. Data analysis involves iterative exploration and interpretation of experimental or computational results, often utilising mathematical models and formulae to investigate relationships between experimental variables. Distinct data analysis techniques and methodologies are applied according to the data type (quantitative vs qualitative)."},
    {"name": "Store", "color": "#b3de69",
     "description": "To record data using technological media appropriate for processing and analysis whilst maintaining data integrity and security."},
    {"name": "Publish", "color": "#fccde5",
     "description": "To release research data in published form for use by others with appropriate metadata for citation (including a unique persistent identifier) based on FAIR principles."},
    {"name": "Preserve", "color": "#d9d9d9",
     "description": "To ensure the safety, integrity, and accessibility of data for as long as necessary so that data is as FAIR as possible. Data preservation is more than data storage and backup, since data can be stored and backed up without being preserved. Preservation should include curation activities such as data cleaning, validation, assigning preservation metadata, assigning representation information, and ensuring acceptable data structures and file formats. At a minimum, data and associated metadata should be published in a trustworthy digital repository and clearly cited in the accompanying journal article unless this is not possible (e.g. due to the privacy or safety concerns)."},
    {"name": "Share", "color": "#bc80bd",
     "description": "To make data available and accessible to humans and/or machines. Data may be shared with project collaborators or published to share it with the wider research community and society at large. Data sharing is not limited to open data or public data, and can be done during various stages of the research data lifecycle. At a minimum, data and associated metadata should be published in a trustworthy digital repository and clearly cited in the accompanying journal article."},
    {"name": "Access", "color": "#ccebc5",
     "description": "To control and manage data access by designated users and reusers. This may be in the form of publicly available published information. Necessary access control and authentication methods are applied."},
    {"name": "Transform", "color": "#ffed6f",
     "description": "To create new data from the original, for example: (i) by migration into a different format; (ii) by creating a subset, by selection or query, to create newly derived results, perhaps for publication; or, iii) combining or appending with other data"}
]

# Updated tool_categories with more information
tool_categories = {
    'Conceptualise': [
        {'name': 'Mind mapping, concept mapping and knowledge modelling', 'examples': [
            {'name': 'Miro', 'description': 'Online collaborative whiteboard platform', 'website': 'https://miro.com'},
            {'name': 'Meister Labs', 'description': 'Mind mapping and task management tools',
             'website': 'https://www.meisterlabs.com'},
            {'name': 'XMind', 'description': 'Mind mapping and brainstorming tool', 'website': 'https://www.xmind.net'}
        ]},
        {'name': 'Diagramming and flowchart', 'examples': [
            {'name': 'Lucidchart', 'description': 'Web-based diagramming application',
             'website': 'https://www.lucidchart.com'},
            {'name': 'Draw.io', 'description': 'Free online diagram software', 'website': 'https://app.diagrams.net'},
            {'name': 'Creately', 'description': 'Visual collaboration software', 'website': 'https://creately.com'}
        ]},
        {'name': 'Wireframing and prototyping', 'examples': [
            {'name': 'Balsamiq', 'description': 'Rapid wireframing tool', 'website': 'https://balsamiq.com'},
            {'name': 'Figma', 'description': 'Collaborative interface design tool', 'website': 'https://www.figma.com'}
        ]}
    ],
    'Plan': [
        {'name': 'Data management planning (DMP)', 'examples': [
            {'name': 'DMP Tool', 'description': 'Online tool for creating data management plans',
             'website': 'https://dmptool.org'},
            {'name': 'DMP Online', 'description': 'Tool for creating and sharing data management plans',
             'website': 'https://dmponline.dcc.ac.uk'},
            {'name': 'RDMO', 'description': 'Research Data Management Organiser',
             'website': 'https://rdmorganiser.github.io'}
        ]},
        {'name': 'Project planning', 'examples': [
            {'name': 'Trello', 'description': 'Web-based Kanban-style list-making application',
             'website': 'https://trello.com'},
            {'name': 'Asana', 'description': 'Web and mobile work management platform', 'website': 'https://asana.com'},
            {'name': 'Microsoft Project', 'description': 'Project management software',
             'website': 'https://www.microsoft.com/en-us/microsoft-365/project/project-management-software'}
        ]},
        {'name': 'Combined DMP/project', 'examples': [
            {'name': 'Data Stewardship Wizard',
             'description': 'Tool for data management planning and project management',
             'website': 'https://ds-wizard.org'},
            {'name': 'Redbox', 'description': 'Research data management platform',
             'website': 'https://www.redboxresearchdata.com.au'},
            {'name': 'Argos', 'description': 'Data management planning tool', 'website': 'https://argos.openaire.eu'}
        ]}
    ],
    # ... Add other categories here ...
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Function to create the circular layout
def create_circular_layout():
    fig = go.Figure()

    for i, stage in enumerate(data):
        angle = (i / len(data)) * 2 * math.pi
        x = math.cos(angle)
        y = math.sin(angle)

        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(size=40, color=stage['color']),
            text=stage['name'],
            textposition='middle center',
            hoverinfo='text',
            hovertext=stage['description'],
            customdata=[stage['name']]
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )

    return fig


app.layout = dbc.Container([
    html.H1("The MaLDReTH Research Data Lifecycle", className='text-center my-4'),

    dcc.Graph(id='lifecycle-graph', figure=create_circular_layout()),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H2(id='stage-name', className='mb-3'),
            html.P(id='stage-description', className='mb-4'),
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
    if not clickData:
        return "Select a stage", "", [], []

    stage_name = clickData['points'][0]['customdata'][0]
    stage = next(stage for stage in data if stage['name'] == stage_name)
    categories = tool_categories.get(stage_name, [])

    accordion_items = []
    all_tools = []
    for i, category in enumerate(categories):
        accordion_items.append(
            dbc.AccordionItem(
                [html.Ul([html.Li([
                    html.Strong(example['name']),
                    html.Span(f": {example['description']}"),
                    html.A(" (Website)", href=example['website'], target="_blank")
                ]) for example in category['examples']])],
                title=category['name'],
                item_id=f"item-{i}"
            )
        )
        for example in category['examples']:
            all_tools.append({
                'name': example['name'],
                'category': category['name'],
                'description': example['description'],
                'website': example['website']
            })

    if sort_value == 'name':
        all_tools.sort(key=lambda x: x['name'])
    else:
        all_tools.sort(key=lambda x: x['category'])

    return stage['name'], stage['description'], accordion_items, all_tools


if __name__ == '__main__':
    app.run_server(debug=True)