# -*- coding: ISO-8859-1 -*-
'''
sk,21,06,22 Ermitteln der Heizungstemperaturen und der Aussentemperatur
sk,22,06,22 Ausgabe an sqlite3
sk,22,06,22 Aussentemperatur unabhängig von den anderen Temps laden. OK
sk,22,06,22 Anzahl der Zugriffe auf Webseite reduziert
sk,23,06,22 Cache beim Zugriff auf die Webseite eingebaut
sk,23,06,22 Gültige User-Agents übermitteln
sk,28,06,22 Absturz bei fehlender Temperatur behoben, weatherstation_9 dazugenommen
sk,28,06,22 Verbesserungen
sk,29,06,22 Fehlerbehandlung verbessert
sk,29,06,22 Code für das Auelsen der Sensoren eingebaut
sk,01,07,22 Fehlerbehandlung verbessert, Sensor VTemp hinterlegt
sk,02,07,22 Sensor RTemp hinterlegt

TODO:





'''

from cachetools import cached, TTLCache
from time import sleep
import requests, os, datetime, time, random
from bs4 import BeautifulSoup
import sqlite3
MEASUREMENT_INTERVAL_SECONDS=60
WEATHER_STATION_ACCESS_INTERVAL_SECONDS=60*15
INVALID_TEMP_STR='-273.0'
INVALID_TEMP_STR='-30.0'


if (os.name == 'nt'):                                            
    DB_NAME='Temperaturen.db'
else:                                                            
	DB_NAME='/var/lib/grafana/Temperaturen.db'
TABLE_NAME='Temperaturen'
VERBOSE=True

BASE_URL='http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php'
WEATHER_STATIONS=['weatherstation_29','weatherstation_69']

SENSORS={
	'VTemp': '28-9283071e64ff',
	'RTemp': '28-01193cfd1606',
	'XTemp': 'ID3'
}

# https://github.com/Pyplate/rpi_temp_logger/blob/master/monitor.py
def get_sensor_temp(temperature_key):
	device_id=SENSORS.get(temperature_key)
	devicefile='/sys/bus/w1/devices/' + device_id + '/w1_slave'
	try:
		fileobj = open(devicefile,'r')
		lines = fileobj.readlines()
		fileobj.close()
	except:
		return float(INVALID_TEMP_STR)

	# get the status from the end of line 1 
	try:
		status = lines[0][-4:-1]
	except:
		status = 'ERROR'

	# is the status is ok, get the temperature from line 2
	if status=="YES":
		#print(status)
		try:
			tempstr= lines[1][-6:-1]
			tempvalue=float(tempstr)/1000
			return tempvalue
		except:
			return float(INVALID_TEMP_STR)
	else:
		#print("There was an error.")
		return float(INVALID_TEMP_STR)

	

def GET_UA():
    uastrings = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",\
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",\
                "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36"\
                ]
    return random.choice(uastrings)


def get_info_from_station(soup, station_id):
	links = soup.findAll('tr', id=station_id)
	station_name = ''
	temperaturecurrent = INVALID_TEMP_STR
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
		try:
			float_temp = float(temp.replace(',','.'))
			temp_arr.append(float_temp)
			if VERBOSE: 
				print('Hole Temperatur von Station ' + station_name + ': ' + temp)	
		except:
			float_temp= None
			if VERBOSE: 
				print('Fehler bei Station ' + station_id)	
	try:
		average_temp = round(sum(temp_arr)/no_of_stations,2)
	except:
		average_temp = None
	return average_temp

@cached(cache=TTLCache(maxsize=1024, ttl=WEATHER_STATION_ACCESS_INTERVAL_SECONDS))
def get_aussen_temperatur(BASE_URL):
	headers = {'User-Agent': GET_UA()}
	r = requests.get(BASE_URL, headers=headers)
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
	if ATemp:
		#TODO
		VTemp = get_sensor_temp('VTemp')
		RTemp = get_sensor_temp('RTemp')

		if VERBOSE: 
			print('Mittelwert: ' + str(ATemp))
		with conn:
			now = datetime.datetime.now()
			unixtime = time.mktime(now.timetuple())	
			temperature_tuple = (unixtime, ATemp, VTemp, RTemp)
			if VERBOSE:
				print('(' + str(i) + ') Speichere Temperaturen: ' + str(temperature_tuple))		
			cur.execute('insert into ' + TABLE_NAME + '(UnixTime, ATemp, VTemp, RTemp) values (?, ?, ?, ?)', temperature_tuple)
	else:
		now = datetime.datetime.now()
		unixtime = time.mktime(now.timetuple())	
		print(str(unixtime) + ': Es konnte keine Temperatur ermittelt werden!')
	sleep(MEASUREMENT_INTERVAL_SECONDS)
	i = i + 1
conn.close()
if VERBOSE: 
	print('Feddisch')
