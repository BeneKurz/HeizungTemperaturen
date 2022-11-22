#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  appDhtWebServer.py
#  
#  Created by MJRoBot.org 
#  10Jan18
# https://www.hackster.io/mjrobot/from-data-to-graph-a-web-journey-with-flask-and-sqlite-4dba35
# sk,22,11,22 Auf Temperaturen.db umgestellt

'''
	RPi Web Server for DHT captured data  
'''

from flask import Flask, render_template, request
app = Flask(__name__)

from HTTools import get_sensor_names, get_field_names
import sqlite3
import datetime
import os
CFG_FILE = 'config.cfg'

if os.path.isfile(CFG_FILE):
    s = open(CFG_FILE, 'r').read()
    SENSORS = {}
    try:
        GLOBALS = eval(s)
        
        # MEASUREMENT_INTERVAL_SECONDS = GLOBALS.get('MEASUREMENT_INTERVAL_SECONDS')
        # WEATHER_STATION_ACCESS_INTERVAL_SECONDS = GLOBALS.get('WEATHER_STATION_ACCESS_INTERVAL_SECONDS')
        # INVALID_TEMP_STR = GLOBALS.get('INVALID_TEMP_STR')
        # DB_NAME = GLOBALS.get('DB_NAME')
        # TABLE_NAME = GLOBALS.get('TABLE_NAME')
        VERBOSE = GLOBALS.get('VERBOSE')
        SENSORS = GLOBALS.get('SENSORS')
    except:
        print('error config file ' + CFG_FILE)

if (os.name == 'nt'):
    DB_FILENAME = GLOBALS.get('DB_NAME')
else:
    DB_FILENAME = '/var/lib/grafana/' + GLOBALS.get('DB_NAME')



SERVER_PORT=3001
sensor_names = get_sensor_names(GLOBALS.get('SENSORS'))
field_names = get_field_names(GLOBALS.get('SENSORS'), sensor_names)
# Retrieve data from database
def getData():
	conn=sqlite3.connect(DB_FILENAME)
	curs=conn.cursor()

	for row in curs.execute("SELECT * FROM Temperaturen ORDER BY UnixTIme DESC LIMIT 1"):
		#field_array = []
		templateData = {}
		for index, field_name in enumerate(field_names):
			#field_array.append(str(row[index]))
			Data = str(row[index])
			templateData[field_name] = Data
		# time = str(row[0])
		# time = datetime.datetime.now()
		# temp = '24.2'
		# temp = row[2]
		# hum = row[2]
		# #hum = '56'
	conn.close()
	print('Data: ' + ' ' + str(templateData))
	return templateData
#bene = templateData=getData()
#print(str(bene))

#main route 
@app.route("/")
def index():
	# time, temp, hum = getData()
	field_tuple = getData()
	templateData=getData()
	#for field,index in enumerate(field_tuple):
	# templateData = {
	#   'time'	: time,
    #   'temp'	: temp,
    #   'hum'		: hum
	# }
	return render_template('index.html', **templateData)


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)