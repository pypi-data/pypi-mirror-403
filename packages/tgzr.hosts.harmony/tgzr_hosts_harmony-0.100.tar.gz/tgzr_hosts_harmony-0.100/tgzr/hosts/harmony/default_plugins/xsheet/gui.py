from PySide6.QtWidgets import (  # type: ignore (imported from harmony)
    QTableView,
    QWidget,
    QVBoxLayout,
    QPushButton,
)
from PySide6.QtCore import QAbstractTableModel, Qt  # type: ignore (imported from harmony)

from .xsheet import XSheet, get_xsheet


class XSheetWidget(QWidget):
    """
    A widget to display a tgzr.hosts.harmony.default_plugins.xsheet.xsheet.XSheet
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    def set_xsheet(self, xsheet: XSheet):
        model = XSheetModel(xsheet)
        self.table_view.setModel(model)


class XSheetModel(QAbstractTableModel):

    def __init__(self, xsheet: XSheet, parent=None):
        super().__init__(parent)
        self._xsheet = xsheet

        self._data = self._xsheet.rows_without_duplicate_keys()
        self._headers = ("Frame",) + self._xsheet.elements()

    def rowCount(self, parent=None):
        """
        Returns the number of rows in the model.
        """
        return len(self._data)

    def columnCount(self, parent=None):
        """
        Returns the number of columns in the model.
        """
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the data for a given index and role.
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            key = self._headers[col]
            return str(self._data[row].get(key, ""))

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the header data for a given section, orientation, and role.
        """
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return self._headers[section]
        return None


class XSheetPanel(QWidget):
    """
    A panel showing a tgzr.hosts.harmony.default_plugins.xsheet.xsheet.XSheet
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        b = QPushButton(text="Load from scene", parent=self)
        b.clicked.connect(self.on_refresh)
        layout.addWidget(b)

        self.xsheet_widget = XSheetWidget(self)
        layout.addWidget(self.xsheet_widget)

        self.setLayout(layout)

    def set_xsheet(self, xsheet: XSheet):
        self.xsheet_widget.set_xsheet(xsheet)
        self.setWindowTitle(f"XSheet {xsheet.name()}")
        self.setMinimumSize(400, 300)

    def on_refresh(self):
        self.set_xsheet(get_xsheet())