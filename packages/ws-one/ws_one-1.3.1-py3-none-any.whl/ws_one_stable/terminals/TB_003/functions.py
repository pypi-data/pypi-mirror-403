""" Функции для терминала CAS"""
from ws_one_stable import settings as s
import re

def get_parsed_input_data(data):
    try:
        data = data.decode()
        pars = re.findall(r'\d+', data)
        if pars:
            weight = pars[0]
            weight_aliq = make_data_aliquot(weight)
            return weight_aliq
    except:
        return s.fail_parse_code

def make_data_aliquot(data, value=10):
    # Сделать вес кратным value
    data = int(data)
    data = data - (data % value)
    return data

def check_scale_disconnected(data):
    # Провреят, отправлен ли бит, означающий отключение Терминала
    return 0

