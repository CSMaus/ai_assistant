import sys
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from queue import Queue
from threading import Thread
from ai_functions_keeper import *

# TODO: fix commands query: now it set commands infinitely
# TODO: modify messages in c# to be more user friendly
# TODO: add commands to make complex requests, like "Analyse all file and prepare report"
# TODO: replace NL processing to be checked via LLM (now it's not fully correct)
# TODO: fix the assistant responses for mistakes

# TODO: use LLM_1 requests for search for correct command based on command_name and its description from user input
# TODO: if find matched command, then use LLM2 to extract arguments from user input required for this command

command_queue = Queue()
def process_input(user_input):
    progress_txt = []
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
            command = get_command_ollama(user_input)
            if command is not None:
                command = command.strip()
                print(f"Command received from ollama is {command}")
                if command in command_names_list:
                    args, warning_txt = extract_arguments(command, user_input)
                    command_queue.put((command, args))
                    progress_txt = status_message(command, args)
                    if warning_txt:
                        progress_txt += f"\n{warning_txt}"
                else:
                    progress_txt = "I'm working on implementing interaction with assistant outside of the command processing"

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


        input_layout = QtWidgets.QHBoxLayout()
        self.inputField = QtWidgets.QLineEdit(self)
        self.sendButton = QtWidgets.QPushButton("Send", self)
        self.inputField.setStyleSheet("color: #FFFFFF;")
        self.sendButton.setStyleSheet("color: #FFFFFF;")
        input_layout.addWidget(self.inputField)
        input_layout.addWidget(self.sendButton)
        main_layout.addLayout(input_layout)


        self.user_color = QtGui.QColor("#323232")  #3C3C3C")  # #272727
        self.assist_color = QtGui.QColor("#242424")
        self.textColor = QtGui.QColor("#FFFFFF")
        self.backgroundColor = QtGui.QColor("#202020")  #  #202020

        self.sendButton.clicked.connect(self.send_message)
        self.inputField.returnPressed.connect(self.send_message)

        self.command_queue = Queue()
        self.listener_thread = Thread(target=self.command_listener, daemon=True)
        self.listener_active = True
        # self.listener_thread = self.listener_thread.start() # this is bug
        self.listener_thread.start()

    def command_listener(self):
        while self.listener_active:
            command, args = command_queue.get()
            msg, response = execute_command_gui(command, *args)
            QtCore.QMetaObject.invokeMethod(
                self, "display_assistant_message",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response)
            )
            command_queue.task_done()

    # to handle threads and GUI safely
    @QtCore.pyqtSlot(str)
    def display_assistant_message(self, response):
        assistant_bubble = TextEdit(alignment='left', bubble_color=self.assist_color.name())
        assistant_bubble.setHtml(f'<span style="color:{self.textColor.name()}">{response}</span>')
        assistant_bubble.update_size()
        self.chat_layout.addWidget(assistant_bubble, alignment=Qt.AlignmentFlag.AlignLeft)
        QtCore.QTimer.singleShot(100, self.auto_scroll_bottom)

    def auto_scroll_down(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_message(self):
        user_text = self.inputField.text().strip()

        if user_text.lower() in ["quit", "exit", "bye"]:
            self.listener_active = False
            self.close()
            sys.exit()

        if user_text:
            user_bubble = TextEdit(alignment='left', bubble_color=self.user_color.name())
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
    app.setStyleSheet("QWidget { background-color: #202020; }")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
