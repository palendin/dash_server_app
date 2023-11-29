import numpy as np
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import dcc, html, Input, Output, State
from dash import dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings
import base64
import io
from flask import Flask
warnings.filterwarnings('ignore')
from pg_query import query_biopsyresult, query_hp_raw


# initialize server for your app deployment
server = Flask(__name__)

# making a dash to run in the server __name__; stylesheet = html styling
app = dash.Dash(__name__, server = server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# if deploy onto a server
server = app.server


# create a background template for plots
templates = ['plotly', 'seaborn', 'simple_white', 'ggplot2',
             'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
             'ygridoff', 'gridon', 'none']


# create a blank figure to prevent plotly dash error when runnng the app, even though it still works without this.
def blankfigure():
    figure = go.Figure(go.Scatter(x=[],y=[]))
    figure.update_layout(template = None)
    figure.update_xaxes(showgrid = False, showticklabels = False, zeroline = False)
    figure.update_yaxes(showgrid = False, showticklabels = False, zeroline = False)

    return figure


app.layout = html.Div([
        
        # components for label and input content by user
        dbc.Row([dbc.Col(html.H1('Vitrolab Analytical Dashboard', style={'textAlign': 'center', "font-size":"60px"}))]), # title
        dbc.Row([dbc.Col(html.Label('Enter an analytical experiment', style={'textAlign': 'left'}))]), 
        dbc.Row([dbc.Input(id = 'experiment_id')]),
        html.Div(id="experiment_id_upload"),
        html.Br(),
        
        # components for submit button for query
        dbc.Row([html.Button('Submit', id='submit button', n_clicks=0,  style={'width': '30%'})]),
        dbc.Row([html.Label('if experiment id is not specified, submit will query all experiment', style={'margin' : '0px 0px 0px 100px', "font-size":"10px"})]), #margin: top, right, bottom, left
        html.Div(id='button output', children=''),  
        dcc.Store(id='intermediate-value'),
        html.Br(),
        
        # components for button for template (for two plots)
        dbc.Row([dbc.Col(dcc.RadioItems(id='template', options = [{'label': k, 'value': k} for k in templates], value = None, inline=True)),
                 dbc.Col(dcc.RadioItems(id='template1', options = [{'label': k, 'value': k} for k in templates], value = None, inline=True)), # grid style
                 ]), # grid style
        html.Br(),

        # components for graph, graph options, and download data from plot (for two plots)
        dbc.Row([dbc.Col(dcc.Graph(id="graph", figure=blankfigure())),
                 dbc.Col(dcc.Graph(id="graph1", figure=blankfigure()))
                 ]),
        dbc.Row([dbc.Col(dcc.RadioItems(id = 'plot_type', options = ['line','bar'], value = 'line', inline=True, style={'font-size':20})),
                 dbc.Col(dcc.RadioItems(id = 'plot_type1', options = ['line','bar'], value = 'line', inline=True, style={'font-size':20})),
                 ]),
        dbc.Row([dbc.Col(html.Button("Download Plot Data", id="download_plot_data_button")),
                 dbc.Col(dcc.Download(id="download-plot-data-csv")),
                 dbc.Col(html.Button("Download Plot Data", id="download_plot_data_button1")),
                 dbc.Col(dcc.Download(id="download-plot-data-csv1"))
                ]),
        html.Br(),
    

        # components for upload file 
        dbc.Row([dbc.Col(html.Label('Upload file') ,style={'textAlign': 'left',"font-size":"30px"})]),
        dbc.Row([dcc.Upload(id='upload-data',children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
                    style={
                        'width': '30%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                            },
                        # Allow multiple files to be uploaded
                        multiple=False
                           )
                ]),
        html.Div(id='output-data-upload', children = ''),    
        
        # component for radio button for show/hide table
        dbc.Row([dcc.RadioItems(id = 'show_hide_table_button', options = ['show', 'hide'], value = 'hide')]),
])



# callback function experiment id input/output
@app.callback(
    Output("experiment_id_upload", "children"),
    Input('experiment_id', 'value')
)

def update_project_id(experiment_id):
    return f"{experiment_id} = analytical exp id"


# callback for submitting query, then generate data table dropdown
@app.callback(
    [Output('button output', 'children'),
    Output('intermediate-value', 'data')],
    Input('submit button', 'n_clicks'),
    State('experiment_id', 'value'),
)

def update_output(n_clicks, experiment_id):

    # create a list from input of experimenet_id
    if not n_clicks:
    #raise dash.exceptions.PreventUpdate
        return dash.no_update
    if not experiment_id:
        experiment_id_list = None
    else:
        experiment_id_list = experiment_id.split(', ')
    print(experiment_id_list)

    # query the result from google cloud through pg admin
    biopsy = query_biopsyresult(experiment_id_list)
    hp_raw = query_hp_raw(experiment_id_list)

    # create global dictionary for data_table 
    data_table_names = ['biopsy','hp_raw_data']
    data_tables = [biopsy,hp_raw]
    print(data_tables)
    
    global table_dict
    table_dict = dict(zip(data_table_names, data_tables))
    print(type(table_dict))

    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Row([dbc.Col(html.Label('Table', style={'fontSize': 30}))]), # title
                dbc.Row([dbc.Col(dcc.Dropdown(id = 'data_table', options = data_table_names, value = None))]),
                html.Div(id='data_table_option', children='')
                ]),
            
        dbc.Row([dbc.Col(html.Button("Download Table", id="download_button")), # input
                  dbc.Col(dcc.Download(id="download-dataframe-csv")) # output
                 ])
           ])
        ]), "done"



