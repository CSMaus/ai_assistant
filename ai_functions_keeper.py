# TODO: This is a note: here I get commands for input NL text input and process them with spacy+sklearn
# TODO: for correct command extraction and mistral (7.25B quantization Q4_0, 4.1GB) for arg extraction
# TODO: I think to remake to make all processing via mistral to get accurate commands and args extractions
import json
from queue import Queue
from command_process import execute_command_gui
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import re
# download ollama and then "ollama pull tinyllama" to run in offline later
# but I use mistral here. tinyllama is too tiny
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import ollama


# now we will use only english. Other languages will be added later
nlp = spacy.load("en_core_web_md")
# TODO: check if file is opened, if ues check is it the file we want to work with and load another if not
# TODO: add delay (in c#) to wait for data file to be loaded before making manipulations with it
# TODO: think, it will be better to do in VS. I e file information is stored there
opened_file_name = ""
command_queue = Queue()

command_keywords = {
    "loadData": ["load", "open", "load file", "open file", "file", "load data", "open data", "open datafile", "load datafile", "datafile"],
    "updatePlot": ["refresh", "update", "redraw", "plot", "modify plot"],
    "getFileInformation": ["info", "details", "metadata", "information"],
    "getDirectory": ["current folder", "current path", "current location", "current directory", "current folder"],
    "doAnalysisSNR": ["snr", "analyze", "signal analysis", "noise ratio", "analyze data", "do analysis", "analysis"],
    "startDefectDetection": ["defect", "detect", "flaw", "detect defects", "search defects", "find defects"],
    "setNewDirectory": ["change folder", "move", "new directory", "set path", "update folder", "change directory", "update directory"]
}

def status_message(command, args):
    if command == "loadData":
        return f"Trying to load datafile: {args}"  # [0][2:-2]
    current_command = f"command: {command}, args: {args}"
    system_prompt = ("Convert input command with arguments into natural language text so it could be used as answer "
                     "about the current running process in program. No additional text. No additional questions. "
                     "Only process following command with args as described: ")
    response = ollama.generate(
        model="mistral",
        prompt=f"{system_prompt}\n\n{current_command}",
        options={"temperature": 0}
    )
    print(response)
    return response['response'].strip()


def extract_folder_ollama(user_input):
    system_prompt = "Extract only the folder name from the input. Return only the folder name. No extra words. No explanations. No formatting."
    response = ollama.generate(
        model="mistral",
        prompt=f"{system_prompt}\n\n{user_input}",
        options={"temperature": 0}
    )
    print(response)
    return response['response'].strip()

def extract_filename_ollama(user_input):
    system_prompt = "Extract only the file name from the input. Return only the file name. No extra words. No explanations. No formatting."
    response = ollama.generate(
        model="mistral",
        prompt=f"{system_prompt}\n\n{user_input}",
        options={"temperature": 0}
    )
    print(response)
    return response['response'].strip()
# llama3

def extract_keywords(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB"] and token.has_vector]

def get_best_matching_commands(user_keywords, threshold=0.5, max_threshold=0.95):
    # TODO: maybe remake this function to return cosine similarity for each command and choose the one with largest value?

    matched_commands = []

    for command, keywords in command_keywords.items():
        command_vectors = [nlp(keyword).vector for keyword in keywords if nlp(keyword).has_vector]

        for user_keyword in user_keywords:
            user_vector = nlp(user_keyword).vector
            if not np.any(user_vector):
                continue

            similarities = [cosine_similarity([user_vector], [cmd_vector])[0][0] for cmd_vector in command_vectors]
            avg_similarity = np.mean(similarities) if similarities else 0
            max_similarity = max(similarities) if similarities else 0
            if avg_similarity > threshold or max_similarity > max_threshold:
                matched_commands.append((command, avg_similarity))

    matched_commands = sorted(set(matched_commands), key=lambda x: x[1], reverse=True)

    return [cmd[0] for cmd in matched_commands]

def extract_arguments(command, user_input):
    args = []
    warning_txt = ""

    if command == "loadData":
        # TODO: it works well, but need to add model warmup (first time it takes few sec to set)
        filename = extract_filename_ollama(user_input).strip()
        if filename:
            args.append(filename)
        else:
            # old code, should be replaced with llm for correct file name extraction
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
                    warning_txt = "No valid file or folder found to load data."
    elif command == "setNewDirectory":
        folder_name = extract_folder_ollama(user_input).strip()
        if folder_name:
            args.extend([folder_name, False, ""])
        else:
            warning_txt = "No valid folder name found to update directory."

    return args, warning_txt



def process_input_legacy(user_input):
    """extract commands, arguments, and add to queue"""
    progress_txt = ""
    try:
        user_keywords = extract_keywords(user_input)
        matched_commands = get_best_matching_commands(user_keywords)

        if matched_commands:
            for command in matched_commands:
                args = extract_arguments(command, user_input)
                command_queue.put((command, args))
                progress_txt = status_message(command, args)
                print(f"Command '{command}' added to queue with args: {args}")
        else:
            progress_txt = "No matching command found."
            print("No matching command found.")

    except Exception as e:
        return f"Error appeared: {e}"
        # print("Error processing input:", e)
    return progress_txt

def command_listener_legacy():
    while True:
        command, args = command_queue.get()
        msg, response = execute_command_gui(command, *args)
        command_queue.task_done()

def run_chat_bot():
    print("Type your command ('quit' to exit):")
    while True:
        user_input = input(">> ")
        if user_input.lower() == "quit":
            break
        process_input_legacy(user_input)

