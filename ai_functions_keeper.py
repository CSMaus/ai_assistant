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
from prompts import command_name_extraction, commands_description, commands_names_extraction


# now we will use only english. Other languages will be added later
nlp = spacy.load("en_core_web_md")
# TODO: check if file is opened, if ues check is it the file we want to work with and load another if not
# TODO: add delay (in c#) to wait for data file to be loaded before making manipulations with it
# TODO: think, it will be better to do in VS. I e file information is stored there
opened_file_name = ""
command_queue = Queue()

command_keywords = {
    "loadData": ["load", "open", "load file", "open file", "file", "load data", "open data", "open datafile", "load datafile", "datafile", "open"],
    "updatePlot": ["refresh", "update", "redraw", "plot", "modify plot"],
    "getFileInformation": ["info", "details", "metadata", "information"],
    "getDirectory": ["current folder", "current path", "current location", "current directory", "current folder"],
    "doAnalysisSNR": ["snr", "analyze", "signal analysis", "noise ratio", "analyze data", "do analysis", "analysis"],
    "startDefectDetection": ["defect", "detect", "flaw", "detect defects", "search defects", "find defects"],
    "setNewDirectory": ["change folder", "move", "new directory", "set path", "update folder", "change directory", "update directory"]
}

command_names_list = ["loadData", "updatePlot", "getFileInformation", "getDirectory",
                "doAnalysisSNR", "startDefectDetection", "setNewDirectory"]



############################   CHAT GPT API   #################
import openai
import os
openai.api_key = ""
with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
    openai.api_key = file.read().strip()


def parse_comma_separated(command):
    command = command.strip()
    if re.fullmatch(r'\s*[a-zA-Z]+(?:\s*,\s*[a-zA-Z]+)*\s*', command):
        return [word.strip() for word in command.split(',')]
    return None

def get_command_gpt(user_input):
    try:
        # TODO: it's NOT competition! Need to fix it
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": commands_names_extraction},# command_name_extraction},
                {"role": "user", "content": user_input }
            ],
            max_tokens=100,
            temperature=0
        )
        response_text = response.choices[0].message['content'].strip()
        response_text = response_text.strip("```")
        return response_text
    except Exception as e:
        print("Error communicating with OpenAI:", e)
        return None

def chat_with_gpt(user_input):
    try:
        # TODO: it's NOT competition! Need to fix it
        system_prompt = f"""You are an AI assistant designed specifically to assist with software that processes Phased Array Ultrasonic Testing (PAUT) data.\n
                    Your primary role is to provide information related to **ultrasonic testing, nondestructive testing (NDT), and PAUT data analysis**.\n
                    Additionally, you can send commands to the software. The list of valid commands you can use is: 
                    {commands_description}
                    #### Strict Rules:\n
                    - You **MUST NOT** answer questions that are unrelated to PAUT, ultrasonic testing, or NDT.\n
                    - If a user asks something outside of your expertise, respond with:  \n
                    *"I am designed only for PAUT and ultrasonic testing-related tasks."*\n
                    - You **MUST NOT** generate or provide programming code.\n
                    - You **CANNOT** discuss or engage in topics unrelated to PAUT, ultrasonic testing, or NDT.\n
                    - Your responses should be **brief, clear, and professional**.\n
                    #### Allowed Actions:\n
                    - Explain **ultrasonic testing principles**.\n
                    - Guide users on **PAUT data interpretation**.\n
                    - Assist with **NDT software commands** and provide usage instructions.\n
                    - Answer **technical questions strictly related to PAUT and NDT**.\n
                    Stay within these boundaries and maintain a professional and technical tone\n.
                    """
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                { "role": "user", "content": user_input}
            ],
            max_tokens=100,
            temperature=0.4
        )

        response_text = response.choices[0].message['content'].strip()
        response_text = response_text.strip("```")
        return response_text
    except Exception as e:
        print("Error communicating with OpenAI:", e)

    return ""


def contains_code(response: str) -> bool:
    """
    Check if the AI response contains any programming code.
    Detects common patterns like indentation, brackets, or keywords.
    """
    allowed_keywords = ["PAUT", "ultrasonic", "nondestructive", "NDT", "wave", "defect", "inspection", "scanning",
                        "probe"]

    code_patterns = [
        r"```.*?```",              # Triple backticks for code blocks
        r"\bimport\b",             # Python imports
        r"\bclass\b|\bdef\b",      # Python functions and classes
        r"\bif\b|\belse\b|\bwhile\b|\bfor\b|\btry\b|\bexcept\b",  # Python keywords
        r"#.*",                    # Comments in Python
        r";",                      # Common in C, Java, JS
        r"\{.*?\}",                # Brackets in C-like languages
        r"<.*?>",                  # HTML tags
        r"System\.out\.print",      # Java print statement
        r"console\.log",            # JavaScript print statement
    ]

    # maybe for later, but not always good
    # f not any(keyword.lower() in response_txt.lower() for keyword in allowed_keywords):
    #         return False

    for pattern in code_patterns:
        if re.search(pattern, response, re.DOTALL):
            return True
    return False

