import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from queue import Queue
from threading import Thread
from ai_functions_keeper import *
import pyaudio
import wave
import time


# TODO: fix commands query: now it set commands infinitely
# TODO: modify messages in c# to be more user friendly
# TODO: add commands to make complex requests, like "Analyse all file and prepare report"
# TODO: replace NL processing to be checked via LLM (now it's not fully correct)
# TODO: fix the assistant responses for mistakes

# TODO: use LLM_1 requests for search for correct command based on command_name and its description from user input
# TODO: if find matched command, then use LLM2 to extract arguments from user input required for this command


command_queue = Queue()
# TODO: fix sending empty messages or msgs repeats
def process_input(user_input):
    progress_txt = ""
    try:
        do_kw_extract = False
        if do_kw_extract:
            user_keywords = extract_keywords(user_input)
            matched_commands = get_best_matching_commands(user_keywords)
            if matched_commands:
                command_idx = 0
                # place only one command into queue - sometimes errors appear to run same commands infinite times
                while (command_idx < len(matched_commands) and command_queue.empty()):
                    command = matched_commands[command_idx]
                    args, warning_txt = extract_arguments(command, user_input)
                    command_queue.put((command, args))
                    command_idx += 1
                    progress_txt = status_message(command, args)
                    if warning_txt:
                        progress_txt += f"\n{warning_txt}"

                    if not command_queue.empty():
                        break
                '''for command in matched_commands:
                    args, warning_txt = extract_arguments(command, user_input)
                    command_queue.put((command, args))
    
                    progress_txt = status_message(command, args)
                    if warning_txt:
                        progress_txt += f"\n{warning_txt}"'''
            else:
                progress_txt = "No matching commands found."
        else:
            # command = get_command_ollama(user_input)
            commands = get_command_gpt(user_input)

            if commands is not None:
                # command = command.strip()
                commands = parse_comma_separated(commands)
                print("Commands list is: ", commands)
                for command in commands:
                    print(f"Command received from AI is {command}")
                    if command in command_names_list:
                        args, warning_txt = extract_arguments(command, user_input)
                        progress_txt = status_message(command, args)
                        command_queue.put((command, args))
                        if warning_txt:
                            progress_txt += f"\n{warning_txt}"
                    elif command == ", ".join(command_names_list):
                        progress_txt = command
                    # else:
                        # progress_txt = chat_with_gpt(user_input)
                        # progress_txt = chat_with_ollama(user_input)
                        # progress_txt = "I'm working on implementing interaction with assistant outside of the command processing"

            else:
                progress_txt = "Sorry, I didn't understand you"
    except Exception as e:
        progress_txt = f"Error processing input: {e}"

    return progress_txt

class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, alignment='right', bubble_color="#323232", parent=None):
        super().__init__(parent)
        self.alignment = alignment
        self.bubble_color = QtGui.QColor(bubble_color)
        self.setReadOnly(True)
        self.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)

        # disable scrollbars bor message text block
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # update the size of text block based on content
        self.document().documentLayout().documentSizeChanged.connect(self.update_size)
        # TODO: remake it to depends on window size
        self.setFixedWidth(350)

    def update_size(self):
        doc_height = int(round(self.document().size().height())) + 5
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

        bubble_width = unitedBlockRect.width()
        bubble_height = unitedBlockRect.height()

        if self.alignment == 'right':
            x = self.viewport().width() - bubble_width - margin
        else:
            x = margin

        rect = QtCore.QRectF(x, margin, bubble_width, bubble_height)
        painter.drawRoundedRect(rect, 10, 10)

        super().paintEvent(event)

