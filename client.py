import socket
import sys
import tarfile
import re
import os


def verify_command(command):
    findfile_pattern = r'^findfile [\w\-\.]+$'
    sgetfiles_pattern = r'^sgetfiles \d+ \d+(-u)?$'
    dgetfiles_pattern = r'^dgetfiles \d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}(-u)?$'
    getfiles_pattern = r'^getfiles [\w\-\.]+( [\w\-\.]+){0,5}(-u)?$'
    gettargz_pattern = r'^gettargz (\w+( \w+){0,5})(-u)?$'
    quit_pattern = r'^quit$'

    if re.match(findfile_pattern, command) or re.match(sgetfiles_pattern, command) or \
            re.match(dgetfiles_pattern, command) or re.match(getfiles_pattern, command) or \
            re.match(gettargz_pattern, command) or re.match(quit_pattern, command):
        return True
    return False

def send_command(s, command):
    s.sendall(command.encode())
    if command.startswith(('sgetfiles', 'dgetfiles', 'getfiles', 'gettargz')):
        response_size = int(s.recv(2).decode("utf-8","ignore").strip())  # Add buffer size 10 here
        response = b""
        while len(response) < response_size:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk
    elif command.startswith('quit'):
        response = s.recv(1024).decode()
        if response == "quit":
            print("Connection closed.")
            s.close()
            sys.exit(0)  # Close the client
        else:
            return None
    else:
        response = s.recv(1024).decode()
        if response == "Invalid command":
            print(response)
            return None
        elif response.startswith("BINARY_RESPONSE"):
            response = response.split(" ", 1)[1]
            response_size = int(response.strip())
            response = b""
            while len(response) < response_size:
                chunk = s.recv(1024)
                if not chunk:
                    break
                response += chunk
    return response


def main():
    host = '192.168.2.24'
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    print("Connected to server", host, ":", port)

    while True:
        command = input("C$ ")
        if not verify_command(command):
            print("Invalid command")
            continue

        response_data = send_command(s, command)  # Corrected variable name

        if command == "quit":
            s.close()
            break

        command, *args = command.split()

        if command.startswith(('sgetfiles', 'dgetfiles', 'getfiles', 'gettargz')):
            if response_data == b"No file found":
                print("No file found")
            else:
                with open("temp.tar.gz", "wb") as tar_file:
                    tar_file.write(response_data)
                if '-u' in command.split():  # Corrected check for -u flag
                    with tarfile.open("temp.tar.gz", "r:gz") as tar:
                        tar.extractall()
                    os.remove("temp.tar.gz")
                    # Notify the server that the client has finished unpacking
                    s.sendall(b"Unpacked")
        else:
            print(response_data)
    s.close()


if __name__ == '__main__':
    main()