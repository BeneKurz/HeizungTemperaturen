
def dict_sort_func(par, the_sensors):
    sensor = the_sensors.get(par)
    return sensor.get('index')

def get_sensor_names(sensor_dict):
    # Nach index-Feld Sortierte Sensornamen
    f_names = []
    sorted_dict = sorted(sensor_dict, key=lambda key: dict_sort_func(key, sensor_dict))
    for key in sorted_dict:
        sensor = sensor_dict.get(key)
        if sensor.get('index') > 0:
            f_names.append(key)
    return tuple(f_names)


def get_field_names(sensor_dict, sensor_names):
    # Nach index-Feld Sortierte Feldnamen
    field_names = []
    for sensor_name in sensor_names:
        field_names.append(sensor_dict.get(sensor_name).get('field_name'))
    return tuple(field_names)

