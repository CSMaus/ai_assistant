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
import io
import wave
from prompts import command_name_extraction, commands_description, commands_names_extraction

# Import the file finder module
try:
    from file_finder import find_file_in_system, find_directory_in_system, find_files_by_extension, get_most_recent_file

    FILE_FINDER_AVAILABLE = True
except ImportError:
    print("Warning: file_finder module not available. File search functionality will be limited.")
    FILE_FINDER_AVAILABLE = False

# now we will use only english. Other languages will be added later
nlp = spacy.load("en_core_web_md")
# TODO: check if file is opened, if ues check is it the file we want to work with and load another if not
# TODO: add delay (in c#) to wait for data file to be loaded before making manipulations with it
# TODO: think, it will be better to do in VS. I e file information is stored there
opened_file_name = ""
command_queue = Queue()

command_keywords = {
    "loadData": ["load", "open", "load file", "open file", "file", "load data", "open data", "open datafile",
                 "load datafile", "datafile", "open"],
    "updatePlot": ["refresh", "update", "redraw", "plot", "modify plot"],
    "getFileInformation": ["info", "details", "metadata", "information"],
    "getDirectory": ["current folder", "current path", "current location", "current directory", "current folder"],
    "doAnalysisSNR": ["snr", "analyze", "signal analysis", "noise ratio", "analyze data", "do analysis", "analysis"],
    "startDefectDetection": ["defect", "detect", "flaw", "detect defects", "search defects", "find defects"],
    "setNewDirectory": ["change folder", "move", "new directory", "set path", "update folder", "change directory",
                        "update directory"]
}

command_names_list = ["loadData", "updatePlot", "getFileInformation", "getDirectory",
                      "doAnalysisSNR", "startDefectDetection", "setNewDirectory", "makeSingleFileOnly",
                      "doFolderAnalysis"]

############################   CHAT GPT API   #################
import openai
import os
import platform
from openai import OpenAI

# Initialize OpenAI client
client = None
try:
    with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
        api_key = file.read().strip()

        # Check the operating system to handle platform-specific initialization
        if platform.system() == "Windows":
            # On Windows, don't use the proxies parameter
            client = OpenAI(api_key=api_key)
        else:
            # On macOS and other systems, use the standard initialization
            client = OpenAI(api_key=api_key)

        print(f"OpenAI client initialized successfully on {platform.system()}")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")


def parse_comma_separated(command):
    command = command.strip()
    if re.fullmatch(r'\s*[a-zA-Z]+(?:\s*,\s*[a-zA-Z]+)*\s*', command):
        return [word.strip() for word in command.split(',')]
    return None