# callback and function for outputing selected table and its dropdown options
@app.callback(
    Output(component_id='data_table_option', component_property='children'),
    Input(component_id='data_table', component_property='value')
)

def data_table_output(data_table):
    
    # create global dataframe for dropdown and accessible by figure 
    global dataframe
    if data_table is not None:
        dataframe = table_dict[data_table]
        experiment_id = dataframe['experiment_id'].unique()
        #experiment_id = np.insert(experiment_id,0,'all')
        dropdown = dataframe.columns
        
    else:
        dropdown = None 
    
    # create global table name for download file
    global selected_table
    selected_table = data_table
    
    # return dropdown menu in the layout
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Row([dbc.Col(html.Label('Select experiment'), width=2), #column contains the text, width = column width. If its 6, then it spans half of the dbc.row
                         dbc.Col(dcc.Dropdown(id = 'experiment_id', options = experiment_id, value = None, multi = True)),
                         dbc.Col(html.Label('All Experiments'), width=6),
                         html.Br()
                        ]),

                dbc.Row([dbc.Col(html.Label('Select x-axis from dropdown'), width=2), #width = between Cols
                         dbc.Col(dcc.Dropdown(id = 'xaxis_column', options = dropdown, value = None)),
                         dbc.Col(html.Label('Select x-axis from dropdown'), width=2), #width = between Cols
                         dbc.Col(dcc.Dropdown(id = 'xaxis_column1', options = dropdown, value = None)),
                        ]),

                dbc.Row([dbc.Col(html.Label('Select y-axis from dropdown'), width=2),
                         dbc.Col(dcc.Dropdown(id = 'yaxis_column', options = dropdown, value = None, multi = True)),
                         dbc.Col(html.Label('Select y-axis from dropdown'), width=2),
                         dbc.Col(dcc.Dropdown(id = 'yaxis_column1', options = dropdown, value = None, multi = True)),
                ]),

         
                # dbc.Row([dbc.Col(html.Label('All Experiments'), width=2)]),
                # dbc.Row([dbc.Col(html.Label('Select x-axis from dropdown'), width=2), #width = between Cols
                #          dbc.Col(dcc.Dropdown(id = 'xaxis_column1', options = dropdown, value = None)),
                #          dbc.Col(html.Label('Select y-axis from dropdown'), width=2),
                #          dbc.Col(dcc.Dropdown(id = 'yaxis_column1', options = dropdown, value = None, multi = True)),
                #         ]),
                ])
            ])
        ])

# callback and function for downloading data table
@app.callback(
    Output(component_id = 'download-dataframe-csv', component_property = 'data'),
    Input(component_id = 'download_button', component_property = 'n_clicks'),
    prevent_initial_call=True
)
def download_data_table(n_clicks):
    return dcc.send_data_frame(dataframe.to_csv, f'{selected_table}.csv')


