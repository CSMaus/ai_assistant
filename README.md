# PAUTReader AI Assistant

An AI-powered assistant for controlling and interacting with the PAUTReader application for ultrasonic testing data analysis.

## Features

- Natural language interface to control PAUTReader application
- Voice recognition for hands-free operation
- Advanced AI-powered responses using OpenAI's GPT-4o models
- Command detection and execution via FastAPI
- Chat history persistence
- Streaming responses for better user experience

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ai_assistant.git
cd ai_assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the required Spacy model:
```bash
python -m spacy download en_core_web_md
```

4. Create a `key.txt` file in the root directory with your OpenAI API key:
```
sk-your-openai-api-key
```

## Usage

1. Make sure the PAUTReader application is running and its API server is available at `http://localhost:5000/api/app`

2. Run the AI assistant:
```bash
python GUI_NLP_improved.py
```

3. Interact with the assistant using text or voice commands

### Available Commands

- `loadData`: Opens or loads a data file for analysis
- `updatePlot`: Refreshes or updates the current plot/scan visualization
- `getFileInformation`: Opens the File Information window
- `getDirectory`: Shows the current working directory
- `doAnalysisSNR`: Opens the SNR analysis window
- `startDefectDetection`: Runs defect detection using AI
- `setNewDirectory`: Changes the current working directory
- `makeSingleFileOnly`: Generates a report for the current file
- `doFolderAnalysis`: Analyzes all files in a folder

### Special Commands

- `/quit` or `/exit` or `/bye`: Exit the application
- `/clear`: Clear the chat history

### Voice Recognition

Click the microphone button to start recording, then click it again to stop and process your voice command.

## Project Structure

- `GUI_NLP_improved.py`: Main application with improved UI and functionality
- `openai_client.py`: Enhanced OpenAI client with streaming support
- `voice_recognition.py`: Improved voice recognition using OpenAI Whisper
- `prompts.py`: System prompts for the AI models
- `command_process.py`: Command execution via FastAPI
- `ai_functions_keeper.py`: Legacy functions (for compatibility)

## Troubleshooting

- **Voice recognition not working**: Make sure your microphone is properly connected and you have the required dependencies installed (`sounddevice`)
- **API connection errors**: Verify that the PAUTReader application is running and its API server is accessible
- **OpenAI API errors**: Check your API key and internet connection

## License

This project is licensed under the MIT License - see the LICENSE file for details.
