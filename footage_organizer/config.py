\
"""
应用配置与运行目录。

这里不要写死用户目录，方便开发环境和 PyInstaller 打包环境共用。
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "Footage Organizer"
APP_EDITION = "Free"
APP_VERSION = "0.9.1-beta"

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mxf", ".mts", ".m2ts",
    ".avi", ".mkv", ".mpg", ".mpeg", ".3gp"
}

DATE_FORMAT = "%Y-%m-%d"


def app_base_dir() -> Path:
    """
    获取软件运行根目录。

    开发环境：
        项目根目录

    PyInstaller onedir 打包后：
        exe 所在目录
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[1]


BASE_DIR = app_base_dir()

# ExifTool 不放进源码仓库，用户/开发者本地复制到这个目录。
EXIFTOOL_PATH = BASE_DIR / "exiftool" / "exiftool.exe"

# 运行时目录。首次启动自动创建，默认被 .gitignore 忽略。
PROJECTS_DIR = BASE_DIR / "projects"
CURRENT_PROJECT_PATH = PROJECTS_DIR / "current_project.json"
RESTORE_LOG_DIR = BASE_DIR / "restore_logs"


def ensure_runtime_dirs() -> None:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    RESTORE_LOG_DIR.mkdir(parents=True, exist_ok=True)
