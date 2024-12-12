import click
from PyQt5.QtWidgets import QApplication
from .questiontool import QuestionTool

@click.group()
@click.version_option()
def cli():
    ""


@cli.command(name="run")
def run():
    app = QApplication([])
    window = QuestionTool()
    window.show()
    app.exec_()