def get_command_gpt(user_input):
    try:
        if client is None:
            print("OpenAI client not initialized")
            return None
        
        # Check if language_prompts module is available
        try:
            from language_prompts import prompt_manager
            LANGUAGE_PROMPTS_AVAILABLE = True
        except ImportError:
            print("Warning: language_prompts module not available. Using default prompts.")
            LANGUAGE_PROMPTS_AVAILABLE = False
        
        # Use the client's language detection if available
        if hasattr(client, 'detect_language'):
            language_code = client.detect_language(user_input)
            print(f"Detected language: {language_code}")
        else:
            # Fallback to basic detection
            is_korean = any('\uac00' <= char <= '\ud7a3' for char in user_input)
            is_russian = any('\u0400' <= char <= '\u04FF' for char in user_input)
            
            language_code = "ko" if is_korean else "ru" if is_russian else "en"
            print(f"Basic language detection: {language_code}")
        
        # Get language-specific prompt if available
        if LANGUAGE_PROMPTS_AVAILABLE:
            commands_names_prompt = prompt_manager.get_prompt("commands_names_extraction", language_code)
        else:
            commands_names_prompt = commands_names_extraction
        
        # Use the client's extract_commands method with language-specific prompt
        if hasattr(client, 'extract_commands'):
            commands = client.extract_commands(user_input)
        else:
            # Fallback to direct API call
            response = client.chat_completion(
                user_input=user_input,
                system_prompt=commands_names_prompt
            )
            commands = response.strip()
        
        return commands
    except Exception as e:
        print(f"Error in get_command_gpt: {e}")
        return None
            
            for pattern, command in korean_file_operations:
                if re.search(pattern, user_input):
                    print(f"Detected Korean file operation pattern: {pattern}")
                    
                    # Check if there's also a defect detection request in Korean
                    if re.search(r"결함|검색|탐지", user_input):
                        print("Also detected Korean defect detection request")
                        return "loadData,startDefectDetection"
                    
                    # Check if there's also an analysis request in Korean
                    if re.search(r"분석|SNR|신호", user_input):
                        print("Also detected Korean analysis request")
                        return "loadData,doAnalysisSNR"
                    
                    # Check if there's also an information request in Korean
                    if re.search(r"정보|상세|메타데이터", user_input):
                        print("Also detected Korean information request")
                        return "loadData,getFileInformation"
                    
                    return command
        
        # Check for combined operations in Russian
        if is_russian:
            russian_combined_operations = [
                (r"файл.*откр.*дефект", "loadData,startDefectDetection"),  # Open file and search for defects
                (r"файл.*откр.*анализ", "loadData,doAnalysisSNR"),         # Open file and analyze
                (r"файл.*откр.*информац", "loadData,getFileInformation"),   # Open file and show information
                (r"дефект.*отчет", "startDefectDetection,makeSingleFileOnly"),  # Defect detection and report
                (r"анализ.*отчет", "doAnalysisSNR,makeSingleFileOnly")      # Analysis and report
            ]
            
            for pattern, commands in russian_combined_operations:
                if re.search(pattern, user_input.lower()):
                    print(f"Detected Russian combined operation pattern: {pattern}")
                    return commands
            
            # Check for file operations in Russian
            russian_file_operations = [
                (r"файл.*откр", "loadData"),    # Open file
                (r"загруз.*файл", "loadData"),  # Load file
                (r"данны.*откр", "loadData"),   # Open data
                (r"\.fpd", "loadData"),
                (r"\.opd", "loadData")
            ]
            
            for pattern, command in russian_file_operations:
                if re.search(pattern, user_input.lower()):
                    print(f"Detected Russian file operation pattern: {pattern}")
                    
                    # Check if there's also a defect detection request in Russian
                    if re.search(r"дефект|поиск|обнаруж", user_input.lower()):
                        print("Also detected Russian defect detection request")
                        return "loadData,startDefectDetection"
                    
                    # Check if there's also an analysis request in Russian
                    if re.search(r"анализ|снр|сигнал", user_input.lower()):
                        print("Also detected Russian analysis request")
                        return "loadData,doAnalysisSNR"
                    
                    # Check if there's also an information request in Russian
                    if re.search(r"информац|детал|метадан", user_input.lower()):
                        print("Also detected Russian information request")
                        return "loadData,getFileInformation"
                    
                    return command
        
        # Check for combined operations like "open file and find defects" (English)
        combined_operations = [
            (r"open.*(?:and|then).*defect", "loadData,startDefectDetection"),
            (r"load.*(?:and|then).*defect", "loadData,startDefectDetection"),
            (r"open.*(?:and|then).*analysis", "loadData,doAnalysisSNR"),
            (r"load.*(?:and|then).*analysis", "loadData,doAnalysisSNR"),
            (r"open.*(?:and|then).*information", "loadData,getFileInformation"),
            (r"load.*(?:and|then).*information", "loadData,getFileInformation"),
            (r"defect.*(?:and|then).*report", "startDefectDetection,makeSingleFileOnly"),
            (r"analysis.*(?:and|then).*report", "doAnalysisSNR,makeSingleFileOnly")
        ]
        
        for pattern, commands in combined_operations:
            if re.search(pattern, user_input.lower()):
                print(f"Detected combined operation pattern: {pattern}")
                return commands
        
        # Check for file operations first - these should take priority
        file_operation_patterns = [
            (r"open.*file", "loadData"),
            (r"load.*file", "loadData"),
            (r"open.*data", "loadData"),
            (r"load.*data", "loadData"),
            (r"show.*file", "loadData"),
            (r"display.*file", "loadData"),
            (r"\.fpd", "loadData"),
            (r"\.opd", "loadData")
        ]
        
        for pattern, command in file_operation_patterns:
            if re.search(pattern, user_input.lower()):
                print(f"Detected file operation pattern: {pattern}")
                
                # Check if there's also a defect detection request
                if re.search(r"defect|flaw|detect", user_input.lower()):
                    print("Also detected defect detection request")
                    return "loadData,startDefectDetection"
                
                # Check if there's also an analysis request
                if re.search(r"analysis|analyze|snr", user_input.lower()):
                    print("Also detected analysis request")
                    return "loadData,doAnalysisSNR"
                
                # Check if there's also an information request
                if re.search(r"information|details|metadata", user_input.lower()):
                    print("Also detected information request")
                    return "loadData,getFileInformation"
                
                return command

        # First, check if this is likely a question rather than a command
        is_question = False
        if user_input.strip().endswith("?"):
            is_question = True

        # Common question words/phrases that indicate information seeking rather than commands
        question_indicators = ["how", "what", "why", "when", "where", "can you explain",
                               "tell me about", "describe", "information on", "details about"]

        for indicator in question_indicators:
            if indicator in user_input.lower():
                is_question = True
                break

        # If it's clearly a question, skip command detection
        if is_question and not re.search(r"can you (open|load|run|find|detect|analyze)", user_input.lower()):
            print("Detected as a question, skipping command detection")
            return ""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": commands_names_extraction},
                {"role": "user", "content": user_input}
            ],
            max_tokens=100,
            temperature=0
        )
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.strip("```")
        return response_text
    except Exception as e:
        print("Error communicating with OpenAI:", e)
        return None