#callback and function for graphs output
@app.callback( 
    Output(component_id='graph', component_property='figure'),
    Input(component_id='template', component_property='value'),
    Input(component_id='experiment_id', component_property='value'),
    Input(component_id='xaxis_column', component_property='value'),
    Input(component_id='yaxis_column', component_property='value'),
    Input(component_id = 'plot_type', component_property = 'value')
)

def update_figure(template, experiment_id, xaxis_column, yaxis_columns, plot_type):
    # if experiment_id == ["all"]:
    #         experiment_id = table_dict[selected_table]['experiment_id']
    #         experiment_id = experiment_id.unique()
    #         print(experiment_id)
    # update data tabe in data filter
    #if xaxis_column or yaxis_columns is None:
    if xaxis_column and yaxis_columns is not None:
        
        data_filtered = dataframe[dataframe['experiment_id'].isin(experiment_id)]

        # create figure object 
        fig = go.Figure()

        # create list of yaxis string for go.Scatter()
        yaxis_num = []
        for count in range(len(yaxis_columns)):
            count += 1
            string = 'y'+ str(count)
            yaxis_num.append(string)

        if plot_type == 'line':
            # create plots 
            if len(experiment_id) >= 2:
                # if go.Scatter is used, here is always a straight line when more than yaxis is selected
                fig = px.line(data_filtered, x=xaxis_column, y=yaxis_columns, color='experiment_id', title = '{} vs {}'.format(xaxis_column, yaxis_columns), markers = True)
    
            else:   
                for i,yaxis_column in enumerate(yaxis_columns):
                    #print(xaxis_column, yaxis_column)
                    fig.add_trace(go.Scatter(x=data_filtered[xaxis_column],y=data_filtered[yaxis_column],name=yaxis_column,yaxis= yaxis_num[i])) #marker_color='#d99b16',hoverinfo='none'))

        if plot_type == 'bar':
             # create plots 
            if len(experiment_id) >= 2:
                # if go.Scatter is used, here is always a straight line when more than yaxis is selected
                fig = px.histogram(data_filtered, x=xaxis_column, y=yaxis_columns, color=xaxis_column, barmode='group', histfunc='avg', text_auto = True, title = '{} vs {}'.format(xaxis_column, yaxis_columns))
    
            else:
                for i,yaxis_column in enumerate(yaxis_columns):
                    #print(xaxis_column, yaxis_column)
                    fig.add_trace(go.Histogram(x=data_filtered[xaxis_column],y=data_filtered[yaxis_column], textposition='auto', bingroup='group', histfunc='avg')) #marker_color='#d99b16',hoverinfo='none'))


        # create a dictionary containing multiple dictionares of yaxis
        args_for_update_layout = dict()
        for i, yaxis_name in enumerate(yaxis_columns):
            key_name = 'yaxis' if i ==0 else f'yaxis{i+1}'
            if i == 0:
                yaxis_args = dict(title=yaxis_columns[0])
            else:
                yaxis_args = dict(title=yaxis_name, anchor = 'free', overlaying =  'y', side = 'left', autoshift = True)
            
            # populate the dictionary
            args_for_update_layout[key_name] = yaxis_args
            #print(args_for_update_layout)
            
        # update layout using yaxis dictionary. 
        fig.update_layout(**args_for_update_layout)
        fig.update_layout(template=template)

        
        # combine selected data together for download in callback
        x = pd.DataFrame(data_filtered[xaxis_column]) # turn series into panda datafrae
        x.reset_index(drop=True, inplace=True) # must drop index (the 0, 1, 2..) or else will get NaN values and columns dont line up when concat
        y = pd.DataFrame(data_filtered[yaxis_columns])
        y.reset_index(drop=True, inplace=True)

        global selected_figure_data  # create global variable for selected data column for download
        selected_figure_data = pd.concat([x,y],axis=1)

    else:
        return blankfigure()

    return fig
   
# callback and function for downloading data table
@app.callback(
    Output(component_id = 'download-plot-data-csv', component_property = 'data'),
    Input(component_id = 'download_plot_data_button', component_property = 'n_clicks'),
    prevent_initial_call=True
)
def download_data_from_figure(n_clicks):
    return dcc.send_data_frame(selected_figure_data.to_csv, 'data_from_figure.csv')


