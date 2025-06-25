"""
Custom chat bubble widget for the AI assistant chat interface.
This provides a modern, polished chat bubble appearance.
"""

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

class ChatBubble(QtWidgets.QWidget):
    """
    A custom widget that displays a chat message in a bubble.
    """
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        
        # Store the message and sender type
        self.message = message
        self.is_user = is_user
        
        # Set up colors - explicitly define bubble colors
        self.user_bubble_color = QtGui.QColor("#91BDF8")  # Blue for user
        self.assistant_bubble_color = QtGui.QColor("#B4D4FF")  # Light blue for assistant
        self.text_color = QtGui.QColor("#111518")  # Dark text
        
        # Make widget background transparent so it doesn't inherit parent's background
        self.setStyleSheet("background-color: transparent;")
        
        # Set up the layout
        self.init_ui()
        
        # Prevent text cursor errors and ensure proper styling
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        
    def init_ui(self):
        # Set up the main layout
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the bubble container
        self.bubble = QtWidgets.QWidget()
        self.bubble.setObjectName("chatBubble")
        
        # Set up the bubble layout
        bubble_layout = QtWidgets.QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        
        # Create the text label - use QLabel instead of QTextEdit to avoid cursor issues
        self.text_label = QtWidgets.QLabel(self.message)
        
        # Calculate appropriate width based on text content
        fm = QtGui.QFontMetrics(self.text_label.font())
        text_width = fm.horizontalAdvance(self.message.replace('<br>', ' '))
        
        # Always set word wrap to true for HTML content
        self.text_label.setWordWrap(True)
        
        # Set minimum width for short messages to prevent excessive narrowness
        min_width = 100
        if text_width < min_width:
            text_width = min_width
            
        # Set fixed width for the text label based on content
        if text_width < 350:  # For shorter messages
            self.text_label.setMinimumWidth(text_width + 20)  # Add padding
        
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Set text color
        palette = self.text_label.palette()
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, self.text_color)
        self.text_label.setPalette(palette)
        
        # Add the text to the bubble
        bubble_layout.addWidget(self.text_label)
        
        # Set up the alignment based on sender
        if self.is_user:
            main_layout.addStretch(1)
            main_layout.addWidget(self.bubble)
            self.bubble.setStyleSheet(f"""
                #chatBubble {{
                    background-color: {self.user_bubble_color.name()};
                    border-radius: 15px;
                    border-bottom-right-radius: 5px;
                }}
            """)
        else:
            main_layout.addWidget(self.bubble)
            main_layout.addStretch(1)
            self.bubble.setStyleSheet(f"""
                #chatBubble {{
                    background-color: {self.assistant_bubble_color.name()};
                    border-radius: 15px;
                    border-bottom-left-radius: 5px;
                }}
            """)
        
        # Set size policy to adjust based on content
        self.bubble.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred
        )
        
        # Set maximum width for the bubble
        self.bubble.setMaximumWidth(400)
        
    def sizeHint(self):
        # Return the size hint from the bubble
        return self.bubble.sizeHint()
        
    def resizeEvent(self, event):
        # Handle resize events safely without touching text cursors
        super().resizeEvent(event)
        
    # Override paintEvent to avoid any text cursor operations
    def paintEvent(self, event):
        super().paintEvent(event)
