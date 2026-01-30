import logging

from PyQt6 import QtWidgets
from PyQt6.QtCore import QObject, pyqtSignal


class TextLoggerWidget(logging.Handler, QObject):
    """
    Logger handler to print log in a QTextEdit widget.

    Signals
    -------
    sig_append_text : internal, emits the log message to be printed in the text box.
    """

    sig_append_text = pyqtSignal(str)
    flushOnClose = True

    def __init__(self, parent):
        super().__init__()
        QObject.__init__(self)

        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

        self.sig_append_text.connect(self.widget.appendPlainText)

    def emit(self, msg):
        msg = self.format(msg)
        self.sig_append_text.emit(msg)
