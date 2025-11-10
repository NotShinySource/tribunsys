# views/userManager.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout,
    QLineEdit, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import db_connection as fb
import hashlib


# Botón con hover consistente con menu.py
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
                    QPushButton {
                        background-color: #dddddd;
                        border-radius: 8px;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QPushButton {
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
            self.setStyleSheet("""
                QPushButton {
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


class UserManagerWindow(QWidget):
    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context
        self.setWindowTitle("Tribun System — Gestionar Usuarios")
        self.setFixedSize(1000, 700)

        # Estado de la vista: "main", "type_selection", "form"
        self.current_view = "main"
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignTop)
        self.main_layout.setContentsMargins(60, 20, 60, 30)
        self.main_layout.setSpacing(10)

        # Flecha de retroceso
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(50, 50)
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                color: black;
                border-radius: 10px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #a6c8ff;
            }
        """)
        self.back_btn.clicked.connect(self.handle_back)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.back_btn)
        top_layout.addStretch()
        self.main_layout.addLayout(top_layout)

        # Contenedor principal dinámico
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignCenter | Qt.AlignHCenter)
        self.content_layout.setContentsMargins(5, 100, 5, 5)
        self.content_layout.setSpacing(16)
        self.main_layout.addLayout(self.content_layout)

        self.setLayout(self.main_layout)
        self.show_main_menu()

    # --- Vista principal (gestión) ---
    def show_main_menu(self):
        self.current_view = "main"
        self.clear_content()

        title = QLabel("Gestión de Usuarios")
        title.setFont(QFont('Arial', 22))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        self.content_layout.addWidget(title)
        self.content_layout.addSpacing(40)

        btn_agregar = HoverButton("Agregar Usuario")
        btn_agregar.setFixedWidth(400)
        btn_agregar.setFont(QFont('Arial', 12))
        btn_eliminar = HoverButton("Eliminar Usuario", active=False)
        btn_eliminar.setFont(QFont('Arial', 12))
        btn_agregar.clicked.connect(self.show_user_type_selection)

        self.content_layout.addWidget(btn_agregar)
        self.content_layout.addWidget(btn_eliminar)

    # --- Vista selección de tipo ---
    def show_user_type_selection(self):
        self.current_view = "type_selection"
        self.clear_content()

        title = QLabel("¿Qué tipo deseas agregar?")
        title.setFont(QFont('Arial', 22))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        self.content_layout.addWidget(title)
        self.content_layout.addSpacing(40)

        btn_cliente = HoverButton("Cliente")
        btn_interno = HoverButton("Usuario Interno")
        btn_admin = HoverButton("Administrador del Sistema")

        btn_cliente.setFixedWidth(400)
        btn_cliente.setFont(QFont('Arial', 12))
        btn_interno.setFont(QFont('Arial', 12))
        btn_admin.setFont(QFont('Arial', 12))

        btn_cliente.clicked.connect(lambda: self.show_user_form("client"))
        btn_interno.clicked.connect(lambda: self.show_user_form("user"))
        btn_admin.clicked.connect(lambda: self.show_user_form("adminsys"))

        self.content_layout.addWidget(btn_cliente)
        self.content_layout.addWidget(btn_interno)
        self.content_layout.addWidget(btn_admin)

    # --- Vista formulario de creación ---
    def show_user_form(self, user_type):
        self.current_view = "form"
        self.clear_content()
        self.fields = {}

        # --- Scroll area para formulario ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setAlignment(Qt.AlignTop)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(14)

        if user_type == "client":
            title_text = "Agregar Cliente"
        elif user_type == "adminsys":
            title_text = "Agregar Administrador"
        else:
            title_text = "Agregar Usuario"

        title = QLabel(title_text)
        title.setFont(QFont('Arial', 18))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        form_layout.addWidget(title)
        form_layout.addSpacing(12)

        # Helper para añadir campos
        def add_field(label_text):
            lbl = QLabel(label_text)
            lbl.setFont(QFont('Arial', 11))
            lbl.setAlignment(Qt.AlignLeft)
            inp = QLineEdit()
            inp.setFixedWidth(520)
            inp.setMinimumHeight(30)
            form_layout.addWidget(lbl)
            form_layout.addWidget(inp)
            form_layout.addSpacing(8)
            self.fields[label_text.lower()] = inp

        # Campos comunes
        for field in ["Rut", "Nombre", "Apellido Paterno", "Apellido Materno", "Email", "Password"]:
            add_field(field)

        # Campos cliente
        if user_type == "client":
            for field in ["Razon Social", "Sector Economico", "Direccion", "Pais"]:
                add_field(field)

        # Campo de autorización admin
        if user_type == "adminsys":
            lbl_auth = QLabel("Contraseña de autorización (tu contraseña actual):")
            lbl_auth.setFont(QFont('Arial', 11))
            inp_auth = QLineEdit()
            inp_auth.setEchoMode(QLineEdit.Password)
            inp_auth.setFixedWidth(520)
            form_layout.addWidget(lbl_auth)
            form_layout.addWidget(inp_auth)
            self.auth_input = inp_auth
            form_layout.addSpacing(8)

        # Botón agregar
        form_layout.addSpacing(10)
        if user_type == "client":
            btn_add = HoverButton("Agregar Cliente")
        elif user_type == "adminsys":
            btn_add = HoverButton("Agregar Administrador")
        else:
            btn_add = HoverButton("Agregar Usuario")
        btn_add.setFixedWidth(320)
        btn_add.setFont(QFont('Arial', 12))
        btn_add.clicked.connect(lambda: self.add_user(user_type))
        form_layout.addWidget(btn_add, alignment=Qt.AlignCenter)

        scroll_area.setWidget(form_container)
        self.content_layout.addWidget(scroll_area)

    # --- Lógica de creación ---
    def add_user(self, user_type):
        if user_type == "adminsys":
            if not hasattr(self, "auth_input"):
                QMessageBox.warning(self, "Error", "Debe ingresar una contraseña de autorización.")
                return

            current_user = self.app_context.get("current_user", None)
            if not current_user:
                QMessageBox.critical(self, "Error", "No hay sesión activa.")
                return

            entered_pass_hash = hashlib.sha256(self.auth_input.text().encode()).hexdigest()
            if entered_pass_hash != current_user.get("password"):
                QMessageBox.warning(self, "Error", "Contraseña de autorización incorrecta.")
                return

        data = {k.replace(" ", "_").lower(): v.text() for k, v in self.fields.items()}
        if "password" in data and data["password"]:
            data["password"] = hashlib.sha256(data["password"].encode()).hexdigest()
        data["rol"] = user_type

        ok = fb.create_client(data) if user_type == "client" else fb.create_user(data)
        if ok:
            QMessageBox.information(self, "Éxito", f"Usuario {data.get('nombre')} agregado correctamente.")
            self.show_main_menu()
        else:
            QMessageBox.critical(self, "Error", "No se pudo agregar el usuario.")

    # --- Botón de retroceso ---
    def handle_back(self):
        if self.current_view == "main":
            self.app_context['main_window'].open_menu()
        elif self.current_view == "form":
            self.show_user_type_selection()
        else:
            self.show_main_menu()

    # --- Limpiar contenido dinámico ---
    def clear_content(self):
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
            else:
                self.content_layout.removeItem(item)