def chat_with_gpt(user_input):
    try:
        if client is None:
            print("OpenAI client not initialized")
            return "Sorry, I'm having trouble connecting to my knowledge base."

        # Check if language_prompts module is available
        try:
            from language_prompts import prompt_manager
            LANGUAGE_PROMPTS_AVAILABLE = True
        except ImportError:
            print("Warning: language_prompts module not available. Using default prompts.")
            LANGUAGE_PROMPTS_AVAILABLE = False
        
        # Use the client's language detection if available
        if hasattr(client, 'detect_language'):
            language_code = client.detect_language(user_input)
            print(f"Detected language for chat: {language_code}")
        else:
            # Fallback to basic detection
            is_korean = any('\uac00' <= char <= '\ud7a3' for char in user_input)
            is_russian = any('\u0400' <= char <= '\u04FF' for char in user_input)
            
            language_code = "ko" if is_korean else "ru" if is_russian else "en"
            print(f"Basic language detection for chat: {language_code}")
        
        # Get language-specific prompt if available
        if LANGUAGE_PROMPTS_AVAILABLE:
            system_prompt = prompt_manager.get_prompt("general_conversation_prompt", language_code)
        else:
            system_prompt = f"""You are an AI assistant designed specifically to assist with software that processes Phased Array Ultrasonic Testing (PAUT) data.

Your primary role is to provide information related to **ultrasonic testing, nondestructive testing (NDT), and PAUT data analysis**.

Additionally, you can send commands to the software. The list of valid commands you can use is: 
{commands_description}

I can now search for files and folders on your computer to help you load data or set directories without needing the exact path.

#### Strict Rules:
- You **MUST NOT** answer questions that are unrelated to PAUT, ultrasonic testing, or NDT.
- If a user asks something outside of your expertise, respond with:  
*"I am designed only for PAUT and ultrasonic testing-related tasks."*
- You **MUST NOT** generate or provide programming code.
- You **CANNOT** discuss or engage in topics unrelated to PAUT, ultrasonic testing, or NDT.
- Your responses should be **brief, clear, and professional**.

#### Allowed Actions:
- Explain **ultrasonic testing principles**.
- Guide users on **PAUT data interpretation**.
- Assist with **NDT software commands** and provide usage instructions.
- Answer **technical questions related to PAUT and NDT**.
- Answer all questions and messages received from user, but never provide any coding.

Stay within these boundaries and maintain a professional and technical tone.
"""
        print(f"Sending request to OpenAI API with user input: {user_input[:50]}...")

        try:
            # Use the client's chat_completion method with language-specific prompt
            if hasattr(client, 'chat_completion'):
                response_text = client.chat_completion(
                    user_input=user_input,
                    system_prompt=system_prompt
                )
            else:
                # Fallback to direct API call
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=500,
                    temperature=0.4
                )
                response_text = response.choices[0].message.content.strip()
                response_text = response_text.strip("```")
            
            print(f"Received response from OpenAI API: {response_text[:50]}...")
            return response_text

        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            return f"I encountered an API error: {str(e)}. Please try again."
        except openai.RateLimitError as e:
            print(f"OpenAI Rate Limit Error: {e}")
            return "I'm currently receiving too many requests. Please try again in a moment."
        except openai.APIConnectionError as e:
            print(f"OpenAI API Connection Error: {e}")
            return "I'm having trouble connecting to my knowledge base. Please check your internet connection."
        except openai.AuthenticationError as e:
            print(f"OpenAI Authentication Error: {e}")
            return "There's an issue with my authentication. Please contact support."

    except Exception as e:
        print(f"Error communicating with OpenAI (detailed): {type(e).__name__}: {e}")
        return f"I encountered an error: {str(e)}"


