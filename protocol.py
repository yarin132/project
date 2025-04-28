SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
COMMAND_LENGTH = 2
DATA_LENGTH = 8


def recv_data(client_socket):
    cmd_len = int(recv_until_done(client_socket, COMMAND_LENGTH).decode())

    command = recv_until_done(client_socket, cmd_len).decode()

    data_len = int(recv_until_done(client_socket, DATA_LENGTH).decode())

    data = recv_until_done(client_socket, data_len)

    return command, data


def recv_until_done(client_socket, wanted_len):
    data = b''
    while len(data) < wanted_len:
        data += client_socket.recv(wanted_len-len(data))
    return data


def send_msg(client_socket, command, data):
    completed_command = create_command(command)
    if isinstance(data, bytes):
        completed_data = create_bin_msg(data)
    else:
        completed_data = create_msg(data)
    client_socket.sendall(completed_command)
    client_socket.sendall(completed_data)


def create_bin_msg(data):
    return (str(len(data)).zfill(DATA_LENGTH)).encode() + data


def create_command(command):
    return (str(len(command)).zfill(COMMAND_LENGTH) + command).encode()


def create_msg(data):
    return (str(len(data)).zfill(DATA_LENGTH) + data).encode()
