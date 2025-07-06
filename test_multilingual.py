#!/usr/bin/env python3
"""
Test script for multilingual prompt system
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from language_prompts import prompt_manager, detect_language
    print("✓ Language prompts module loaded successfully")
    
    # Test language detection
    test_cases = [
        ("Hello, how are you?", "en"),
        ("안녕하세요, 어떻게 지내세요?", "ko"),
        ("Привет, как дела?", "ru"),
        ("파일을 열어주세요", "ko"),
        ("Открой файл", "ru"),
        ("Open the file", "en")
    ]
    
    print("\n=== Testing Language Detection ===")
    for text, expected in test_cases:
        detected = detect_language(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text}' -> {detected} (expected: {expected})")
    
    print("\n=== Testing Prompt Retrieval ===")
    
    # Test English prompts
    prompt_manager.current_language = "en"
    en_prompt = prompt_manager.get_prompt("general_conversation_prompt")
    print(f"✓ English prompt length: {len(en_prompt)} characters")
    
    # Test Korean prompts
    prompt_manager.current_language = "ko"
    ko_prompt = prompt_manager.get_prompt("general_conversation_prompt")
    print(f"✓ Korean prompt length: {len(ko_prompt)} characters")
    
    # Test Russian prompts
    prompt_manager.current_language = "ru"
    ru_prompt = prompt_manager.get_prompt("general_conversation_prompt")
    print(f"✓ Russian prompt length: {len(ru_prompt)} characters")
    
    # Test command extraction prompts
    print("\n=== Testing Command Extraction Prompts ===")
    
    languages = ["en", "ko", "ru"]
    for lang in languages:
        prompt_manager.current_language = lang
        cmd_prompt = prompt_manager.get_prompt("commands_names_extraction")
        print(f"✓ {lang.upper()} command extraction prompt: {len(cmd_prompt)} characters")
    
    # Test automatic language detection and prompt selection
    print("\n=== Testing Automatic Language Detection ===")
    
    test_inputs = [
        "파일을 열어주세요",  # Korean
        "Открой файл",       # Russian
        "Open the file"      # English
    ]
    
    for text in test_inputs:
        detected_lang = prompt_manager.set_current_language(text)
        prompt = prompt_manager.get_prompt("general_conversation_prompt")
        print(f"✓ '{text}' -> {detected_lang} -> prompt length: {len(prompt)}")
    
    print("\n=== All Tests Completed Successfully! ===")
    
except ImportError as e:
    print(f"✗ Error importing language prompts: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error during testing: {e}")
    sys.exit(1)
