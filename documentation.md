# AI Assistant for PAUT Data Analysis - Technical Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Command Processing System](#command-processing-system)
5. [Language Support](#language-support)
6. [API Integration](#api-integration)
7. [User Interface](#user-interface)
8. [Voice Recognition](#voice-recognition)
9. [File Management](#file-management)
10. [Extending the System](#extending-the-system)
11. [Implementing RAG](#implementing-rag)

## Introduction

This AI assistant is designed to help users interact with Phased Array Ultrasonic Testing (PAUT) data analysis software. It provides a natural language interface for executing commands, answering questions about ultrasonic testing, and guiding users through data analysis workflows.

The assistant uses a combination of:
- Natural language processing to understand user intent
- Command detection and extraction
- API integration with PAUT software
- Voice recognition for hands-free operation
- Multi-language support

## System Architecture

The system follows a modular architecture with these main components:

1. **GUI Layer**: Handles user interaction through a chat interface
2. **NLP Layer**: Processes natural language input to detect commands and extract parameters
3. **Command Processing Layer**: Executes commands through API calls to the PAUT software
4. **Knowledge Layer**: Provides responses to questions using LLM integration
5. **Voice Recognition Layer**: Converts speech to text for hands-free operation
6. **File Management Layer**: Handles file search and directory operations

### Data Flow

1. User inputs text or voice command
2. Input is processed to detect language and intent
3. If a command is detected, it's executed through the API
4. If a question is detected, it's sent to the LLM for a response
5. Results are displayed in the chat interface

## Core Components

### Main Application (GUI_NLP_improved.py)

The main application file that initializes the GUI and coordinates between different components. It handles:
- Chat interface management
- User input processing
- Command execution
- Response display
- Voice recognition integration

### AI Functions (ai_functions_keeper_updated.py)

Contains the core NLP functionality:
- Command detection using LLM
- Parameter extraction
- Command execution
- Chat functionality for non-command queries
- Language detection

### OpenAI Client (openai_client.py)

Manages communication with OpenAI's API:
- Chat completions for answering questions
- Command extraction
- Language detection
- Conversation history management
- Token usage optimization

### Command Processing (command_process.py)

Handles the execution of commands through API calls:
- Defines command endpoints
- Formats API requests
- Processes API responses
- Error handling

### Language Prompts (language_prompts.py)

Manages language-specific prompts:
- Loads prompts for different languages
- Provides appropriate prompts based on detected language
- Reduces token usage by using language-specific prompts

### File Finder (file_finder.py)

Provides file search functionality:
- Fuzzy matching for file names
- Directory traversal
- File type filtering
- Recent file detection

## Command Processing System

The system supports the following commands:

1. **loadData**: Opens or loads a data file for analysis
2. **updatePlot**: Refreshes or updates the current plot/scan visualization
3. **getFileInformation**: Displays metadata about the currently opened file
4. **getDirectory**: Shows the current working directory
5. **doAnalysisSNR**: Performs signal quality analysis
6. **startDefectDetection**: Runs AI neural network to detect flaws or defects
7. **setNewDirectory**: Changes the current working directory
8. **makeSingleFileOnly**: Generates a report for the current file
9. **doFolderAnalysis**: Analyzes all files in a specified folder

### Command Detection Process

1. User input is analyzed using language detection
2. Language-specific prompts are used to extract commands
3. If a command is detected, parameters are extracted
4. The command is executed through the API
5. Results are displayed to the user

## Language Support

The system supports multiple languages through the language_prompts module:

### Supported Languages
- English (default)
- Korean
- (Extensible to other languages)

### Language Detection

The system uses the `langdetect` library to identify the language of user input. For fallback, it also uses character range detection for Korean and Russian.

### Language-Specific Prompts

For each supported language, the system maintains separate prompts for:
- Command descriptions
- Command extraction
- General conversation
- File path extraction
- Folder path extraction

This approach reduces token usage and improves accuracy for non-English languages.

## API Integration

The system integrates with PAUT software through a REST API:

### API Endpoints

- `/api/app/loadData`: Load a data file
- `/api/app/updatePlot`: Update the visualization
- `/api/app/getFileInformation`: Get file metadata
- `/api/app/getDirectory`: Get current directory
- `/api/app/setNewDirectory`: Change directory
- `/api/app/startSNRAnalysis`: Run SNR analysis
- `/api/app/startDefectDetection`: Run defect detection
- `/api/app/makeSingleFileOnly`: Generate report
- `/api/app/doFolderAnalysis`: Analyze folder

### Request Methods

The system uses appropriate HTTP methods for each endpoint:
- GET for retrieving data
- POST for actions that modify state

## User Interface

The user interface is built with PyQt6 and features:

### Components
- Chat message area with bubbles for user and assistant messages
- Text input field
- Send button
- Voice recording button
- Language selection menu

### Features
- Responsive message bubbles that adapt to window size
- Process message display for long-running operations
- Chat history persistence
- Clear chat functionality
- Voice recording with visual feedback

## Voice Recognition

The system includes voice recognition capabilities:

### Features
- Real-time speech-to-text conversion
- Support for multiple languages
- Visual feedback during recording
- Automatic command processing from voice input

### Implementation
- Uses PyAudio for audio capture
- Integrates with OpenAI Whisper for transcription
- Handles different audio formats and sample rates

## File Management

The file management system provides:

### Features
- Fuzzy file name matching
- Directory traversal
- File extension filtering
- Recent file detection
- Current directory prioritization

### Search Algorithm
1. First searches in the application's current directory
2. Then looks for exact matches in other locations
3. Finally performs fuzzy matching if needed

## Extending the System

### Adding New Commands

To add a new command:
1. Define the command endpoint in `command_process.py`
2. Add the command to the command list in `prompts.py`
3. Update the command descriptions for all supported languages
4. Add any special handling in `ai_functions_keeper_updated.py`

### Adding New Languages

To add support for a new language:
1. Create language-specific prompts in the language_prompts module
2. Add detection support if needed
3. Test with sample inputs in the new language

## Implementing RAG

To implement Retrieval-Augmented Generation (RAG) in this system:

### Required Components

1. **Document Processing Pipeline**
   - Create a module to ingest and process documents
   - Implement chunking strategies for different document types
   - Add support for extracting metadata

2. **Vector Database Integration**
   - Integrate with a vector database (like Chroma, FAISS, or Pinecone)
   - Implement embedding creation using OpenAI's embedding models
   - Create storage and retrieval functions

3. **Retrieval System**
   - Develop query processing to convert user questions to embeddings
   - Implement similarity search to find relevant documents
   - Add relevance scoring and filtering

4. **Context Augmentation**
   - Create a system to combine retrieved information with user queries
   - Implement prompt engineering to effectively use retrieved context
   - Handle context window limitations

5. **Response Generation**
   - Modify the existing LLM integration to use augmented prompts
   - Add citation and source tracking
   - Implement fallback mechanisms when no relevant information is found

### Implementation Steps

1. Create a new `rag_system.py` module with classes for:
   - Document processing
   - Embedding creation
   - Vector storage
   - Retrieval
   - Context augmentation

2. Modify `openai_client.py` to:
   - Accept retrieved context in prompts
   - Handle larger context windows
   - Include source information in responses

3. Create a document ingestion pipeline that:
   - Accepts various document formats
   - Processes and chunks documents
   - Creates and stores embeddings

4. Update the UI to:
   - Show source information
   - Allow document uploading
   - Provide feedback on retrieval quality

5. Implement multilingual support in the RAG system:
   - Use multilingual embedding models
   - Handle cross-lingual retrieval
   - Process documents in multiple languages

### Considerations for Multilingual RAG

- Use embedding models that support multiple languages (like multilingual-e5)
- Consider language-specific chunking strategies
- Implement language detection for documents
- Store language information as metadata
- Test retrieval quality across languages

By implementing these components, the system will be able to retrieve relevant information from a knowledge base and use it to generate more accurate and informative responses to user queries.
