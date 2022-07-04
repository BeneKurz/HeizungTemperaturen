'''
show_temp.py
Temperaturen anzeigen mit dash
sk,04,07,22 Erster Versuch
'''
from datetime import date
import pandas as pd
import dash
from dash import dash_table
import sqlite3
from dash import Dash, html, dcc
import plotly.express as px
from dateutil import tz
from dash.dependencies import Input, Output


conn = sqlite3.connect('Temperaturen.db')
#cursor =conn.cursor()
sel_string = 'SELECT * FROM temperaturen'
#cursor.execute(sel_string)

df = pd.read_sql(sel_string,conn)
app = dash.Dash(__name__)

# Unix epoch in DateTime umwandeln 
# https://stackoverflow.com/questions/65948018/how-to-convert-unix-epoch-time-to-datetime-with-timezone-in-pandas
df['UnixTime'] = pd.to_datetime(df['UnixTime'],unit='s', utc=True).apply(lambda x: x.tz_convert('Europe/Berlin'))
Temps = px.line(df, x=df['UnixTime'], y=df.columns)

# @app.callback(Output("histogramm", "figure"),[Input("verteilung-dropdown", "value"), Input("n-input", "value")])
app.layout = html.Div([
    # html.Div(dcc.Input(id='input-box', type='text')),
    # html.Button('Submit', id='button-example-1'),
    # html.Div(id='output-container-button', children='Enter a value and press submit'),
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