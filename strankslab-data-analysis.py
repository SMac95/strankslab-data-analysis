import dash
import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import h5py
import math
from bisect import bisect_left

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

#Data storage variables
DATA = pd.DataFrame(index = ['wavelength', 'time', 'dtt', 'timescale'])
TIME_SLICES = pd.DataFrame()
WVL_SLICES = pd.DataFrame()

#Used for styling Plotly graphs
standard_template = dict(layout=go.Layout(
    font = dict(family="Arial", size=12, color='black'), 
    paper_bgcolor = '#ffffff', 
    plot_bgcolor = '#ffffff', 
    xaxis=dict(showline=True, showgrid=False, mirror=True, linewidth=1.5,
               linecolor='black', ticks='outside', tickwidth=1.5,
               tickprefix="<b>", ticksuffix ="</b>"
               ),
    yaxis=dict(showline=True, showgrid=False, mirror=True, linewidth=1.5,
               linecolor='black', ticks='outside', tickwidth=1.5,
               tickprefix="<b>", ticksuffix ="</b>"
               )
    ))
    
#Placeholder figure before plotting data
blank_fig = px.scatter(pd.DataFrame(), template=standard_template)
blank_fig.update_xaxes(title_text = '', zeroline=False)
blank_fig.update_yaxes(title_text='', zeroline=False)

#Interactive Dash components
nav_dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Entry 1"),
        dbc.DropdownMenuItem("Entry 2"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Entry 3"),
    ],
    label="Menu",
    color='secondary',
    in_navbar=True)


file_dropdown = dcc.Dropdown(id='file-dropdown', options={})

upload = dcc.Upload(id='file-load', 
                    children = dbc.Button("Add file", 
                                          id="file-load-button", 
                                          n_clicks=0, 
                                          color="primary", 
                                          size='sm'
                                          )
                    )
delete = dbc.Button("Delete", id="file-delete", n_clicks=0,
                    color="danger", size='sm')


time_switch = dbc.Switch(id="time-switch", label='Time slices:', value=True)
                
wvl_switch = dbc.Switch(id="wvl-switch", label='Wavelength slices:',
                        value=False)
                

time_dropdown = dcc.Dropdown(id='time-dropdown', options=[], 
                             value = [], multi=True)

wvl_dropdown = dcc.Dropdown(id='wvl-dropdown', options= [], 
                            value = [], multi=True)


time_input = dbc.InputGroup([ 
    dbc.Input(id='time-min', type='number', placeholder='Min', size='sm'),
    dbc.Input(id='time-max', type='number', placeholder='Max', size='sm'),
    dbc.Button("Add", id='add-time-slice', n_clicks=0, 
               size='sm', color="primary"),
    dbc.Button('Clear', id='clear-time-slice', n_clicks=0, 
               size='sm', color="danger")
    ])

wvl_input = dbc.InputGroup([
    dbc.Input(id='wvl-min', type='number', 
              placeholder='Min', size='sm'),
    dbc.Input(id='wvl-max', type='number', 
              placeholder='Max', size='sm'),
    dbc.Button("Add", id='add-wvl-slice', n_clicks=0, 
               size='sm', color="primary"),
    dbc.Button('Clear', id='clear-wvl-slice', n_clicks=0, 
               size='sm', color="danger")
    ])

x_axis_options = html.Div([
    html.Div('X-Axis:  ', style={'width': '100px', 'display': 'inline-block'}),
    html.Div([dbc.RadioItems(
        options=[
                {"label": "Linear", "value": 'linear'},
                {"label": "Log", "value": 'log'},
            ],
            value='linear',
            id="x-axis-type",
            inline=True,
        )], style={'display': 'inline-block'}),
    html.Div([
        dbc.InputGroup([
            dbc.Input(id='x-axis-min', type='number', placeholder='Min', size='sm'),
            dbc.Input(id='x-axis-max', type='number', placeholder='Max', size='sm')])
        ])
    ])


y_axis_options = html.Div([
    html.Div('Y-Axis:  ', style={'width': '100px', 'display': 'inline-block'}),
    html.Div([dbc.RadioItems(
        options=[
            {"label": "Linear", "value": 'linear'},
            {"label": "Log", "value": 'log'},
            ],
            value='linear',
            id="y-axis-type",
            inline=True,
            )], style={'display': 'inline-block'}),
    html.Div([
        dbc.InputGroup([
            dbc.Input(id='y-axis-min', type='number', placeholder='Min', size='sm'),
            dbc.Input(id='y-axis-max', type='number', placeholder='Max', size='sm')])
        ])
    ])

