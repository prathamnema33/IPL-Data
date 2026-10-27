import dash
app=dash.Dash(__name__)
app.layout=dash.html.Div(children=[
    dash.html.H1(children='Hello Dash'),
    dash.html.Div(children='''Dash: A web application framework for Python.'''),
    dash.dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
])
if __name__ == "__main__":
    app.run(debug=True)