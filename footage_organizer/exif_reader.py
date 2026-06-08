\
"""
ExifTool 读取模块。

当前只读取日期字段，不做缩略图或媒体库索引。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .config import EXIFTOOL_PATH
from .utils import parse_exif_datetime


def check_exiftool() -> str:
    """检查 ExifTool 是否存在且可运行。"""
    if not EXIFTOOL_PATH.exists():
        raise FileNotFoundError(
            f"未找到 ExifTool：{EXIFTOOL_PATH}\n\n"
            "请将 ExifTool 放到：\n"
            "exiftool/exiftool.exe\n"
            "exiftool/exiftool_files/"
        )

    result = subprocess.run(
        [str(EXIFTOOL_PATH), "-ver"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip()


def get_metadata_date_from_info(info: dict):
    """从 ExifTool JSON 结果中按优先级提取日期。"""
    tags = [
        "DateTimeOriginal",
        "CreateDate",
        "CreationDate",
        "MediaCreateDate",
        "TrackCreateDate",
        "ModifyDate",
    ]

    for tag in tags:
        value = info.get(tag)
        dt = parse_exif_datetime(value) if value else None
        if dt:
            return dt

    return None


def read_metadata_batch(files: list[Path]) -> dict[Path, object]:
    """批量读取元数据日期。"""
    result_map: dict[Path, object] = {}

    if not files:
        return result_map

    temp_file = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        ) as f:
            temp_file = Path(f.name)
            for file in files:
                f.write(str(file) + "\n")

        cmd = [
            str(EXIFTOOL_PATH),
            "-j",
            "-charset",
            "filename=UTF8",
            "-DateTimeOriginal",
            "-CreateDate",
            "-CreationDate",
            "-MediaCreateDate",
            "-TrackCreateDate",
            "-ModifyDate",
            "-@",
            str(temp_file)
        ]

        run = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if run.returncode != 0 and not run.stdout.strip():
            return result_map

        data = json.loads(run.stdout)

        for item in data:
            source = item.get("SourceFile")
            if not source:
                continue

            result_map[Path(source)] = get_metadata_date_from_info(item)

    finally:
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass

    return result_map
