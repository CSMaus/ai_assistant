import json
from queue import Queue
from threading import Thread
from command_process import execute_command
import os
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity
import re
# download ollama and then "ollama pull tinyllama" to run in offline later
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
    "loadData": ["load", "open", "file", "import", "load file"],
    "updatePlot": ["refresh", "update", "redraw", "plot", "modify plot"],
    "getFileInformation": ["info", "details", "metadata", "information"],
    "getDirectory": ["current folder", "current path", "current location", "current directory", "current folder"],
    "doAnalysisSNR": ["snr", "analyze", "signal analysis", "noise ratio", "analyze data", "do analysis", "analysis"],
    "startDefectDetection": ["defect", "detect", "flaw", "detect defects", "search defects", "find defects"],
    "setNewDirectory": ["change folder", "move", "new directory", "set path", "update folder", "change directory", "update directory"]
}

# here is the code to work with llm models to extract correct commands and arguments for them
def extract_folder_ollama(user_input):
    prompt = f"'{user_input}'"
    '''system_prompt = f"You are folder or directory name extractor. You have to return ONLY folder or directory name which" \
                    f" you find in input text. All other responses are forbidden. You will be killed of you provide " \
                    f"something else in addition to folder name."
    response = ollama.chat(model="tinyllama", messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}])'''
    #
    # tinyllama is too tiny to execute commands correctly
    system_prompt = "Extract only the folder name from the input. Return only the folder name. No extra words. No explanations. No formatting."
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
        # match = re.search(r"(?:(?:to|into|set|set new|change to|folder is|directory is| is| new is| new to|)\s+)?([\w/\\]+)", user_input)

        folder_name = extract_folder_ollama(user_input).strip()
        if folder_name:
            # folder = match.group(1)
            args.extend([folder_name, False, ""])
        else:
            print("No valid folder name found to update directory.")

    return args



def process_input(user_input):
    """extract commands, arguments, and add to queue"""
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
