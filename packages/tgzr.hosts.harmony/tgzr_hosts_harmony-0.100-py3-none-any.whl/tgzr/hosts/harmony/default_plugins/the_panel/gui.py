
from PySide6.QtCore import Qt, QEvent, QObject, Signal, Slot  # type: ignore import from harmony
from PySide6.QtGui import QTextOption # type: ignore import from harmony
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTabWidget, QTextEdit  # type: ignore import from harmony


class InfoPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        layout = QVBoxLayout(self)

        import html
        import sys
        import tgzr.hosts.harmony
        import tgzr.hosts.harmony._version
        from tgzr.hosts.harmony.launch.settings import get_settings

        settings_text = get_settings().model_dump_json()

        escape = lambda x: html.escape(str(x))

        html = f"""
        <table>
        <tr>
            <td style="text-align: right">
            python
            </td>
            <td>
                {escape(sys.executable)}
            </td>
        </tr>
        <tr>
            <td style="text-align: right">
            tgzr.hosts.harmony
            </td>
            <td>
                {escape(tgzr.hosts.harmony)}
            </td>
        </tr>
        <tr>
            <td style="text-align: right">
            tgzr.hosts.harmony version
            </td>
            <td>
                {escape(tgzr.hosts.harmony._version.__version__)}
            </td>
        </tr>
        <tr>
            <td style="text-align: right">
            Settings
            </td>
            <td>
                <pre>{escape(settings_text)}</pre>
            </td>
        </tr>
        </table>
        """
        te = QTextEdit()
        te.setReadOnly(True)
        te.setWordWrapMode(QTextOption.NoWrap)
        te.setHtml(html)
        layout.addWidget(te)

class ThePanel(QWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("✨ My Harmony Plugin GUI ✨")

        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.tab_widget.addTab(InfoPanel(self.tab_widget), "Info")

    def add_tab(self, widget:QWidget, title:str)->None:
        self.tab_widget.addTab(widget, title)