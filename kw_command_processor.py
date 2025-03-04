import json
from queue import Queue
from threading import Thread
from command_process import execute_command
import os
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import re

# now we will use only english. Other languages will be added later
nlp = spacy.load("en_core_web_md")

command_queue = Queue()

command_keywords = {
    "loadData": ["load", "open", "file", "import", "load file"],
    "updatePlot": ["refresh", "update", "redraw", "plot", "modify plot"],
    "getFileInformation": ["info", "details", "metadata", "information"],
    "getDirectory": ["folder", "path", "location", "directory", "current folder"],
    "doAnalysisSNR": ["snr", "analyze", "signal analysis", "noise ratio", "analyze data", "do analysis", "analysis"],
    "startDefectDetection": ["defect", "detect", "flaw", "detect defects", "search defects", "find defects"],
    "setNewDirectory": ["change folder", "move", "new directory", "set path", "update folder", "change directory", "update directory"]
}

def extract_keywords(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB"] and token.has_vector]

def get_best_matching_commands(user_keywords, threshold=0.5):
    matched_commands = []

    for command, keywords in command_keywords.items():
        command_vectors = [nlp(keyword).vector for keyword in keywords if nlp(keyword).has_vector]

        for user_keyword in user_keywords:
            user_vector = nlp(user_keyword).vector
            if not np.any(user_vector):
                continue

            similarities = [cosine_similarity([user_vector], [cmd_vector])[0][0] for cmd_vector in command_vectors]
            avg_similarity = np.mean(similarities) if similarities else 0

            if avg_similarity > threshold:
                matched_commands.append((command, avg_similarity))

    matched_commands = sorted(set(matched_commands), key=lambda x: x[1], reverse=True)

    # only command names
    return [cmd[0] for cmd in matched_commands]

def extract_arguments(command, user_input):
    """Extracts necessary arguments for commands that require them."""
    args = []

    if command == "loadData":
        # extract fpd or opd file
        match = re.search(r"(\b\w+\.(fpd|opd)\b)", user_input)

        # TODO: remake to get some file not by name:
        # TODO: i e it can be last created file in folder, or all files in folder
        # TODO: i e it can be folder, not file itself
        if match:
            args.append(match.group(1))
        else:
            folder_match = re.search(r"(?:from|in|at)\s+([\w/\\]+)", user_input)
            if folder_match:
                folder_path = folder_match.group(1)
                args.append(folder_path)

                # this part will be used later, but I think, I'll make it in program itself, not here
                '''latest_file = get_latest_file_in_folder(folder_path)
                if latest_file:
                    args.append(latest_file)
                else:
                    args.append(folder_path)'''

            else:
                print("No valid file or folder found to load data.")

    elif command == "setNewDirectory":
        match = re.search(r"(?:(?:to|into|set|change to|folder is|directory is| is|)\s+)?([\w/\\]+)", user_input)
        if match:
            folder = match.group(1)
            # default parameters
            args.extend([folder, False, ""])
        else:
            print("No valid folder name found to update directory.")

    return args



def process_input(user_input):
    """Process user input, extract commands, arguments, and add to queue."""
    try:
        user_keywords = extract_keywords(user_input)
        matched_commands = get_best_matching_commands(user_keywords)

        if matched_commands:
            for command in matched_commands:
                args = extract_arguments(command, user_input)
                command_queue.put((command, args))
                print(f"Command '{command}' added to queue with args: {args}")
        else:
            print("No matching command found.")

    except Exception as e:
        print("Error processing input:", e)

def command_listener():
    while True:
        command, args = command_queue.get()
        execute_command(command, *args)
        command_queue.task_done()

def run_chat_bot():
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
