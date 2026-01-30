""" Функции для терминала CAS"""
from ws_one_stable import settings as s


def get_parsed_input_data(data):
    try:
        data = data.decode()
        data = str(data)
        data = data[:-5]
        data = data.replace('+', '')
        if data.isdigit():
            return data
        else:
            return s.fail_parse_code
    except:
        return s.fail_parse_code



def check_scale_disconnected(data):
    # Провреят, отправлен ли бит, означающий отключение Терминала
    return 0
