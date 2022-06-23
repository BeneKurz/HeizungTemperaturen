# -*- coding: ISO-8859-1 -*-
'''
sk,21,06,22 Ermitteln der Heizungstemperaturen und der Aussentemperatur
sk,22,06,22 Ausgabe an sqlite3
sk,22,06,22 Anzahl der Zugriffe auf Webseite reduziert
sk,23,06,22 Cache beim Zugriff auf die Webseite eingebaut

TODO:
- Aussentemperatur unabhängig von den anderen Temps laden
- Heizungstemperaturen mit Sensoren auslesen

'''

from multiprocessing.connection import wait
from cachetools import cached, TTLCache
from time import sleep
import requests, os, datetime, time
from bs4 import BeautifulSoup
import sqlite3
MEASUREMENT_INTERVAL_SECONDS=6
WEATHER_STATION_ACCESS_INTERVAL_SECONDS=60*15
DB_NAME='Temperaturen.db'
TABLE_NAME='Temperaturen'
VERBOSE=True

BASE_URL='http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php'
WEATHER_STATIONS=['weatherstation_29','weatherstation_69']

def get_info_from_station(soup, station_id):
	links = soup.findAll('tr', id=station_id)
	station_name = ''
	temperaturecurrent = -273
	for link in links:
		table_data = link.find_all('td')	
		for table_entry in table_data:
			str_table_entry = str(table_entry)
			if 'temperaturecurrent positive' in str_table_entry:
				temperaturecurrent = table_entry.text
			if 'name' in str_table_entry:
				station_name = table_entry.text
	return temperaturecurrent, station_name


def do_get_aussen_temperatur(soup):
	temp_arr = []
	no_of_stations = len(WEATHER_STATIONS)
	for station_id in WEATHER_STATIONS:
		temp, station_name = get_info_from_station(soup, station_id)
		float_temp = float(temp.replace(',','.'))
		temp_arr.append(float_temp)
		if VERBOSE: 
			print('Hole Temperatur von Station ' + station_name + ': ' + temp)		
	return round(sum(temp_arr)/no_of_stations,5)

@cached(cache=TTLCache(maxsize=1024, ttl=WEATHER_STATION_ACCESS_INTERVAL_SECONDS))
def get_aussen_temperatur(BASE_URL):
	r = requests.get(BASE_URL)
	soup = BeautifulSoup(r.text, 'html.parser')
	AussenTemp = do_get_aussen_temperatur(soup)
	return AussenTemp



if not os.path.isfile(DB_NAME):
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()
	cur.execute('create table ' + TABLE_NAME + '(UnixTime integer, ATemp, VTemp, RTemp)')
else:
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

i = 0 
while True:
	ATemp = get_aussen_temperatur(BASE_URL)

	#TODO
	VTemp = float(ATemp + 30.0)
	RTemp = float(ATemp + 25.0)

	if VERBOSE: 
		print('Mittelwert: ' + str(ATemp))
	with conn:
		now = datetime.datetime.now()
		unixtime = time.mktime(now.timetuple())	
		temperature_tuple = (unixtime, ATemp, VTemp, RTemp)
		print('(' + str(i) + ') Speichere Temperaturen: ' + str(temperature_tuple))		
		cur.execute('insert into ' + TABLE_NAME + '(UnixTime, ATemp, VTemp, RTemp) values (?, ?, ?, ?)', temperature_tuple)
	sleep(MEASUREMENT_INTERVAL_SECONDS)
	i = i + 1
conn.close()
if VERBOSE: 
	print('Feddisch')