"""
应用入口与全局样式。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .config import ensure_runtime_dirs
from .main_window import MainWindow


def resource_path(relative_path: str) -> Path:
    """
    获取资源文件路径。

    开发环境：
        G:/PythonProject/FootageOrganizerFree/icon.ico

    PyInstaller 打包后：
        dist/FootageOrganizerFree/_internal/icon.ico
        或临时解包目录中的 icon.ico
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent.parent / relative_path


def run_app() -> int:
    ensure_runtime_dirs()

    app = QApplication(sys.argv)

    icon_path = resource_path("icon.ico")
    app_icon = QIcon(str(icon_path))

    app.setWindowIcon(app_icon)

    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1f22;
            color: #e6e6e6;
        }

        QMenuBar {
            background-color: #1e1f22;
            color: #e6e6e6;
        }

        QMenuBar::item:selected {
            background-color: #2f3136;
        }

        QMenu {
            background-color: #25262b;
            color: #e6e6e6;
            border: 1px solid #3b3d42;
        }

        QMenu::item:selected {
            background-color: #315f9f;
        }

        QWidget {
            background-color: #1e1f22;
            color: #e6e6e6;
            font-family: "Segoe UI", "Microsoft YaHei", Arial;
            font-size: 10pt;
        }

        QLabel {
            color: #e6e6e6;
        }

        QTabWidget::pane {
            border: 1px solid #3b3d42;
            background: #1e1f22;
            border-radius: 6px;
        }

        QTabBar::tab {
            background: #2b2d33;
            color: #d6d6d6;
            padding: 9px 18px;
            border: 1px solid #3b3d42;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
        }

        QTabBar::tab:selected {
            background: #3d6fb6;
            color: white;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #3b3d42;
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px;
            background-color: #25262b;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px 0 6px;
            color: #8ab4f8;
        }

        #StatCard {
            background-color: #25262b;
            border: 1px solid #3b3d42;
            border-radius: 10px;
        }

        QPushButton {
            background-color: #2f3136;
            color: #f1f1f1;
            border: 1px solid #4a4d55;
            border-radius: 6px;
            padding: 7px 12px;
        }

        QPushButton:hover {
            background-color: #3a3d44;
            border: 1px solid #6a6d78;
        }

        QPushButton:pressed {
            background-color: #24262b;
        }

        QPushButton:disabled {
            background-color: #25262a;
            color: #777777;
            border: 1px solid #333333;
        }

        QPushButton#PrimaryButton {
            background-color: #315f9f;
            border: 1px solid #4d8dff;
            font-weight: bold;
        }

        QPushButton#DangerButton {
            background-color: #7a2e2e;
            border: 1px solid #ff6b6b;
            font-weight: bold;
        }

        QLineEdit {
            background-color: #17181b;
            color: #f1f1f1;
            border: 1px solid #3f424a;
            border-radius: 5px;
            padding: 6px;
            selection-background-color: #3d6fb6;
        }

        QTextEdit {
            background-color: #151619;
            color: #dcdcdc;
            border: 1px solid #3f424a;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #3d6fb6;
        }

        QTableWidget {
            background-color: #17181b;
            alternate-background-color: #202126;
            color: #f1f1f1;
            gridline-color: #34363c;
            border: 1px solid #3f424a;
            border-radius: 6px;
            selection-background-color: #2f5f9f;
            selection-color: #ffffff;
        }

        QTableWidget::item {
            padding: 5px;
        }

        QHeaderView::section {
            background-color: #2b2d33;
            color: #f1f1f1;
            border: 1px solid #3b3d42;
            padding: 6px;
            font-weight: bold;
        }

        QListWidget {
            background-color: #17181b;
            color: #f1f1f1;
            border: 1px solid #3f424a;
            border-radius: 6px;
            selection-background-color: #2f5f9f;
            selection-color: #ffffff;
        }

        QListWidget::item {
            padding: 5px;
        }

        QComboBox {
            background-color: #17181b;
            color: #f1f1f1;
            border: 1px solid #3f424a;
            border-radius: 5px;
            padding: 6px;
        }

        QComboBox QAbstractItemView {
            background-color: #17181b;
            color: #f1f1f1;
            selection-background-color: #2f5f9f;
        }

        QCheckBox {
            color: #e6e6e6;
            spacing: 6px;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }

        QCheckBox::indicator:unchecked {
            background-color: #202126;
            border: 2px solid #6c6f78;
            border-radius: 4px;
        }

        QCheckBox::indicator:checked {
            background-color: #3d6fb6;
            border: 2px solid #3d6fb6;
            border-radius: 4px;
        }

        QProgressBar {
            background-color: #17181b;
            color: #f1f1f1;
            border: 1px solid #3f424a;
            border-radius: 6px;
            text-align: center;
            height: 18px;
        }

        QProgressBar::chunk {
            background-color: #3d6fb6;
            border-radius: 5px;
        }

        QStatusBar {
            background-color: #17181b;
            color: #cfcfcf;
            border-top: 1px solid #34363c;
        }

        QSplitter::handle {
            background-color: #2b2d33;
        }
    """)

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()

    return app.exec()