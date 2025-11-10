# views/menu.py
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QMessageBox, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
import os

class HoverButton(QPushButton):
    def __init__(self, text, active=True):
        super().__init__(text)
        self.active = active
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style(normal=True)

    def update_style(self, normal=True):
        if not self.active:
            self.setStyleSheet("background-color: #bbbbbb; border-radius: 8px;")
        else:
            if normal:
                self.setStyleSheet("""
                    QPushButton{
                        background-color: #dddddd;
                        border-radius: 8px;
                    }
                """)
            else:
                # hover state
                self.setStyleSheet("""
                    QPushButton{
                        background-color: #bddfff;
                        border-radius: 8px;
                    }
                """)

    def enterEvent(self, event):
        if self.active:
            self.update_style(normal=False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.active:
            self.update_style(normal=True)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.active:
            # pressed color darker
            self.setStyleSheet("""
                QPushButton{
                    background-color: #1e40af;
                    color: white;
                    border-radius: 8px;
                }
            """)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active:
            self.update_style(normal=False)
        super().mouseReleaseEvent(event)


class MenuWindow(QWidget):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.setWindowTitle("Tribun System — Menú")
        self.setFixedSize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        # left logo
        left_frame = QFrame()
        left_frame.setFixedWidth(500)
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'logo.png')
        logo_path = os.path.normpath(logo_path)
        logo_label = QLabel()
        pix = QPixmap(logo_path)
        if not pix.isNull():
            pix = pix.scaled(420, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        left_layout.addWidget(logo_label)
        left_frame.setLayout(left_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setLineWidth(2)
        divider.setStyleSheet("color: #cccccc;")

        # right interactive area
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setContentsMargins(30, 30, 30, 30)

        user = self.app_context.get('current_user') or {}
        nombre = user.get('nombre', 'Usuario')
        rol = user.get('rol', 'client')
        welcome = QLabel(f"Bienvenido {nombre}.")
        welcome.setFont(QFont('Arial', 20))
        small = QLabel("¿Qué desea hacer?")
        small.setFont(QFont('Arial', 12))

        # Roles
        role = user.get('rol', 'client')

        # Definición de botones con visibilidad y activación según rol
        options = []

        if role == 'adminsys':
            options = [
                ("Gestionar Usuarios", True),
                ("Gestionar Calificaciones Tributarias", False),
                ("Carga Masiva de Datos", False),
                ("Gestionar Subsidios y Beneficios", False),
                ("Consultar y Filtrar Datos", False),
                ("Generar Reportes Tributarios", False),
            ]
        elif role == 'user':
            options = [
                ("Gestionar Calificaciones Tributarias", False),
                ("Carga Masiva de Datos", False),
                ("Gestionar Subsidios y Beneficios", False),
                ("Consultar y Filtrar Datos", False),
                ("Generar Reportes Tributarios", False),
            ]
        else:  # client
            options = [
                ("Sin opciones", False),
            ]

        right_layout.addWidget(welcome)
        right_layout.addWidget(small)
        right_layout.addSpacing(20)

        for text, active in options:
            btn = HoverButton(text, active=active)
            btn.clicked.connect(lambda checked, t=text: self.handle_button(t))
            btn.setFixedWidth(320)
            right_layout.addWidget(btn)
            right_layout.addSpacing(10)

        right_frame.setLayout(right_layout)

        # Flecha de retroceso en la esquina superior izquierda de toda la ventana
        back_btn = QPushButton("←")
        back_btn.setFixedSize(50, 50)
        back_btn.setStyleSheet("""
            QPushButton{
                font-size: 20px;
                font-weight: bold;
                color: black;
                border-radius: 10px;
            }
            QPushButton:hover{
                background-color: #a6c8ff;
            }
        """)
        back_btn.clicked.connect(self.attempt_logout)

        # Layout superior con flecha
        top_layout = QHBoxLayout()
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        top_layout.setContentsMargins(10, 10, 10, 10)

        # Layout principal horizontal con logo y menú
        content_layout = QHBoxLayout()
        content_layout.addWidget(left_frame)
        content_layout.addWidget(divider)
        content_layout.addWidget(right_frame)

        # Layout final de la ventana
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)


    def handle_button(self, text):
        # Para el prototipo abrimos ventanas de ejemplo para 2 botones
        if text == "Gestionar Usuarios":
            self.app_context['main_window'].open_user_manager()
        elif text == "Gestionar Calificaciones Tributarias":
            self.app_context['main_window'].open_calif_manager()
        else:
            QMessageBox.information(self, "Prototipo", f"Ventana de '{text}' (no implementada aún).")

    def attempt_logout(self):
        r = QMessageBox.question(self, "Cerrar sesión", "¿Quieres cerrar la sesión?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r == QMessageBox.Yes:
            # volver al login
            self.app_context['current_user'] = None
            self.app_context['main_window'].open_login()
