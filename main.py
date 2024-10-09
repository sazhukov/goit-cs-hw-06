from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process
import mimetypes
import json
import urllib.parse
import pathlib
import socket
import logging
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

# MongoDB URI
uri = "mongodb://mongodb_service:27017"

# HTTP Server Port and UDP Socket Info
HTTPServer_Port = 3000
UDP_IP = '127.0.0.1'
UDP_PORT = 5000

# Веб-сервер для обробки запитів
class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.send_data_to_socket(post_data)
            self.send_response(302)
            self.send_header('Location', '/')  # Після надсилання форми перенаправлення на головну сторінку
            self.end_headers()
        else:
            self.send_error(404, "Page Not Found")

    def do_GET(self):
        # Маршрутизація для сторінок
        if self.path == '/':
            self.send_html_file('index.html')
        elif self.path == '/message.html':
            self.send_html_file('message.html')
        elif self.path == '/style.css':
            self.send_static('style.css')
        elif self.path == '/logo.png':
            self.send_static('logo.png')
        else:
            self.send_error(404, "Page Not Found")

    # Метод для відправки HTML-файлів
    def send_html_file(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        file_path = pathlib.Path("front-init") / filename  # Змінено на правильний шлях до файлів
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.wfile.write(file.read().encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "File not found")

    # Метод для відправки статичних файлів (CSS, зображення)
    def send_static(self, filename):
        self.send_response(200)
        mime_type, _ = mimetypes.guess_type(filename)
        self.send_header('Content-type', mime_type)
        self.end_headers()
        with open(pathlib.Path("front-init") / filename, 'rb') as file:
            self.wfile.write(file.read())

    # Метод для відправки даних через сокет
    def send_data_to_socket(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = (UDP_IP, UDP_PORT)
        sock.sendto(data, server)

# HTTP сервер
def run_http_server(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('0.0.0.0', HTTPServer_Port)
    http = server_class(server_address, handler_class)
    logging.info(f"Starting HTTP server on port {HTTPServer_Port}...")
    http.serve_forever()

# Функція для збереження даних у MongoDB
def save_data(data):
    client = MongoClient(uri, server_api=ServerApi("1"))
    db = client.messages_db
    data_parse = urllib.parse.unquote_plus(data.decode())
    params = urllib.parse.parse_qs(data_parse)
    message_data = {
        "date": str(datetime.now()),
        "username": params['username'][0],
        "message": params['message'][0]
    }
    db.messages.insert_one(message_data)

# Сокет сервер
def run_socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = (ip, port)
    sock.bind(server)
    logging.info(f"Starting socket server on {ip}:{port}...")
    while True:
        data, addr = sock.recvfrom(1024)
        save_data(data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')

    # Запуск HTTP і Socket серверів у різних процесах
    http_server_process = Process(target=run_http_server)
    http_server_process.start()

    socket_server_process = Process(target=run_socket_server, args=(UDP_IP, UDP_PORT))
    socket_server_process.start()
