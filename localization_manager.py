"""
Centralized localization manager for the AI assistant.
Replaces the old language_prompts.py system with proper dictionary-based localization.
"""
import os
import json
from typing import Dict, Any, Optional

class LocalizationManager:
    """Manager for all localized content including prompts and UI text"""
    
    def __init__(self, localization_dir="localization"):
        self.localization_dir = localization_dir
        self.current_language = "en"  # Default language
        self.dictionaries = {}
        self.available_languages = []
        
        # Ensure localization directory exists
        os.makedirs(localization_dir, exist_ok=True)
        
        # Load all available languages
        self.load_all_dictionaries()
    
    def load_all_dictionaries(self):
        """Load all available localization dictionary files"""
        try:
            # Get all JSON files in localization directory
            if os.path.exists(self.localization_dir):
                for filename in os.listdir(self.localization_dir):
                    if filename.startswith("localization-") and filename.endswith(".json"):
                        lang_code = filename.replace("localization-", "").replace(".json", "")
                        self.load_dictionary(lang_code)
                        if lang_code not in self.available_languages:
                            self.available_languages.append(lang_code)
            
            print(f"Loaded localization dictionaries for languages: {self.available_languages}")
        except Exception as e:
            print(f"Error loading localization dictionaries: {e}")
            # Fallback to English only
            self.available_languages = ["en"]
    
    def load_dictionary(self, language_code: str):
        """Load dictionary for a specific language"""
        try:
            file_path = os.path.join(self.localization_dir, f"localization-{language_code}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.dictionaries[language_code] = json.load(f)
                print(f"Loaded localization dictionary for: {language_code}")
            else:
                print(f"Localization dictionary not found: {file_path}")
        except Exception as e:
            print(f"Error loading dictionary for {language_code}: {e}")
    
    def set_language(self, language_code: str):
        """Set the current language"""
        if language_code in self.available_languages:
            self.current_language = language_code
            print(f"Localization language set to: {language_code}")
        else:
            print(f"Language {language_code} not available, using {self.current_language}")
    
    def get_text(self, key: str, language_code: str = None, **kwargs) -> str:
        """
        Get localized text by key
        
        Args:
            key: Text key (e.g., "status.file_loaded", "prompts.general_conversation_prompt")
            language_code: Language code (uses current if None)
            **kwargs: Format parameters for the text
            
        Returns:
            Localized text
        """
        if language_code is None:
            language_code = self.current_language
        
        # Try to get text in requested language
        if language_code in self.dictionaries:
            dictionary = self.dictionaries[language_code]
            
            # Navigate through nested keys (e.g., "status.file_loaded")
            keys = key.split('.')
            current = dictionary
            
            try:
                for k in keys:
                    current = current[k]
                
                # Format text with provided parameters
                if kwargs:
                    return current.format(**kwargs)
                return current
            except (KeyError, TypeError):
                pass
        
        # Fallback to English if key not found
        if language_code != "en" and "en" in self.dictionaries:
            return self.get_text(key, "en", **kwargs)
        
        # Final fallback - return the key itself
        return f"[{key}]"
    
    def get_prompt(self, prompt_type: str, language_code: str = None) -> str:
        """
        Get a localized prompt by type
        
        Args:
            prompt_type: Type of prompt (e.g., "general_conversation_prompt")
            language_code: Language code (uses current if None)
            
        Returns:
            Localized prompt text
        """
        return self.get_text(f"prompts.{prompt_type}", language_code)
    
    def get_status_message(self, message_type: str, language_code: str = None, **kwargs) -> str:
        """
        Get a localized status message
        
        Args:
            message_type: Type of status message (e.g., "file_loaded")
            language_code: Language code (uses current if None)
            **kwargs: Format parameters
            
        Returns:
            Localized status message
        """
        return self.get_text(f"status.{message_type}", language_code, **kwargs)
    
    def get_error_message(self, error_type: str, language_code: str = None, **kwargs) -> str:
        """
        Get a localized error message
        
        Args:
            error_type: Type of error message (e.g., "api_error")
            language_code: Language code (uses current if None)
            **kwargs: Format parameters
            
        Returns:
            Localized error message
        """
        return self.get_text(f"errors.{error_type}", language_code, **kwargs)
    
    def get_suggestion(self, suggestion_type: str, language_code: str = None) -> str:
        """
        Get a localized suggestion message
        
        Args:
            suggestion_type: Type of suggestion (e.g., "run_defect_detection")
            language_code: Language code (uses current if None)
            
        Returns:
            Localized suggestion text
        """
        return self.get_text(f"suggestions.{suggestion_type}", language_code)
    
    def get_ui_text(self, ui_element: str, language_code: str = None, **kwargs) -> str:
        """
        Get localized UI text
        
        Args:
            ui_element: UI element key (e.g., "language_settings")
            language_code: Language code (uses current if None)
            **kwargs: Format parameters
            
        Returns:
            Localized UI text
        """
        return self.get_text(f"ui.{ui_element}", language_code, **kwargs)
    
    def get_command_status(self, command_type: str, language_code: str = None) -> str:
        """
        Get localized command status message
        
        Args:
            command_type: Type of command (e.g., "load_data")
            language_code: Language code (uses current if None)
            
        Returns:
            Localized command status text
        """
        return self.get_text(f"commands.{command_type}", language_code)

# Global localization manager instance
localization_manager = LocalizationManager()

# Compatibility functions for existing code
def detect_language(text: str) -> str:
    """
    Centralized function to detect language from text
    (Kept for compatibility with existing code)
    """
    try:
        import langdetect
        language = langdetect.detect(text)
        return language
    except:
        # Basic detection for common languages if langdetect fails
        is_korean = any('\uac00' <= char <= '\ud7a3' for char in text)
        is_russian = any('\u0400' <= char <= '\u04FF' for char in text)
        is_japanese = any('\u3040' <= char <= '\u30ff' for char in text) or any('\u4e00' <= char <= '\u9FFF' for char in text)
        
        if is_korean:
            return "ko"
        elif is_russian:
            return "ru"
        elif is_japanese:
            return "ja"
        else:
            return "en"

def set_current_language(text: str) -> str:
    """
    Detect and set the current language based on input text
    (Kept for compatibility with existing code)
    """
    language_code = detect_language(text)
    localization_manager.set_language(language_code)
    return language_code
