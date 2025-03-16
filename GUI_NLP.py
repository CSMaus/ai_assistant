# TODO: this is note: NL to commands processor for my PAUT SW with GUI like chat-bot (AI Assistant)

import sys
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
# TODO: place correct command here
from command_process import process_input


class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Chat")
        self.resize(500, 400)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)
        # Chat display area
        self.chatDisplay = QtWidgets.QTextBrowser(self)
        layout.addWidget(self.chatDisplay)

        # Input field and send button
        input_layout = QtWidgets.QHBoxLayout()
        self.inputField = QtWidgets.QLineEdit(self)
        self.sendButton = QtWidgets.QPushButton("Send", self)
        input_layout.addWidget(self.inputField)
        input_layout.addWidget(self.sendButton)
        layout.addLayout(input_layout)

        # Connect button and Enter key to send message
        self.sendButton.clicked.connect(self.send_message)
        self.inputField.returnPressed.connect(self.send_message)

    def send_message(self):
        user_text = self.inputField.text().strip()
        if user_text:
            # Display the user message in the chat area
            self.chatDisplay.append(f"<b>You:</b> {user_text}")
            # Process the input using your command processor
            process_input(user_text)
            # For demonstration, append a placeholder assistant response
            self.chatDisplay.append("<b>Assistant:</b> Command processed.")
            self.inputField.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
