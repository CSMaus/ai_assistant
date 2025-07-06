import sys
import os
import json
import time
import re
from queue import Queue
from threading import Thread

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, pyqtSignal, QObject, pyqtSlot

from voice_recognition_improved import VoiceRecognizer
from command_process import execute_command_gui
from prompts import commands_description
from chat_bubble import ChatBubble

# Import localization manager instead of language_prompts
try:
    from localization_manager import localization_manager, detect_language, set_current_language
    LOCALIZATION_AVAILABLE = True
    LANGUAGE_PROMPTS_AVAILABLE = True  # For backward compatibility
except ImportError:
    print("Warning: localization_manager module not available. Trying fallback...")
    LOCALIZATION_AVAILABLE = False
    # Fallback to old system
    try:
        from language_prompts import prompt_manager
        LANGUAGE_PROMPTS_AVAILABLE = True
    except ImportError:
        print("Warning: language_prompts module not available. Using default prompts.")
        LANGUAGE_PROMPTS_AVAILABLE = False

# Import from the updated file
import ai_functions_keeper_updated as ai_functions

# Constants
CHAT_HISTORY_FILE = "chat_history.json"
MAX_HISTORY_ENTRIES = 100
command_queue = Queue()  # Global command queue for compatibility

class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, alignment='right', bubble_color="#F5FAFF", parent=None):
        super().__init__(parent)
        self.alignment = alignment
        self.bubble_color = QtGui.QColor(bubble_color)
        self.setReadOnly(True)
        self.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)

        # disable scrollbars for message text block
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # update the size of text block based on content
        self.document().documentLayout().documentSizeChanged.connect(self.update_size)
        # Use improved width
        self.setFixedWidth(400)
        
        # Set transparent background
        palette = self.palette()
        palette.setBrush(QtGui.QPalette.ColorRole.Base, QtGui.QBrush(QtCore.Qt.GlobalColor.transparent))
        self.setPalette(palette)
        
        # Add padding to the text
        self.document().setDocumentMargin(10)

    def update_size(self):
        doc_height = int(round(self.document().size().height())) + 10
        self.setFixedHeight(doc_height)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QBrush(self.bubble_color))

        doc = self.document()
        margin = doc.documentMargin()
        unitedBlockRect = QtCore.QRectF()

        for b in range(doc.blockCount()):
            block = doc.findBlockByNumber(b)
            blockRect = doc.documentLayout().blockBoundingRect(block)
            layout = block.layout()
            lineRect = QtCore.QRectF()

            for k in range(layout.lineCount()):
                line = layout.lineAt(k)
                lineRect = lineRect.united(line.rect())

            unitedBlockRect = blockRect.united(lineRect)

        # Calculate bubble dimensions with proper padding
        bubble_width = unitedBlockRect.width() + margin * 2
        bubble_height = unitedBlockRect.height() + margin * 2
        
        # Draw the bubble with rounded corners
        if self.alignment == 'right':
            # User message (right side)
            rect = QtCore.QRectF(self.width() - bubble_width - margin, margin, bubble_width, bubble_height)
            radius = 15
            
            path = QtGui.QPainterPath()
            path.moveTo(rect.right() - radius, rect.top())
            path.lineTo(rect.left() + radius, rect.top())
            path.arcTo(rect.left(), rect.top(), radius * 2, radius * 2, 90, 90)
            path.lineTo(rect.left(), rect.bottom() - radius)
            path.arcTo(rect.left(), rect.bottom() - radius * 2, radius * 2, radius * 2, 180, 90)
            path.lineTo(rect.right() - radius, rect.bottom())
            path.arcTo(rect.right() - radius * 2, rect.bottom() - radius * 2, radius * 2, radius * 2, 270, 90)
            path.lineTo(rect.right(), rect.top() + radius)
            path.arcTo(rect.right() - radius * 2, rect.top(), radius * 2, radius * 2, 0, 90)
            path.closeSubpath()
            
            painter.drawPath(path)
        else:
            # Assistant message (left side)
            rect = QtCore.QRectF(margin, margin, bubble_width, bubble_height)
            radius = 15
            
            path = QtGui.QPainterPath()
            path.moveTo(rect.right() - radius, rect.top())
            path.lineTo(rect.left() + radius, rect.top())
            path.arcTo(rect.left(), rect.top(), radius * 2, radius * 2, 90, 90)
            path.lineTo(rect.left(), rect.bottom() - radius)
            path.arcTo(rect.left(), rect.bottom() - radius * 2, radius * 2, radius * 2, 180, 90)
            path.lineTo(rect.right() - radius, rect.bottom())
            path.arcTo(rect.right() - radius * 2, rect.bottom() - radius * 2, radius * 2, radius * 2, 270, 90)
            path.lineTo(rect.right(), rect.top() + radius)
            path.arcTo(rect.right() - radius * 2, rect.top(), radius * 2, radius * 2, 0, 90)
            path.closeSubpath()
            
            painter.drawPath(path)

        super().paintEvent(event)