#callback and function for 2nd graph output 
@app.callback( 
    Output(component_id='graph1', component_property='figure'),
    Input(component_id='template1', component_property='value'),
    Input(component_id='xaxis_column1', component_property='value'),
    Input(component_id='yaxis_column1', component_property='value'),
    Input(component_id = 'plot_type1', component_property = 'value')
)

def update_figure(template, xaxis_column, yaxis_columns, plot_type):
    # if experiment_id == ["all"]:
    #         experiment_id = table_dict[selected_table]['experiment_id']
    #         experiment_id = experiment_id.unique()
    #         print(experiment_id)
    # update data tabe in data filter
    #if xaxis_column or yaxis_columns is None:
    if xaxis_column and yaxis_columns is not None:
        
        data_filtered = dataframe
        #data_filtered = dataframe[dataframe['experiment_id'].isin(experiment_id)]

        # create figure object 
        fig = go.Figure()

        # create list of yaxis string for go.Scatter()
        yaxis_num = []
        for count in range(len(yaxis_columns)):
            count += 1
            string = 'y'+ str(count)
            yaxis_num.append(string)

        if plot_type == 'line':
            fig = px.line(data_filtered, x=xaxis_column, y=yaxis_columns, color='experiment_id', title = '{} vs {}'.format(xaxis_column, yaxis_columns), markers = True)
    
        if plot_type == 'bar':
            # if go.Scatter is used, here is always a straight line when more than yaxis is selected
            fig = px.histogram(data_filtered, x=xaxis_column, y=yaxis_columns, color=xaxis_column, barmode='group', histfunc='avg', text_auto = True, title = '{} vs {}'.format(xaxis_column, yaxis_columns))

        # create a dictionary containing multiple dictionares of yaxis
        args_for_update_layout = dict()
        for i, yaxis_name in enumerate(yaxis_columns):
            key_name = 'yaxis' if i ==0 else f'yaxis{i+1}'
            if i == 0:
                yaxis_args = dict(title=yaxis_columns[0])
            else:
                yaxis_args = dict(title=yaxis_name, anchor = 'free', overlaying =  'y', side = 'left', autoshift = True)
            
            # populate the dictionary
            args_for_update_layout[key_name] = yaxis_args
            #print(args_for_update_layout)
            
        # update layout using yaxis dictionary. 
        fig.update_layout(**args_for_update_layout)
        fig.update_layout(template=template)

        
        # combine selected data together for download in callback
        x = pd.DataFrame(data_filtered[xaxis_column]) # turn series into panda datafrae
        x.reset_index(drop=True, inplace=True) # must drop index (the 0, 1, 2..) or else will get NaN values and columns dont line up when concat
        y = pd.DataFrame(data_filtered[yaxis_columns])
        y.reset_index(drop=True, inplace=True)

        global selected_figure_data1  # create global variable for selected data column for download
        selected_figure_data1 = pd.concat([x,y],axis=1)

    else:
        return blankfigure()

    return fig
   
# callback and function for downloading data table
@app.callback(
    Output(component_id = 'download-plot-data-csv1', component_property = 'data'),
    Input(component_id = 'download_plot_data_button1', component_property = 'n_clicks'),
    prevent_initial_call=True
)
def download_data_from_figure(n_clicks):
    return dcc.send_data_frame(selected_figure_data1.to_csv, 'data_from_all_experiment.csv')


# callback and functions for uploading data table. Must decode contents first, hence the parse function first.
def parse_contents(contents, file_name): # 'contents/filename' property is needed for callbacks
    
    content_type, content_string = contents.split(',')
    #print(content_type)
    
    decoded = base64.b64decode(content_string)
    #print(decoded)
   
    if 'csv' in file_name:
        # Assume that the user uploaded a CSV file
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    elif 'xls' in file_name:
        # Assume that the user uploaded an excel file
        df = pd.read_excel(io.BytesIO(decoded))
    elif 'txt' in file_name:
        # Assume that the user uploaded an text file
        # 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte -> USE utf-16
        df = pd.read_csv(io.StringIO(decoded.decode('utf-16')), delimiter = '\t') # \t separates columns separated by tabs

    return df
        