navbar = dbc.NavbarSimple(
    children=[nav_dropdown],
    brand="StranksLab",
    color = 'primary',
    className="mb-5"
)

hidden_triggers = html.Div([
    html.Div(id='time-from-graph', n_clicks=0),
    html.Div(id='time-from-input', n_clicks=0),
    html.Div(id='time-from-clear', n_clicks=0),
    html.Div(id='wvl-from-graph', n_clicks=0),
    html.Div(id='wvl-from-input', n_clicks=0),
    html.Div(id='wvl-from-clear', n_clicks=0)],
    style={'display': 'none'})


#Sidebar contains components for interacting with data
sidebar = dbc.Col([
    html.Div([
        html.H5("Data"),
        html.Hr()]),
    html.Div([
        html.Div(upload, style={'display': 'inline-block'}),
        html.Div(delete, style={'display': 'inline-block'})]),
    file_dropdown,
    html.Div([
        html.H5("Processing"),
        html.Hr(),
        ]),
    html.Div([
        html.Div(time_switch, style={'display': 'inline-block'}),
        time_input,
        time_dropdown,
        html.Br()]),
    html.Div([
        html.Div(wvl_switch, style={'display': 'inline-block'}),
        wvl_input,
        wvl_dropdown]),
    html.Div([
        html.H5('Options'),
        html.Hr(),
        x_axis_options,
        y_axis_options])
    ],width=3, style={'height': '80vh', 'borderWidth': '4px',
                      'borderStyle': 'solid', 'borderColor': '#a3c1ad', 
                      'overflow': 'scroll'})


main_graph = dbc.Col([dcc.Graph(id='ta-graph', 
                                figure=blank_fig, style={'height': '80vh'})
                      ], width=True)

spec_graph = dcc.Graph(id='spec-graph', figure=blank_fig, 
                       style={'height': '80vh'})

kin_graph = dcc.Graph(id='kin-graph', figure=blank_fig, 
                      style={'height': '80vh'})
      
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("StranksLab")
            ], width=True),
            dbc.Col([
                nav_dropdown], width=1)
            ], style={'background-color': '#a3c1ad'}, align='end'),
    html.Hr(),
    dbc.Row([
        sidebar,
        main_graph]),
    dbc.Row([
        dbc.Col(spec_graph, width=6),
        dbc.Col(kin_graph, width=6)]),
    hidden_triggers               
    ])

# Returns index and value of element in list closet to the given number
def take_closest(my_list, my_number):
    pos = bisect_left(my_list, my_number)
    if pos == 0:
        return [0, my_list[0]]
    if pos == len(my_list):
        return [pos, my_list[-1]]
    before = my_list[pos - 1]
    after = my_list[pos]
    if after - my_number < my_number - before:
        return [pos, after]
    else:
        return [pos - 1, before]

# Takes data from .hdf5 file and stores in DataFrame with key equal to filename
## NEEDS TO BE UPDATED TO ACCOMODATE MORE DELAY TYPES
def import_data(options, filename):
    global DATA
    with h5py.File(filename, 'r') as f:
        wavelength = f['Average'][0, 1:]
        time = f['Average'][1:, 0]
        dtt = f['Average'][1:, 1:]
        delay_type = f['Average'].attrs['delay type']
    if delay_type == 'Short':
        timescale = 'fs'
    elif delay_type == 'Long':
        timescale = 'ps'
    else:
        timescale = 'fs'
    new_data = pd.DataFrame(
        {filename: [wavelength, time, dtt, timescale]},
        index = ['wavelength', 'time', 'dtt', 'timescale']) 
    DATA = pd.concat([DATA, new_data], axis=1)
    options[filename] = filename
    return options

def delete_data(options, value):
    global DATA
    if value == None:
        return no_update, no_update
    else:
        DATA.drop(columns=value)
        del options[value]
        return options, None
    
# Adds time slice from rectangle dragged over graph
def graph_time_slice(relayoutData, time_clicks, file_selection):
    timescale = DATA.loc['timescale', file_selection]
    x0 = relayoutData['shapes'][-1]['x0']
    x1 = relayoutData['shapes'][-1]['x1']
    if x0 > x1:
        x_min = x1
        x_max = x0
    else:
        x_min = x0
        x_max = x1
    key = str(round(x_min)) + ' ' + timescale + ' - ' + str(round(x_max)) + ' ' + timescale
    TIME_SLICES[key] = [x_min, x_max]
    return time_clicks + 1, TIME_SLICES