class ProcessMessageManager(QObject):
    """
    Manages process messages in the chat interface.
    """
    def __init__(self, chat_window):
        super().__init__()
        self.chat_window = chat_window
        self.current_process_label = None
        self.process_id = 0

    @pyqtSlot(str)
    def update_process_message(self, message):
        """Update or create a process message in the chat interface"""
        if self.current_process_label is None:
            # Create a new process label
            self.process_id += 1
            self.current_process_label = QtWidgets.QLabel(message)
            self.current_process_label.setObjectName(f"process_message_{self.process_id}")
            self.current_process_label.setStyleSheet("""
            QLabel {
                    color: #555555;
                     font-style: italic;
                     background-color: transparent;
                     padding: 5px;
                 }""")
            self.chat_window.chat_layout.addWidget(self.current_process_label)
            self.chat_window.auto_scroll_bottom()
        else:
            # Update existing process label
            self.current_process_label.setText(message)
            self.chat_window.auto_scroll_bottom()

    @pyqtSlot()
    def clear_process_message(self):
        """Clear the current process message"""
        if self.current_process_label is not None:
            self.current_process_label.deleteLater()
            self.current_process_label = None


class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Chat")
        self.resize(600, 500)  # Improved size
        
        # Track pending command suggestions
        self.pending_command = None
        self.pending_args = None

        self.process_manager = ProcessMessageManager(self)
        
        # Initialize voice recognizer
        self.voice_recognizer = VoiceRecognizer()
        self.voice_recognizer.transcription_complete.connect(self.handle_transcribed_text)
        self.voice_recognizer.recording_status.connect(self.update_mic_status)
        self.voice_recognizer.error_occurred.connect(self.handle_voice_error)
        # self.voice_recognizer.audio_level.connect(self.update_audio_level)
        
        # Setup UI
        self.setup_ui()
        
        # Command queue and processing thread
        self.listener_thread = Thread(target=self.command_listener, daemon=True)
        self.listener_active = True
        self.listener_thread.start()
        
        # Display welcome message
        QtCore.QTimer.singleShot(0, lambda: self.display_assistant_message("Hello! How can I assist you?"))

    def setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add language selector in the top right
        top_bar = QtWidgets.QHBoxLayout()
        top_bar.addStretch(1)  # Push language selector to the right
        
        # Create language menu button with icon
        self.language_button = QtWidgets.QPushButton()
        self.language_button.setIcon(QtGui.QIcon("icons/AI-Assistant_icon.jpg"))
        self.language_button.setIconSize(QtCore.QSize(48, 48))
        self.language_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
                border-radius: 12px;
            }
        """)
        self.language_button.setToolTip("Language Settings")
        self.language_button.clicked.connect(self.show_language_menu)
        
        top_bar.addWidget(self.language_button)
        main_layout.addLayout(top_bar)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(10)  # Improved spacing

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area)

        # Input area
        input_layout = QtWidgets.QHBoxLayout()
        

        # Text input - improved style
        self.inputField = QtWidgets.QTextEdit()
        self.inputField.setMaximumHeight(80)  # Increased height
        self.inputField.setPlaceholderText("Type your message here...")
        self.inputField.setStyleSheet("""
            QTextEdit {
                border: 1px solid #B4D4FF;
                border-radius: 15px;
                padding: 8px;
                background-color: #F5FAFF;
                color: #111518;
            }
        """)
        self.inputField.installEventFilter(self)

        # Send button - improved style
        self.sendButton = QtWidgets.QPushButton()
        self.sendButton.setIcon(QtGui.QIcon("icons/send.png"))
        self.sendButton.setIconSize(QtCore.QSize(24, 24))
        self.sendButton.setStyleSheet("""
            QPushButton {
                background-color: #91BDF8;
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7BAAF7;
            }
        """)
        self.sendButton.setFixedSize(50, 50)

        # Microphone button - improved style
        self.micButton = QtWidgets.QPushButton()
        self.micButton.setIcon(QtGui.QIcon("icons/mic.png"))
        self.micButton.setIconSize(QtCore.QSize(24, 24))
        self.micButton.setCheckable(True)
        self.micButton.setToolTip("Click to record voice")
        self.micButton.setStyleSheet("""
            QPushButton {
                background-color: #91BDF8;
                border-radius: 15px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #7BAAF7;
            }
            QPushButton:checked {
                background-color: #FF6B6B;
            }
        """)
        self.micButton.setFixedSize(50, 50)
        self.micButton.clicked.connect(self.handle_microphone_button)

        # Add widgets to input layout
        input_layout.addWidget(self.inputField, 1)
        input_layout.addWidget(self.sendButton)
        input_layout.addWidget(self.micButton)
        main_layout.addLayout(input_layout)

        # Connect signals
        self.sendButton.clicked.connect(self.send_message)
        
        # Set application style - explicitly set background to #F5FCFF
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5FCFF;
            }
            QScrollArea {
                background-color: #F5FCFF;
                border: none;
            }
            QWidget#chat_container {
                background-color: #F5FCFF;
            }
        """)
        
        # Set object name for styling
        self.chat_container.setObjectName("chat_container")
        
        # Explicitly set background colors for all widgets to ensure they're not system-defined
        central_widget.setStyleSheet("background-color: #F5FCFF;")
        self.scroll_area.setStyleSheet("background-color: #F5FCFF;")
        self.chat_container.setStyleSheet("background-color: #F5FCFF;")
        
        # Force the background color to be applied
        central_widget.setAutoFillBackground(True)
        self.scroll_area.setAutoFillBackground(True)
        self.chat_container.setAutoFillBackground(True)
        
        # Set palette colors as well to ensure background is properly set
        palette = QtGui.QPalette()
        background_color = QtGui.QColor("#F5FCFF")
        palette.setColor(QtGui.QPalette.ColorRole.Window, background_color)
        palette.setColor(QtGui.QPalette.ColorRole.Base, background_color)
        
        self.setPalette(palette)
        central_widget.setPalette(palette)
        self.scroll_area.setPalette(palette)
        self.chat_container.setPalette(palette)

    def show_language_menu(self):
        """Show the language selection menu for voice recognition and prompts"""
        menu = QtWidgets.QMenu(self)

        # Create submenu for voice recognition
        voice_menu = menu.addMenu("Voice Recognition")
        
        # Create submenu for prompt language
        if LANGUAGE_PROMPTS_AVAILABLE:
            prompt_menu = menu.addMenu("Prompt Language")
        
        languages = [
            {"name": "English", "code": "en"},
            {"name": "한국어 (Korean)", "code": "ko"},
            {"name": "日本語 (Japanese)", "code": "ja"},
            {"name": "中文 (Chinese)", "code": "zh"},
            {"name": "Español (Spanish)", "code": "es"},
            {"name": "Français (French)", "code": "fr"},
            {"name": "Deutsch (German)", "code": "de"},
            {"name": "Русский (Russian)", "code": "ru"}
        ]

        # Add voice recognition language options
        for lang in languages:
            action = voice_menu.addAction(lang["name"])
            action.setCheckable(True)
            action.setChecked(self.voice_recognizer.language == lang["code"])
            action.triggered.connect(
                lambda checked, code=lang["code"], name=lang["name"]: self.change_voice_language(code, name))
        
        # Add prompt language options if available
        if LANGUAGE_PROMPTS_AVAILABLE:
            # Add auto-detect option
            auto_action = prompt_menu.addAction("Auto-detect (Default)")
            auto_action.setCheckable(True)
            auto_action.setChecked(not hasattr(prompt_manager, 'fixed_language'))
            auto_action.triggered.connect(lambda: self.set_prompt_language("auto"))
            
            prompt_menu.addSeparator()
            
            # Add supported languages
            supported_langs = ["en", "ko", "ru"]  # Languages with prompt support
            for lang in languages:
                if lang["code"] in supported_langs:
                    action = prompt_menu.addAction(lang["name"])
                    action.setCheckable(True)
                    action.setChecked(hasattr(prompt_manager, 'fixed_language') and 
                                     prompt_manager.fixed_language == lang["code"])
                    action.triggered.connect(
                        lambda checked, code=lang["code"], name=lang["name"]: self.set_prompt_language(code, name))

        menu.exec(self.language_button.mapToGlobal(QtCore.QPoint(0, self.language_button.height())))

    def change_voice_language(self, language_code, language_name):
        """Change the voice recognition language"""
        if language_code != self.voice_recognizer.language:
            self.voice_recognizer.language = language_code
            self.display_assistant_message(f"Voice recognition language changed to {language_name}.")
            
    def set_prompt_language(self, language_code, language_name=None):
        """Set the language for prompts"""
        if LANGUAGE_PROMPTS_AVAILABLE:
            if language_code == "auto":
                # Remove fixed language to enable auto-detection
                if hasattr(prompt_manager, 'fixed_language'):
                    delattr(prompt_manager, 'fixed_language')
                self.display_assistant_message("Prompt language set to auto-detect")
            else:
                # Set fixed language to override auto-detection
                prompt_manager.fixed_language = language_code
                prompt_manager.current_language = language_code
                self.display_assistant_message(f"Prompt language set to {language_name}")
        else:
            self.display_assistant_message("Language prompts module not available. Using default language.")

    @pyqtSlot(str)
    def update_language_indicator(self, language_name):
        """Update the language indicator in the UI"""
        if hasattr(self, 'language_button'):
            self.language_button.setToolTip(f"Language Settings (Detected: {language_name})")

    def eventFilter(self, source, event):
        if source == self.inputField:
            if event.type() == QtCore.QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return:
                    if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                        cursor = self.inputField.textCursor()
                        cursor.insertText('\n')
                        return True
                    else:
                        self.send_message()
                        return True
                elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    clipboard = QtWidgets.QApplication.clipboard()
                    self.inputField.insertPlainText(clipboard.text())
                    return True
        return super().eventFilter(source, event)

    # @pyqtSlot(float)
    # def update_audio_level(self, level):
    #     """Update the audio level indicator"""
        # self.audio_level_indicator.setValue(int(min(level, 100)))

    def handle_microphone_button(self):
        if self.micButton.isChecked():
            self.voice_recognizer.start_recording()
            # self.audio_level_indicator.show()
        else:
            self.voice_recognizer.stop_recording()
            # self.audio_level_indicator.hide()
            # self.audio_level_indicator.setValue(0)

    def update_mic_status(self, is_recording):
        if is_recording:
            self.micButton.setToolTip("Recording... Click to stop")
            self.micButton.setChecked(True)
            # self.audio_level_indicator.show()
        else:
            self.micButton.setToolTip("Click to record voice")
            self.micButton.setChecked(False)
            # self.audio_level_indicator.hide()
            # self.audio_level_indicator.setValue(0)

    def handle_voice_error(self, error_message):
        self.display_assistant_message(f"Voice recognition error: {error_message}")

    @pyqtSlot(str)
    def handle_transcribed_text(self, text):
        if text:
            self.inputField.setPlainText(text)
            self.send_message()



    def command_listener(self):
        # Keep track of commands in a sequence
        command_sequence = []
        
        while self.listener_active:
            try:
                command, args = command_queue.get()
                
                # Add command to the sequence
                command_sequence.append(command)
                
                def execute_and_display():
                    try:
                        msg, response = execute_command_gui(command, *args)
                        print(f"Command executed, response: {response[:50]}...")
                        
                        # Only display response for commands after the first one
                        # The first command's status message is already displayed in process_input
                        # if len(command_sequence) > 1 or command_sequence[0] != command:
                        QtCore.QMetaObject.invokeMethod(
                            self, "display_assistant_message",
                            QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(str, response)
                        )
                        # else:
                        #     print("Skipping display of first command response to avoid duplication")
                            
                        # Reset command sequence after all commands are processed
                        if command_queue.empty():
                            command_sequence.clear()
                            
                    except Exception as e:
                        error_msg = f"Error executing command: {str(e)}"
                        print(f"Error executing command: {e}")
                        QtCore.QMetaObject.invokeMethod(
                            self, "display_assistant_message",
                            QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(str, error_msg)
                        )
                    finally:
                        command_queue.task_done()

                execution_thread = Thread(target=execute_and_display, daemon=True)
                execution_thread.start()
                execution_thread.join()
            except Exception as e:
                print(f"Error in command listener: {e}")
    
    def display_assistant_message_from_thread(self, message):
        """Safe method to call display_assistant_message from a thread"""
        QtCore.QMetaObject.invokeMethod(
            self, "display_assistant_message",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(str, message)
        )

    @pyqtSlot(str)
    def display_user_message(self, message):
        message = message.replace('\n', '<br>')
        bubble = ChatBubble(message, is_user=True)
        self.chat_layout.addWidget(bubble)
        QtCore.QTimer.singleShot(100, self.auto_scroll_bottom)

    @pyqtSlot(str)
    def display_assistant_message(self, response):
        response = response.replace('\n', '<br>')
        bubble = ChatBubble(response, is_user=False)
        self.chat_layout.addWidget(bubble)
        QtCore.QTimer.singleShot(100, self.auto_scroll_bottom)

    def auto_scroll_bottom(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_message(self):
        user_text = self.inputField.toPlainText().strip()
        
        if not user_text:
            return
            
        if user_text.lower() in ["/quit", "/exit", "/bye"]:
            self.listener_active = False
            self.close()
            sys.exit()
            
        if user_text.lower() == "/clear":
            self.clear_chat()
            self.inputField.clear()
            return

        # Display user message
        self.display_user_message(user_text)
        self.inputField.clear()
        
        # Special handling for simple yes/no responses to pending commands
        if self.pending_command and user_text.lower() in ["yes", "yeah", "yep", "sure", "ok", "okay", "y"]:
            # Don't show the user's message twice - we'll handle it in process_input
            pass
        elif self.pending_command and user_text.lower() in ["no", "nope", "n"]:
            # Clear the pending command and acknowledge
            self.pending_command = None
            self.pending_args = None
            self.display_assistant_message("Okay, I won't run that command.")
            return
        
        # Process the message in a separate thread
        Thread(target=self.process_input, args=(user_text,), daemon=True).start()

    def process_input(self, user_input):
        """Process user input using the updated functions"""
        try:
            # Clear any previous process messages
            QtCore.QMetaObject.invokeMethod(
                self.process_manager, "clear_process_message",
                QtCore.Qt.ConnectionType.QueuedConnection
            )
            
            # Detect language if localization is available
            if LOCALIZATION_AVAILABLE:
                language_code = set_current_language(user_input)
                print(f"Input language detected as: {language_code}")
                
                # Update language button tooltip with detected language
                language_names = {
                    "en": "English", 
                    "ko": "Korean", 
                    "ru": "Russian",
                    "ja": "Japanese",
                    "zh": "Chinese",
                    "es": "Spanish",
                    "fr": "French",
                    "de": "German"
                }
                language_name = language_names.get(language_code, language_code)
                QtCore.QMetaObject.invokeMethod(
                    self, "update_language_indicator",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, language_name)
                )
            elif LANGUAGE_PROMPTS_AVAILABLE:
                language_code = prompt_manager.set_current_language(user_input)
                print(f"Input language detected as: {language_code}")
                
                # Update language button tooltip with detected language
                if not hasattr(prompt_manager, 'fixed_language'):
                    language_names = {
                        "en": "English", 
                        "ko": "Korean", 
                        "ru": "Russian",
                        "ja": "Japanese",
                        "zh": "Chinese",
                        "es": "Spanish",
                        "fr": "French",
                        "de": "German"
                    }
                    language_name = language_names.get(language_code, language_code)
                    QtCore.QMetaObject.invokeMethod(
                        self, "update_language_indicator",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, language_name)
                    )
            
            # Define a callback for process updates
            def update_process(message):
                # Use QMetaObject.invokeMethod to safely update from another thread
                QtCore.QMetaObject.invokeMethod(
                    self.process_manager, "update_process_message",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, message)
                )
            
            # Check if this is a response to a pending command suggestion
            if self.pending_command and user_input.lower() in ["yes", "yeah", "yep", "sure", "ok", "okay", "y"]:
                print(f"User confirmed pending command: {self.pending_command}")
                command = self.pending_command
                args = self.pending_args
                progress_txt = ai_functions.status_message(command, args)
                command_queue.put((command, args))
                self.pending_command = None
                self.pending_args = None
                # self.display_assistant_message_from_thread(str(progress_txt))
                update_process(progress_txt)
                return
            elif self.pending_command:
                # User didn't confirm, clear the pending command
                self.pending_command = None
                self.pending_args = None
            
            # Check if input is likely a question about defects before command detection
            is_defect_question = False
            defect_question_patterns = []
            
            # Set language-specific defect question patterns
            if LOCALIZATION_AVAILABLE:
                current_lang = localization_manager.current_language
                if current_lang == "ko":
                    defect_question_patterns = [
                        r"어떻게.*결함.*찾",
                        r"어떻게.*결함.*감지",
                        r"어떻게.*결함.*식별",
                        r"결함.*어떻게.*보이",
                        r"결함.*감지.*설명"
                    ]
                elif current_lang == "ru":
                    defect_question_patterns = [
                        r"как.*найти.*дефект",
                        r"как.*обнаружить.*дефект",
                        r"как.*определить.*дефект",
                        r"что.*дефект.*выглядит",
                        r"объясни.*обнаружение.*дефект"
                    ]
                else:  # Default to English
                    defect_question_patterns = [
                        r"how.*find.*defect",
                        r"how.*detect.*defect",
                        r"how.*identify.*defect",
                        r"how.*understand.*defect",
                        r"what.*defect.*look like",
                        r"explain.*defect.*detection"
                    ]
            elif LANGUAGE_PROMPTS_AVAILABLE:
                current_lang = prompt_manager.current_language
                if current_lang == "ko":
                    defect_question_patterns = [
                        r"어떻게.*결함.*찾",
                        r"어떻게.*결함.*감지",
                        r"어떻게.*결함.*식별",
                        r"결함.*어떻게.*보이",
                        r"결함.*감지.*설명"
                    ]
                elif current_lang == "ru":
                    defect_question_patterns = [
                        r"как.*найти.*дефект",
                        r"как.*обнаружить.*дефект",
                        r"как.*определить.*дефект",
                        r"что.*дефект.*выглядит",
                        r"объясни.*обнаружение.*дефект"
                    ]
                else:  # Default to English
                    defect_question_patterns = [
                        r"how.*find.*defect",
                        r"how.*detect.*defect",
                        r"how.*identify.*defect",
                        r"how.*understand.*defect",
                        r"what.*defect.*look like",
                        r"explain.*defect.*detection"
                    ]
            else:
                # Fallback to English patterns
                defect_question_patterns = [
                    r"how.*find.*defect",
                    r"how.*detect.*defect",
                    r"how.*identify.*defect",
                    r"how.*understand.*defect",
                    r"what.*defect.*look like",
                    r"explain.*defect.*detection"
                ]
            
            for pattern in defect_question_patterns:
                if re.search(pattern, user_input.lower()):
                    is_defect_question = True
                    print("Detected as a question about defects, skipping command detection")
                    break
                    
            if is_defect_question:
                progress_txt = ai_functions.chat_with_gpt(user_input)
                self.display_assistant_message_from_thread(str(progress_txt))
                
                # Suggest running defect detection with localized text
                if LOCALIZATION_AVAILABLE:
                    suggestion = "\n" + localization_manager.get_suggestion("run_defect_detection")
                elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ko":
                    suggestion = "\n현재 파일에서 결함 감지를 실행하시겠습니까?"
                elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ru":
                    suggestion = "\nХотите ли вы запустить обнаружение дефектов в текущем файле?"
                else:
                    suggestion = "\nWould you like me to run defect detection on the current file?"
                    
                self.display_assistant_message_from_thread(suggestion)
                self.pending_command = "startDefectDetection"
                self.pending_args = []
                return
                
            # Check for ambiguous cases that could be either questions or commands
            # Updated for multilingual support using localization
            ambiguous_patterns = {}
            
            # Detect language and set appropriate patterns
            if LOCALIZATION_AVAILABLE:
                current_lang = localization_manager.current_language
                if current_lang == "ko":
                    ambiguous_patterns = {
                        "결함": "startDefectDetection",
                        "분석": "doAnalysisSNR", 
                        "SNR": "doAnalysisSNR",
                        "파일 정보": "getFileInformation",
                        "디렉토리": "getDirectory",
                        "폴더": "getDirectory"
                    }
                elif current_lang == "ru":
                    ambiguous_patterns = {
                        "дефект": "startDefectDetection",
                        "анализ": "doAnalysisSNR",
                        "снр": "doAnalysisSNR", 
                        "информация": "getFileInformation",
                        "директория": "getDirectory",
                        "папка": "getDirectory"
                    }
                else:  # Default to English
                    ambiguous_patterns = {
                        "defect": "startDefectDetection",
                        "analysis": "doAnalysisSNR",
                        "snr": "doAnalysisSNR",
                        "file information": "getFileInformation",
                        "directory": "getDirectory",
                        "folder": "getDirectory"
                    }
            elif LANGUAGE_PROMPTS_AVAILABLE:
                current_lang = prompt_manager.current_language
                if current_lang == "ko":
                    ambiguous_patterns = {
                        "결함": "startDefectDetection",
                        "분석": "doAnalysisSNR", 
                        "SNR": "doAnalysisSNR",
                        "파일 정보": "getFileInformation",
                        "디렉토리": "getDirectory",
                        "폴더": "getDirectory"
                    }
                elif current_lang == "ru":
                    ambiguous_patterns = {
                        "дефект": "startDefectDetection",
                        "анализ": "doAnalysisSNR",
                        "снр": "doAnalysisSNR", 
                        "информация": "getFileInformation",
                        "директория": "getDirectory",
                        "папка": "getDirectory"
                    }
                else:  # Default to English
                    ambiguous_patterns = {
                        "defect": "startDefectDetection",
                        "analysis": "doAnalysisSNR",
                        "snr": "doAnalysisSNR",
                        "file information": "getFileInformation",
                        "directory": "getDirectory",
                        "folder": "getDirectory"
                    }
            else:
                # Fallback to English patterns
                ambiguous_patterns = {
                    "defect": "startDefectDetection",
                    "analysis": "doAnalysisSNR",
                    "snr": "doAnalysisSNR",
                    "file information": "getFileInformation",
                    "directory": "getDirectory",
                    "folder": "getDirectory"
                }
            
            is_ambiguous = False
            suggested_command = None
            
            for keyword, command in ambiguous_patterns.items():
                if keyword in user_input.lower() and not user_input.strip().endswith("?"):
                    # This could be ambiguous - not clearly a question but mentions keywords
                    is_ambiguous = True
                    suggested_command = command
                    break
            
            # Use the new consolidated command detection logic (with fallback to old method)
            commands = ai_functions.get_command_gpt_consolidated(user_input)
            print(f"Commands detected: {commands}")
            
            command_executed = False
            progress_txt = ""
            
            if commands is not None and commands.strip():
                commands = ai_functions.parse_comma_separated(commands)
                if commands:
                    print("Commands list is: ", commands)
                    for i, command in enumerate(commands):
                        print(f"Processing command {i+1}/{len(commands)}: {command}")
                        
                        if command in ["loadData", "updatePlot", "getFileInformation", "getDirectory",
                                      "doAnalysisSNR", "startDefectDetection", "setNewDirectory", "makeSingleFileOnly",
                                      "doFolderAnalysis"]:
                            args, warning_txt = ai_functions.extract_arguments_consolidated(command, user_input,
                                                                               process_callback=update_process)
                            
                            if i == 0:
                                progress_txt = ai_functions.status_message(command, args)
                                if warning_txt:
                                    progress_txt += f"\n{warning_txt}"
                                # self.display_assistant_message_from_thread(str(progress_txt))
                            
                            command_queue.put((command, args))
                            command_executed = True
                            
                            # If this is not the last command, add a small delay
                            if i < len(commands) - 1:
                                time.sleep(0.5)  # Small delay between commands
                        
                        elif command == ", ".join(["loadData", "updatePlot", "getFileInformation", "getDirectory",
                                      "doAnalysisSNR", "startDefectDetection", "setNewDirectory", "makeSingleFileOnly",
                                      "doFolderAnalysis"]):
                            progress_txt = command
                            command_executed = True

                        update_process(progress_txt)
            
            # If no valid command was executed but it's ambiguous, answer as question and suggest command
            if not command_executed and is_ambiguous:
                print(f"Ambiguous input detected, suggesting command: {suggested_command}")
                answer_txt = ai_functions.chat_with_gpt(user_input)
                self.display_assistant_message_from_thread(str(answer_txt))
                
                args = []
                # Generate language-appropriate suggestions
                if suggested_command == "startDefectDetection":
                    if LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ko":
                        suggestion = "\n현재 파일에서 결함 감지를 실행하시겠습니까?"
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ru":
                        suggestion = "\nХотите ли вы запустить обнаружение дефектов в текущем файле?"
                    else:
                        suggestion = "\nWould you like me to run defect detection on the current file?"
                    self.pending_command = suggested_command
                    self.pending_args = args
                    self.display_assistant_message_from_thread(suggestion)
                elif suggested_command == "doAnalysisSNR":
                    if LOCALIZATION_AVAILABLE:
                        suggestion = "\n" + localization_manager.get_suggestion("run_snr_analysis")
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ko":
                        suggestion = "\n현재 파일에서 SNR 분석을 실행하시겠습니까?"
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ru":
                        suggestion = "\nХотите ли вы запустить анализ SNR в текущем файле?"
                    else:
                        suggestion = "\nWould you like me to run SNR analysis on the current file?"
                    self.pending_command = suggested_command
                    self.pending_args = args
                    self.display_assistant_message_from_thread(suggestion)
                elif suggested_command == "getFileInformation":
                    if LOCALIZATION_AVAILABLE:
                        suggestion = "\n" + localization_manager.get_suggestion("show_file_info")
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ko":
                        suggestion = "\n파일 정보를 보여드릴까요?"
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ru":
                        suggestion = "\nХотите ли вы показать информацию о файле?"
                    else:
                        suggestion = "\nWould you like me to show the file information?"
                    self.pending_command = suggested_command
                    self.pending_args = args
                    self.display_assistant_message_from_thread(suggestion)
                elif suggested_command == "getDirectory":
                    if LOCALIZATION_AVAILABLE:
                        suggestion = "\n" + localization_manager.get_suggestion("show_directory")
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ko":
                        suggestion = "\n현재 디렉토리를 보여드릴까요?"
                    elif LANGUAGE_PROMPTS_AVAILABLE and prompt_manager.current_language == "ru":
                        suggestion = "\nХотите ли вы показать текущую директорию?"
                    else:
                        suggestion = "\nWould you like me to show the current directory?"
                    self.pending_command = suggested_command
                    self.pending_args = args
                    self.display_assistant_message_from_thread(suggestion)
                return
            
            if not command_executed:
                print("No valid command detected, using chat_with_gpt")
                progress_txt = ai_functions.chat_with_gpt(user_input)
                
            if not progress_txt:
                if LOCALIZATION_AVAILABLE:
                    progress_txt = localization_manager.get_error_message("no_response")
                else:
                    progress_txt = "I processed your request but couldn't generate a proper response. Please try again."

            # Clear process message when done
            QtCore.QMetaObject.invokeMethod(
                self.process_manager, "clear_process_message",
                QtCore.Qt.ConnectionType.QueuedConnection
            )
            
            print(f"Displaying response: {progress_txt[:50]}...")
            self.display_assistant_message_from_thread(str(progress_txt))
        except Exception as e:
            if LOCALIZATION_AVAILABLE:
                error_msg = localization_manager.get_error_message("general_error", error=str(e))
            else:
                error_msg = f"Error processing input: {str(e)}"
            print(f"Error processing input: {e}")
            
            # Try to update process message with error
            try:
                QtCore.QMetaObject.invokeMethod(
                    self.process_manager, "update_process_message",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, error_msg)
                )
            except:
                pass
                
            # Clear process message after error
            QtCore.QMetaObject.invokeMethod(
                self.process_manager, "clear_process_message",
                QtCore.Qt.ConnectionType.QueuedConnection
            )
            
            self.display_assistant_message_from_thread(error_msg)

    def clear_chat(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Display welcome message
        QtCore.QTimer.singleShot(100, lambda: self.display_assistant_message(
            "Chat history cleared. How can I help you?"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better cross-platform appearance
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
