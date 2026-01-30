from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt


class DropListWidget(QtWidgets.QListWidget):
    """A list widget with drag & drop."""

    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSortingEnabled(True)

    def move_item_from_other(
        self, item: QtWidgets.QListWidgetItem, otherList: QtWidgets.QListWidget
    ):
        """Move `item` from `otherList` to this list."""
        if not self.findItems(item.text(), Qt.MatchFlag.MatchExactly):
            otherList.takeItem(otherList.indexFromItem(item).row())
            self.addItem(item)

    def add_selected_items_from_other(self, otherList: QtWidgets.QListWidget):
        """Take selected items from `otherList` list and add it to this list."""
        selectedItems = otherList.selectedItems()
        for item in selectedItems:
            self.move_item_from_other(item, otherList)

    def add_all_items_from_other(self, otherList: QtWidgets.QListWidget):
        """Take all items from `other` list and add it to this list."""
        while otherList.count() != 0:
            item = otherList.takeItem(0)
            if item is not None and (
                not self.findItems(item.text(), Qt.MatchFlag.MatchExactly)
            ):
                self.addItem(item)

    def get_list_of_items(self) -> list[str]:
        """Get the list of items as strings."""
        return [self.item(idx).text() for idx in range(self.count())]
