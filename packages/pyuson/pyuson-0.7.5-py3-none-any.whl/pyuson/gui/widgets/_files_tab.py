"""File browser with folder section button."""

from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal, pyqtSlot

from ._file_browser import FileBrowser


class FileBrowserWidget(QtWidgets.QWidget):
    """
    File browser and picker.

    Signals
    -------
    sig_file_selected : emits when an item is double-clicked. Emits True if the file is
        a TOML file, False otherwise, and the file path.
    sig_autoload_changed : emits when the autoload checkbox is changed.
    """

    sig_file_selected = pyqtSignal(bool, str)
    sig_autoload_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Build the push button
        self.button_open_folder = QtWidgets.QPushButton("Open Folder...", self)
        self.button_open_folder.clicked.connect(self.open_folder)

        # Build the load data checkbox
        self.checkbox_autoload_data = QtWidgets.QCheckBox(
            "Load data automatically", self
        )
        self.checkbox_autoload_data.setChecked(True)
        self.checkbox_autoload_data.stateChanged.connect(self.sig_autoload_changed)

        # Build the file browser tree view
        self.file_browser = FileBrowser()
        self.file_browser.doubleClicked.connect(self.select_file)

        # Define layout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.button_open_folder, 0, 0)
        grid.addWidget(self.checkbox_autoload_data, 0, 1)
        grid.addWidget(self.file_browser, 1, 0, -1, 2)

        # Create widget
        self.setLayout(grid)

    @pyqtSlot()
    def open_folder(self):
        """
        Open a folder picker.

        Callback for the "Open Folder" button in the file browser.
        """
        dirname = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open folder...",
        )
        if dirname:
            self.file_browser.set_directory(dirname)

    @pyqtSlot()
    def select_file(self):
        """
        Load the file selected in the file browser tab.

        Callback for when a file is double-clicked in the file browser tab.
        """
        filepath = self.file_browser.get_current_file()

        if filepath.endswith(".toml"):
            # This is a configuration file
            self.sig_file_selected.emit(True, filepath)
        else:
            # Not really sure but let's assume it is a data file used to change the
            # experiment ID
            self.sig_file_selected.emit(False, filepath)