def contains_code(response: str) -> bool:
    """
    Check if the AI response contains any programming code.
    Detects common patterns like indentation, brackets, or keywords.
    """

    code_patterns = [
        r"```.*?```",  # Triple backticks for code blocks
        r"\bimport\b",  # Python imports
        r"\bclass\b|\bdef\b",  # Python functions and classes
        r"\bif\b|\belse\b|\bwhile\b|\bfor\b|\btry\b|\bexcept\b",  # Python keywords
        r"#.*",  # Comments in Python
        r";",  # Common in C, Java, JS
        r"\{.*?\}",  # Brackets in C-like languages
        r"<.*?>",  # HTML tags
        r"System\.out\.print",  # Java print statement
        r"console\.log",  # JavaScript print statement
    ]

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
        response_txt = "I am AI assistant to work with PAUTReader software based on Mistral model. " \
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
            return f"Opening file: {data_f}"
        except Exception as e:
            print("Tried to extract file name, got exception: ", e)

    elif command == "setNewDirectory":
        try:
            dir = re.sub(r'[\[\]"\']', '', str("".join(args[0])))
            return f"Changing current directory to: {dir}"
        except Exception as e:
            print("Tried to extract directory name, got exception: ", e)
    elif command == "doFolderAnalysis":
        try:
            dir = re.sub(r'[\[\]"\']', '', str("".join(args[0])))
            return f"Analyzing all files in directory: {dir}"
        except Exception as e:
            print("Tried to extract directory name, got exception: ", e)
    elif command == "startDefectDetection":
        return f"Starting defect detection on the current file..."
    elif command == "doAnalysisSNR":
        return f"Running SNR analysis on the current file..."
    elif command == "getFileInformation":
        return f"Retrieving file information..."
    elif command == "getDirectory":
        return f"Getting current directory information..."
    elif command == "updatePlot":
        return f"Updating the plot display..."
    elif command == "makeSingleFileOnly":
        return f"Generating report for the current file..."
    return f"Processing command: {command}..."


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