def chat_with_ollama(user_input):
    system_prompt_old = f"""You are an AI assistant designed specifically to assist with software that processes Phased Array Ultrasonic Testing (PAUT) data.\n
                    Your primary role is to provide information related to **ultrasonic testing, nondestructive testing (NDT), and PAUT data analysis**.\n
                    Additionally, you can send commands to the software. The list of valid commands you can use is: 
                    {commands_description}
                    #### Strict Rules:\n
                    - You **MUST NOT** answer questions that are unrelated to PAUT, ultrasonic testing, or NDT.\n
                    - If a user asks something outside of your expertise, respond with:  \n
                    *"I am designed only for PAUT and ultrasonic testing-related tasks."*\n
                    - You **MUST NOT** generate or provide programming code.\n
                    - You **CANNOT** discuss or engage in topics unrelated to PAUT, ultrasonic testing, or NDT.\n
                    - Your responses should be **brief, clear, and professional**.\n
                    #### Allowed Actions:\n
                    - Explain **ultrasonic testing principles**.\n
                    - Guide users on **PAUT data interpretation**.\n
                    - Assist with **NDT software commands** and provide usage instructions.\n
                    - Answer **technical questions strictly related to PAUT and NDT**.\n
                    Stay within these boundaries and maintain a professional and technical tone\n.
                    """
    prompt_new = f"""You are an AI assistant designed to assist with **PAUTReader software** and topics related to **Phased Array Ultrasonic Testing (PAUT), Nondestructive Testing (NDT), and ultrasonic testing**.
            #### **Your Responsibilities:**
            1. **Explain PAUT and NDT principles** – Provide technical details and best practices related to ultrasonic testing.
            2. **Guide users on PAUT data interpretation** – Help users understand how to analyze PAUT data.
            3. **Assist with PAUTReader software commands** – When asked about software commands, provide the full list:
            {commands_description}
            4. **Help users troubleshoot PAUTReader software issues** – Offer solutions for common problems.
            
            #### **Rules:**
            - **Allowed Topics:**
            - PAUT/NDT concepts, techniques, and industry best practices.
            - How to use PAUTReader software, including available commands.
            - Common troubleshooting steps for PAUTReader software.
            
            - **Restricted Topics (DO NOT Answer):**
            - Questions **not related** to PAUT, NDT, or PAUTReader software.
            - **Programming/code generation** (You cannot write or explain code).
            - General knowledge topics (history, politics, entertainment, etc.).
            - Personal opinions or discussions outside PAUT/NDT.
            
            #### **If the user asks about software commands:**
            - List **only the commands from {commands_description}** and their descriptions.
            - Do **NOT invent additional commands**.
            
            #### **If the question is unrelated to PAUT or NDT:**
            - Respond with: *"I am designed only for PAUT and ultrasonic testing-related tasks."*
            
            Now, respond to the user input below:
            
            [USER]
            {user_input}
            
            [ASSISTANT]
            
            """

    response = ollama.generate(
        model="mistral",
        prompt=f"{prompt_new}",
        options={"temperature": 0.5}
    )
    response_txt = response['response'].strip()

    if contains_code(response_txt):
        response_txt = "I am AI assistant to work with PAUTReader software based on Mistral model. "\
                        "I am designed only for PAUT and ultrasonic testing-related tasks."

    return response_txt

def get_command_ollama(user_input):
    response = ollama.generate(
        model="mistral",
        # prompt=f"{command_name_extraction}\n\n{user_input}",
        prompt=f"""
                You are an AI assistant that **ONLY extracts command names** from user input.
            
                ### **RULES:**
                1. If the user's request **matches one of the following commands**, **return ONLY the command name** with **no additional text**.
                2. If the user's input **does NOT match any command**, **return an empty string (`""`)**. **DO NOT explain. DO NOT respond with any text. DO NOT add any formatting.**
                3. **COMMAND LIST:**
                {commands_description}
            
                **USER INPUT:** "{user_input}"
            
                **YOUR RESPONSE (ONLY command name OR empty string):**
                """,
        options={"temperature": 0}
    )

    # prompt = f"""[SYSTEM]\n{command_name_extraction} \n\n[USER]\n{user_input}\n[ASSISTANT]""",  # Ensures Mistral responds like a chatbot

    '''
        You are an AI assistant that **ONLY extracts command names** from user input.
        ### **RULES:**
        1. If the user's request **matches one of the following commands**, **return ONLY the command name** with **no additional text**.
        2. If the user's input **does NOT match any command**, **return an empty string (`""`)**. **DO NOT explain. DO NOT respond with any text. DO NOT add any formatting.**
        3. **COMMAND LIST:**
        {commands_description}
        **USER INPUT:** "{user_input}"
        **YOUR RESPONSE (ONLY command name OR empty string):**
        """
    '''
    print(response)
    return response['response'].strip()

def status_message(command, args):
    if command == "loadData":
        try:
            data_f = re.sub(r'[\[\]"\']', '', str(", ".join(args)))
            return f"Trying to load datafile: {data_f}"
        except Exception as e:
            print("Tried to extract file name, got exception: ", e)

    elif command == "setNewDirectory":
        try:
            dir = re.sub(r'[\[\]"\']', '', str("".join(args[0])))
            return f"Trying to change current directory to: {dir}"
        except Exception as e:
            print("Tried to extract file name, got exception: ", e)
    return f"Working on it..."
    # Command: {command}.\nReceiving status about command execution will be implemented later."


def extract_folder_ollama(user_input):
    system_prompt = "Extract full folder path with folder name from the input. Return only the folder path. No extra words. No explanations. No formatting."
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

