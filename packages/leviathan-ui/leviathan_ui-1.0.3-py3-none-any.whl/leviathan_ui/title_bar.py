import os
import platform

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtCore import Qt, QSize, QPoint, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath, QPixmap

try:
    import winreg
except ImportError:
    winreg = None

def is_icon_file(filepath):
    """Verifica si el string es una ruta a un archivo de imagen soportado."""
    if not isinstance(filepath, str):
        return False
    extensions = ('.png', '.ico', '.svg', '.jpg', '.jpeg', '.bmp')
    return filepath.lower().endswith(extensions) and os.path.isfile(filepath)


def get_accent_color():
    """Obtiene el color de acento de Windows 10/11."""
    if platform.system() == "Windows" and winreg:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            value, _ = winreg.QueryValueEx(key, "ColorizationColor")
            color = "{:08x}".format(value)
            return "#" + color[2:8]
        except: pass
    return "#0078d4"

def darken_color(hex_color, factor=0.7):
    """Oscurece un color hex por un factor (0.0 = negro, 1.0 = sin cambio)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

class Win11Button(QPushButton):
    """Boton con estilo Windows 11 y dibujo SVG nativo."""
    def __init__(self, btn_type, parent=None):
        super().__init__(parent)
        self._type = btn_type # "min", "max", "close"
        self.setFixedSize(46, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.hover_color = "#e81123" if btn_type == "close" else "rgba(255, 255, 255, 0.1)"
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo en Hover
        if self.underMouse():
            painter.fillRect(self.rect(), QColor(self.hover_color))
        
        painter.setPen(QPen(QColor("white"), 1))
        center = self.rect().center()
        
        if self._type == "min":
            painter.drawLine(center.x() - 5, center.y(), center.x() + 5, center.y())
        elif self._type == "max":
            painter.drawRect(center.x() - 5, center.y() - 5, 10, 10)
        elif self._type == "close":
            painter.drawLine(center.x() - 5, center.y() - 5, center.x() + 5, center.y() + 5)
            painter.drawLine(center.x() + 5, center.y() - 5, center.x() - 5, center.y() + 5)

class CustomTitleBar(QWidget):
    """Barra de título Windows 11 con color oscurecido del acento del sistema."""
    def __init__(self, parent, title="Leviathan", icon="🐉", hide_max=False):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(34)
        self._hide_max = hide_max
        
        # Obtenemos el color de acento y lo oscurecemos para resaltar

        accent = get_accent_color()
        dark_accent = darken_color(accent, 0.6)
        
        # Fondo sólido oscurecido que resalta sobre el cuerpo de la ventana
        self.setStyleSheet(f"""
            background-color: {dark_accent};
            border-top-left-radius: 25px;
            border-top-right-radius: 25px;
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)
        
        self.icon_lbl = QLabel()
        if is_icon_file(icon):
            pixmap = QPixmap(icon)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_lbl.setPixmap(pixmap)
            else:
                self.icon_lbl.setText(icon)
                self.icon_lbl.setFont(QFont("Segoe UI Emoji", 11))
        else:
            self.icon_lbl.setText(icon)
            self.icon_lbl.setFont(QFont("Segoe UI Emoji", 11))

        self.icon_lbl.setStyleSheet("color: white; background: transparent;")
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: white; background: transparent; font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; font-weight: 500;")
        
        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)
        layout.addStretch()
        
        self.btn_min = Win11Button("min", self)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        
        self.btn_max = Win11Button("max", self)
        self.btn_max.clicked.connect(self._toggle_max)
        if self._hide_max:
            self.btn_max.hide()
        
        self.btn_close = Win11Button("close", self)

        self.btn_close.clicked.connect(self.parent.close)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def _toggle_max(self):
        if self.parent.isMaximized(): self.parent.showNormal()
        else: self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self.parent.windowHandle()
            if handle: handle.startSystemMove()
            event.accept()
