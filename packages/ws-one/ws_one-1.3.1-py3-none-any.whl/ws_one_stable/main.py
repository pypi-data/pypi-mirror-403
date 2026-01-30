from ws_one_stable.pds_one.main import PortDataSplitter
from ws_one_stable import support_functions as sup_func
from traceback import format_exc
import ws_one_stable.settings as s


class WeightSplitter(PortDataSplitter):
    def __init__(self, ip, port, sql_shell=None, port_name='/dev/ttyUSB0',
                 terminal_name='CAS', debug=False, scale_protocol=None,
                 logger=None, baudrate=9600, emulate=False, web_port=8003,
                 **kwargs):
        super().__init__(ip, port, port_name, device_name=terminal_name,
                         debug=debug, scale_protocol=scale_protocol,
                         baudrate=baudrate, emulate=emulate, **kwargs)
        self.terminal_name = terminal_name
        self.terminal_funcs = sup_func.extract_terminal_func(
            self.terminal_name)
        self.start_weight = 0
        self.logger = logger
        self.round_info = {}
        self.web_port = web_port
        self.sql_shell = sql_shell

    def block_auto_null(self):
        pass

    def make_new_record(self, car_number, carrier, record_id):
        self.round_info['car_number'] = car_number
        self.round_info['carrier'] = carrier
        self.round_info['record_id'] = record_id

    def make_final_record(self, weight, *args, **kwargs):
        self.round_info['weight'] = weight

    def turn_off_logging(self):
        pass

    def make_log(self, message, level='error'):
        if self.logger and level == 'critical':
            self.logger.critical(message)
        if self.logger and level == 'error':
            self.logger.error(message)

    def set_stable_wight(self, start_weight):
        self.start_weight = start_weight

    def upd_stable_weight(self, new_weight):
        self.start_weight += new_weight
        self.start_weight = self.make_data_aliquot(self.start_weight)

    def make_data_aliquot(self, data, value=10):
        # Сделать вес кратным value
        try:
            data = int(data)
            data = data - (data % value)
        except:
            self.show_print(format_exc())
        return data

    def stable_weight(self, data):
        try:
            data = int(data)
            data -= self.start_weight
            return data
        except:
            print(format_exc())
            return data

    def check_data(self, data):
        # Проверить данные, вызывал функцию этого терминала
        if self.terminal_funcs.check_scale_disconnected(data):
            data = s.scale_disconnected_code
        else:
            data = self.terminal_funcs.get_parsed_input_data(data)
            data = self.stable_weight(data)
        return data

    def send_data(self, data, **kwargs):
        # Отправить данные
        data = self.auto_stabilization(data)
        data = str(data)
        try:
            data = bytes(data, encoding='utf-8')
            self.show_print('Sending:', data, debug=True)
            super().send_data(data, **kwargs)
        except TypeError:
            self.show_print("Reconnecting...", debug=True)
            self.make_log(message='Отключение весового терминала',
                          level='critical')
            self.reconnect_logic()

    def auto_stabilization(self, data):
        """ Сделать автоматическую стабилизацию
        (если околонулевые значения - возвращать ноль)"""
        try:
            data_int = int(data)
            if data_int == 0:
                return data
            if ((data_int < 0 and not data_int < -50) or
                    (data_int > 0 and not data_int > 50)):
                #self.logger.info(
                 #   f"Произведена стабилизация весов на 0. ({data})")
                return 0
            else:
                return data
        except:
            self.logger.error(f"Ошибка стабилизации весов! ({data})")
            return data
