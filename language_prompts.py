"""
Language-specific prompts for the AI assistant.
This module provides functionality to:
1. Store different prompts for different languages
2. Retrieve the appropriate prompt based on detected language
3. Optimize token usage by using language-specific prompts
"""
import os
import json
from typing import Dict, Any, Optional

# Constants
PROMPTS_DIR = "language_prompts"
DEFAULT_LANGUAGE = "en"

# Ensure prompts directory exists
os.makedirs(PROMPTS_DIR, exist_ok=True)

class LanguagePromptManager:
    """Manager for language-specific prompts"""
    
    def __init__(self):
        """Initialize the language prompt manager"""
        self.prompts = {}
        self.load_prompts()
    
    def load_prompts(self):
        """Load all language prompts from the prompts directory"""
        try:
            # Load default prompts first
            self._load_default_prompts()
            
            # Load custom prompts from files
            if os.path.exists(PROMPTS_DIR):
                for filename in os.listdir(PROMPTS_DIR):
                    if filename.endswith('.json'):
                        language_code = os.path.splitext(filename)[0]
                        file_path = os.path.join(PROMPTS_DIR, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.prompts[language_code] = json.load(f)
                            print(f"Loaded prompts for language: {language_code}")
        except Exception as e:
            print(f"Error loading language prompts: {e}")
    
    def _load_default_prompts(self):
        """Load default English prompts"""
        from prompts import (
            commands_description,
            command_name_extraction,
            commands_names_extraction,
            general_conversation_prompt,
            file_path_extraction_prompt,
            folder_path_extraction_prompt
        )
        
        # Store default English prompts
        self.prompts[DEFAULT_LANGUAGE] = {
            "commands_description": commands_description,
            "command_name_extraction": command_name_extraction,
            "commands_names_extraction": commands_names_extraction,
            "general_conversation_prompt": general_conversation_prompt,
            "file_path_extraction_prompt": file_path_extraction_prompt,
            "folder_path_extraction_prompt": folder_path_extraction_prompt
        }
    
    def get_prompt(self, prompt_type: str, language_code: str = DEFAULT_LANGUAGE) -> str:
        """
        Get a specific prompt for the specified language
        
        Args:
            prompt_type: Type of prompt to retrieve
            language_code: Language code (e.g., 'en', 'ko', 'es')
            
        Returns:
            The prompt text for the specified language or default language if not found
        """
        # If language not available, fall back to default
        if language_code not in self.prompts:
            language_code = DEFAULT_LANGUAGE
        
        # If prompt type not available in this language, fall back to default
        if prompt_type not in self.prompts[language_code]:
            return self.prompts[DEFAULT_LANGUAGE].get(prompt_type, "")
        
        return self.prompts[language_code][prompt_type]
    
    def add_prompt(self, prompt_type: str, prompt_text: str, language_code: str):
        """
        Add or update a prompt for a specific language
        
        Args:
            prompt_type: Type of prompt to add
            prompt_text: The prompt text
            language_code: Language code (e.g., 'en', 'ko', 'es')
        """
        # Initialize language if not exists
        if language_code not in self.prompts:
            self.prompts[language_code] = {}
        
        # Add/update prompt
        self.prompts[language_code][prompt_type] = prompt_text
        
        # Save to file
        self._save_language_prompts(language_code)
    
    def _save_language_prompts(self, language_code: str):
        """
        Save prompts for a specific language to file
        
        Args:
            language_code: Language code to save
        """
        try:
            if language_code in self.prompts:
                file_path = os.path.join(PROMPTS_DIR, f"{language_code}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.prompts[language_code], f, ensure_ascii=False, indent=2)
                print(f"Saved prompts for language: {language_code}")
        except Exception as e:
            print(f"Error saving language prompts: {e}")

# Example Korean prompts
korean_prompts = {
    "commands_description": """
"loadData": 데이터 파일을 분석을 위해 열거나 로드합니다. 사용자가 특정 파일을 열고 싶을 때 사용됩니다.
예: "test_data.fpd 파일을 열어줘" 또는 "최신 스캔 데이터를 로드해"

"updatePlot": 현재 플롯/스캔 시각화를 새로 고치거나 업데이트합니다.
예: "플롯을 새로 고쳐" 또는 "시각화를 업데이트해"

"getFileInformation": 현재 열린 파일에 대한 메타데이터를 표시하기 위해 파일 정보 창을 엽니다.
예: "파일 세부 정보를 보여줘" 또는 "이 파일에 대한 정보가 뭐야?"

"getDirectory": 응용 프로그램이 파일을 찾고 있는 현재 작업 디렉토리(폴더)를 표시합니다.
예: "현재 폴더가 뭐야?" 또는 "작업 디렉토리를 보여줘"

"doAnalysisSNR": 신호 품질 분석을 수행하기 위해 SNR(신호 대 잡음비) 분석 창을 엽니다.
예: "SNR 분석을 실행해" 또는 "신호 대 잡음비를 분석해"

"startDefectDetection": AI 신경망을 실행하여 데이터에서 결함이나 결점을 감지하고 C-스캔 플롯에 표시합니다.
예: "이 스캔에서 결함을 찾아" 또는 "결함 감지를 실행해"

"setNewDirectory": 현재 작업 디렉토리를 다른 폴더로 변경합니다.
예: "디렉토리를 C:/Data로 변경해" 또는 "Documents 폴더로 전환해"

"makeSingleFileOnly": 현재 열린 파일에 대한 분석을 기반으로 보고서를 생성합니다.
예: "이 파일에 대한 보고서를 만들어" 또는 "분석 보고서를 생성해"

"doFolderAnalysis": 지정된 폴더의 모든 파일을 분석하고 종합 보고서를 준비합니다.
예: "Data 폴더의 모든 파일을 분석해" 또는 "스캔 디렉토리에서 배치 분석을 실행해"
""",

    "command_name_extraction": """당신은 위상 배열 초음파 검사(PAUT) 데이터 분석 애플리케이션을 제어하는 데 특화된 AI 어시스턴트입니다.

당신의 임무는 사용자의 입력을 기반으로 어떤 명령을 실행할지 식별하는 것입니다.

사용 가능한 명령:
{commands_description}

규칙:
1. 사용자의 요청이 하나 이상의 명령과 일치하면 쉼표로 구분된 명령 이름만 반환하세요.
2. 사용자의 요청과 일치하는 명령이 없으면 빈 문자열을 반환하세요.
3. 설명, 서식 또는 추가 텍스트를 포함하지 마세요.
4. 정확한 키워드 매칭보다는 사용자의 의도에 집중하세요.

예시:
사용자: "test_scan.fpd 파일을 열어줄래?"
응답: loadData

사용자: "현재 폴더에 무엇이 있는지 확인해야 해"
응답: getDirectory

사용자: "결함 감지를 실행하고 보고서를 작성해"
응답: startDefectDetection,makeSingleFileOnly

사용자: "오늘 기분이 어때?"
응답: 
"""
}

# Create an instance of the manager
prompt_manager = LanguagePromptManager()

# Add Korean prompts
for prompt_type, prompt_text in korean_prompts.items():
    prompt_manager.add_prompt(prompt_type, prompt_text, "ko")
