import requests

BASE_URL = "http://localhost:5000/api/app"
# revise all the methods to be corectly defined as POST or GET:
#  ______________________ REST principles ______________________
# GET:
# Use for retrieving data (read-only operations).
# Parameters are included in the URL query string.
# Should not modify the state of the application or server.
#
# POST:
# Use for sending data to the server to initiate actions or modify state.
# Parameters are included in the body, ensuring flexibility and better security for sensitive data.


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
    "getDirectory": {
        "endpoint": f"{BASE_URL}/getDirectory?folderName=Documents",
        "method": "GET",

    },
    "setNewDirectory": {
        "endpoint": f"{BASE_URL}/setNewDirectory",
        "method": "POST",
        "payload": lambda folder, is_root_path, root_path: {
            "TargetFolder": folder,
            "isrootPathForSearchIsCurrentDir": is_root_path,
            "rootPathForFolderSearch": root_path,
        },
    },
    "startSNRAnalysis": {
        "endpoint": f"{BASE_URL}/startSNRAnalysis",
        "method": "POST",
        "payload": lambda: {},
    },
    "startDefectDetection": {
        "endpoint": f"{BASE_URL}/startDefectDetection",
        "method": "POST",
        "payload": lambda: {},
    },
}
# "payload": lambda: {},  # get methods should not contain it
'''"setNewDirectory": {
    "endpoint": f"{BASE_URL}/setNewDirectory",
    "method": "POST",
    "payload": lambda file_path: {"FilePath": file_path, "make_search_for_folder": False, "isrootPathForSearchCurrentDir": False, "rootPathForSearch": ""},
},'''


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
