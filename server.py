import logging
import selectors
import socket
import sys
import os
import platform
from datetime import datetime

HOST, PORT = '', 8000  # Порт сервера

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

def new_connection(selector: selectors.BaseSelector, sock: socket.socket):
    new_conn, address = sock.accept()
    logger.info('accepted new_conn from %s', address)
    new_conn.setblocking(False)

    selector.register(new_conn, selectors.EVENT_READ, read_callback)

def read_callback(selector: selectors.BaseSelector, sock: socket.socket):
    data = sock.recv(1024)
    if data:
        command = data.decode()
        response = handle_command(command)
        sock.send(response.encode())
    else:
        logger.info('closing connection %s', sock)
        selector.unregister(sock)
        sock.close()

def handle_command(command):
    if command == "quit":
        return "Соединение закрыто"
    elif command == "time":
        return f"Текущее время в UTC: {datetime.utcnow()}"
    elif command == "info":
        system_info = f"Система: {platform.system()}, Версия интерпретатора: {platform.python_version()}"
        return system_info
    elif command.startswith("find"):
        _, file_name, path = command.split()
        try:
            file_path = os.path.join(path, file_name)
            stat_info = os.stat(file_path)
            return f"Файл: {file_name}, Дата создания: {datetime.utcfromtimestamp(stat_info.st_ctime)}, Размер: {stat_info.st_size} байт"
        except FileNotFoundError:
            return "Файл не найден"
    else:
        return "Неизвестная команда"

def run_iteration(selector: selectors.BaseSelector):
    events = selector.select()
    for key, mask in events:
        callback = key.data
        callback(selector, key.fileobj)

def serve_forever():
    """
    Метод запускает сервер на постоянное прослушивание новых сообщений
    """
    with selectors.SelectSelector() as selector:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            server_socket.bind((HOST, PORT))
            server_socket.listen()
            server_socket.setblocking(False)
            logger.info('Server started on port %s', PORT)

            selector.register(server_socket, selectors.EVENT_READ, new_connection)

            while True:
                run_iteration(selector)

if __name__ == '__main__':
    serve_forever()
