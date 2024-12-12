import os
import sqlite3
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLineEdit, QListWidget, QLabel,
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
                             QTextEdit, QFileDialog, QInputDialog, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from fuzzywuzzy import fuzz
import subprocess

class QuestionTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaTeX Question Tool")
        self.setGeometry(100, 100, 900, 700)

        # Initialize database
        self.db_path = "questions.db"
        self.init_db()

        # UI elements
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search questions by tag or text...")
        self.search_input.textChanged.connect(self.search_questions)

        self.question_list = QListWidget()
        self.question_list.itemClicked.connect(self.preview_question)

        self.preview_label = QLabel("Select a question to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedHeight(300)

        self.add_button = QPushButton("Add Question from File")
        self.add_button.clicked.connect(self.add_question)

        self.add_text_button = QPushButton("Add Question from Text")
        self.add_text_button.clicked.connect(self.add_question_from_text)

        self.edit_button = QPushButton("Edit Selected Question")
        self.edit_button.clicked.connect(self.edit_question)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter question title")

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter tags (comma-separated)")

        self.latex_input = QTextEdit()
        self.latex_input.setPlaceholderText("Enter LaTeX code for the question")

        self.compile_button = QPushButton("Compile Test")
        self.compile_button.clicked.connect(self.compile_test)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.question_list)
        layout.addWidget(self.preview_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.add_text_button)
        button_layout.addWidget(self.edit_button)
        layout.addLayout(button_layout)

        layout.addWidget(self.title_input)
        layout.addWidget(self.tag_input)
        layout.addWidget(self.latex_input)
        layout.addWidget(self.compile_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load questions
        self.load_questions()

    def init_db(self):
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    latex_code TEXT,
                    tags TEXT
                )
            """)
            conn.commit()
            conn.close()

    def load_questions(self):
        self.question_list.clear()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, tags FROM questions")
        for question_id, title, tags in cursor.fetchall():
            item = QListWidgetItem(f"{question_id}: {title} [{tags}]")
            item.setCheckState(Qt.Unchecked)
            self.question_list.addItem(item)
        conn.close()

    def search_questions(self):
        query = self.search_input.text().strip().lower()
        for i in range(self.question_list.count()):
            item = self.question_list.item(i)
            if fuzz.partial_ratio(query, item.text().lower()) >= 70:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def preview_question(self, item):
        question_id = int(item.text().split(":")[0])
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, tags, latex_code FROM questions WHERE id = ?", (question_id,))
        title, tags, latex_code = cursor.fetchone()
        conn.close()
        self.title_input.setText(title)
        self.tag_input.setText(tags)
        self.latex_input.setText(latex_code)
        self.preview_label.setText(f"<pre>{latex_code}</pre>")

    def add_question(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select LaTeX File", "", "LaTeX Files (*.tex)")
        if file_path:
            with open(file_path, "r") as file:
                latex_code = file.read()
            title = os.path.basename(file_path)
            tags, ok = QInputDialog.getText(self, "Add Tags", "Enter tags (comma-separated):")
            if ok:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO questions (title, latex_code, tags) VALUES (?, ?, ?)", (title, latex_code, tags))
                conn.commit()
                conn.close()
                self.load_questions()

    def add_question_from_text(self):
        title = self.title_input.text().strip()
        latex_code = self.latex_input.toPlainText().strip()
        tags, ok = QInputDialog.getText(self, "Add Tags", "Enter tags (comma-separated):")
        if ok:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO questions (title, latex_code, tags) VALUES (?, ?, ?)", (title, latex_code, tags))
            conn.commit()
            conn.close()
            self.load_questions()

    def edit_question(self):
        selected_items = self.question_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a question to edit.")
            return

        item = selected_items[0]
        question_id = int(item.text().split(":")[0])

        title = self.title_input.text().strip()
        latex_code = self.latex_input.toPlainText().strip()
        tags = self.tag_input.text().strip()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET title = ?, latex_code = ?, tags = ? WHERE id = ?", (title, latex_code, tags, question_id))
        conn.commit()
        conn.close()
        self.load_questions()
        QMessageBox.information(self, "Question Updated", "The question has been updated successfully.")

    def compile_test(self):
        selected_questions = []
        for i in range(self.question_list.count()):
            item = self.question_list.item(i)
            if item.checkState() == Qt.Checked:
                question_id = int(item.text().split(":")[0])
                selected_questions.append(question_id)

        if not selected_questions:
            QMessageBox.warning(self, "No Questions Selected", "Please select at least one question to compile.")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT latex_code FROM questions WHERE id IN ({})".format(
            ",".join("?" * len(selected_questions))), selected_questions)
        questions = cursor.fetchall()
        conn.close()

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Compiled Test", "", "LaTeX Files (*.tex)")
        if not output_path:
            return

        with open(output_path, "w") as file:
            file.write("\\documentclass{article}\n")
            file.write("\\begin{document}\n")
            for latex_code, in questions:
                file.write(latex_code + "\n\n")
            file.write("\\end{document}")

        QMessageBox.information(self, "Test Compiled", f"Test successfully compiled and saved to {output_path}.")

# Required to run the application
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = QuestionTool()
    window.show()
    sys.exit(app.exec_())
