import socket
import threading
import time
from serial import Serial
import serial.tools.list_ports
from time import sleep
from . import settings as s
from . import functions
from traceback import format_exc


class PortDataSplitter:
    """ Сервер для прослушивания порта port_name (USB, COM),
     и переотправки данных подключенным к нему клиентам (Clients)."""

    def __init__(self, ip, port, port_name='/dev/ttyUSB0', debug=False,
                 device_name='unknown', scale_protocol=None, baudrate=9600,
                 emulate=False, **kwargs):
        self.device_name = device_name
        self.scale_protocol = scale_protocol
        self.debug = debug
        self.port_name = port_name
        self.subscribers = []
        self.data_list = [s.no_data_code]
        self.server_ip = ip
        self.server_port = port
        self.test_mode = False
        self.baudrate = baudrate
        self.emulate = emulate


    def get_all_connected_devices(self):
        # Показать все подключенные к этому компьютеру устройства
        ports = serial.tools.list_ports.comports()
        self.show_print('\nAll connected devices:')
        for port in ports:
            self.show_print('\t', port)
        return ports

    def get_device_name(self):
        # Вернуть заданный этому устройству имя
        return self.device_name

    def set_emulate_data(self, data):
        self.data_list.append(data)

    def start(self):
        """ Запустить работу PortDataSplitter"""
        # Создать сервер рассылки
        self.create_server(self.server_ip, self.server_port)
        # Запустить параллельный поток, который будет принимать клиентов
        threading.Thread(target=self.connection_reciever_loop, args=()).start()
        # Запустить параллельный поток, который отправляет данные из self.data_list
        # Запустить основной поток, слушаюший заданный порт и отправляющий эти данные клиентам
        if self.emulate:
            self.data_list.append(self.emulate)
            threading.Thread(target=self.sending_thread, args=(0.3,)).start()
            return
        while True:
            try:
                if self.scale_protocol == 'belo':
                    self.beloretsk_mainloop()
                else:
                    self._mainloop()
            except:
                print(format_exc())
                sleep(5)

    def sending_thread(self, timing=1):
        # Поток отправки показаний весов
        while True:
            sleep(timing)
            self.send_data(self.data_list[-1])

    def create_server(self, ip, port):
        """ Создать сервер"""
        self.show_print('Creating {} server'.format(self.device_name))
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind((ip, port))
        self.serv.listen(10)

    def connection_reciever_loop(self):
        # Отдельный поток, принимающий подключения и добавляющий их в список self.subscribers для дальнейшней
        # работы
        while True:
            self.show_print('\nWaiting for client...')
            conn, addr = self.serv.accept()
            self.subscribers.append(conn)
            self.show_print('\tGot new client! From IP:',
                            conn.getpeername()[0])

    def set_splitter(self, data, splitter="X0"):
        return f"{data}{splitter}"

    def send_data(self, data, *args, **kwargs):
        # Отправить данные по клиентам
        data_frmt = data.decode()
        data_frmt = self.set_splitter(data_frmt)
        data_frmt = data_frmt.encode()
        for conn in self.subscribers:
            try:
                conn.send(data_frmt)
            except:
                # Если данные отправить клиенту не удалось, удалить клиента из списка подписчиков
                self.show_print('\tFailed to send data to client', conn)
                self.show_print(format_exc())
                self.subscribers.remove(conn)

    def make_str_tuple(self, msg):
        # Перед отправкой данных в стандартный поток вывывода форматировать
        return ' '.join(map(str, msg))

    def show_print(self, *msg, debug=False):
        # Отправка данных в стандартный поток выводы
        msg = self.make_str_tuple(msg)
        if debug and self.debug:
            print(msg)
        elif not debug:
            print(msg)

    def _mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        self.show_print('\nЗапущен основной цикл отправки весов')
        # Нужно подождать около 5 секунд после запуска всего компа
        sleep(5)
        self.port = Serial(self.port_name, bytesize=8, parity='N', stopbits=1,
                           timeout=1, baudrate=self.baudrate)
        if self.scale_protocol == '6.43':
            self.connection_operation(self.port)
        while True:
            try:
                if self.scale_protocol == 'art':
                    data = self.port.read_until(expected=b'\rG')
                elif self.scale_protocol == 'monolit':
                    data = self.port.read_until(expected=b'\x03\x02')
                elif self.scale_protocol == "6.43 without connection":
                    self.port.write([16])
                    data = self.port.read_until(b"=")
                    time.sleep(0.1)
                elif self.scale_protocol == 'uzvo':
                    data = self.port.read_until(expected=b"\x03\x02")
                else:
                    if self.scale_protocol == '6.43':
                        self.port.write([16])
                    if self.scale_protocol == "middle":
                        self.port.write(bytes.fromhex("0A"))
                    data = self.port.readline()
            except serial.serialutil.SerialException:
                data = s.scale_disconnected_code
                print(format_exc())
            self.show_print('Data from port:', data, debug=True)
            if data:
                # Если есть данные проверить их и добавить в список отправки data_list
                data = self.check_data(data)
                #self.prepare_data_to_send(data)
                self.send_data(data)
            else:
                self.reconnect_logic()

    def beloretsk_mainloop(self):
        # Основной цикл работы программы, слушает порт и передает данные клиентам
        self.show_print('\n\n\nЗапущен основной цикл отправки весов')
        # Нужно подождать около 5 секунд после запуска всего компа
        # sleep(5)
        if not self.test_mode:
            self.port = Serial(self.port_name, 9600)
            self.port.bytesize = serial.EIGHTBITS  # number of bits per bytes
            self.port.parity = serial.PARITY_NONE  # set parity check: no parity
            self.port.stopbits = serial.STOPBITS_ONE  # number of stop bits
            self.port.timeout = None  # block read
            self.port.timeout = 2  # timeout block read
            self.port.xonxoff = False  # disable software flow control
            self.port.rtscts = False  # disable hardware (RTS/CTS) flow control
            self.port.dsrdtr = False  # disable hardware (DSR/DTR) flow control
            self.port.writeTimeout = 0  # timeout for write
            self.port.close()
            self.port.open()
            sleep(0.5)
            sleep(0.5)
        while True:
            # if self.port.isOpen():
            if True:
                if not self.test_mode:
                    data = functions.get_data_from_port(self.port)
                    #print('\nDATA:', data)
                    self.port.write(b'\x10')
                else:
                    data = self.test_value
                    sleep(1)
                self.show_print('Data from port:', data, debug=True)
                if data:
                    # Если есть данные проверить их и добавить в список отправки data_list
                    data = self.check_data(data)
                    #print('\nRESULT CHECK:', data)
                    #self.prepare_data_to_send(data)
                    self.send_data(data)
                else:
                    print('No data')
                    pass

    def connection_operation(self, port):
        bufer = [0x2, 0x1, 0x30, 0x30, 0x30, 0x31]
        # инициализация
        while (len(port.read_all()) == 0):
            port.write(bufer)
            sleep(1)
            print("*")

    def check_data(self, data):
        self.show_print('Checking data in {}'.format(self.device_name),
                        debug=True)
        return data

    def prepare_data_to_send(self, data):
        # Подготовить данные перед отправкой
        self.data_list = self.data_list[-15:]
        self.data_list.append(data)

    def reconnect_logic(self):
        # Логика, реализуемая при выключении терминала
        self.show_print('Терминал выключен!')
        self.port.close()
        self._mainloop()

