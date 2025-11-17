import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QTableWidget, QTableWidgetItem, 
    QProgressBar, QTextEdit, QMessageBox, QHeaderView, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor, QDragEnterEvent, QDropEvent


class FileDropZone(QFrame):
    """Zona de drag & drop para archivos"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        self.setFixedHeight(200)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #E94E1B;
                background-color: #fef5f1;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("📤")
        icon_label.setFont(QFont("Arial", 48))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(icon_label)
        
        text_label = QLabel("Arrastrar archivo CSV/Excel aquí\no hacer clic para seleccionar")
        text_label.setFont(QFont("Arial", 11))
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #7f8c8d;")
        text_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(text_label)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            if file_path.endswith(('.csv', '.xlsx', '.xls')):
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Archivo inválido", 
                                  "Por favor seleccione un archivo CSV o Excel")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar archivo", "",
                "Archivos CSV/Excel (*.csv *.xlsx *.xls)"
            )
            if file_path:
                self.file_dropped.emit(file_path)


class CargaMasivaContent(QWidget):
    """Contenido de carga masiva (sin ser ventana independiente)"""
    
    back_requested = pyqtSignal()
    
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.file_path = None
        self.dataframe = None
        self.validation_passed = False
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        # Scroll area principal
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f5f6fa; }")
        
        # Contenido
        content_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        
        # Header con botón volver
        self.add_header(main_layout)
        
        # Zona de carga
        self.add_file_zone(main_layout)
        
        # Info del archivo
        self.add_file_info(main_layout)
        
        # Vista previa
        self.add_preview_table(main_layout)
        
        # Validaciones
        self.add_validation_area(main_layout)
        
        # Progreso
        self.add_progress_bar(main_layout)
        
        # Botones
        self.add_action_buttons(main_layout)
        
        content_widget.setLayout(main_layout)
        scroll_area.setWidget(content_widget)
        
        # Layout principal del widget
        widget_layout = QVBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(scroll_area)
        self.setLayout(widget_layout)
    
    def add_header(self, layout):
        """Header con botón volver"""
        header_layout = QHBoxLayout()
        
        back_button = QPushButton("←")
        back_button.setFont(QFont("Arial", 10))
        back_button.setCursor(QCursor(Qt.PointingHandCursor))
        back_button.clicked.connect(self.back_requested.emit)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #3498db;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        header_layout.addWidget(back_button)
        
        title = QLabel("Carga Masiva de Datos Tributarios")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
    
    def add_file_zone(self, layout):
        self.drop_zone = FileDropZone()
        self.drop_zone.file_dropped.connect(self.on_file_selected)
        layout.addWidget(self.drop_zone)
        
        # Panel de ayuda (se muestra cuando no hay archivo)
        self.add_help_panel(layout)
    
    def add_file_info(self, layout):
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4f8;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout()
        
        self.file_name_label = QLabel("📄 Archivo: Ninguno seleccionado")
        self.file_name_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.file_name_label)
        
        self.file_records_label = QLabel("📊 Registros detectados: 0")
        self.file_records_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.file_records_label)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        info_frame.hide()
        self.info_frame = info_frame
    
    def add_help_panel(self, layout):
        """Panel de ayuda con instrucciones"""
        help_frame = QFrame()
        help_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        help_layout = QVBoxLayout()
        
        # Título
        title = QLabel("📋 Instrucciones de Carga Masiva")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        help_layout.addWidget(title)
        
        # Pasos
        steps = [
            "1. Descarga la plantilla CSV/Excel haciendo clic en 'Descargar Plantilla'",
            "2. Completa la plantilla con tus datos tributarios",
            "3. Arrastra el archivo o haz clic en la zona de carga",
            "4. Revisa la vista previa y validaciones",
            "5. Haz clic en 'Importar Datos' para confirmar"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setFont(QFont("Arial", 10))
            step_label.setStyleSheet("color: #555; margin: 5px 0px;")
            step_label.setWordWrap(True)
            help_layout.addWidget(step_label)
        
        help_layout.addSpacing(15)
        
        # Información adicional en grid
        info_grid = QHBoxLayout()
        
        # Tarjeta: Formatos aceptados
        format_card = self.create_info_card(
            "📂 Formatos",
            "CSV, XLSX, XLS"
        )
        info_grid.addWidget(format_card)
        
        # Tarjeta: Límite
        limit_card = self.create_info_card(
            "📊 Límite",
            "Hasta 1000 registros por archivo"
        )
        info_grid.addWidget(limit_card)
        
        # Tarjeta: Validaciones
        validation_card = self.create_info_card(
            "✅ Validaciones",
            "RUT, montos, factores 8-19 ≤ 1.0"
        )
        info_grid.addWidget(validation_card)
        
        help_layout.addLayout(info_grid)
        help_frame.setLayout(help_layout)
        layout.addWidget(help_frame)
        
        self.help_frame = help_frame
    
    def create_info_card(self, title: str, content: str):
        """Crea una tarjeta de información"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        
        card_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        card_layout.addWidget(title_label)
        
        content_label = QLabel(content)
        content_label.setFont(QFont("Arial", 9))
        content_label.setStyleSheet("color: #7f8c8d;")
        content_label.setWordWrap(True)
        card_layout.addWidget(content_label)
        
        card.setLayout(card_layout)
        return card
    
    def add_preview_table(self, layout):
        preview_label = QLabel("Vista Previa (primeras 10 filas)")
        preview_label.setFont(QFont("Arial", 12, QFont.Bold))
        preview_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.preview_table)
        
        preview_label.hide()
        self.preview_table.hide()
        self.preview_label = preview_label
    
    def add_validation_area(self, layout):
        validation_label = QLabel("Validaciones:")
        validation_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(validation_label)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(150)
        self.validation_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
                font-family: 'Courier New';
                font-size: 10px;
            }
        """)
        layout.addWidget(self.validation_text)
        
        validation_label.hide()
        self.validation_text.hide()
        self.validation_label = validation_label
    
    def add_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
            }
        """)
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
    
    def add_action_buttons(self, layout):
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.template_button = QPushButton("📥 Descargar Plantilla")
        self.template_button.setFont(QFont("Arial", 10))
        self.template_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.template_button.setFixedHeight(40)
        self.template_button.clicked.connect(self.download_template)
        self.template_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        buttons_layout.addWidget(self.template_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFont(QFont("Arial", 10))
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self.reset_form)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        buttons_layout.addWidget(self.cancel_button)
        self.cancel_button.hide()
        
        self.import_button = QPushButton("Importar Datos")
        self.import_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.import_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_data)
        self.import_button.setEnabled(False)
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        buttons_layout.addWidget(self.import_button)
        self.import_button.hide()
        
        layout.addLayout(buttons_layout)
    
    def on_file_selected(self, file_path: str):
        self.file_path = file_path
        self.validate_file()
    
    def validate_file(self):
        from utils.csvValidator import CSVValidator
        
        # Ocultar panel de ayuda cuando se carga archivo
        self.help_frame.hide()
        
        self.validation_text.setText("⏳ Validando archivo...")
        self.validation_label.show()
        self.validation_text.show()
        
        is_valid, message, df = CSVValidator.validate_file(self.file_path)
        
        self.dataframe = df
        self.validation_passed = is_valid
        
        self.file_name_label.setText(f"📄 Archivo: {os.path.basename(self.file_path)}")
        self.file_records_label.setText(f"📊 Registros detectados: {len(df) if df is not None else 0}")
        self.info_frame.show()
        
        if is_valid:
            self.validation_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #27ae60;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #d5f4e6;
                    color: #27ae60;
                    font-family: 'Courier New';
                }
            """)
            self.validation_text.setText(f"✅ {message}")
            self.import_button.setEnabled(True)
            self.show_preview(df)
        else:
            self.validation_text.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #e74c3c;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #fadbd8;
                    color: #e74c3c;
                    font-family: 'Courier New';
                }
            """)
            self.validation_text.setText(f"❌ {message}")
            self.import_button.setEnabled(False)
            if df is not None:
                self.show_preview(df)
        
        self.cancel_button.show()
        self.import_button.show()
    
    def show_preview(self, df):
        if df is None or df.empty:
            return
        
        preview_df = df.head(10)
        self.preview_table.setRowCount(len(preview_df))
        self.preview_table.setColumnCount(len(preview_df.columns))
        self.preview_table.setHorizontalHeaderLabels(preview_df.columns.tolist())
        
        for i, row in enumerate(preview_df.itertuples(index=False)):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.preview_table.setItem(i, j, item)
        
        self.preview_label.show()
        self.preview_table.show()
    
    def download_template(self):
        from utils.csvValidator import CSVValidator
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Plantilla",
            "plantilla_carga_masiva.csv",
            "CSV (*.csv);;Excel (*.xlsx)"
        )
        
        if file_path:
            success = CSVValidator.export_template(file_path)
            if success:
                QMessageBox.information(self, "Plantilla Descargada",
                    f"Plantilla guardada en:\n{file_path}")
    
    def import_data(self):
        """Importa los datos validados a Firebase"""
        if not self.validation_passed or self.dataframe is None:
            return
        
        from services.massiveLoadService import CargaMasivaService
        from PyQt5.QtCore import QThread
        
        # Confirmar importación
        reply = QMessageBox.question(
            self, "Confirmar Importación",
            f"¿Desea importar {len(self.dataframe)} registros?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Mostrar barra de progreso
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.import_button.setEnabled(False)
        
        # Crear servicio
        service = CargaMasivaService()
        
        # Callback para actualizar progreso
        def update_progress(value):
            self.progress_bar.setValue(value)
        
        # Importar (esto debería estar en un thread, pero por ahora directo)
        result = service.import_data(
            self.dataframe,
            self.user_data.get("_id"),
            progress_callback=update_progress
        )
        
        # Mostrar resultados
        if result["success"]:
            msg = f"Importación completada!\n\n"
            msg += f"✅ Creados: {result['created']}\n"
            msg += f"🔄 Actualizados: {result['updated']}\n"
            msg += f"❌ Errores: {len(result['errors'])}"
            QMessageBox.information(self, "Importación Exitosa", msg)
        else:
            QMessageBox.warning(self, "Importación con errores", 
                f"Se procesaron {result['total_processed']} registros con {len(result['errors'])} errores")
        
        self.import_button.setEnabled(True)

    def reset_form(self):
        self.file_path = None
        self.dataframe = None
        self.validation_passed = False
        
        self.help_frame.show()  # Mostrar panel de ayuda nuevamente
        self.info_frame.hide()
        self.preview_label.hide()
        self.preview_table.hide()
        self.validation_label.hide()
        self.validation_text.hide()
        self.progress_bar.hide()
        self.cancel_button.hide()
        self.import_button.hide()