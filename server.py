
import socket
import os
import threading
import datetime
import tarfile
import glob
import tarfile
import io
import time


def get_file_info(file_path):
    file_size = os.path.getsize(file_path)
    file_ctime = os.path.getctime(file_path)
    file_date = time.strftime('%Y-%m-%d', time.gmtime(file_ctime))
    return f"{file_path}, {file_size} bytes, {file_date}"
def create_and_send_tar(conn, files_list, args):
    if not files_list:
        conn.sendall(b"No file found")
        return

    with io.BytesIO() as tar_buffer:
        with tarfile.open(fileobj=tar_buffer, mode='') as tar:
            for file_path in files_list:
                tar.add(file_path, arcname=os.path.relpath(file_path, os.getcwd()))

        tar_data = tar_buffer.getvalue()
        tar_size = len(tar_data)
        conn.sendall(f"{tar_size}\n".encode() + tar_data)

        if '-u' in args:
            conn.recv(1024)  # Wait for client to finish unpacking


def find_file(filename, root):
    for root, dirs, files in os.walk(root):
        if filename in files:
            return os.path.join(root, filename)
    return None

def send_file(s, file_path):
    file_size = os.path.getsize(file_path)
    s.sendall(f"{file_size}\n".encode())

    with open(file_path, "rb") as f:
        while (data := f.read(1024)):
            s.sendall(data)
def get_files_by_size(size1, size2, root):
    files_list = []
    for root, dirs, files in os.walk(root):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if size1 <= file_size <= size2:
                files_list.append(file_path)
    return files_list
def get_files_by_date(date1, date2, root):
    files_list = []
    for root, dirs, files in os.walk(root):
        for file in files:
            file_path = os.path.join(root, file)
            file_ctime = os.path.getctime(file_path)
            file_date = datetime.datetime.fromtimestamp(file_ctime).date()
            if date1 <= file_date <= date2:
                files_list.append(file_path)
    return files_list
def get_files_by_names(filenames, root):
    files_list = []
    for filename in filenames:
        file_path = find_file(filename, root)
        if file_path:
            files_list.append(file_path)
    return files_list
def get_files_by_extensions(extensions, root):
    files_list = []
    for root, dirs, files in os.walk(root):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[-1].strip('.').lower()
            if file_extension in extensions:
                files_list.append(file_path)
    return files_list

shared_counter_lock = threading.Lock()
shared_counter = 0
def send_response(conn, response):
    if isinstance(response, bytes):
        conn.sendall(b"BINARY_RESPONSE")
        conn.sendall(f"{len(response):010}".encode())
        conn.sendall(response)
    else:
        conn.sendall(response.encode())
def process_client(conn):
    

    while True:
        data = conn.recv(1024).decode()
        if not data:
            break

        command, *args = data.split()

        if command == 'findfile':
            filename = args[0]
            file_path = find_file(filename, os.getcwd())
            if file_path:
                file_info = get_file_info(file_path)
                conn.sendall(file_info.encode())
            else:
                conn.sendall(b"File not found")
        # In process_client()

        elif command == 'sgetfiles':
            size1, size2 = int(args[0]), int(args[1])
            files_list = get_files_by_size(size1, size2, os.getcwd())
            create_and_send_tar(conn, files_list, args)

        elif command == 'dgetfiles':
            date1 = datetime.datetime.strptime(args[0], "%Y-%m-%d").date()
            date2 = datetime.datetime.strptime(args[1], "%Y-%m-%d").date()
            files_list = get_files_by_date(date1, date2, os.getcwd())
            create_and_send_tar(conn, files_list, args)

        elif command == 'getfiles':
            filenames = args[:-1] if args[-1] == '-u' else args
            files_list = get_files_by_names(filenames, os.getcwd())
            create_and_send_tar(conn, files_list, args)

        elif command == 'gettargz':
            extensions = args[:-1] if args[-1] == '-u' else args
            files_list = get_files_by_extensions(extensions, os.getcwd())
            create_and_send_tar(conn, files_list, args)
        elif command.startswith(('sgetfiles', 'dgetfiles', 'getfiles', 'gettargz')):
            root_dir = os.path.expanduser("~")  # Define the root directory for file search

            response = create_and_send_tar(command, root_dir, args)
            if response == b"Invalid command":
                conn.sendall(response)
            else:
                conn.sendall(f"{len(response):010}".encode())
                conn.sendall(response)
        elif command.startswith('quit'):
            conn.sendall("quit".encode())
            break
        
        else:
            conn.sendall(b"Invalid command")

def main():
    host = ''
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print("Server is listening on", host, ":", port)

    while True:
        conn, addr = s.accept()
        print("Connected with", addr)

        t = threading.Thread(target=process_client, args=(conn,))
        t.start()

if __name__ == '__main__':
    main()