@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'), # refer to first arg in upload_data_file()
    Input('upload-data', 'filename'), # refer to 2nd arg in upload_data_file()
    Input(component_id = 'show_hide_table_button', component_property = 'value') # refer to 3rd arg in upload_data_file()
    
    #State('upload-data', 'last_modified'),
    #prevent_initial_call=True
)
    
def upload_data_file(contents, file_name, display):
    table = html.Div()
    
    global uploaded_df
    if contents is not None:
        uploaded_df = parse_contents(contents, file_name) # dataframe object
        dropdown = uploaded_df.columns
        table = html.Div([
                    dbc.Row([dbc.Col([html.H5(file_name)])]),
                    
                    # show data table
                    dbc.Row([dbc.Col([dash_table.DataTable(data=uploaded_df.to_dict('rows'), columns=[{"name": i, "id": i} for i in uploaded_df.columns])])]),
                    html.Br(),
            
                    # component for show dropdown options
                    dbc.Row([
                        dbc.Col([
                            dbc.Row([dbc.Col(html.Label('Select x-axis from dropdown'), width=2), #width = between Cols
                                     dbc.Col(dcc.Dropdown(id = 'xaxis_column_from_upload_data', options = dropdown, value = None)),
                                     dbc.Col(html.Label('Select y-axis from dropdown'), width=2),
                                     dbc.Col(dcc.Dropdown(id = 'yaxis_column_from_upload_data', options = dropdown, value = None, multi = True)),
                                    ])
                                ])
                            ]),
            
                    # component for output graph when data is uploaded
                    dbc.Row([dbc.Col(dcc.RadioItems(id='template2', options = [{'label': k, 'value': k} for k in templates], value = None, inline=True))]), # grid style
                    dbc.Row([dbc.Col(dcc.Graph(id="graph_from_upload", figure=blankfigure()))]),
                    ])
        
    # connecting radio button options with output of upload button
    if display == 'show': 
        return table
    if display == 'hide':
        return None

@app.callback( 
    Output(component_id='graph_from_upload', component_property='figure'),
    Input(component_id='template2', component_property='value'),
    Input(component_id='xaxis_column_from_upload_data', component_property='value'),
    Input(component_id='yaxis_column_from_upload_data', component_property='value'),
)

def update_figure_from_upload(template, xaxis_column, yaxis_columns):
    
    # create figure object 
    fig = go.Figure()
 
    if xaxis_column and yaxis_columns:

        # create list of yaxis string for go.Scatter()
        yaxis_num = []
        for count in range(len(yaxis_columns)):
            count += 1
            string = 'y'+ str(count)
            yaxis_num.append(string)
         
        # create plots 
        for i,yaxis_column in enumerate(yaxis_columns):
            #print(xaxis_column, yaxis_column)
            fig.add_trace(go.Scatter(x=uploaded_df[xaxis_column],y=uploaded_df[yaxis_column],name= yaxis_column,yaxis= yaxis_num[i])) #marker_color='#d99b16',hoverinfo='none'))
         
        # create a dictionary containing multiple dictionares of yaxis
        args_for_update_layout = dict()
        for i, yaxis_name in enumerate(yaxis_columns):
            key_name = 'yaxis' if i ==0 else f'yaxis{i+1}'
            if i == 0:
                yaxis_args = dict(title=yaxis_columns[0])
            else:
                yaxis_args = dict(title=yaxis_name, anchor = 'free', overlaying =  'y', side = 'left', autoshift = True)
            
            # populate the dictionary
            args_for_update_layout[key_name] = yaxis_args
            #print(args_for_update_layout)
            
        # update layout using yaxis dictionary. 
        fig.update_layout(**args_for_update_layout)
        
        # update plot background templates
        fig.update_layout(template=template)
        
    else:
        return blankfigure()

    return fig

if __name__ == "__main__":
    #app.run_server(debug=True, host='0.0.0.0', port=8080)
    app.run_server(debug=False)
    #app.run(debug=False)
    #kill port https://stackoverflow.com/questions/73309491/port-xxxx-is-in-use-by-another-program-either-identify-and-stop-that-program-o