def graph_wvl_slice(relayoutData, wvl_clicks):
    y0 = relayoutData['shapes'][-1]['y0']
    y1 = relayoutData['shapes'][-1]['y1']
    if y0 > y1:
        y_min = y1
        y_max = y0
    else:
        y_min = y0
        y_max = y1
    key = str(round(y_min)) + ' nm - ' + str(round(y_max)) + ' nm'
    WVL_SLICES[key] = [y_min, y_max]
    return wvl_clicks + 1, WVL_SLICES

def update_axes(fig, x_type, x_min, x_max, y_type, y_min, y_max):
    if x_type == 'log':
        fig.update_xaxes(type='log')
        if x_min != None and x_max != None:
            fig.update_xaxes(range=[math.log(x_min, 10), math.log(x_max, 10)])
    else:
        fig.update_xaxes(type='linear')
        if x_min != None and x_max != None:
            fig.update_xaxes(range=[x_min, x_max])
    if y_type == 'log':
        fig.update_yaxes(type='log')
        if y_min != None and y_max != None:
            fig.update_yaxes(range=[math.log(y_min, 10), math.log(y_max, 10)])
    else:
        fig.update_yaxes(type='linear')
        if y_min != None and y_max != None:
            fig.update_yaxes(range=[y_min, y_max])
    return fig
    
        
# All functions with @app.callback decorator return an updated output to the
# Dash components labeled in the first lines. Only one function can output to
# a given component.


@app.callback(
    Output("file-dropdown", "options"),
    Output("file-dropdown", "value"),
    Input('file-load', 'contents'),
    Input('file-delete', 'n_clicks'),
    State('file-load', 'filename'),
    State("file-dropdown", "options"),
    State('file-dropdown', 'value'),
    prevent_initial_call=True)
def update_file_dropdown(contents, delete_clicks, filename, options, value):
    global DATA
    ctx = dash.callback_context #Identifies which input triggered callback
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if switch_id == 'file-delete':
        options, value = delete_data(options, value)
        return options, value
    else:
        options = import_data(options, filename) 
        return options, filename

# Toggles slicing switches so that only one is activated at any time
@app.callback(
    Output('time-switch', 'value'),
    Output('wvl-switch', 'value'),
    Input('time-switch', 'value'),
    Input('wvl-switch', 'value'))
def toggle_time_switch(time_switch_val, wvl_switch_val):
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if switch_id == 'time-switch':
        if time_switch_val:
            return True, False
        else:
            return False, True
    else:
        if wvl_switch_val:
            return False, True
        else:
            return True, False

# Time slices dropdown responds to changes in the graph or input box
@app.callback(
    Output('time-dropdown', 'options'),
    Output('time-dropdown', 'value'),
    Input('time-from-graph', 'n_clicks'),
    Input('time-from-input', 'n_clicks'),
    Input('time-from-clear', 'n_clicks'),
    State('time-dropdown', 'options'),
    State('time-dropdown', 'value'),
    prevent_initial_call=True)
def update_time_dropdown(graph_clicks, input_clicks, clear_clicks, options, value):
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if TIME_SLICES.empty:
        raise PreventUpdate
    elif switch_id == 'time-from-graph' or switch_id == 'time-from-input':
        options.append(TIME_SLICES.columns[-1])
        value.append(TIME_SLICES.columns[-1])
        return options, value
    else: # Must have been triggered by clear button
        return [], []
        
# Wavelength slices dropdown responds to changes in the graph or input box
@app.callback(
    Output('wvl-dropdown', 'options'),
    Output('wvl-dropdown', 'value'),
    Input('wvl-from-graph', 'n_clicks'),
    Input('wvl-from-input', 'n_clicks'),
    Input('wvl-from-clear', 'n_clicks'),
    State('wvl-dropdown', 'options'),
    State('wvl-dropdown', 'value'),
    prevent_initial_call=True)
def update_wvl_dropdown(graph_clicks, input_clicks, clear_clicks, options, value):
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if WVL_SLICES.empty:
        raise PreventUpdate
    elif switch_id == 'wvl-from-graph' or switch_id == 'wvl-from-input':
        options.append(WVL_SLICES.columns[-1])
        value.append(WVL_SLICES.columns[-1])
        return options, value
    else: # Must have been triggered by clear button
        return [], []

