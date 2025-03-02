# here only convert commands to the json based on the keywords from input text
# the idea is:
# 1. for each command define list of keywords
# 2. from input text extract the keywords
# 3. compare keywords from the input text with the keywords from the command using similarity and
#   build list of commands

# need to define variables to store what actions were already done
# *I e is file opened?
# *What name of opened file?
# *What analysis was done and what results do we have?
# if we already did analysis for requested file, we have to ask user, should we remake analysis and prepare report


import json
from queue import Queue
from threading import Thread
from command_process import execute_command
import os
import spacy
from spacy.matcher import Matcher


def parse_response(response_text):
    """
    Parse the response text from the chat-bot to identify the command and arguments.
    """
    try:
        # Remove backticks and ensure response starts with `{`
        response_text = response_text.strip("`").strip()
        if not response_text.startswith("{"):
            raise ValueError("Response does not contain valid JSON")

        # Attempt to load JSON response
        response_data = json.loads(response_text)
        print("Parsed response data:", response_data)  # Debugging print

        # Extract command and args, ensuring they're correctly structured
        command = response_data.get("command")
        args = response_data.get("args", [])

        # Verify command and args are in the expected format
        if not command or not isinstance(args, list):
            raise ValueError("Parsed response does not contain expected 'command' and 'args' format")

        # Return parsed values
        return command, args
    except Exception as e:
        print("Failed to parse response:", e)
        print("Raw response text:", response_text)  # For debugging purposes
        return None, []

def process_input(user_input):
    """
    Send the user's input to OpenAI's API to generate a command response.
    """
    try:
        # TODO: it's NOT competition! Need to fix it
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Replace with "gpt-4" or other chat model if needed
            messages=[
                {"role": "system", "content": "You are a converter that transforms input text into API commands. "
                    "Always respond with a command in valid JSON format. "
                    "The JSON must include a 'command' key (string) and an 'args' key (list of values). "
                    "Example of the correct format: {\"command\": \"setNewDirectory\", \"args\": [\"SomeFolder\", true, \"\"]}. "
                    "Do not include additional words, symbols, or formatting outside of the JSON structure."},
                # You are an assistant that helps to transform input text into commands in desired format
                {
                    "role": "user",
                    "content": f"Interpret the following text: {user_input} into command."
                               f"Available commands: 'loadData' which requires file path as input, 'updatePlot', "
                               f"'getFileInformation' which  return string with information,"
                               f"'getDirectory' which returns string with the full path to the folder where opened file is located,"
                               f"'startSNRAnalysis' no argument method which makes analysis"
                               f"'startDefectDetection' no argument method which do search for defects, "
                               f"'setNewDirectory' to set new the working directory with three arguments always: string TargetFolder, bool isrootPathForSearchIsCurrentDir, string rootPathForFolderSearch,"
                               f"If the command specifies a directory path (e.g., 'in Documents folder'), resolve the directory name to its absolute path with isrootPathForSearchIsCurrentDir to be false"
           f"using environment variables (e.g., '%USERPROFILE%\\Documents' for Windows). "
           f"If no explicit search root is specified, set 'isrootPathForSearchIsCurrentDir' to True. "
           f"Start response with open bracket, followed by 'command', and fill the rest based on the text analysis. "
                               f"'args' should always be a list of values only (no key names in the list)."
                }
            ],
            max_tokens=100,
            temperature=0.2
        )

        response_text = response.choices[0].message['content'].strip()
        response_text = response_text.strip("```")
        if '{' in response_text:
            response_text = response_text[response_text.index('{'):]
        print("Chat-bot Response:", response_text)

        # Parse the response to extract command and arguments
        command, args = parse_response(response_text)

        if command:
            command_queue.put((command, args))
            # command_queue.put({"command": command, "args": args})
            print(f"Command '{command}' added to queue with args: {args}")
        else:
            print("Failed to interpret command.")

    except Exception as e:
        print("Error communicating with OpenAI:", e)


def command_listener():
    while True:
        command, args = command_queue.get()
        execute_command(command, *args)
        command_queue.task_done()


def run_chat_bot():
    """
    Continuously listen for user input, process it with the chatbot, and queue the command.
    """
    print("Type your command ('quit' to exit):")
    while True:
        user_input = input(">> ")
        if user_input.lower() == "quit":
            break
        process_input(user_input)


if __name__ == "__main__":
    listener_thread = Thread(target=command_listener)
    listener_thread.daemon = True
    listener_thread.start()
    run_chat_bot()
