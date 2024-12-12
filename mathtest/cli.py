import sys
import click
from PyQt5.QtWidgets import QApplication
from .questiontool import QuestionApp

@click.group()
@click.version_option()
def cli():
    ""


@cli.command(name="run")
def run():
    app = QApplication(sys.argv)
    window = QuestionApp()
    window.show()
    app.exec_()