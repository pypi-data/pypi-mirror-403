from pathlib import Path

from PyQt6 import QtWidgets
from PyQt6.QtCore import QSortFilterProxyModel
from PyQt6.QtGui import QFileSystemModel


class FileBrowser(QtWidgets.QTreeView):
    """File browser and picker."""

    def __init__(self, startDir: str | Path = ""):
        super().__init__()

        self.fsModel = QFileSystemModel()
        self.fsModel.setRootPath("")

        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.fsModel)

        self.setModel(self.proxyModel)

        start_dir = Path(startDir)
        if start_dir.is_file():
            start_dir = str(start_dir.parent)
        elif start_dir.is_dir():
            start_dir = str(start_dir)
        else:
            start_dir = ""

        index = self.fsModel.index(start_dir)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.setRootIndex(proxyIndex)

    def set_directory(self, dirname: str | Path):
        """Set the current folder in the tree view."""
        dirname = str(dirname)

        index = self.fsModel.index(dirname)
        proxyIndex = self.proxyModel.mapFromSource(index)
        self.setRootIndex(proxyIndex)

    def get_current_file(self) -> str:
        """Return the currently selected file."""
        index = self.currentIndex()
        sourceIndex = self.proxyModel.mapToSource(index)

        return self.fsModel.filePath(sourceIndex)
