import sys
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPixmap

from .title_bar import get_accent_color, is_icon_file



class InmersiveSplash(QWidget):
    """
    🌊 InmersiveSplash: Ciclo de vida completo del Bot.
    Modos: 
    - adaptive: Ocupa toda la pantalla respetando la barra de tareas.
    - full: Ocupa absolutamente toda la pantalla (Kiosk).
    """
    def __init__(self, title="Sincronizando...", logo="🐉", color="auto", is_exit=False, splash_type="LV"):
        super().__init__()
        self.is_exit = is_exit
        self._title = title
        self._logo = logo
        self._color_cfg = color
        self._type = splash_type.upper()
        self._mode = "adaptive"
        self._phrases = []
        self._callback = None
        self._marquee = False
        self._final_color = "#0078d4"
        
        # Flags de ventana
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)


    def set_mode(self, mode):
        """'adaptive' o 'full'."""
        self._mode = mode
        return self

    def set_phrases(self, phrases):
        """Lista de strings que se mostrarán durante la carga."""
        self._phrases = phrases
        return self

    def on_finish(self, callback):
        self._callback = callback
        return self

    def set_progress_mode(self, marquee=False):
        self._marquee = marquee
        return self

    def launch(self):
        # 1. Ajuste de Pantalla
        desktop = QDesktopWidget()
        if self._mode == "adaptive":
            geom = desktop.availableGeometry() # Respeta Taskbar
        else:
            geom = desktop.screenGeometry() # Full Kiosk
            
        self.setGeometry(geom)
        
        # 2. Color de Fondo
        self._final_color = get_accent_color() if self._color_cfg == "auto" else self._color_cfg
        
        # 3. UI
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Botones de control si es UWP o BUNDLED
        if self._type in ["UWP", "BUNDLED"]:
            from .title_bar import CustomTitleBar
            self.title_bar = CustomTitleBar(self, title="", icon="", hide_max=False)
            self.title_bar.setStyleSheet("background: transparent;")
            self.title_bar.title_lbl.hide()
            self.title_bar.icon_lbl.hide()
            self.main_layout.addWidget(self.title_bar, alignment=Qt.AlignTop)

        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(30)
        self.main_layout.addLayout(content_layout, 1)
        
        # Configuración según TYPE
        if self._type == "UWP":
            self._logo = "app/app-icon.ico" if os.path.exists("app/app-icon.ico") else self._logo
            self._marquee = True
            # Solo usar negro si no se especificó 'auto'
            if self._color_cfg != "auto":
                self._final_color = "#000000"
        elif self._type == "BUNDLED":
            self._logo = "assets/splash.png" if os.path.exists("assets/splash.png") else self._logo
            self._marquee = True
            if self._color_cfg != "auto":
                self._final_color = "#000000"

        self.logo_lbl = QLabel()
        if is_icon_file(self._logo):
            from PyQt5.QtGui import QIcon
            icon_obj = QIcon(self._logo)
            size_px = 192 if self._type in ["UWP", "BUNDLED"] else 256
            pixmap = icon_obj.pixmap(size_px, size_px)
            
            if not pixmap.isNull():
                self.logo_lbl.setPixmap(pixmap)
            else:
                self.logo_lbl.setText(self._logo)
                self.logo_lbl.setFont(QFont("Segoe UI Variable Display", 120))

        else:
            self.logo_lbl.setText(self._logo)
            self.logo_lbl.setFont(QFont("Segoe UI Variable Display", 120))

        self.logo_lbl.setStyleSheet("color: white; background: transparent;")
        content_layout.addWidget(self.logo_lbl, alignment=Qt.AlignCenter)
        
        from .progress_bar import LeviathanProgressBar
        self.pbar = LeviathanProgressBar()
        self.pbar.setFixedWidth(int(self.width() * 0.4))
        self.pbar.setFixedHeight(8)
        if self._marquee:
            self.pbar.setMarquee(True)
        else:
            self.pbar.setRange(0, 100)
        content_layout.addWidget(self.pbar, alignment=Qt.AlignCenter)
        
        if self._type == "LV":
            self.status_lbl = QLabel(self._title)
            self.status_lbl.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 18px; font-weight: 600; background: transparent;")
            content_layout.addWidget(self.status_lbl, alignment=Qt.AlignCenter)
        
        # 4. Animación de Entrada
        self.setWindowOpacity(0)
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(800)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.start()
        
        # 5. Lógica de Pasos / Timer
        self._current_step = 0
        self.timer = QTimer()
        
        if self._type in ["UWP", "BUNDLED"]:
            # Esperar a que termine el fade-in, LUEGO mostrar por 3 segundos
            self.fade_in.finished.connect(lambda: QTimer.singleShot(3000, self._close_splash))
        else:
            # Modo LV clásico con frases
            self.timer.timeout.connect(self._update_progress)
            self.timer.start(800) 
        
        self.show()
        return self


    def _update_progress(self):
        if not self._phrases:
            self._phrases = ["Analizando datos...", "Sincronizando...", "Preparando interfaz..."]
            
        if self._current_step < len(self._phrases):
            msg = self._phrases[self._current_step]
            prog = int(((self._current_step + 1) / len(self._phrases)) * 100)
            self.status_lbl.setText(msg)
            self.pbar.setValue(prog)
            self._current_step += 1
        else:
            self.timer.stop()
            QTimer.singleShot(600, self._close_splash)

    def _close_splash(self):
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(600)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.finished.connect(self._finalize)
        self.fade_out.start()

    def _finalize(self):
        self.close()
        if self.is_exit:
            QApplication.instance().quit()
        elif self._callback:
            self._callback()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(self._final_color))

    def attach_to_window(self, window, exit_phrases=None):
        """Registra el splash de salida automáticamente."""
        QApplication.instance().setQuitOnLastWindowClosed(False)
        phrases = exit_phrases or ["Cerrando sesiones...", "Guardando logs...", "Leviathan fuera."]
        
        def on_close(event):
            InmersiveSplash(title="Saliendo...", logo=self._logo, color=self._color_cfg, is_exit=True, splash_type=self._type)\
                .set_mode(self._mode)\
                .set_phrases(phrases)\
                .set_progress_mode(self._marquee)\
                .launch()


            event.accept()
            
        window.closeEvent = on_close
        return self

    def start(self): return self.launch()
    @staticmethod
    def create(): return InmersiveSplash()
