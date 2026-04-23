import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
    QLabel, QStackedWidget, QFrame
)
from PySide6.QtCore import QThread, Signal
from llm import chat
from database import create_tables, seed_data, search_products

class AIThread(QThread):
    response_ready = Signal(str)

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input

    def run(self):
        response = chat(self.user_input)
        self.response_ready.emit(response)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lidl Assistant")
        self.setMinimumSize(700, 600)
        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        central.setStyleSheet("background: #004F9F;")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #004F9F; padding: 12px;")
        header_layout = QHBoxLayout(header)
        title = QLabel("Lidl Assistant")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        main_layout.addWidget(header)

        # Navigation
        nav = QFrame()
        nav.setStyleSheet("background: #FFD700; border-bottom: 2px solid #e6c200;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.btn_chat = QPushButton("AI Assistant")
        self.btn_db = QPushButton("Database")

        for btn in [self.btn_chat, self.btn_db]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 12px 24px;
                    border: none;
                    font-size: 14px;
                    background: #FFD700;
                    color: #333;
                }
                QPushButton:hover { background: #e6c200; }
            """)

        self.btn_chat.clicked.connect(lambda: self.switch_tab(0))
        self.btn_db.clicked.connect(lambda: self.switch_tab(1))
        nav_layout.addWidget(self.btn_chat)
        nav_layout.addWidget(self.btn_db)
        nav_layout.addStretch()
        main_layout.addWidget(nav)

        # Pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #004F9F;")
        self.stack.addWidget(self.build_chat_page())
        self.stack.addWidget(self.build_db_page())
        main_layout.addWidget(self.stack)

        self.switch_tab(0)

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        active = "padding: 12px 24px; font-size: 14px; background: #e6c200; color: black; font-weight: bold; border: none; border-bottom: 2px solid black;"
        inactive = "padding: 12px 24px; border: none; font-size: 14px; background: #FFD700; color: #333;"
        self.btn_chat.setStyleSheet(active if index == 0 else inactive)
        self.btn_db.setStyleSheet(active if index == 1 else inactive)

    def build_chat_page(self):
        page = QWidget()
        page.setStyleSheet("background: #004F9F;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background: #004F9F;
            color: white;
            border: 1px solid #003d7a;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
        """)
        self.chat_display.append("<b style='color:#FFD700'>Assistant:</b> <span style='color:white'>Hello! I am the Lidl assistant. How can I help you?</span>")
        layout.addWidget(self.chat_display)

        input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message...")
        self.chat_input.setStyleSheet("""
            padding: 10px;
            border: 1px solid #003d7a;
            border-radius: 8px;
            font-size: 14px;
            background: #003d7a;
            color: white;
        """)
        self.chat_input.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background: #FFD700;
                color: black;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: #e6c200; }
        """)
        send_btn.clicked.connect(self.send_message)

        input_row.addWidget(self.chat_input)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        return page

    def send_message(self):
        user_input = self.chat_input.text().strip()
        if not user_input:
            return

        self.chat_display.append(f"<b style='color:#FFD700'>You:</b> <span style='color:white'>{user_input}</span>")
        self.chat_input.clear()
        self.chat_display.append("<i style='color:#aaa'>Assistant is typing...</i>")

        self.ai_thread = AIThread(user_input)
        self.ai_thread.response_ready.connect(self.show_response)
        self.ai_thread.start()

    def show_response(self, response):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()
        self.chat_display.append(f"<b style='color:#FFD700'>Assistant:</b> <span style='color:white'>{response}</span>")

    def build_db_page(self):
        page = QWidget()
        page.setStyleSheet("background: #004F9F;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)

        search_row = QHBoxLayout()
        self.db_input = QLineEdit()
        self.db_input.setPlaceholderText("Search product or category (e.g. Lactate, Mere...)")
        self.db_input.setStyleSheet("""
            padding: 10px;
            border: 1px solid #003d7a;
            border-radius: 8px;
            font-size: 14px;
            background: #003d7a;
            color: white;
        """)
        self.db_input.returnPressed.connect(self.search_db)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background: #FFD700;
                color: black;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background: #e6c200; }
        """)
        search_btn.clicked.connect(self.search_db)

        search_row.addWidget(self.db_input)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        self.db_results = QTextEdit()
        self.db_results.setReadOnly(True)
        self.db_results.setStyleSheet("""
            background: #004F9F;
            color: white;
            border: 1px solid #003d7a;
            border-radius: 8px;
            padding: 8px;
            font-size: 14px;
        """)
        self.db_results.setText("Enter a search term to see products.")
        layout.addWidget(self.db_results)

        return page

    def search_db(self):
        query = self.db_input.text().strip()
        if not query:
            return

        results = search_products(query)

        if not results:
            self.db_results.setHtml("<span style='color:white'>No products found.</span>")
            return

        text = f"<b style='color:#FFD700'>Results for '{query}':</b><br><br>"
        text += "<table width='100%' cellspacing='0' cellpadding='0'>"
        text += "<tr style='background:#FFD700;'><th style='color:black; padding:8px;'>Name</th><th style='color:black; padding:8px;'>Category</th><th style='color:black; padding:8px;'>Price</th><th style='color:black; padding:8px;'>Stock</th></tr>"

        for i, p in enumerate(results):
            bg = "#003d7a" if i % 2 == 0 else "#004F9F"
            text += f"<tr><td style='background:{bg}; color:white; padding:8px;'>{p['nume']}</td><td style='background:{bg}; color:white; padding:8px;'>{p['categorie']}</td><td style='background:{bg}; color:white; padding:8px;'>{p['pret']} RON</td><td style='background:{bg}; color:white; padding:8px;'>{p['stoc']}</td></tr>"

        text += "</table>"
        self.db_results.setHtml(text)


if __name__ == "__main__":
    create_tables()
    seed_data()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())