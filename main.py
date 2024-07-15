import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

# Define the data
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

tool_categories = {
    'Conceptualise': [
        {'name': 'Mind mapping, concept mapping and knowledge modelling',
         'examples': ['Miro', 'Meister Labs (MindMeister + MeisterTask)', 'XMind']},
        {'name': 'Diagramming and flowchart', 'examples': ['Lucidchart', 'Draw.io (now Diagrams.net)', 'Creately']},
        {'name': 'Wireframing and prototyping', 'examples': ['Balsamiq', 'Figma']}
    ],
    'Plan': [
        {'name': 'Data management planning (DMP)', 'examples': ['DMP Tool', 'DMP Online', 'RDMO']},
        {'name': 'Project planning', 'examples': ['Trello', 'Asana', 'Microsoft project']},
        {'name': 'Combined DMP/project', 'examples': ['Data Stewardship Wizard', 'Redbox research data', 'Argos']}
    ],
    # ... Add other categories here ...
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def create_lifecycle_stage(stage):
    return dbc.Button(
        stage['name'],
        id={'type': 'stage-button', 'index': stage['name']},
        className='m-1',
        style={'backgroundColor': stage['color'], 'borderColor': stage['color']}
    )


app.layout = dbc.Container([
    html.H1("The MaLDReTH Research Data Lifecycle", className='text-center my-4'),

    dbc.Row([
        dbc.Col([create_lifecycle_stage(stage) for stage in data], className='d-flex flex-wrap justify-content-center')
    ]),

    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H2(id='stage-name', className='mb-3'),
            html.P(id='stage-description', className='mb-4'),
            html.H3("Tool Categories:", className='mb-3'),
            dbc.Accordion(id='tool-categories')
        ])
    ])
])


@app.callback(
    [Output('stage-name', 'children'),
     Output('stage-description', 'children'),
     Output('tool-categories', 'children')],
    [Input({'type': 'stage-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'stage-button', 'index': dash.dependencies.ALL}, 'id')]
)
def update_stage_info(n_clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Select a stage", "", []

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    stage_name = eval(button_id)['index']
    stage = next(stage for stage in data if stage['name'] == stage_name)
    categories = tool_categories.get(stage_name, [])

    accordion_items = []
    for i, category in enumerate(categories):
        accordion_items.append(
            dbc.AccordionItem(
                [html.Ul([html.Li(example) for example in category['examples']])],
                title=category['name'],
                item_id=f"item-{i}"
            )
        )

    return stage['name'], stage['description'], accordion_items


if __name__ == '__main__':
    app.run_server(debug=True)