""" Функции для терминала CAS"""
from ws_one_stable import settings as s

def get_parsed_input_data(data):
    try:
        res_hex = data.hex()
        w_int = res_hex[1:12:2][::-1]
        return w_int
    except:
        return s.fail_parse_code

def check_scale_disconnected(data):
    # Провреят, отправлен ли бит, означающий отключение Терминала
    return 0
