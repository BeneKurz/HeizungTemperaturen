# Ermitteln der Heizungstemperaturen und der Aussentemperatur
# Ausgabe an sqlite3
from multiprocessing.connection import wait
from time import sleep
import requests, os, datetime, time
from bs4 import BeautifulSoup
import sqlite3
MEASUREMENT_INTERVAL=20
DB_NAME='Temperaturen.db'
TABLE_NAME='Temperaturen'



OX_Stadt='http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php'

station_dict= {
	'OX_Stadt' : ['http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php','weatherstation_69'],
	'Erlenmoos' : ['http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_erlenmoos.php', 'weatherstation_29']
}

def get_temp_from_site(station_entry):
	site = station_entry[0]
	station_id = station_entry[1]
	temperaturecurrent = None
	station_name = None
	r = requests.get(site)
	soup = BeautifulSoup(r.text, 'html.parser')
	links = soup.findAll('tr', id=station_id)

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
	# cur.execute('create table ' + TABLE_NAME + '(UnixTime integer, ts timestamp, ATemp)')
	cur.execute('create table ' + TABLE_NAME + '(UnixTime integer, ATemp, VTemp, RTemp)')
else:
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

i = 0 
while i < 20:
	no_of_stations = len(station_dict.keys())
	print(str(no_of_stations))
	temp_arr = []
	for key in station_dict.keys():
		temp, station_name = get_temp_from_site(station_dict.get(key))
		float_temp = float(temp.replace(',','.'))
		temp_arr.append(float_temp)
		print('Die Temperatur der Station ' + station_name + ' ist: ' + temp)

	now = datetime.datetime.now()
	unixtime = time.mktime(now.timetuple())
	
	ATemp = round(sum(temp_arr)/no_of_stations,5)
	VTemp = float(ATemp + 30.0)
	RTemp = float(ATemp + 25.0)

	print('Mittelwert: ' + str(ATemp))
	with conn:
		cur.execute('insert into ' + TABLE_NAME + '(UnixTime, ATemp, VTemp, RTemp) values (?, ?, ?, ?)', (unixtime, ATemp, VTemp, RTemp))
		#conn.commit()
	sleep(MEASUREMENT_INTERVAL)
	i = i + 1
conn.close()
print('Feddisch')