class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Chat")
        self.resize(500, 400)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(5)  # Fixed spacing between messages

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area)

        # scrollable messages. I do not like it, but maybe later someone will
        '''scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.chat_container)
        layout.addWidget(scroll_area)'''

        # set the global style of the AI assistant

        input_layout = QtWidgets.QHBoxLayout()
        # self.inputField = QtWidgets.QLineEdit(self)
        self.inputField = QtWidgets.QTextEdit(self)
        self.inputField.setMaximumHeight(50)
        self.inputField.setStyleSheet("color: #111518;")


        palette = self.inputField.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#111518"))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#F5FAFF"))  # background  F5FAFF
        self.inputField.setPalette(palette)

        self.inputField.installEventFilter(self)  # to intercept key presses


        # self.sendButton = QtWidgets.QPushButton("Send", self)
        self.sendButton = QtWidgets.QPushButton(self)
        self.sendButton.setIcon(QtGui.QIcon("icons/send.png"))
        self.sendButton.setIconSize(QtCore.QSize(24, 24))

        # microphone
        self.micButton = QtWidgets.QPushButton(self)
        self.micButton.setIcon(QtGui.QIcon("icons/mic.png"))
        self.micButton.setIconSize(QtCore.QSize(24, 24))
        self.micButton.setCheckable(True)
        self.micButton.setToolTip("Hold to record voice")
        self.micButton.clicked.connect(self.handle_microphone_input)

        self.recording = False
        self.audio_stream = None
        self.audio_frames = []
        self.audio_interface = pyaudio.PyAudio()

        # TODO: style all the squared to the rounded edges
        self.sendButton.setStyleSheet("color: #111518;")
        input_layout.addWidget(self.inputField)
        input_layout.addWidget(self.sendButton)
        input_layout.addWidget(self.micButton)
        main_layout.addLayout(input_layout)


        self.user_color = QtGui.QColor("#91BDF8") # 323232  //// #3C3C3C")  # #272727
        self.assist_color = QtGui.QColor("#B4D4FF")  # 242424
        self.textColor = QtGui.QColor("#111518")  # FFFFFFtext
        self.backgroundColor = QtGui.QColor("#F5FAFF")  #  #202020

        self.sendButton.clicked.connect(self.send_message)
        # self.inputField.returnPressed.connect(self.send_message)

        self.command_queue = Queue()
        self.listener_thread = Thread(target=self.command_listener, daemon=True)
        self.listener_active = True
        # self.listener_thread = self.listener_thread.start() # this is bug
        self.listener_thread.start()
        QtCore.QTimer.singleShot(0, lambda: self.display_assistant_message("Hello! How can I assist you?"))

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

    def handle_microphone_input(self):
        if self.micButton.isChecked():
            self.micButton.setToolTip("Recording... Click again to stop.")
            self.recording = True
            self.audio_frames = []

            def record_audio():
                CHUNK = 1024
                FORMAT = pyaudio.paInt16
                CHANNELS = 1
                RATE = 16000

                stream = self.audio_interface.open(format=FORMAT,
                                                   channels=CHANNELS,
                                                   rate=RATE,
                                                   input=True,
                                                   frames_per_buffer=CHUNK)

                self.audio_stream = stream
                print("Recording started...")

                while self.recording:
                    data = stream.read(CHUNK)
                    self.audio_frames.append(data)

                stream.stop_stream()
                stream.close()
                print("Recording stopped.")

                # frames into raw audio bytes
                audio_data = b''.join(self.audio_frames)

                try:
                    # TODO: fill logic in extract_text placeholder
                    transcribed_text = extract_text(audio_data)
                    text = "Test sending message text"
                    print(f"Transcribed text is: {transcribed_text}")
                    QtCore.QMetaObject.invokeMethod(
                        self,
                        "handle_transcribed_text",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, text)
                    )

                except Exception as e:
                    print(f"Error transcribing audio: {e}")
                    self.inputField.setPlainText("[Error processing voice input]")

            Thread(target=record_audio, daemon=True).start()

        else:
            self.recording = False
            self.micButton.setToolTip("Hold to record voice")

    @QtCore.pyqtSlot(str)
    def handle_transcribed_text(self, text):
        self.inputField.setPlainText(text)
        self.send_message()

    def command_listener_old(self):
        while self.listener_active:
            command, args = command_queue.get()
            msg, response = execute_command_gui(command, *args)
            QtCore.QMetaObject.invokeMethod(
                self, "display_assistant_message",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response)
            )
            command_queue.task_done()

    # display messages in real time about commands execution status
    def command_listener(self):
        while self.listener_active:
            command, args = command_queue.get()

            """QtCore.QMetaObject.invokeMethod(
                self, "display_assistant_message",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, f"{status_message(command, args)}...")
            )"""

            def execute_and_display():
                msg, response = execute_command_gui(command, *args)
                QtCore.QMetaObject.invokeMethod(
                    self, "display_assistant_message",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, response)
                )
                command_queue.task_done()

            # execution_thread = Thread(target=execute_and_display, daemon=True)
            execution_thread = Thread(
                target=execute_and_display,
                daemon=True
            )
            execution_thread.start()
            execution_thread.join()

    @QtCore.pyqtSlot(str)
    def display_user_message(self, message):
        user_bubble = TextEdit(alignment='right', bubble_color=self.user_color.name())
        message = message.replace('\n', '<br>')
        user_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>You:</b><br>{message}</span>')
        user_bubble.update_size()
        self.chat_layout.addWidget(user_bubble, alignment=Qt.AlignmentFlag.AlignRight)
        QtCore.QTimer.singleShot(100, self.auto_scroll_bottom)

        
    def auto_scroll_down(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_message(self):
        # user_text = self.inputField.text().strip()
        user_text = self.inputField.toPlainText().strip() # text with new lines by using shift+Enter

        if user_text in ["Who are you?", "What can you do?"]:
            user_bubble = TextEdit(alignment='right', bubble_color=self.user_color.name())
            user_text = user_text.replace('\n', '<br>')
            user_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>You:</b><br>{user_text}</span>')
            user_bubble.update_size()
            self.chat_layout.addWidget(user_bubble, alignment=Qt.AlignmentFlag.AlignRight)

            self.inputField.clear()
            self.chat_container.adjustSize()
            QtCore.QTimer.singleShot(0, self.auto_scroll)

            answer = ("I’m an AI assistant bot designed to help analyze PAUT data and control the application to open, view, and analyze those datasets.")
            self.display_assistant_message(answer)
            self.inputField.clear()
            return

        if user_text.lower() in ["/quit", "/exit", "/bye"]:
            self.listener_active = False
            self.close()
            sys.exit()

        if user_text:
            user_bubble = TextEdit(alignment='right', bubble_color=self.user_color.name())
            user_text = user_text.replace('\n', '<br>')
            user_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>You:</b><br>{user_text}</span>')
            user_bubble.update_size()
            self.chat_layout.addWidget(user_bubble, alignment=Qt.AlignmentFlag.AlignRight)

            self.inputField.clear()
            self.chat_container.adjustSize()
            QtCore.QTimer.singleShot(0, self.auto_scroll)

            # place it in different thread
            # progress_txt = process_input(user_text)
            Thread(target=self.process_user_input, args=(user_text,), daemon=True).start()

            # place assistant bubble in separate function with separate thread
            # response = f"Command processed. User input was: {user_text}"
            # assistant_bubble = TextEdit(alignment='left', bubble_color=self.assist_color.name())
            # assistant_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>Assistant:</b><br>{progress_txt}<br></span>')
            # assistant_bubble.update_size()
            # self.chat_layout.addWidget(assistant_bubble, alignment=Qt.AlignmentFlag.AlignLeft)

    def process_user_input(self, user_text):
        progress_txt = process_input(user_text)
        if not isinstance(progress_txt, str):
            progress_txt = str(progress_txt)

        QtCore.QMetaObject.invokeMethod(
            self, "display_assistant_message",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(str, progress_txt))

    @QtCore.pyqtSlot(str)
    def display_assistant_message(self, response):
        assistant_bubble = TextEdit(alignment='left', bubble_color=self.assist_color.name())
        response = response.replace('\n', '<br>')
        assistant_bubble.setHtml(
            f'<span style="color:{self.textColor.name()}"><b>Assistant:</b><br>{response}</span>')
        assistant_bubble.update_size()
        self.chat_layout.addWidget(assistant_bubble, alignment=Qt.AlignmentFlag.AlignLeft)
        QtCore.QTimer.singleShot(100, self.auto_scroll_bottom)

    def auto_scroll(self):
        QtCore.QTimer.singleShot(0, self.auto_scroll_bottom)

    def auto_scroll_bottom(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())


if __name__ == "__main__":
    command_queue = Queue()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: #F5FAFF; }")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
