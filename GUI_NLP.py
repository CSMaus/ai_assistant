# TODO: this is note: NL to commands processor for my PAUT SW with GUI like chat-bot (AI Assistant)

import sys
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt
# TODO: place correct commands here
# from command_process import process_input


class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Chat")
        self.resize(500, 400)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)

        self.chatDisplay = QtWidgets.QTextBrowser(self)
        self.chatDisplay.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.chatDisplay)

        input_layout = QtWidgets.QHBoxLayout()
        self.inputField = QtWidgets.QLineEdit(self)
        self.sendButton = QtWidgets.QPushButton("Send", self)
        input_layout.addWidget(self.inputField)
        input_layout.addWidget(self.sendButton)
        layout.addLayout(input_layout)

        self.user_color = QtGui.QColor("#3C3C3C")
        self.assist_color = QtGui.QColor("#17172F")

        self.sendButton.clicked.connect(self.send_message)
        self.inputField.returnPressed.connect(self.send_message)

    def send_message(self):
        user_text = self.inputField.text().strip()
        if user_text:

            # right side alignment
            cursor = self.chatDisplay.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setAlignment(Qt.AlignmentFlag.AlignRight)
            blockFormat.setBackground(self.user_color)
            cursor.insertBlock(blockFormat)
            cursor.insertHtml(f"<b>You:</b> {user_text}")

            #TODO: process_input(user_text)
            response = f"Command processed. User input was: {user_text}"

            cursor = self.chatDisplay.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            blockFormat = QtGui.QTextBlockFormat()
            blockFormat.setAlignment(Qt.AlignmentFlag.AlignLeft)
            blockFormat.setBackground(self.assist_color)
            cursor.insertBlock(blockFormat)
            cursor.insertHtml(f"<b>Assistant:</b> {response}")

            self.inputField.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: #001111; }")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
