import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

# Define your data here (similar to the React component)
data = [
    {"name": "Fund", "color": "#8dd3c7", "description": "To identify and acquire financial resources to support the research project, including data collection, management, analysis, sharing, publishing and preservation."},
    {"name": "Conceptualise", "color": "#ffffb3", "description": "..."},
    # ... add all other stages
]

tool_categories = {
    "Conceptualise": [
        {"name": "Mind mapping, concept mapping and knowledge modelling",
         "examples": ["Miro", "Meister Labs", "XMind"]},
        # ... add other categories and examples
    ],
    # ... add for all other stages
}

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("The MaLDReTH Research Data Lifecycle"),
    html.Div([
        html.Button(stage["name"], id=f"button-{stage['name']}", style={"backgroundColor": stage["color"]})
        for stage in data
    ]),
    html.Div(id="stage-info")
])


@app.callback(
    Output("stage-info", "children"),
    [Input(f"button-{stage['name']}", "n_clicks") for stage in data]
)
def update_stage_info(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Click a stage to see more information"
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    stage_name = button_id.split("-")[1]
    stage = next(stage for stage in data if stage["name"] == stage_name)
    categories = tool_categories.get(stage_name, [])

    return html.Div([
        html.H2(stage["name"]),
        html.P(stage["description"]),
        html.H3("Tool Categories:"),
        html.Ul([
            html.Li([
                html.H4(category["name"]),
                html.Ul([html.Li(example) for example in category["examples"]])
            ]) for category in categories
        ])
    ])


if __name__ == "__main__":
    app.run_server(debug=True)