import json
import mimetypes
import pathlib
import socket
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

BASE_DIR = pathlib.Path()
UDP_IP = "127.0.0.1"
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_response_html("index.html")
        elif pr_url.path == "/message.html":
            self.send_response_html("message.html")
        else:
            file = BASE_DIR.joinpath(pr_url.path[1:])
            if file.exists():
                self.send_static(file)
            else:
                self.send_response_html("error.html", 404)

    def send_response_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename):
        self.send_response(200)
        mt = mimetypes.guess_type(filename)
        if mt[0]:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        form_data = self.rfile.read(content_length)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = UDP_IP, UDP_PORT
        server_socket.sendto(form_data, server)
        server_socket.close()

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    try:
        while True:
            data, address = sock.recvfrom(1024)
            save_data(data)

    except KeyboardInterrupt:
        print(f"Destroy server")
    finally:
        sock.close()


def save_data(form_data):
    form_data = urllib.parse.unquote_plus(form_data.decode())
    payload = {
        key: value for key, value in [el.split("=") for el in form_data.split("&")]
    }
    data_dict = {datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"): payload}

    data_file_path = "storage/data.json"

    try:
        with open(data_file_path, "r", encoding="utf-8") as existing_fd:
            existing_data = json.load(existing_fd)
    except FileNotFoundError:
        existing_data = {}

    existing_data.update(data_dict)

    with open(data_file_path, "w", encoding="utf-8") as fd:
        json.dump(existing_data, fd, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    Thread(target=run).start()
    Thread(target=run_server).start()
