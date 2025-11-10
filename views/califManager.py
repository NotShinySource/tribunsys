# views/califManager.py
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

class CalifManagerWindow(QWidget):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.setWindowTitle("Tribun System — Gestionar Calificaciones Tributarias")
        self.setFixedSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        top = QHBoxLayout()
        back = QPushButton("←")
        back.setFixedSize(36, 36)
        back.clicked.connect(self.go_back)
        top.addWidget(back)
        top.addStretch()
        main_layout.addLayout(top)

        title = QLabel("Gestión de Calificaciones Tributarias (pantalla de ejemplo)")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        info = QLabel("Aquí se implementará la lógica para administrar calificaciones.")
        info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info)

        self.setLayout(main_layout)

    def go_back(self):
        self.app_context['main_window'].open_menu()
