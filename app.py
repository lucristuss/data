from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

if 'year' in df.columns:
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
for col in ['pop', 'lifeExp', 'gdpPercap']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

countries = sorted(df['country'].dropna().unique().tolist())
country_options = [{'label': c, 'value': c} for c in countries]
y_measures = [m for m in ['lifeExp', 'pop', 'gdpPercap'] if m in df.columns]
bubble_measures = y_measures.copy()
years = sorted(df['year'].dropna().unique().tolist())
year_min, year_max = (min(years), max(years)) if years else (0, 0)

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H2("Dash — Demography (extended minimal-app)", style={'textAlign':'center'}),
    html.Hr(),

    html.Div([
        html.Div([
            html.Label('1) Выберите страны (множественный выбор)'),
            dcc.Dropdown(id='countries-dropdown', options=country_options, value=['Canada'], multi=True)
        ], style={'width':'48%', 'display':'inline-block'}),

        html.Div([
            html.Label('2) Выбор оси Y для линейного графика'),
            dcc.Dropdown(id='yaxis-dropdown', options=[{'label':m,'value':m} for m in y_measures], value=y_measures[0] if y_measures else None)
        ], style={'width':'48%', 'display':'inline-block', 'marginLeft':'4%'}),
    ], style={'marginBottom': 20}),

    html.Div([
        html.Label('3) Выбор года (влияет на bubble / top15 / pie)'),
        dcc.Slider(id='year-slider', min=year_min, max=year_max, step=None,
                   marks={int(y): str(int(y)) for y in years} if years else {}, value=year_max if year_max else None)
    ], style={'marginBottom': 30}),

    # Line chart
    dcc.Graph(id='line-chart'),

    html.Hr(),

    # Bubble controls
    html.Div([
        html.Div([
            html.Label('4) Bubble — ось X'),
            dcc.Dropdown(id='bubble-x', options=[{'label':m, 'value':m} for m in bubble_measures], value=bubble_measures[0] if bubble_measures else None)
        ], style={'width':'32%', 'display':'inline-block'}),
        html.Div([
            html.Label('5) Bubble — ось Y'),
            dcc.Dropdown(id='bubble-y', options=[{'label':m,'value':m} for m in bubble_measures], value=bubble_measures[1] if len(bubble_measures)>1 else bubble_measures[0] if bubble_measures else None)
        ], style={'width':'32%', 'display':'inline-block', 'marginLeft':'2%'}),
        html.Div([
            html.Label('6) Bubble — размер (radius)'),
            dcc.Dropdown(id='bubble-size', options=[{'label':m,'value':m} for m in bubble_measures], value='pop' if 'pop' in bubble_measures else (bubble_measures[0] if bubble_measures else None))
        ], style={'width':'32%', 'display':'inline-block', 'marginLeft':'2%'}),
    ], style={'marginBottom': 20}),

    # Graphs: bubble | top15 | pie
    html.Div([
        html.Div(dcc.Graph(id='bubble-chart'), style={'width':'60%', 'display':'inline-block', 'verticalAlign':'top'}),
        html.Div([dcc.Graph(id='top15-bar'), dcc.Graph(id='continent-pie')], style={'width':'38%', 'display':'inline-block', 'marginLeft':'2%'}),
    ]),

    html.Div('Подсказка: графики Bubble / Top15 / Pie реагируют на выбор года.', style={'marginTop': 12, 'fontStyle': 'italic'})
])


@app.callback(
    Output('line-chart', 'figure'),
    Input('countries-dropdown', 'value'),
    Input('yaxis-dropdown', 'value')
)
def update_line(selected_countries, y_col):
    if not selected_countries:
        selected_countries = countries[:5]
    dff = df[df['country'].isin(selected_countries)]
    if y_col not in dff.columns:
        return px.line(title='Selected Y metric not available')
    fig = px.line(dff, x='year', y=y_col, color='country', markers=True, title=f'{y_col} by year for selected countries')
    fig.update_layout(legend_title_text='Country', height=450)
    return fig


@app.callback(
    Output('bubble-chart', 'figure'),
    Input('bubble-x', 'value'),
    Input('bubble-y', 'value'),
    Input('bubble-size', 'value'),
    Input('year-slider', 'value')
)
def update_bubble(x_col, y_col, size_col, year_value):
    dff = df.copy()
    if year_value is not None:
        dff = dff[dff['year'] == year_value]
    for col in (x_col, y_col, size_col):
        if col not in dff.columns:
            return px.scatter(title='One of selected metrics is not available')
    size_series = dff[size_col].fillna(0).abs()
    fig = px.scatter(dff, x=x_col, y=y_col, size=size_series, color='continent', hover_name='country', size_max=70,
                     title=f'Bubble: {x_col} vs {y_col} (size={size_col}) — {year_value}')
    fig.update_layout(height=500)
    return fig


@app.callback(
    Output('top15-bar', 'figure'),
    Input('year-slider', 'value')
)
def update_top15(year_value):
    dff = df.copy()
    if year_value is not None:
        dff = dff[dff['year'] == year_value]
    if 'pop' not in dff.columns:
        return px.bar(title='Population column not available')
    top15 = dff.sort_values('pop', ascending=False).head(15)
    fig = px.bar(top15[::-1], x='pop', y='country', orientation='h', title=f'Top 15 countries by population — {year_value}')
    fig.update_layout(height=360)
    return fig


@app.callback(
    Output('continent-pie', 'figure'),
    Input('year-slider', 'value')
)
def update_pie(year_value):
    dff = df.copy()
    if year_value is not None:
        dff = dff[dff['year'] == year_value]
    if 'pop' not in dff.columns or 'continent' not in dff.columns:
        return px.pie(title='Not enough data for pie chart')
    cont = dff.groupby('continent', as_index=False')['pop'].sum()
    fig = px.pie(cont, names='continent', values='pop', title=f'Population by continent — {year_value}')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=300)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
