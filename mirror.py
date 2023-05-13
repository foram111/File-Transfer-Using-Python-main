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
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
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
# def send_response(conn, response):
#     if isinstance(response, bytes):
#         conn.sendall(b"BINARY_RESPONSE")
#         conn.sendall(f"{len(response):010}".encode())
#         conn.sendall(response)
#     else:
#         conn.sendall(response.encode())
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
        if command.startswith(('sgetfiles', 'dgetfiles', 'getfiles', 'gettargz')):
            root_dir = os.path.expanduser("~")  # Define the root directory for file search

            response = create_and_send_tar(command, root_dir, args)
            if response == b"Invalid command":
                conn.sendall(response)
            else:
                conn.sendall(f"{len(response):010}".encode())
                conn.sendall(response)
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

        elif command.startswith('quit'):
            conn.sendall("quit".encode())
            break
        
        else:
            conn.sendall(b"Invalid command".decode)

# def process_client(conn):
#     while True:
#         command = conn.recv(1024).decode()
#         if not command:
#             break

#         cmd_parts = command.split()

#         if cmd_parts[0] == "findfile":
#             filename = cmd_parts[1]
#             file_path = find_file(filename, os.getcwd())

#             if file_path:
#                 file_info = os.stat(file_path)
#                 response = f"{filename}, {file_info.st_size} bytes, {datetime.datetime.fromtimestamp(file_info.st_ctime)}"
#             else:
#                 response = "File not found"

#         elif cmd_parts[0] in {"sgetfiles", "dgetfiles", "getfiles", "gettargz"}:
#             # Implement the logic for the other commands
#             file_list = []
#             root = os.path.expanduser("~")

#             if cmd_parts[0] == "sgetfiles":
#                 size1, size2 = int(cmd_parts[1]), int(cmd_parts[2])
#                 file_list = get_files_by_size(size1, size2, os.getcwd())

#                 for root, dirs, files in os.walk(root):
#                     for file in files:
#                         file_path = os.path.join(root, file)
#                         file_info = os.stat(file_path)
#                         if size1 <= file_info.st_size <= size2:
#                             file_list.append(file_path)

#             elif cmd_parts[0] == "dgetfiles":
#                 date1, date2 = datetime.datetime.strptime(cmd_parts[1], "%Y-%m-%d"), datetime.datetime.strptime(cmd_parts[2], "%Y-%m-%d")
#                 file_list = get_files_by_date(date1, date2, os.getcwd())

#                 for root, dirs, files in os.walk(root):
#                     for file in files:
#                         file_path = os.path.join(root, file)
#                         file_info = os.stat(file_path)
#                         file_date = datetime.datetime.fromtimestamp(file_info.st_ctime)
#                         if date1 <= file_date <= date2:
#                             file_list.append(file_path)

#             elif cmd_parts[0] == "getfiles":
#                 filenames = cmd_parts[1:-1] if cmd_parts[-1] == "-u" else cmd_parts[1:]

#                 for root, dirs, files in os.walk(root):
#                     for file in files:
#                         if file in filenames:
#                             file_list.append(os.path.join(root, file))
#                             filenames.remove(file)
#                         if not filenames:
#                             break

#             elif cmd_parts[0] == "gettargz":
#                 ext_list = cmd_parts[1:-1] if cmd_parts[-1] == "-u" else cmd_parts[1:]

#                 for root, dirs, files in os.walk(root):
#                     for file in files:
#                         if any(file.endswith(ext) for ext in ext_list):
#                             file_list.append(os.path.join(root, file))

#             if file_list:
#                 with tarfile.open("temp.tar.gz", "w:gz") as tar:
#                     for file in file_list:
#                         tar.add(file, arcname=os.path.relpath(file, root))

#                 with open("temp.tar.gz", "rb") as f:
#                     conn.sendall("temp.tar.gz".encode())
#                     conn.sendfile(f)

#                 os.remove("temp.tar.gz")
#             else:
#                 response = "No file found"

#         elif cmd_parts[0] == "quit":
#             response = "Goodbye"
#         else:
#             response = "Invalid command"

#         conn.sendall(response.encode())

#         if command.startswith("quit"):
#             break

#     conn.close()

# def main(server_type, port):
#     # server_type: 0 - main server, 1 - mirror

#     host = '127.0.0.1'

#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind((host, port))
#     s.listen(5)

#     print(f"{'Main Server' if server_type == 0 else 'Mirror'} is listening on", host, ":", port)

#     while True:
#         conn, addr = s.accept()

#         with shared_counter_lock:
#             if (server_type == 0 and shared_counter < 4) or (server_type == 1 and 4 <= shared_counter < 8) or shared_counter % 2 == server_type:
#                 shared_counter += 1
#                 print("Connected with", addr)

#                 t = threading.Thread(target=process_client, args=(conn,))
#                 t.start()
#             else:
#                 # Reject connection
#                 conn.close()
                
def main(server_type, port):
    host = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    print(f"{'Main Server' if server_type == 0 else 'Mirror'} is listening on", host, ":", port)

    while True:
        conn, addr = s.accept()

        with shared_counter_lock:
            if (server_type == 0 and shared_counter < 4) or (server_type == 1 and 4 <= shared_counter < 8) or shared_counter % 2 == server_type:
                shared_counter += 1
                print("Connected with", addr)

                t = threading.Thread(target=process_client, args=(conn,))
                t.start()
            else:
                # Reject connection
                conn.close()

    
    
    
    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # server_socket.bind(('0.0.0.0', port))
    # server_socket.listen(5)

    # print(f"Server (type {server_type}) is listening on port {port}")

    # while True:
    #     conn, addr = server_socket.accept()
    #     print(f"Connection from {addr}")
    #     threading.Thread(target=process_client, args=(conn,)).start()

if __name__ == '__main__':
    server_type = int(input("Enter server type (0 for main server, 1 for mirror): "))
    port = int(input("Enter port number: "))
    main(server_type, port)