# Stores input from box to TIME_SLICES. Output triggers dropdown function
# to update the display
@app.callback(
    Output('time-from-input', 'n_clicks'),
    Input('add-time-slice', 'n_clicks'),
    State('time-min', 'value'),
    State('time-max', 'value'),
    State('time-from-input', 'n_clicks'),
    State('file-dropdown', 'value'),
    prevent_initial_call=True)
def add_time_from_input(add_clicks, time_min, time_max, input_clicks, file_selection):
    global TIME_SLICES
    timescale = DATA.loc['timescale', file_selection]
    if time_max == None:
        key = str(time_min) + ' ' + timescale
    elif time_min == None:
        key = str(time_max) + ' ' + timescale
    else: 
        key = str(time_min) + ' ' + timescale + ' - ' + str(time_max) + ' ' + timescale
    
    TIME_SLICES[key] = ([time_min, time_max])
    return input_clicks + 1

# Stores input from box to WVL_SLICES. Output triggers dropdown function
# to update the display
@app.callback(
    Output('wvl-from-input', 'n_clicks'),
    Input('add-wvl-slice', 'n_clicks'),
    State('wvl-min', 'value'),
    State('wvl-max', 'value'),
    State('wvl-from-input', 'n_clicks'),
    prevent_initial_call=True)
def add_wvl_from_input(add_clicks, wvl_min, wvl_max, input_clicks):
    global WVL_SLICES
    if wvl_max == None:
        key = str(wvl_min) + ' nm'
    elif wvl_min == None:
        key = str(wvl_max) + ' nm'
    else: 
        key = str(wvl_min) + ' nm - ' + str(wvl_max) + ' nm'
    WVL_SLICES[key] = ([wvl_min, wvl_max])
    return input_clicks + 1

@app.callback(
    Output('time-from-clear', 'n_clicks'),
    Input('clear-time-slice', 'n_clicks'),
    State('time-from-clear', 'n_clicks'))
def clear_time_slices(clear_button_clicks, clear_time_clicks):
    global TIME_SLICES
    TIME_SLICES = pd.DataFrame()
    return clear_time_clicks + 1

@app.callback(
    Output('wvl-from-clear', 'n_clicks'),
    Input('clear-wvl-slice', 'n_clicks'),
    State('wvl-from-clear', 'n_clicks'))
def clear_wvl_slices(clear_button_clicks, clear_wvl_clicks):
    global WVL_SLICES
    WVL_SLICES = pd.DataFrame()
    return clear_wvl_clicks + 1

# Single function responsible for updating the main TA data figure. 
# Uses a number of helper functions defined above @app.callback section.
@app.callback(
    Output('ta-graph', 'figure'),
    Output('time-from-graph', 'n_clicks'),
    Output('wvl-from-graph', 'n_clicks'),
    Input('file-dropdown', 'value'),
    Input('time-switch', 'value'),
    Input('ta-graph', 'relayoutData'),
    Input('x-axis-type', 'value'),
    Input('x-axis-min', 'value'),
    Input('x-axis-max', 'value'),
    Input('y-axis-type', 'value'),
    Input('y-axis-min', 'value'),
    Input('y-axis-max', 'value'),
    State('time-from-graph', 'n_clicks'),
    State('wvl-from-graph', 'n_clicks'),
    prevent_initial_call=True)
def update_ta_graph(file_selection, time_switch_val, relayoutData, 
                    x_type, x_min, x_max, y_type, y_min, y_max, 
                    time_clicks, wvl_clicks):
    global TIME_SLICES
    global WVL_SLICES
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if DATA.empty or file_selection == None :
        raise PreventUpdate
    elif switch_id == 'ta-graph':
        if 'shapes' not in relayoutData:
            raise PreventUpdate()
        elif time_switch_val:
            time_clicks, TIME_SLICES = graph_time_slice(relayoutData, 
                                                        time_clicks, 
                                                        file_selection) 
            wvl_clicks = no_update
        else:
            wvl_clicks, WVL_SLICES = graph_wvl_slice(relayoutData, 
                                                     wvl_clicks)
            time_clicks = no_update                
    timescale = DATA.loc['timescale', file_selection]   
    fig = px.imshow(DATA.loc['dtt', file_selection].transpose(),
                    labels=dict(x='<b>Delay Time (' + timescale + ')</b>', 
                                y='<b>Wavelength (nm)</b>', 
                                color= '<b>\u0394'+ 'T/T</b>'),
                    x = DATA.loc['time', file_selection],
                    y = DATA.loc['wavelength', file_selection],
                    aspect='auto', origin='lower', template = standard_template,
                    color_continuous_scale=px.colors.diverging.RdBu)
    fig = update_axes(fig, x_type, x_min, x_max, y_type, y_min, y_max)
    if time_switch_val:
        fig.update_layout(clickmode='event+select', 
                          dragmode='drawrect',
                          modebar_add = ['drawrect', 'eraseshape'], 
                          newshape = dict(drawdirection='vertical', 
                                          fillcolor='red', line_width=0)
                          )
    else:
        fig.update_layout(clickmode='event+select', 
                          dragmode='drawrect',
                          modebar_add = ['drawrect', 'eraseshape'], 
                          newshape = dict(drawdirection='horizontal', 
                                          fillcolor='red', line_width=0)
                          ) 
    return fig, time_clicks, wvl_clicks

