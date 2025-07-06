import os
import json
from typing import List, Dict, Any, Optional, Callable, Generator
import openai
import tiktoken

# Import language prompt manager
try:
    from language_prompts import prompt_manager, detect_language
    LANGUAGE_PROMPTS_AVAILABLE = True
except ImportError:
    print("Warning: language_prompts module not available. Using default prompts.")
    LANGUAGE_PROMPTS_AVAILABLE = False

class OpenAIClient:
    """
    Enhanced OpenAI client for the AI assistant with language detection
    """
    def __init__(self):
        # Load API key
        try:
            with open(os.path.join(os.path.dirname(__file__), 'key.txt'), 'r') as file:
                api_key = file.read().strip()
                openai.api_key = api_key
        except Exception as e:
            print(f"Error loading API key: {e}")
            
        # Default models
        self.chat_model = "gpt-4-turbo"  # Use gpt-4-turbo instead of gpt-4o for compatibility
        self.command_model = "gpt-3.5-turbo"  # Use gpt-3.5-turbo instead of gpt-4o-mini
        
        # Message history
        self.conversation_history = []
        self.max_history_tokens = 4000  # Limit history to avoid token limits
        
        # Current language (default to English)
        self.current_language = "en"
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")  # Use gpt-4 tokenizer
        except Exception as e:
            print(f"Error initializing tokenizer: {e}")
            # Fallback to cl100k_base tokenizer which works for most models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text and update current_language
        
        Args:
            text: Input text
            
        Returns:
            Language code (e.g., 'en', 'ko', 'es')
        """
        if LANGUAGE_PROMPTS_AVAILABLE:
            # Use the centralized language detection and update prompt manager
            self.current_language = prompt_manager.set_current_language(text)
        else:
            # Fallback to direct detection
            try:
                self.current_language = detect_language(text)
            except:
                # If detect_language is not available, use basic detection
                is_korean = any('\uac00' <= char <= '\ud7a3' for char in text)
                is_russian = any('\u0400' <= char <= '\u04FF' for char in text)
                
                self.current_language = "ko" if is_korean else "ru" if is_russian else "en"
        
        print(f"Language detected: {self.current_language}")
        return self.current_language
    
    def extract_commands(self, user_input: str, commands_description: str = None) -> str:
        """
        Extract commands from user input using the command model
        
        Args:
            user_input: User input text
            commands_description: Optional commands description (if not provided, will use language-specific one)
            
        Returns:
            Extracted command name(s) or empty string
        """
        try:
            # Detect language and update current_language
            language_code = self.detect_language(user_input)
            
            # Get language-specific prompt if available
            if LANGUAGE_PROMPTS_AVAILABLE:
                if commands_description is None:
                    commands_description = prompt_manager.get_prompt("commands_description", language_code)
                
                # Get the command extraction prompt for the detected language
                command_extraction_prompt = prompt_manager.get_prompt("command_name_extraction", language_code)
                
                # Format the prompt with commands description
                system_prompt = command_extraction_prompt.format(commands_description=commands_description)
                print(f"Using {language_code} prompt for command extraction")
            else:
                # Fallback to default prompt
                system_prompt = f"""You are an AI assistant that **ONLY extracts command names** from user input.
                
                ### **RULES:**
                1. If the user's request **matches one of the following commands**, **return ONLY the command name** or a comma-separated list of command names with **no additional text**.
                2. If the user's input **does NOT match any command**, **return an empty string (`""`)**. **DO NOT explain. DO NOT respond with any text. DO NOT add any formatting.**
                3. **COMMAND LIST:**
                {commands_description}
                
                **USER INPUT:** "{user_input}"
                
                **YOUR RESPONSE (ONLY command name OR empty string):**
                """
            
            response = openai.ChatCompletion.create(
                model=self.command_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=50,
                temperature=0
            )
            
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error extracting commands: {e}")
            return ""
    
    def chat_completion(self, 
                       user_input: str, 
                       system_prompt: str = None,
                       stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """
        Get chat completion with optional streaming and language detection
        
        Args:
            user_input: User input text
            system_prompt: Optional system prompt (if not provided, will use language-specific one)
            stream_handler: Optional handler for streaming responses
            
        Returns:
            Generated response text
        """
        try:
            # Detect language if not already done for this input
            language_code = self.detect_language(user_input)
            
            # Get language-specific prompt if available and not explicitly provided
            if system_prompt is None and LANGUAGE_PROMPTS_AVAILABLE:
                system_prompt = prompt_manager.get_prompt("general_conversation_prompt", language_code)
                print(f"Using {language_code} prompt for conversation")
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Trim history if needed
            self._trim_conversation_history()
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history)
            
            if stream_handler:
                # Streaming mode
                full_response = ""
                
                stream = openai.ChatCompletion.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.get('content'):
                        content = chunk.choices[0].delta.get('content', '')
                        full_response += content
                        stream_handler(content)
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": full_response})
                return full_response
            else:
                # Non-streaming mode
                response = openai.ChatCompletion.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=0.7
                )
                
                response_text = response.choices[0].message['content']
                
                # Add assistant response to history
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text
                
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}"
    
    def _trim_conversation_history(self):
        """
        Trim conversation history to stay within token limits
        """
        if not self.conversation_history:
            return
            
        # Count tokens in the current history
        total_tokens = sum(len(self.tokenizer.encode(msg["content"])) for msg in self.conversation_history)
        
        # Remove oldest messages until we're under the limit
        while total_tokens > self.max_history_tokens and len(self.conversation_history) > 1:
            removed_msg = self.conversation_history.pop(0)
            total_tokens -= len(self.tokenizer.encode(removed_msg["content"]))
    
    def clear_conversation_history(self):
        """
        Clear the conversation history
        """
        self.conversation_history = []
