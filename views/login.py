# views/login.py
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QSize
import os

class LoginWindow(QWidget):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context  # referencia al controlador principal (main.py)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Tribun System — Login")
        self.setFixedSize(1000, 700)

        # Left: logo area (ocupa la mitad)
        left_frame = QFrame()
        left_frame.setFixedWidth(500)
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'logo.png')
        logo_path = os.path.normpath(logo_path)
        logo_label = QLabel()
        pix = QPixmap(logo_path)
        if not pix.isNull():
            pix = pix.scaled(QSize(420, 420), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        left_layout.addWidget(logo_label)
        left_frame.setLayout(left_layout)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setLineWidth(2)
        divider.setStyleSheet("color: #cccccc;")

        # Right: interactive area
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)

        welcome = QLabel("¡Bienvenido!")
        welcome.setFont(QFont('Arial', 22))
        welcome.setAlignment(Qt.AlignCenter)

        small = QLabel("Ingresa tu RUT")
        small.setFont(QFont('Arial', 10))
        self.rut_input = QLineEdit()
        self.rut_input.setFixedWidth(300)
        self.rut_input.setPlaceholderText("(ej. 12345678-9)")

        pass_label = QLabel("Ingresa tu Contraseña")
        self.pass_input = QLineEdit()
        self.pass_input.setFixedWidth(300)
        self.pass_input.setPlaceholderText("********")
        self.pass_input.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setFixedWidth(180)
        login_btn.clicked.connect(self.attempt_login)

        right_layout.addWidget(welcome)
        right_layout.addSpacing(40)
        right_layout.addWidget(small)
        right_layout.addWidget(self.rut_input)
        right_layout.addSpacing(8)
        right_layout.addWidget(pass_label)
        right_layout.addWidget(self.pass_input)
        right_layout.addSpacing(20)
        right_layout.addWidget(login_btn)

        right_frame.setLayout(right_layout)

        # Layout horizontal
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_frame)
        main_layout.addWidget(divider)
        main_layout.addWidget(right_frame)
        self.setLayout(main_layout)

    def attempt_login(self):
        rut = self.rut_input.text().strip()
        password = self.pass_input.text()
        if not rut or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingrese RUT y contraseña.")
            return
        user = self.app_context['auth_fn'](rut, password)
        if user:
            # pasa al menú
            self.app_context['current_user'] = user
            self.app_context['main_window'].open_menu()
        else:
            QMessageBox.critical(self, "Error", "RUT o contraseña incorrectos.")
    
    def reset_fields(self):
        self.rut_input.clear()
        self.pass_input.clear()
