'''
show_temp.py
Temperaturen anzeigen mit dash
sk,04,07,22 Erster Versuch
sk,04,07,22 Variablen ausgelagert in config.cfg
'''
from datetime import date
import pandas as pd
import dash
from dash import dash_table
import sqlite3, os
from dash import Dash, html, dcc
import plotly.express as px
from dateutil import tz
from dash.dependencies import Input, Output

CFG_FILE='.\config.cfg'
# MEASUREMENT_INTERVAL_SECONDS=60
# WEATHER_STATION_ACCESS_INTERVAL_SECONDS=60*15
# INVALID_TEMP_STR='-30.0'

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
#cursor =conn.cursor()
sel_string = 'SELECT * FROM ' + TABLE_NAME
#cursor.execute(sel_string)

df = pd.read_sql(sel_string,conn)
app = dash.Dash(__name__)

# Unix epoch in DateTime umwandeln 
# https://stackoverflow.com/questions/65948018/how-to-convert-unix-epoch-time-to-datetime-with-timezone-in-pandas
df['UnixTime'] = pd.to_datetime(df['UnixTime'],unit='s', utc=True).apply(lambda x: x.tz_convert('Europe/Berlin'))
Temps = px.line(df, x=df['UnixTime'], y=df.columns)

app.layout = html.Div([
    # dcc.Dropdown(['New York City', 'Montreal', 'San Francisco'], 'Montreal'),

    dcc.Markdown('''
        #### Dash and Markdown
        Dash supports [Markdown](http://commonmark.org/help).
        Markdown is a simple way to write and format text.

        It includes a syntax for things like **bold text** and *italics*,
        [links](http://commonmark.org/help), inline `code` snippets, lists,
        quotes, and more.
    '''),

    html.H1("Temperaturen", style={'text-align': 'center'}),
    dcc.DatePickerRange(
        id='date-picker-range',
        display_format="DD.MM.YYYY",
        start_date = date.today(),
        end_date = date.today(),
        #start_date=date(1997, 5, 3),
        end_date_placeholder_text='Select a date!'
    ),
        dcc.Graph(
        id='Temperaturen',
        figure=Temps
    ),


])



if __name__ == '__main__':
    app.run_server(debug=False)