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
sk,29,06,22 Code für das Auslesen der Sensoren eingebaut
sk,01,07,22 Fehlerbehandlung verbessert, Sensor VTemp hinterlegt
sk,02,07,22 Sensor RTemp hinterlegt
sk,04,07,22 Sensor-Dict geändert
sk,04,07,22 Sensor-Dict und Variablen ausgelagert in config.cfg
sk,09,11,22 Umbau Program und cfg, Abfrage enFactory Sensoren
sk,09,11,22 Umbau Programm fast fertig
sk,11,11,22 Umbau Programm fertig, ungetestet
sk,11,11,22 timeout rtl_433
sk,11,11,22 Fertig, getestet
sk,11,11,22 rowcount

TODO:
timeout für rtl_433

'''

from cachetools import cached, TTLCache
from time import sleep
import os
import sys
import requests
import datetime
import time
import random
import subprocess
import signal
from bs4 import BeautifulSoup
import json
import sqlite3
encoding = 'utf-8'
CFG_FILE = 'config.cfg'
# MEASUREMENT_INTERVAL_SECONDS=60
# WEATHER_STATION_ACCESS_INTERVAL_SECONDS=60*15
# INVALID_TEMP_STR='-30.0'

if os.path.isfile(CFG_FILE):
    s = open(CFG_FILE, 'r').read()
    SENSORS = {}
    try:
        GLOBALS = eval(s)
        MEASUREMENT_INTERVAL_SECONDS = GLOBALS.get(
            'MEASUREMENT_INTERVAL_SECONDS')
        WEATHER_STATION_ACCESS_INTERVAL_SECONDS = GLOBALS.get(
            'WEATHER_STATION_ACCESS_INTERVAL_SECONDS')
        INVALID_TEMP_STR = GLOBALS.get('INVALID_TEMP_STR')
        DB_NAME = GLOBALS.get('DB_NAME')
        TABLE_NAME = GLOBALS.get('TABLE_NAME')
        VERBOSE = GLOBALS.get('VERBOSE')
        SENSORS = GLOBALS.get('SENSORS')
    except:
        print('error config file ' + CFG_FILE)


if (os.name == 'nt'):
    DB_FILENAME = DB_NAME
else:
    DB_FILENAME = '/var/lib/grafana/' + DB_NAME


BASE_URL = 'http://www.wetterwarte-sued.com/v_1_0/aktuelles/messwerte/messwerte_aktuell_ochsenhausenstadt.php'
WEATHER_STATIONS = ['weatherstation_29', 'weatherstation_69']


# {
# 'MEASUREMENT_INTERVAL_SECONDS': 60,
# 'WEATHER_STATION_ACCESS_INTERVAL_SECONDS' : 60*15,
# 'INVALID_TEMP_STR': '-30.0',
# 'DB_NAME': 'Temperaturen.db' ,
# 'TABLE_NAME': 'Temperaturen' ,
# 'VERBOSE': True,
#
# 	'SENSORS' : {
# 		'UTime': {
# 			'ID': None,
# 			'field_name': 'UnixTime',
# 			'descr': 'Zeitfeld'
# 		},
# 		'ATemp': {
# 			'ID': None,
# 			'field_name': 'AussenTemp',
# 			'descr': 'Aussentemperatur-Feld'
# 		},

# 		'VTemp': {
# 			'ID': '28-9283071e64ff',
# 			'field_name': 'VorlaufTemp',
# 			'descr': 'Vorlauftemperatur, hersteller= 28-ff-64-1e-07-83-92-c6'
# 			},
# 		'RTemp': {
# 			'ID': '28-01193cfd1606',
# 			'field_name': 'RuecklaufTemp',
# 			'descr': 'Ruecklauftemperatur, id='
# 		},
# 	},
# }


# https://github.com/Pyplate/rpi_temp_logger/blob/master/monitor.py
def get_DS18B20_data(sensor_dict):
    device_id = sensor_dict.get('ID')
    if not device_id:
        return float(INVALID_TEMP_STR)
    devicefile = '/sys/bus/w1/devices/' + device_id + '/w1_slave'
    try:
        fileobj = open(devicefile, 'r')
        lines = fileobj.readlines()
        fileobj.close()
    except:
        return float(INVALID_TEMP_STR)

    # get the status from the end of line 1
    try:
        status = lines[0][-4:-1]
    except:
        if VERBOSE:
            print('Error get lines')
        status = 'ERROR'

    # is the status is ok, get the temperature from line 2
    if status == "YES":
        try:
            tempstr = lines[1][-6:-1]
            tempvalue = float(tempstr)/1000
            return tempvalue
        except:
            if VERBOSE:
                print('Error convert float')
            return float(INVALID_TEMP_STR)
    else:
        if VERBOSE:
            print('status: ' + status)
        return float(INVALID_TEMP_STR)


def GET_UA():
    uastrings = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
                 "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",
                 "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
                 "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10",
                 "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
                 "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
                 "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36"
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
            float_temp = float(temp.replace(',', '.'))
            temp_arr.append(float_temp)
            if VERBOSE:
                print('Hole Temperatur von Station ' +
                      str(station_name) + ': ' + str(temp))
        except:
            float_temp = None
            if VERBOSE:
                print('Fehler bei Station ' + station_id)
    try:
        average_temp = round(sum(temp_arr)/no_of_stations, 2)
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


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    ps_command = subprocess.Popen(
        "ps -o pid --ppid %d --noheaders" % parent_pid, shell=True, stdout=subprocess.PIPE)
    ps_output = ps_command.stdout.read()
    retcode = ps_command.wait()
    # assert retcode == 0, "ps command returned %d" % retcode
    if retcode == 0:
        split_output = ps_output.decode().split("\n")
        for pid_str in split_output[:-1]:
            os.kill(int(pid_str), sig)


def compare_dict(probe_dict, in_dict):
    for key in probe_dict:
        if probe_dict.get(key) != in_dict.get(key):
            return False
    return True


def get_rtl_433_data(sensor_dict):
    query_dict = sensor_dict.get('query_dict')
    temperature = get_rtl_data(query_dict)
    if VERBOSE:
        print(sensor_dict.get('field_name') + ': ' + str(temperature))
    return temperature


def get_rtl_data(query_dict):
    try:
        start_time = datetime.datetime.now()
        sensor_types = GLOBALS.get('SENSOR_TYPES')
        sensor_rtl_433 = sensor_types.get('rtl_433')
        command_line = sensor_rtl_433.get('command_line')
        time_delay_ms = sensor_rtl_433.get('time_delay_ms')
        time_out_s = sensor_rtl_433.get('time_out_s')
    except AttributeError:
        print('command_line not defined in Sensor rtl_433')
        sys.exit(-1)

    if VERBOSE:
        print('Suche: ' + str(query_dict))
    proc = subprocess.Popen(
        command_line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    act_pid = proc.pid
    while True:
        now = datetime.datetime.now()
        duration = now - start_time
        duration_in_s = duration.total_seconds()
        if duration_in_s > time_out_s:
            if VERBOSE:
                print('Timeout erreicht: ' + str(time_out_s))
            time.sleep(2)
            kill_child_processes(act_pid, sig=signal.SIGTERM)
            return INVALID_TEMP_STR

        line = str(proc.stdout.readline(), encoding).strip()
        time.sleep(time_delay_ms/1000)
        if not 'model' in line:
            continue
        line_dict = json.loads(line)
        if compare_dict(query_dict, line_dict):
            if VERBOSE:
                print('gefunden: ' + str(query_dict.get('model')))
            time.sleep(5)
            kill_child_processes(act_pid, sig=signal.SIGTERM)
            temperature = line_dict.get('temperature_C')
            return temperature


def dict_sort_func(par):
    sensor = SENSORS.get(par)
    return sensor.get('index')


def get_sensor_names():
    # Nach index-Feld Sortierte Sensornamen
    f_names = []
    sorted_dict = sorted(SENSORS, key=dict_sort_func)
    for key in sorted_dict:
        sensor = SENSORS.get(key)
        if sensor.get('index') > 0:
            f_names.append(key)
    return tuple(f_names)


def get_field_names(sensor_names):
    # Nach index-Feld Sortierte Feldnamen
    field_names = []
    for sensor_name in sensor_names:
        field_names.append(SENSORS.get(sensor_name).get('field_name'))
    return tuple(field_names)

conn= ''
sensor_names = get_sensor_names()
field_names = get_field_names(sensor_names)
if not os.path.isfile(DB_FILENAME):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    create_string = 'create table ' + TABLE_NAME + str(field_names)
    cur.execute(create_string)
else:
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

i = 0
while True:
	sensors = GLOBALS.get('SENSORS')
	ret_code = 0
	temp_dict = {}
	temperature_list = []
	for sensor_name in sensor_names:
		sensor_dict = SENSORS.get(sensor_name)
		field_name = sensor_dict.get('field_name')
		sensor_type = sensor_dict.get('sensor_type')
		if sensor_type == 'UnixTime':
			now = datetime.datetime.now()
			unixtime = time.mktime(now.timetuple())
			temp_dict[field_name] = unixtime
			temperature_list.append(unixtime)

		if sensor_type == 'DS18B20':
			temp_dict[field_name] = get_DS18B20_data(sensor_dict)
			temperature_list.append(temp_dict[field_name])
		if sensor_type == 'rtl_433':
			temp_dict[field_name] = get_rtl_433_data(sensor_dict)
			temperature_list.append(temp_dict[field_name])

	if float(temp_dict['AussenTemp']) > -50:
		temperature_tuple = (temperature_list)
		if VERBOSE:
			print('AussenTemperatur: ' + str(temp_dict['AussenTemp']))
		with conn:
			if VERBOSE:
				print('(' + str(i) + ') Speichere Temperaturen: ' + str(temperature_tuple))
			sql = "INSERT INTO " + TABLE_NAME + str(field_names) + " VALUES (" + ",".join(["?"]*len(temperature_tuple)) + ")"
			result = cur.execute(sql, temperature_tuple)
			if VERBOSE: print('Rows inserted: ' + str(result.rowcount))
	else:
		now = datetime.datetime.now()
		unixtime = time.mktime(now.timetuple())
		print(str(unixtime) + ': Es konnte keine Temperatur ermittelt werden!')
	if VERBOSE:
		print('Warte ' + str(MEASUREMENT_INTERVAL_SECONDS) + 's ...')

	sleep(MEASUREMENT_INTERVAL_SECONDS)
	i = i + 1
conn.close()
if VERBOSE:
    print('Feddisch')
