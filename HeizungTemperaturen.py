# Ermitteln der Heizungstemperaturen und der Aussentemperatur
import requests
from bs4 import BeautifulSoup

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



for key in station_dict.keys():
	temp, station_name = get_temp_from_site(station_dict.get(key))
	print('Die Temperatur der Station ' + station_name + ' ist: ' + temp)
print('Feddisch')


