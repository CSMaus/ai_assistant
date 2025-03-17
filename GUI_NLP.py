# TODO: this is note: NL to commands processor for my PAUT SW with GUI like chat-bot (AI Assistant)
# TODO: place parameters of settings into separate group
import sys
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt
from PyQt6 import QtCore
# TODO: place correct commands here
# from command_process import process_input


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
        self.chat_layout.setSpacing(10)  # Fixed spacing between messages

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
        input_layout.addWidget(self.inputField)
        input_layout.addWidget(self.sendButton)
        main_layout.addLayout(input_layout)

        self.user_color = QtGui.QColor("#323232")  #3C3C3C")  # #272727
        self.assist_color = QtGui.QColor("#242424")
        self.textColor = QtGui.QColor("#FFFFFF")
        self.backgroundColor = QtGui.QColor("#202020")  #  #202020

        self.sendButton.clicked.connect(self.send_message)
        self.inputField.returnPressed.connect(self.send_message)

    def send_message(self):
        user_text = self.inputField.text().strip()
        if user_text:
            user_bubble = TextEdit(alignment='right', bubble_color=self.user_color.name())
            user_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>You:</b><br>{user_text}</span>')
            user_bubble.update_size()
            self.chat_layout.addWidget(user_bubble, alignment=Qt.AlignmentFlag.AlignRight)

            response = f"Command processed. User input was: {user_text}"
            assistant_bubble = TextEdit(alignment='left', bubble_color=self.assist_color.name())
            assistant_bubble.setHtml(f'<span style="color:{self.textColor.name()}"><b>Assistant:</b><br>{response}</span>')
            assistant_bubble.update_size()
            self.chat_layout.addWidget(assistant_bubble, alignment=Qt.AlignmentFlag.AlignLeft)

            self.inputField.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: #202020; }")
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
