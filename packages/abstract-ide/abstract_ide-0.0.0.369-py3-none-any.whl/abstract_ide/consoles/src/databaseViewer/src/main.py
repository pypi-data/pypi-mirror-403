from .imports import *
from PyQt6.QtWidgets import QSplitter
from PyQt6.QtCore import Qt
from abstract_ide.consoles.src.logConsole.src.main import logConsole

class databaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        initFuncs(self)
        self.setWindowTitle("Database Browser")

        self.browser = None
        self.controller = None

        self._build_ui()
        self._connect_signals()


    def _build_ui(self):
        self.tables = QListWidget()
        self.columns = QListWidget()
        self.table_view = QTableView()
        self.search_column = QLineEdit()
        self.search_column.setPlaceholderText("Column name")

        self.search_value = QLineEdit()
        self.search_value.setPlaceholderText("Search value")

        self.search_btn = QPushButton("Search")

        search_row = QHBoxLayout()
        search_row.addWidget(self.search_column)
        search_row.addWidget(self.search_value)
        search_row.addWidget(self.search_btn)


        self.refresh_btn = QPushButton("Refresh")
        self.export_btn = QPushButton("Export")
        self.delete_btn = QPushButton("Delete Table")
        self.connect_btn = QPushButton("Connect")

        toolbar = QHBoxLayout()
        for b in (
            self.connect_btn,
            self.refresh_btn,
            self.export_btn,
            self.delete_btn,
        ):
            toolbar.addWidget(b)

        left = QVBoxLayout()
        left.addWidget(self.tables)
        left.addWidget(self.columns)

        self.log_console = logConsole(self)

        self.search_btn.clicked.connect(self.run_search)
        splitter = QSplitter(Qt.Orientation.Vertical)
        right = QVBoxLayout()
        right.addLayout(search_row)
        right.addWidget(splitter)
        splitter.addWidget(self.table_view)
        splitter.addWidget(self.log_console)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        right = QVBoxLayout()
        right.addWidget(splitter)


        layout = QHBoxLayout()
        layout.addLayout(left, 1)
        layout.addLayout(right, 3)

        root = QVBoxLayout()
        root.addLayout(toolbar)
        root.addLayout(layout)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def _connect_signals(self):
        self.connect_btn.clicked.connect(self.prompt_for_connection)

    def prompt_for_connection(self):
        dialog = DatabaseConnectionDialog(self)
        if dialog.exec():
            params = dialog.get_values()
            self.connect_database(**params)

    def connect_database(self, dbUrl=None, dbPath=None):
       
            if not dbUrl and not dbPath:
                raise ValueError("You must provide either a dbUrl or dbPath")

            self.browser = DatabaseBrowser(
                dbUrl=dbUrl if dbUrl else None,
                dbPath=dbPath if dbPath else None,
            )
            self.controller = DBController(self, self.browser)
            self.log_console.append_line("✅ Connected to database")
            self.controller.load_tables()
    def run_search(self):
        table_item = self.tables.currentItem()
        if not table_item:
            return

        table = table_item.text()
        column = self.search_column.text().strip()
        value = self.search_value.text().strip()

        if not column:
            return

        df = self.browser.search_table(
            table_name=table,
            column_name=column,
            search_value=value,
            print_value=False,
        )

        if df is not None:
            self.table_view.setModel(PandasTableModel(df))

    def start():
        startConsole(databaseViewer)
