#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  appDhtWebServer.py
#  
#  Created by MJRoBot.org 
#  10Jan18
# https://www.hackster.io/mjrobot/from-data-to-graph-a-web-journey-with-flask-and-sqlite-4dba35

'''
	RPi Web Server for DHT captured data  
'''

from flask import Flask, render_template, request
app = Flask(__name__)

import sqlite3
import datetime

DATABASE_PATH='/var/lib/grafana/Temperaturen.db'
SERVER_PORT=3001
# Retrieve data from database
def getData():
	conn=sqlite3.connect(DATABASE_PATH)
	curs=conn.cursor()

	for row in curs.execute("SELECT * FROM Temperaturen ORDER BY UnixTIme DESC LIMIT 1"):
		time = str(row[0])
		time = datetime.datetime.now()
		temp = '24.2'
		hum = row[2]
		hum = '56'
	conn.close()
	print(str(time) + ' ' + str(temp))
	return time, temp, hum

# main route 
@app.route("/")
def index():
	time, temp, hum = getData()
	templateData = {
	  'time'	: time,
      'temp'	: temp,
      'hum'		: hum
	}
	return render_template('index.html', **templateData)


if __name__ == "__main__":
   app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)