@app.callback(
    Output('kin-graph', 'figure'),
    Input('file-dropdown', 'value'),
    Input('wvl-dropdown', 'value'),
    Input('wvl-from-clear', 'n_clicks'),
    Input('x-axis-type', 'value'),
    Input('x-axis-min', 'value'),
    Input('x-axis-max', 'value'),
    Input('y-axis-type', 'value'),
    Input('y-axis-min', 'value'),
    Input('y-axis-max', 'value'),
    prevent_initial_call=True)
def update_kin_graph(file_selection, value, n_clicks, x_type, x_min, x_max,
                     y_type, y_min, y_max):
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if switch_id == 'wvl-from-clear':
        return blank_fig
    elif WVL_SLICES.empty or file_selection == None:
        raise PreventUpdate
    else:
        dtt = DATA.loc['dtt', file_selection]
        wavelength = DATA.loc['wavelength', file_selection]
        timescale = DATA.loc['timescale', file_selection]
        kin = pd.DataFrame(dict(time = DATA.loc['time', file_selection]))
        for key in value:
            [wvl_min, wvl_max] = WVL_SLICES[key]
            [index_min, __] = take_closest(wavelength, wvl_min)
            [index_max, __] = take_closest(wavelength, wvl_max)
            kin[key] = np.mean(dtt[:, index_min:index_max], axis=1)
        fig = px.line(kin, x='time', y = kin.columns[1:],
                      template=standard_template,
                      color_discrete_sequence = px.colors.qualitative.Pastel)
        fig.update_layout(legend_x=1,
                          legend_xanchor='right',
                          legend_title_text = '',
                          xaxis=dict(title_text = '<b>Delay Time (' + timescale + ')</b>'),
                          yaxis=dict(title_text='<b>\u0394'+ 'T/T</b>'))
        fig = update_axes(fig,x_type, x_min, x_max, y_type, y_min, y_max)
        return fig


@app.callback(
    Output('spec-graph', 'figure'),
    Input('file-dropdown', 'value'),
    Input('time-dropdown', 'value'),
    Input('time-from-clear', 'n_clicks'),
    Input('x-axis-type', 'value'),
    Input('x-axis-min', 'value'),
    Input('x-axis-max', 'value'),
    Input('y-axis-type', 'value'),
    Input('y-axis-min', 'value'),
    Input('y-axis-max', 'value'),
    prevent_initial_call=True)
def update_spec_graph(file_selection, value, n_clicks, x_type, x_min, x_max,
                      y_type, y_min, y_max):
    ctx = dash.callback_context
    switch_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if switch_id == 'time-from-clear':
        return blank_fig
    elif TIME_SLICES.empty or file_selection == None:
        raise PreventUpdate
    else:
        dtt = DATA.loc['dtt', file_selection]
        time = DATA.loc['time', file_selection]
        spec = pd.DataFrame(dict(wavelength = DATA.loc['wavelength', file_selection]))
        for key in value:
            [time_min, time_max] = TIME_SLICES[key]
            [index_min, __] = take_closest(time, time_min)
            [index_max, __] = take_closest(time, time_max)
            spec[key] = np.mean(dtt[index_min:index_max, :], axis=0)
        fig = px.line(spec, x='wavelength', y=spec.columns[1:], 
                      template = standard_template, 
                      color_discrete_sequence = px.colors.qualitative.Pastel)
        fig.update_layout(legend_title_text = '',
                          legend_x = 1, 
                          legend_xanchor = 'right',
                          xaxis=dict(title_text = '<b>Wavelength (nm)</b>'),
                          yaxis=dict(title_text='<b>\u0394'+ 'T/T</b>'))
        fig = update_axes(fig, x_type, x_min, x_max, y_type, y_min, y_max)
        return fig

if __name__ == "__main__":
    app.run_server(debug=True, port=8888)
    
    