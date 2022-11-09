'''
show_temp.py
Temperaturen anzeigen mit dash
sk,04,07,22 Erster Versuch
sk,04,07,22 Variablen ausgelagert in config.cfg
'''
from datetime import date
import datetime
import pandas as pd
import dash
from dash import dash_table
import sqlite3, os
from dash import Dash, html, dcc
import plotly.express as px
from dateutil import tz

from dash.dependencies import Input, Output

CFG_FILE='.\config.cfg'

start = datetime.datetime(2022, 6, 25)
end = datetime.datetime(2022, 6, 26)


if os.path.isfile(CFG_FILE):       
	s = open(CFG_FILE, 'r').read() 
	SENSORS = {}                  
	try:                          
		GLOBALS = eval(s)
		MEASUREMENT_INTERVAL_SECONDS=GLOBALS.get('MEASUREMENT_INTERVAL_SECONDS')
		WEATHER_STATION_ACCESS_INTERVAL_SECONDS=GLOBALS.get('WEATHER_STATION_ACCESS_INTERVAL_SECONDS')
		INVALID_TEMP_STR=GLOBALS.get('INVALID_TEMP_STR')
		DB_NAME=GLOBALS.get('DB_NAME')
		TABLE_NAME=GLOBALS.get('TABLE_NAME')
		VERBOSE= GLOBALS.get('VERBOSE')
		SENSORS = GLOBALS.get('SENSORS')
	except:     
		print('error config file '+ CFG_FILE)  

if (os.name == 'nt'):                                            
    DB_FILENAME=DB_NAME
else:                                                            
	DB_FILENAME='/var/lib/grafana/' + DB_NAME


conn = sqlite3.connect(DB_FILENAME)
sel_string = 'SELECT * FROM ' + TABLE_NAME
original_df = pd.read_sql(sel_string,conn)


def filter_df(df, start_date, end_date):
    return df
    filtered_df = df.query(str(unix_epoch(start_date)) + ' <= UnixTime <= ' + str(unix_epoch(end_date)))

    print('Filter von : ' + str(filtered_df["UnixTime"].min()) + ' bis: ' + str(filtered_df["UnixTime"].max() ))
    filtered_df['UnixTime'] = pd.to_datetime(filtered_df['UnixTime'],unit='s', utc=True).apply(lambda x: x.tz_convert('Europe/Berlin'))
    return filtered_df

def unix_epoch(dattime):
    return (dattime - datetime.datetime(1970,1,1)).total_seconds()

start_date = datetime.datetime(2022, 6, 27)
end_date = datetime.datetime(2022, 6, 28)
temp_df = filter_df(original_df, start_date, end_date)
print(temp_df[:10])


app = dash.Dash(__name__)


# Unix epoch in DateTime umwandeln 
# https://stackoverflow.com/questions/65948018/how-to-convert-unix-epoch-time-to-datetime-with-timezone-in-pandas
# df['UnixTime'] = pd.to_datetime(df['UnixTime'],unit='s', utc=True).apply(lambda x: x.tz_convert('Europe/Berlin'))
# df['UnixTime'] = pd.to_datetime(df['UnixTime'],unit='s', utc=True)
# df[(df['UnixTime'] > '27.06.2022') & (df['UnixTime'] < '28.06.2022')]

# df[(df['UnixTime']>pd.Timestamp(2016,1,1)) & (df['UnixTime']<pd.Timestamp(2022,6,28))]

# Temps = px.line(df, x=df['UnixTime'], y=df.columns)


app.layout = html.Div([
    # dcc.Dropdown(['New York City', 'Montreal', 'San Francisco'], 'Montreal'),
    # html.Div(dcc.Input(id='input-on-submit', type='text')),
    html.Button('Aktualisieren', id='do-refresh', n_clicks=0),

    # dcc.Markdown('''
    #     #### Dash and Markdown
    #     Dash supports [Markdown](http://commonmark.org/help).
    #     Markdown is a simple way to write and format text.

    #     It includes a syntax for things like **bold text** and *italics*,
    #     [links](http://commonmark.org/help), inline `code` snippets, lists,
    #     quotes, and more.
    # '''),

    html.H1("Temperaturen", style={'text-align': 'center'}),
    dcc.DatePickerRange(
        id='date_filter',
        display_format="DD.MM.YYYY",
        start_date=datetime.datetime.fromtimestamp(original_df["UnixTime"].min()),
        end_date=datetime.datetime.fromtimestamp(original_df["UnixTime"].max()),
        min_date_allowed=datetime.datetime.fromtimestamp(original_df["UnixTime"].min()),
        max_date_allowed=datetime.datetime.fromtimestamp(original_df["UnixTime"].max()),
        end_date_placeholder_text='Select a date!',
        minimum_nights=0,
    ),
        dcc.Graph(
        id='Temperaturen',
        #figure=Temps
    ),
])


@app.callback(Output("Temperaturen", "figure"),
              [Input("date_filter", "start_date"), 
              Input("date_filter", "end_date")])
              
def updateGraph(start_date, end_date):
    df = filter_df(original_df, start_date, end_date)
    print('sd: ' + str(start_date) + ' ed: ' + str(end_date))
    if not start_date or not end_date:
        raise dash.exceptions.PreventUpdate
    #start = datetime.datetime(2022, 6, 25)
    #end = datetime.datetime(2022, 6, 28)

    # Das fehlt hier noch!
    # https://stackoverflow.com/questions/69017021/dash-datepickerrange-with-graph
    return px.line(
        df,  
        #df["UnixTime"].between(pd.to_datetime(start_date), pd.to_datetime(end_date)),
        x=df['UnixTime'], 
        y=df.columns
        )
    # return Temps



if __name__ == '__main__':
    app.run_server(debug=False)