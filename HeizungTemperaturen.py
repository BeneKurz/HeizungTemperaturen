# Ermitteln der Heizungstemperaturen und der Aussentemperatur
# sk,22,06,22 Ausgabe an sqlite3
# sk,22,06,22 Anzahl derZugriffe auf Webseite reduziert

from multiprocessing.connection import wait
from time import sleep
import requests, os, datetime, time
from bs4 import BeautifulSoup
import sqlite3
MEASUREMENT_INTERVAL=10
DB_NAME='Temperaturen.db'
TABLE_NAME='Temperaturen'
VERBOSE=False

BASE_URL='http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php'
WEATHER_STATIONS=['weatherstation_29','weatherstation_69']

def get_info_from_station(soup, station_id):

	links = soup.findAll('tr', id=station_id)
	station_name = ''
	temperaturecurrent = -200
	for link in links:
		table_data = link.find_all('td')	
		for table_entry in table_data:
			str_table_entry = str(table_entry)
			if 'temperaturecurrent positive' in str_table_entry:
				temperaturecurrent = table_entry.text
			
				#return temperaturecurrent
			if 'name' in str_table_entry:
				station_name = table_entry.text
	return temperaturecurrent, station_name

if not os.path.isfile(DB_NAME):
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()
	cur.execute('create table ' + TABLE_NAME + '(UnixTime integer, ATemp, VTemp, RTemp)')
else:
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

i = 0 
while i < 20:
	r = requests.get(BASE_URL)
	soup = BeautifulSoup(r.text, 'html.parser')
	temp_arr = []
	no_of_stations = len(WEATHER_STATIONS)
	for station_id in WEATHER_STATIONS:
		temp, station_name = get_info_from_station(soup, station_id)
		float_temp = float(temp.replace(',','.'))
		temp_arr.append(float_temp)
		if VERBOSE: 
			print('Die Temperatur der Station ' + station_name + ' ist: ' + temp)

	now = datetime.datetime.now()
	unixtime = time.mktime(now.timetuple())
	
	ATemp = round(sum(temp_arr)/no_of_stations,5)
	#TODO
	VTemp = float(ATemp + 30.0)
	RTemp = float(ATemp + 25.0)

	if VERBOSE: 
		print('Mittelwert: ' + str(ATemp))
	with conn:
		cur.execute('insert into ' + TABLE_NAME + '(UnixTime, ATemp, VTemp, RTemp) values (?, ?, ?, ?)', (unixtime, ATemp, VTemp, RTemp))
	sleep(MEASUREMENT_INTERVAL)
	i = i + 1
conn.close()
if VERBOSE: 
	print('Feddisch')