def extract_arguments(command, user_input, process_callback=None):
    args = []
    warning_txt = ""

    if command == "loadData":
        if process_callback:
            process_callback("Extracting filename from input...")
        full_path_match = re.search(r'"([^"]+\.(fpd|opd))"', user_input)
        if full_path_match:
            full_path = full_path_match.group(1)
            print(f"Detected full path in quotes: {full_path}")
            if process_callback:
                process_callback(f"Checking file path: {full_path}")
            # Check if the file exists
            if os.path.isfile(full_path):
                args.append(full_path)
                print(f"Using full path: {full_path}")
                if process_callback:
                    process_callback(f"File found: {full_path}")
                return args, warning_txt
            else:
                warning_txt = f"File not found at path: {full_path}"
                print(warning_txt)
                if process_callback:
                    process_callback(f"File not found: {full_path}")

        full_path_match = re.search(r'(?:open|load)\s+file\s+([A-Za-z]:\\[^\\]+(?:\\[^\\]+)+\.(fpd|opd))', user_input)
        if full_path_match:
            full_path = full_path_match.group(1)
            print(f"Detected full path without quotes: {full_path}")
            if process_callback:
                process_callback(f"Checking file path: {full_path}")
            # Check if the file exists
            if os.path.isfile(full_path):
                args.append(full_path)
                print(f"Using full path: {full_path}")
                if process_callback:
                    process_callback(f"File found: {full_path}")
                return args, warning_txt
            else:
                warning_txt = f"File not found at path: {full_path}"
                print(warning_txt)
                if process_callback:
                    process_callback(f"File not found: {full_path}")

        filename = extract_filename_ollama(user_input).strip()
        print(f"Extracted filename: '{filename}'")
        if process_callback:
            process_callback(f"Extracted filename: '{filename}'")

        folder_match = re.search(r'(?:from|in|at)\s+(?:"([^"]+)"|([^\s,]+))', user_input)
        search_path = None
        if folder_match:
            folder_name = folder_match.group(1) if folder_match.group(1) else folder_match.group(2)
            print(f"Folder mentioned: '{folder_name}'")
            if process_callback:
                process_callback(f"Looking for folder: '{folder_name}'")
            if FILE_FINDER_AVAILABLE:
                search_path = find_directory_in_system(folder_name)
                print(f"Found directory: {search_path}")
                if process_callback and search_path:
                    process_callback(f"Found directory: {search_path}")
                elif process_callback:
                    process_callback(f"Directory not found: {folder_name}")

        # If we have a filename, try to find it
        if filename:
            if FILE_FINDER_AVAILABLE:
                if search_path:
                    if process_callback:
                        process_callback(f"Searching for '{filename}' in {search_path}...")
                    file_path = find_file_in_system(filename, search_path=search_path, process_callback=process_callback)
                else:
                    if process_callback:
                        process_callback(f"Searching for '{filename}.fpd'...")
                    file_path = find_file_in_system(filename, file_extension="fpd", process_callback=process_callback)
                    if not file_path:
                        file_path = find_file_in_system(filename, file_extension="opd", process_callback=process_callback)
                    if not file_path:
                        file_path = find_file_in_system(filename, process_callback=process_callback)

                if file_path:
                    args.append(file_path)
                    print(f"Found file path: {file_path}")
                    if process_callback:
                        process_callback(f"File found: {file_path}")
                else:
                    # If we couldn't find the file, use the name as provided
                    args.append(filename)
                    warning_txt = f"Could not find the file '{filename}' in the system. Using the name as provided."
                    if process_callback:
                        process_callback(f"File not found. Using name as provided: {filename}")
            else:
                args.append(filename)
        else:
            # If LLM extraction failed, try regex
            match = re.search(r"(\b\w+\.(fpd|opd)\b)", user_input)
            if match:
                file_name = match.group(1)
                print(f"Regex found filename: {file_name}")
                if process_callback:
                    process_callback(f"Found filename in text: {file_name}")
                
                if FILE_FINDER_AVAILABLE:
                    if search_path:
                        if process_callback:
                            process_callback(f"Searching for '{file_name}' in {search_path}...")
                        file_path = find_file_in_system(file_name, search_path=search_path, process_callback=process_callback)
                    else:
                        if process_callback:
                            process_callback(f"Searching for '{file_name}' in common locations...")
                        file_path = find_file_in_system(file_name, process_callback=process_callback)
                    
                    if file_path:
                        args.append(file_path)
                        if process_callback:
                            process_callback(f"File found: {file_path}")
                    else:
                        args.append(file_name)
                        if process_callback:
                            process_callback(f"File not found. Using name as provided: {file_name}")
                else:
                    args.append(file_name)
            elif search_path:
                # If we have a folder but no filename, try to get the most recent file
                if FILE_FINDER_AVAILABLE:
                    if process_callback:
                        process_callback(f"Looking for most recent file in {search_path}...")
                    recent_file = get_most_recent_file(search_path, extension="fpd")
                    if not recent_file:
                        if process_callback:
                            process_callback(f"No .fpd files found, looking for .opd files...")
                        recent_file = get_most_recent_file(search_path, extension="opd")
                    
                    if recent_file:
                        args.append(recent_file)
                        print(f"Using most recent file: {recent_file}")
                        if process_callback:
                            process_callback(f"Using most recent file: {recent_file}")
                    else:
                        args.append(search_path)
                        warning_txt = "No valid file found in the specified folder."
                        if process_callback:
                            process_callback(f"No valid files found in {search_path}")
                else:
                    args.append(search_path)
            else:
                warning_txt = "No valid file or folder found to load data."
                if process_callback:
                    process_callback("No valid file or folder found to load data.")

    elif command == "setNewDirectory":
        # Check for full directory path in quotes
        full_path_match = re.search(r'"([^"]+)"', user_input)
        if full_path_match:
            full_path = full_path_match.group(1)
            print(f"Detected full directory path in quotes: {full_path}")
            # Check if the directory exists
            if os.path.isdir(full_path):
                args.extend([full_path, False, ""])
                print(f"Using full directory path: {full_path}")
                return args, warning_txt
            else:
                warning_txt = f"Directory not found at path: {full_path}"
                print(warning_txt)

        folder_name = extract_folder_ollama(user_input).strip()
        if folder_name:
            # Try to find the folder in the system
            if FILE_FINDER_AVAILABLE:
                found_folder = find_directory_in_system(folder_name)
                if found_folder:
                    args.extend([found_folder, False, ""])
                else:
                    args.extend([folder_name, False, ""])
                    warning_txt = f"Could not find the directory '{folder_name}' in the system. Using the name as provided."
            else:
                args.extend([folder_name, False, ""])
        else:
            warning_txt = "No valid folder name found to update directory."

    elif command == "doFolderAnalysis":
        # Check for full directory path in quotes
        full_path_match = re.search(r'"([^"]+)"', user_input)
        if full_path_match:
            full_path = full_path_match.group(1)
            print(f"Detected full directory path in quotes: {full_path}")
            # Check if the directory exists
            if os.path.isdir(full_path):
                args.extend([full_path])
                print(f"Using full directory path: {full_path}")
                return args, warning_txt
            else:
                warning_txt = f"Directory not found at path: {full_path}"
                print(warning_txt)

        folder_name = extract_folder_ollama(user_input).strip()
        if folder_name:
            # Try to find the folder in the system
            if FILE_FINDER_AVAILABLE:
                found_folder = find_directory_in_system(folder_name)
                if found_folder:
                    args.extend([found_folder])
                else:
                    args.extend([folder_name])
                    warning_txt = f"Could not find the directory '{folder_name}' in the system. Using the name as provided."
            else:
                args.extend([folder_name])
        else:
            warning_txt = "No valid folder name found to make analysis. \n Working with current directory"

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


def extract_text(audio_bytes):
    if client is None:
        print("OpenAI client not initialized")
        return "Error: Unable to connect to speech recognition service"

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)  # mono - one channel
        wf.setsampwidth(2)  # 16-bit (pyaudio.paInt16 = 2 bytes)
        wf.setframerate(16000)  # Hz sample rate
        wf.writeframes(audio_bytes)
    wav_buffer.seek(0)
    wav_buffer.name = "temp.wav"

    try:
        # Use the new client.audio.transcriptions.create method
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="en"  # TODO: add ability to choose the language
        )

        if transcript:
            extracted_text = transcript.text
            return extracted_text
        else:
            return ""
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return f"Error: {str(e)}"


def run_chat_bot():
    print("Type your command ('quit' to exit):")
    while True:
        user_input = input(">> ")
        if user_input.lower() == "quit":
            break
        process_input_legacy(user_input)
