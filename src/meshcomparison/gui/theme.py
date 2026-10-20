from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#5b9bff"

_DARK = {
    "window": "#111821", "base": "#0c1219", "alt": "#18222d", "text": "#e6edf5",
    "muted": "#8ea0b3", "button": "#202c39", "border": "#2c3a49",
    "surface": "#151f2a", "surface_hover": "#243343", "input_focus": "#263648",
}
_LIGHT = {
    "window": "#f3f6fa", "base": "#ffffff", "alt": "#f7f9fc", "text": "#172333",
    "muted": "#65768a", "button": "#e8eef5", "border": "#d7e0ea",
    "surface": "#ffffff", "surface_hover": "#eaf2fc", "input_focus": "#f2f7ff",
}


def apply_theme(app: QApplication, dark: bool):
    c = _DARK if dark else _LIGHT
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(c["window"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(c["text"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(c["base"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(c["alt"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(c["text"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(c["button"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(c["text"]))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["base"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(c["muted"]))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(c["muted"]))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(c["muted"]))
    app.setPalette(pal)

    app.setStyleSheet(f"""
        * {{ font-family: "Segoe UI", "Inter", sans-serif; font-size: 9pt; }}
        QMainWindow, QWidget {{ color: {c['text']}; }}
        QMainWindow {{ background: {c['window']}; }}
        QWidget#sidePanel {{ background: {c['window']}; }}
        QFrame#viewerToolbar {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 9px; }}
        QLabel#panelHeading {{ font-size: 15pt; font-weight: 700; }}
        QLabel#panelSubtitle {{ color: {c['muted']}; font-size: 8pt; margin-top: -5px; }}

        QGroupBox#card {{ background: {c['surface']}; border: 1px solid {c['border']};
            border-radius: 9px; margin-top: 10px; padding: 7px 8px 7px 8px; }}
        QGroupBox#card::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px;
            color: {c['muted']}; font-size: 9pt; font-weight: 650; }}
        QGroupBox {{ border: 1px solid {c['border']}; border-radius: 10px; margin-top: 14px;
            padding: 14px 12px 12px 12px; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; font-weight: 600; }}

        QPushButton {{ border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 8px;
            background: {c['button']}; min-height: 15px; }}
        QPushButton:hover {{ background: {c['surface_hover']}; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: {c['input_focus']}; }}
        QPushButton:disabled {{ color: {c['muted']}; background: {c['alt']}; }}
        QPushButton#primary {{ background: {ACCENT}; color: #ffffff; border: none;
            border-radius: 7px; font-weight: 700; padding: 8px 12px; }}
        QPushButton#primary:hover {{ background: #78adff; }}
        QPushButton#primary:disabled {{ background: {c['border']}; color: {c['muted']}; }}

        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
            border: 1px solid {c['border']}; border-radius: 5px; padding: 3px 6px;
            background: {c['base']}; selection-background-color: {ACCENT}; }}
        QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{ border-color: {c['muted']}; }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {ACCENT}; background: {c['input_focus']}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{ background: {c['surface']}; border: 1px solid {c['border']};
            selection-background-color: {ACCENT}; padding: 4px; outline: 0; }}
        QCheckBox {{ spacing: 8px; }}
        QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid {c['border']};
            border-radius: 5px; background: {c['base']}; }}
        QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
        QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        QSlider::groove:horizontal {{ height: 4px; background: {c['border']}; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
        QSlider::handle:horizontal {{ width: 14px; margin: -5px 0; border-radius: 7px;
            background: {c['text']}; border: 2px solid {ACCENT}; }}

        QTabWidget::pane {{ background: {c['base']}; border: 1px solid {c['border']}; border-radius: 10px; top: -1px; }}
        QTabBar::tab {{ padding: 9px 18px; margin-right: 3px; color: {c['muted']};
            border: 1px solid transparent; border-top-left-radius: 7px; border-top-right-radius: 7px; }}
        QTabBar::tab:hover {{ color: {c['text']}; background: {c['surface']}; }}
        QTabBar::tab:selected {{ color: {c['text']}; background: {c['surface']};
            border: 1px solid {c['border']}; border-bottom: 2px solid {ACCENT}; font-weight: 650; }}
        QSplitter::handle {{ background: {c['border']}; width: 1px; }}
        QSplitter::handle:hover {{ background: {ACCENT}; }}
        QScrollArea {{ border: none; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 28px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

        QProgressBar {{ background: {c['base']}; border: 1px solid {c['border']};
            border-radius: 6px; text-align: center; height: 12px; color: {c['text']}; }}
        QProgressBar::chunk {{ background: {ACCENT}; border-radius: 5px; }}
        QStatusBar {{ background: {c['surface']}; color: {c['muted']}; border-top: 1px solid {c['border']}; }}
        QMenuBar {{ background: {c['window']}; padding: 3px 6px; }}
        QMenuBar::item {{ padding: 5px 9px; border-radius: 5px; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {c['surface_hover']}; }}
        QMenu {{ background: {c['surface']}; border: 1px solid {c['border']}; padding: 5px; }}
        QMenu::item {{ padding: 6px 28px 6px 10px; border-radius: 4px; }}
        QLabel#hint, QLabel#panelSubtitle {{ color: {c['muted']}; }}
        QLabel#parameterLabel {{ color: {c['muted']}; font-size: 9pt; }}
        QLabel#parameterValue {{ color: {c['text']}; font-weight: 600; padding: 3px 2px; }}
        QLabel#warning {{ color: #f0a45d; }}
        QHeaderView::section {{ background: {c['button']}; border: none; padding: 7px 9px; font-weight: 600; }}
    """)
