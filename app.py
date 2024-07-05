
# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
from dash.dash_table.Format import Format, Scheme
import pandas as pd
import numpy as np
import plotly.express as px
from utils import get_df

from datetime import datetime, date

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Incorporate data
df0 = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')
df = get_df()
df["amount"] = df["amount"].astype("double")
df['month'] = df['date'].str[:-3] # get month
df['first'] = df['date'].str[-2:] > '15'
dis = df[~df['tag'].isin({'savings', 'income', 'home'})] # discretionary spending

# Initialize the app
app = Dash(__name__)

def get_pichart(df1):
    """
    pie chart for income allocation
    """
    BAR = 50

    excess = (df1.loc['savings', 'percent'] - BAR) * df1.amount.sum() / 100
    fig = px.pie(df1, values='amount', names=df1.index, hole=0.5,
                   title=f'{excess:.3f} excess', hover_data=['percent'])
    fig.update_traces(textposition='inside')
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
    return fig

def get_bars(df1):
    """
    bar chart for income allocation

    assumes
    - df1.index = tags
    - df1.columns = [amount, percent]
    """
    fig = px.bar(df1, x="amount", orientation='h', log_x=True, text_auto=True, hover_data=['percent'],
                    title='income allocation by category')
    return fig

def get_table():
    """
    table for income allocation
    """

    alloc = df[df['tag'] != 'income']
    alloc = alloc.groupby('tag').sum().sort_values('amount', ascending=False)
    alloc['percent'] = 100 * alloc['amount'] / alloc['amount'].sum()
    alloc.reset_index(inplace=True)
    return alloc[['tag', 'amount', 'percent']]

def spending():
    """
    bar chart with monthly spending
    """
    dis_mo = dis.groupby('month').sum()
    avg = dis_mo['amount'].mean()
    fig = px.bar(
        dis_mo,
        y = 'amount',
        title = f'monthly discretionary spending, {avg:.3f} avg'
    )
    
    fig.add_hline(avg)
    return fig

def get_traces():
    # get cumsums for each pay period
    trace = {}
    grouping = dis.groupby(by=['month', 'first'])
    for (month, order), group in grouping:
        cumsum = np.empty(16)
        pseudodates = group['date'].str[-2:].apply(int)
        if order: pseudodates -= 15
        for i in range(16):
            cumsum[i] = group[pseudodates <= 1 + i]['amount'].sum()
        trace[month + ('B' if order else 'A')] = cumsum

    trace = pd.DataFrame(trace)
    trace.index = range(1, 17)
    return trace


def spending_biweekly():
    trace = get_traces()
    avg = trace.iloc[-1, :].mean()
    fig = px.bar(
        trace.iloc[-1, :],
        title = f'biweekly discretionary spending, {avg:.3f} avg'
    )
    fig.add_hline(avg)
    return fig



def traces():
    trace = get_traces()
    today = int(datetime.today().strftime('%d'))
    pseud = today if today <= 15 else today - 15

    # compare current spending with historic spending
    # at this time point
    historic = trace.loc[pseud, :]
    idx = f"{datetime.today().strftime('%Y-%m')}{'B' if today > 15 else 'A'}"
    current = historic[idx] if idx in historic else 0

    n = len(historic)
    lower = sum(historic < current)
    greater = sum(historic > current)
    # you are doing worse off than usual
    titlestr = f"{100 * lower / n:.2f}% < spending < {100 * greater / n:.2f}%"

    fig = px.line(trace, title=titlestr)
    fig.add_vline(pseud) # today: date - 1
    fig.add_scatter(x=[pseud], y=[current], marker=dict(
                    color='red',
                    size=10
                ))
    fig.update_traces(dict(opacity=0.3))
    
    return fig

css=[
        {"selector": ".dash-spreadsheet tr th", "rule": "height: 2px; min-height: 5px"},  # set height of header
        {"selector": ".dash-spreadsheet-inner tr", "rule": "height: 2px; min-height: 1px;"},  # set height of body rows
    ]


# get savings over time for both timeframes
def savings_():
    pass

def net_worth():
    d = get_df('networth')
    d = d.apply(pd.to_numeric, errors='ignore')
    fig = px.line(d, x = 'date', y = 'sum')
    return fig


