import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QFileDialog, QDialog,
    QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt
from fuzzywuzzy import fuzz
from jinja2 import Template
import subprocess

# Database Initialization
DB_FILE = "questions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            tags TEXT
        )
    """)
    conn.commit()
    conn.close()


class QuestionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Question Manager")
        self.setGeometry(100, 100, 800, 600)

        # Main Layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Splitter to separate list and preview pane
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Left Panel - Question List and Buttons
        left_panel = QVBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        self.splitter.addWidget(left_widget)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search questions...")
        self.search_bar.textChanged.connect(self.search_questions)
        left_panel.addWidget(self.search_bar)

        # Question List
        self.question_list = QListWidget()
        self.question_list.itemSelectionChanged.connect(self.update_preview)
        left_panel.addWidget(self.question_list)

        # Buttons
        button_layout = QHBoxLayout()
        left_panel.addLayout(button_layout)

        self.add_button = QPushButton("Add Question")
        self.add_button.clicked.connect(self.add_question)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Question")
        self.edit_button.clicked.connect(self.edit_question)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Question")
        self.delete_button.clicked.connect(self.delete_question)
        button_layout.addWidget(self.delete_button)

        self.generate_button = QPushButton("Generate Test PDF")
        self.generate_button.clicked.connect(self.generate_pdf)
        left_panel.addWidget(self.generate_button)

        # Right Panel - Preview Pane
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.splitter.addWidget(self.preview_text)

        # Load Questions
        self.load_questions()

    def load_questions(self):
        self.question_list.clear()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, tags FROM questions")
        for qid, title, tags in cursor.fetchall():
            item = QListWidgetItem(f"{title} [{tags}]")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, qid)
            self.question_list.addItem(item)
        conn.close()

    def search_questions(self):
        query = self.search_bar.text()
        self.question_list.clear()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, tags FROM questions")
        for qid, title, tags in cursor.fetchall():
            if fuzz.partial_ratio(query.lower(), title.lower()) > 60 or fuzz.partial_ratio(query.lower(), tags.lower()) > 60:
                item = QListWidgetItem(f"{title} [{tags}]")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, qid)
                self.question_list.addItem(item)
        conn.close()

    def add_question(self):
        dialog = QuestionForm()
        if dialog.exec_():
            self.load_questions()

    def edit_question(self):
        item = self.question_list.currentItem()
        if item:
            qid = item.data(Qt.UserRole)
            dialog = QuestionForm(qid)
            if dialog.exec_():
                self.load_questions()

    def delete_question(self):
        item = self.question_list.currentItem()
        if item:
            qid = item.data(Qt.UserRole)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM questions WHERE id=?", (qid,))
            conn.commit()
            conn.close()
            self.load_questions()

    def update_preview(self):
        item = self.question_list.currentItem()
        if item:
            qid = item.data(Qt.UserRole)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM questions WHERE id=?", (qid,))
            content = cursor.fetchone()[0]
            conn.close()
            self.preview_text.setText(content)

    def generate_pdf(self):
        selected_questions = []
        for index in range(self.question_list.count()):
            item = self.question_list.item(index)
            if item.checkState() == Qt.Checked:
                qid = item.data(Qt.UserRole)
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT title, content FROM questions WHERE id=?", (qid,))
                title, content = cursor.fetchone()
                selected_questions.append({"title": title, "content": content})
                conn.close()

        if not selected_questions:
            QMessageBox.warning(self, "No Selection", "Select at least one question to generate the test.")
            return

        template = Template(r"""
        \documentclass{article}
        \usepackage{amsmath}
        \begin{document}
        {% for q in questions %}
        \section*{{ q.title }}
        {{ q.content }}
        \newpage
        {% endfor %}
        \end{document}
        """)

        with open("test_document.tex", "w") as f:
            f.write(template.render(questions=selected_questions))

        subprocess.run(["pdflatex", "test_document.tex"])
        QMessageBox.information(self, "Success", "Test document compiled successfully!")


class QuestionForm(QDialog):
    def __init__(self, qid=None):
        super().__init__()
        self.setWindowTitle("Add/Edit Question")
        self.qid = qid
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Question Title")
        self.layout.addWidget(self.title_input)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Enter LaTeX code here...")
        self.layout.addWidget(self.content_input)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Tags (comma-separated)")
        self.layout.addWidget(self.tags_input)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_question)
        self.layout.addWidget(self.save_button)

        if qid:
            self.load_question()

    def load_question(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT title, content, tags FROM questions WHERE id=?", (self.qid,))
        title, content, tags = cursor.fetchone()
        self.title_input.setText(title)
        self.content_input.setText(content)
        self.tags_input.setText(tags)
        conn.close()

    def save_question(self):
        title = self.title_input.text()
        content = self.content_input.toPlainText()
        tags = self.tags_input.text()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if self.qid:
            cursor.execute("UPDATE questions SET title=?, content=?, tags=? WHERE id=?", (title, content, tags, self.qid))
        else:
            cursor.execute("INSERT INTO questions (title, content, tags) VALUES (?, ?, ?)", (title, content, tags))
        conn.commit()
        conn.close()
        self.accept()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = QuestionApp()
    window.show()
    sys.exit(app.exec_())
