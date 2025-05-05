# here I write prompts which NN will yse to extract command, corresponding for this command arguments
# and proces the answer based on input message and results received from SW

# 1. did we find command match to the NL input text?
#   O : search for the arguments if required and put in the queue
#   X : answer to the user using description from "who you are"

commands_description = """
                        "loadData" is command which is used to read or open or load data file which user want to work with;\n
                        "updatePlot" command is used to refresh or update any plot or scan;\n
                        "getFileInformation" command opens File Information window and to display information about opened file;\n
                        "getDirectory" command gives information in which folder or directory on computer we are working now 
                        usually where opened current data file; \n
                        "doAnalysisSNR" command opens new window to do SNR analysis, where SNR means signal to noise ratio analysis; \n
                        "startDefectDetection" command runs AI neural network to make search for flaws or any other defects in data file 
                        and displays them in C-scan plot image; \n
                        "setNewDirectory" command changes the folder or directory where we are working now \n
                        "makeSingleFileOnly" makes report only for ONE SINGLE currently opened file based on its analysis \n
                        "doFolderAnalysis" does analysis of all files in folder and prepares report for them
                        """

command_name_extraction = f'Here is list of commands ith their descriptions:\n {commands_description}\n\n'\
                          'If user ask you to do something which described in command description and it can be done buy any of this command return exact command name with nothing else! \n'\
                          'But if user input just want to talk, or greet you, or ask you to do something but this commands '\
                          'and their description do NOT math the user input, return only empty row. ' \
                          'No words. No explanations. No formatting. No extension. No symbols.'
                          # 'If you cannot find command that match the user request or there is no request in user input '\
                          # 'return empty row. No extra words. No explanations. No formatting.'
commands_names_extraction = f'Here is list of commands ith their descriptions:\n {commands_description}\n\n'\
                          'If user ask you to do something which described in command description '\
                          'and it can be done buy any of this command or combination of commands return exact command name or commands list separated by comma with nothing else! \n'\
                          'But if user input just want to talk, or greet you, or ask you to do something else '\
                          'and non of commands description do NOT math the user input, return only empty row. ' \
                          'No words. No explanations. No formatting. No extension. No symbols.'
                          # 'If you cannot find command that match the user request or there is no request in user input '\
                          # 'return empty row. No extra words. No explanations. No formatting.'

#  Find only one command that match the user input the most and return only exact command from the list!

def extract_folder_ollama(user_input):
    system_prompt = "Extract only the folder name from the input. Return only the folder name. No extra words. No explanations. No formatting."




