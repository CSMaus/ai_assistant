import os
import json
from typing import List, Dict, Any, Optional, Callable, Generator
import openai
import tiktoken

class OpenAIClient:
    """
    Enhanced OpenAI client for the AI assistant
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
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")  # Use gpt-4 tokenizer
        except Exception as e:
            print(f"Error initializing tokenizer: {e}")
            # Fallback to cl100k_base tokenizer which works for most models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def extract_commands(self, user_input: str, commands_description: str) -> str:
        """
        Extract commands from user input using the command model
        """
        try:
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
                       system_prompt: str,
                       stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """
        Get chat completion with optional streaming
        """
        try:
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
