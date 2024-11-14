import requests

BASE_URL = "http://localhost:5000/api/app"

COMMAND_ENDPOINTS = {
    "loadData": {
        "endpoint": f"{BASE_URL}/loadData",
        "method": "POST",
        "payload": lambda file_path: {"FilePath": file_path},
    },
    "updatePlot": {
        "endpoint": f"{BASE_URL}/updatePlot",
        "method": "POST",
        "payload": lambda: {},
    },
    "getFileInformation": {
        "endpoint": f"{BASE_URL}/getFileInformation",
        "method": "POST",
        "payload": lambda: {},
    },
    "getFileDirectory": {
        "endpoint": f"{BASE_URL}/getFileDirectory",
        "method": "POST",
        "payload": lambda: {},
    },
    "setNewWorkingDirectory": {
        "endpoint": f"{BASE_URL}/setNewWorkingDirectory",
        "method": "POST",
        "payload": lambda file_path: {"FilePath": file_path},
    },
}


def execute_command(command_name, *args):
    if command_name in COMMAND_ENDPOINTS:
        command_info = COMMAND_ENDPOINTS[command_name]
        endpoint = command_info["endpoint"]
        method = command_info["method"]
        payload = command_info["payload"](*args)

        if method == "POST":
            response = requests.post(endpoint, json=payload)
        elif method == "GET":
            response = requests.get(endpoint, params=payload)
        else:
            raise ValueError("Unsupported HTTP method")

        if response.status_code == 200:
            print(f"Command '{command_name}' executed successfully.")
            print("Response:", response.json())
        else:
            print(f"Failed to execute command '{command_name}'. Status code:", response.status_code)
            print("Response:", response.text)
    else:
        print(f"Unknown command '{command_name}'")


