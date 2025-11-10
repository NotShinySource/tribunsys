import sys
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtCore import Qt
import os

# importar vistas
import db_connection as fb
from views.login import LoginWindow
from views.menu import MenuWindow
from views.califManager import CalifManagerWindow
from views.userManager import UserManagerWindow

class MainApp:
    def __init__(self):
        # app-level context que pasaremos a las vistas
        self.context = {
            'current_user': None,
            'auth_fn': fb.authenticate_user,
            'main_window': self
        }
        # inicializamos firebase (será perezoso si no hay llave)
        try:
            fb.init_firebase()
        except Exception as e:
            print("Advertencia: no se pudo inicializar Firebase. Asegúrate de colocar serviceAccount.json en assets/db/")
            print("Error:", e)

        # vistas
        self.login_win = LoginWindow(self.context)
        if self.context.get('current_user') is None:
            self.context['current_user'] = {}
        self.menu_win = MenuWindow(self.context)
        self.calif_win = CalifManagerWindow(self.context)
        self.user_win = UserManagerWindow(self.context)

        # para que cada vista pueda referenciar main window
        self.context['login_win'] = self.login_win
        self.context['menu_win'] = self.menu_win
        self.context['calif_win'] = self.calif_win
        self.context['user_win'] = self.user_win

    def open_login(self):
        self.hide_all()
        self.login_win.reset_fields()  # limpia los campos al mostrar login
        self.login_win.show()

    def open_menu(self):
        self.hide_all()
        self.menu_win = MenuWindow(self.context)  # reconstruir para actualizar nombre/rol
        self.menu_win.show()

    def open_calif_manager(self):
        self.hide_all()
        self.calif_win.show()

    def open_user_manager(self):
        self.hide_all()
        self.user_win.show()

    def hide_all(self):
        for w in [self.login_win, self.menu_win, self.calif_win, self.user_win]:
            try:
                w.hide()
            except:
                pass

def confirm_exit(event):
    reply = QMessageBox.question(None, 'Salir', "¿Estás seguro?", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
    if reply == QMessageBox.Yes:
        return True
    return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # fuerza tamaño de ventana - la manejan las clases
    main = MainApp()
    main.open_login()
    original_close = QWidget.closeEvent
    def custom_close(self, event):
        if confirm_exit(event):
            event.accept()
        else:
            event.ignore()
    QWidget.closeEvent = custom_close

    sys.exit(app.exec())