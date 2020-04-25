import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from urllib.request import urlopen
import json

# Extracting all the tables from the url. This will return all the tables in the form of a list
dfs=pd.read_html('https://www.mohfw.gov.in/')

# Total length of the list is 1.
df=dfs[0]

# Removing the last 3 rows using slicing
# This step is very important because the data in the govt. website keeps on Changing, So first look at the govt. website to see how many rows you have to delete.
df=df.iloc[0:-4,:] 

# Removing the first column of S. No.
df=df.drop('S. No.',axis=1)

# If we look at our Geojson file, it has property of NAME_1 which we will be our key.
# So, have to make sure that name of the state in our data and Geojson file is same.

# Changing name of the state in our data to match with the Geojson data.
data=df.replace('Andaman and Nicobar Islands','Andaman and Nicobar')
data=data.replace('Odisha','Orissa')
data=data.replace('Uttarakhand','Uttaranchal')
data=data.replace('Telengana','Telangana')

# Changing the column names
data.columns=['Name of State / UT','Total Confirmed Cases','Cured/Discharged/Migrated','Death']

data['Total Confirmed Cases'] = data['Total Confirmed Cases'].astype(int)

# Our Geojson data does not contain Ladakh. So, we will add Ladakh cases in Jammu & Kashmir
lvalue=data.loc[data['Name of State / UT']=='Ladakh','Total Confirmed Cases'].item()  #Extracting Ladakh cases

# Adding Jammu & Kashmir cases with Ladakh and storing in Jammu & Kashmir.
data.loc[data['Name of State / UT']=='Jammu and Kashmir','Total Confirmed Cases'] = data.loc[data['Name of State / UT']=='Jammu and Kashmir','Total Confirmed Cases'].item() + lvalue

#Dropping "Ladakh from 1st column as we do not have Ladakh in Geojson file"
data=data.drop(data[data['Name of State / UT']=='Ladakh'].index)

#print(data) ----> Final Data

sum=data['Total Confirmed Cases'].sum()

app=dash.Dash(__name__)

with urlopen('https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson') as response:
    states=json.load(response)

options=[{'label':i,'value':i} for i in data['Name of State / UT'].unique()]

app.layout=html.Div([
            html.H1('India COVID-19 Tracker', style={'text-align':'center'}),
            html.Div([
                dash_table.DataTable(
                    id='table',
                    columns=[{"name":i,"id":i} for i in data.columns],
                    data=data.to_dict('records'),
                    style_cell={'textAlign':'left'},
                    style_table={'height':'40%','width':'40%','margin-left':'40px'},
                    style_data_conditional=[{
                            'if':{'row_index':'odd'},
                            'backgroundColor':'rgb(248, 248, 248)'
                    }],
                    style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                    }
                )
            ], style={'height':'50%','width':'50%','margin-left':'40px','margin-top':'40px','display':'inline-block'}),
            html.Div([dcc.Graph(id='choropleth',
                        figure={'data':[
                        go.Choroplethmapbox(geojson=states, featureidkey='properties.NAME_1', locations=data['Name of State / UT'], z=data['Total Confirmed Cases'],
                                            name='Confirmed Cases', text=data['Name of State / UT'], hoverinfo='location+z', marker_opacity=0.5, colorscale=[[0,'#fee0d2'],[0.5,'#fc9272'],[1,'#de2d26']],
                                            colorbar={'title':{'text':'Confirmed Cases','font':{'family':'Arial','color':'#000000'}}})
                        ],
                        'layout':go.Layout(title='India Map', mapbox_style="carto-positron", mapbox_zoom=3, mapbox_center = {"lat": 20.5937, "lon": 78.9629}, hovermode='closest',height=800)}),

                        html.P(children="Total Number of Cases in India: {}".format(sum),
                            id='total-count',
                            style={'text-align':'center','font-size':'150%'})
                    ],
                        style={'display':'inline-block','verticalAlign':'top','height':'80%','width':'40%'}),
            html.Div([
                html.Br(),
                html.Br(),
                html.Br(),
                html.Br(),
                dcc.Dropdown(
                    id='statepicker',
                    options=options,
                    value=data['Name of State / UT'].unique(),
                    multi=True,
                    placeholder='Select a state',
                    #style={'margin-left':'40px','margin-right':'40px'}
                )
            ],style={'margin-left':'50px','margin-right':'50px'}),
            html.Div([
                dcc.Graph(
                    id='bargraph',
                    figure={'data':[
                        {'x':data['Name of State / UT'].unique(),
                        'y':data['Total Confirmed Cases'],
                        'type':'bar'}],
                    'layout':{'title':'State Wise Cases','autosize':True}
                    }
            )])
            ])


@app.callback(
    Output('bargraph','figure'),
    [Input('statepicker','value')]
)
def update_graph(states):
    temp=data.loc[data['Name of State / UT'].isin(states)]
    y=temp['Total Confirmed Cases']
    trace=[{'x':states,'y':y,'type':'bar'}]

    fig={'data':trace,
        'layout':{'title':'State Wise Cases'}}

    return fig



if __name__ == '__main__':
    app.run_server(debug=False)