# App layout
app.layout = html.Div([
    html.Div(className='row', style={'display': 'flex'}, children=[
        dcc.Graph(id="graph1", 
                  style={'display': 'inline-block', 
                         'width': '50vw', 'height': '60vh'}),
        dcc.Graph(id="graph2", 
                  style={'display': 'inline-block',
                         'width': '50vw', 'height': '60vh'})
    ]),
    html.Center(children=[
        dcc.DatePickerRange(id='date-picker-range',
                            start_date=date.fromisoformat(df['date'].min()),
                            end_date=date.fromisoformat(df['date'].max())
        )
    ]),
    dcc.Tabs([
        dcc.Tab(label='biweekly', children=[
            dcc.Graph(id="graph3", figure=spending_biweekly(), 
                  style={'display': 'inline-block', 
                         'width': '50vw', 'height': '60vh'}),
            dcc.Graph(id="graph4", figure=traces(), 
                    style={'display': 'inline-block',
                            'width': '45vw', 'height': '60vh'})
        ]),
        dcc.Tab(label='monthly', children=[
            dcc.Graph(id="graph5", figure=spending(), 
                  style={'display': 'inline-block', 
                         'width': '50vw', 'height': '60vh'}),
        ])
    ]),
    html.Div(className='row', style={'display': 'flex'}, children=[
        dcc.Graph(id="graph7", figure=spending(), 
                  style={'display': 'inline-block', 
                         'width': '50vw', 'height': '60vh'}),
        dcc.Graph(id="graph6", figure=traces(), 
                  style={'display': 'inline-block',
                         'width': '45vw', 'height': '60vh'})
    ]),
    dcc.Graph(id="graph9", figure=net_worth(), 
                  style={'display': 'inline-block', 
                         'width': '50vw', 'height': '60vh'}),
    html.Div(className='row', style={'display': 'flex'}, children=[
        html.Div(style={'display': 'inline-block', 'width': '60vw'}, children = [
            dash_table.DataTable(
                data=df[['date', 'description', 'amount', 'tag', 'notes']].to_dict('records'), 
                page_size=30, 
                style_cell = {
                    'font_size': '12px',
                    'text_align': 'left'
                }, 
                style_cell_conditional = [{
                    'if': {'column_id': 'amount'},
                    'textAlign': 'right'
                }, {
                    'if': {'column_id': 'notes'},
                    'max-width': '500px'
                }],
                style_data = {
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                css = css,
            )
        ]),
        html.Div(style={'display': 'inline-block', 'width': '1vw'}),
        html.Div(style={'display': 'inline-block', 'width': '15vw'}, children = [
            dash_table.DataTable(data=get_table().to_dict('records'), 
                columns = [
                    dict(id='tag', name='tag'),
                    dict(id='amount', name='amount', type='numeric', format=Format(precision=2, scheme=Scheme.fixed)),
                    dict(id='percent', name='percent', type='numeric', format=Format(precision=2, scheme=Scheme.fixed)),
                ],
                style_cell = {
                    'font_size': '12px',
                    'text_align': 'right',
                }, 
                style_cell_conditional = [{
                    'if': {'column_id': 'tag'},
                    'textAlign': 'left'
                }],
                css = css
            )
        ])
    ]),
    html.Hr(),
    dash_table.DataTable(data=df.to_dict('records'), page_size=30, style_cell = {
                'font_size': '12px',
                'text_align': 'right'
            }),
    dcc.RadioItems(options=['pop', 'lifeExp', 'gdpPercap'], value='lifeExp', id='controls-and-radio-item'),
    dcc.Graph(figure={}, id='controls-and-graph')
])

# Add controls to build the interaction
@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
def update_graph(col_chosen):
    fig = px.histogram(df0, x='continent', y=col_chosen, histfunc='avg')
    return fig


@callback(
    Output('graph1', 'figure'),
    Output('graph2', 'figure'),
    Input(component_id='date-picker-range', component_property='start_date'),
    Input(component_id='date-picker-range', component_property='end_date')
)
def update_dates(start, end):
    """
    graph1 and graph2
    """
    df1 = df[df['tag'] != 'income']
    df1 = df1[(start <= df1['date']) &  (df1['date'] <= end)]
    df1 = df1.groupby("tag").sum().sort_values('amount')
    df1.loc[:, 'percent'] = (100 * df1['amount'] / df1['amount'].sum()).round(3)
    return get_pichart(df1), get_bars(df1)



# Run the app
if __name__ == '__main__':
    app.run(debug=True)