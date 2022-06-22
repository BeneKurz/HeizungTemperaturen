# Ermitteln der Heizungstemperaturen und der Aussentemperatur
# Ausgabe an sqlite3
from multiprocessing.connection import wait
from time import sleep
import requests, os, datetime
from bs4 import BeautifulSoup
import sqlite3
MEASUREMENT_INTERVAL=10
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
	cur.execute('create table ' + TABLE_NAME + '(d date, ts timestamp, ATemp)')
else:
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

i = 0 
while i < 100:
	no_of_stations = len(station_dict.keys())
	print(str(no_of_stations))
	temp_arr = []
	for key in station_dict.keys():
		temp, station_name = get_temp_from_site(station_dict.get(key))
		float_temp = float(temp.replace(',','.'))
		temp_arr.append(float_temp)
		print('Die Temperatur der Station ' + station_name + ' ist: ' + temp)

	today = datetime.date.today()
	now = datetime.datetime.now()
	mittelwert = round(sum(temp_arr)/no_of_stations,5)
	print('Mittelwert: ' + str(mittelwert))
	with conn:
		cur.execute('insert into ' + TABLE_NAME + '(d, ts, ATemp) values (?, ?, ?)', (today, now, mittelwert))
		#conn.commit()
	sleep(MEASUREMENT_INTERVAL)
	i = i + 1
conn.close()
print('Feddisch')


