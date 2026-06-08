\
"""
通用工具函数。
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .config import VIDEO_EXTENSIONS


DATE_FOLDER_PATTERN = re.compile(r"^20\d{2}-\d{2}-\d{2}")


def sanitize_folder_name(name: str) -> str:
    """清理不适合出现在文件夹名中的字符。"""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def build_project_folder_name(date_keys: list[str], title: str) -> str:
    """根据多个日期和项目名生成文件夹名。"""
    clean_title = sanitize_folder_name(title)
    sorted_dates = sorted(date_keys)
    start = sorted_dates[0]
    end = sorted_dates[-1]

    if start == end:
        prefix = start
    else:
        sy, sm, _sd = start.split("-")
        ey, em, ed = end.split("-")
        if sy == ey and sm == em:
            prefix = f"{start}_to_{ed}"
        else:
            prefix = f"{start}_to_{end}"

    return f"{prefix}_{clean_title}" if clean_title else prefix


def is_video_file(path: Path) -> bool:
    """判断是否为 Free 版支持的视频文件。"""
    return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS


def get_date_from_filename(filename: str) -> datetime | None:
    """
    从文件名中提取拍摄日期。

    优先识别常见相机 / 无人机 / 运动相机文件名中的完整时间。
    如果只能识别日期，则返回当天 00:00:00。
    """

    name = filename

    # DJI 新格式：
    # DJI_2024121212133545_0008_D_A02.mp4
    # 其中前 14 位通常是 YYYYMMDDHHMMSS，后面可能还有毫秒/序号
    dji_match = re.search(r'DJI[_-](20\d{12,14})', name, re.IGNORECASE)
    if dji_match:
        raw = dji_match.group(1)[:14]
        try:
            return datetime.strptime(raw, "%Y%m%d%H%M%S")
        except ValueError:
            pass

    # 通用完整时间：
    # 20241212121335
    # 2024-12-12_12-13-35
    # 2024.12.12-12.13.35
    full_datetime_patterns = [
        r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([01]\d|2[0-3])([0-5]\d)([0-5]\d)(?!\d)',
        r'(?<!\d)(20\d{2})[-_\.](0[1-9]|1[0-2])[-_\.](0[1-9]|[12]\d|3[01])[-_\s\.]?([01]\d|2[0-3])[-_\.]?([0-5]\d)[-_\.]?([0-5]\d)(?!\d)',
    ]

    for pattern in full_datetime_patterns:
        match = re.search(pattern, name)
        if match:
            y, mo, d, h, mi, s = match.groups()
            try:
                return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
            except ValueError:
                pass

    # 通用日期：
    # 20241212
    # 2024-12-12
    # 2024_12_12
    # 2024.12.12
    date_patterns = [
        r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)',
        r'(?<!\d)(20\d{2})[-_\.](0[1-9]|1[0-2])[-_\.](0[1-9]|[12]\d|3[01])(?!\d)',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, name)
        if match:
            y, mo, d = match.groups()
            try:
                return datetime(int(y), int(mo), int(d))
            except ValueError:
                pass

    return None


def parse_exif_datetime(value: str) -> datetime | None:
    """解析 ExifTool 输出的日期字符串。"""
    if not value:
        return None

    value = str(value).strip()
    value = re.sub(r"[+-]\d{2}:\d{2}$", "", value)
    value = value.replace("Z", "")

    patterns = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for pattern in patterns:
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            pass

    match = re.search(r"(20\d{2})[:\-](\d{2})[:\-](\d{2})", value)
    if match:
        y, m, d = match.groups()
        try:
            return datetime(int(y), int(m), int(d))
        except ValueError:
            return None

    return None


def get_file_mtime_date(path: Path) -> datetime:
    """无法识别拍摄日期时，用文件修改时间兜底。"""
    return datetime.fromtimestamp(path.stat().st_mtime)


def should_skip_sorted_folder(path: Path, source_dir: Path, enabled: bool) -> bool:
    """
    跳过已经整理过的日期文件夹或零散素材文件夹，避免二次整理。
    """
    if not enabled:
        return False

    try:
        parts = path.relative_to(source_dir).parts
    except ValueError:
        return False

    for part in parts[:-1]:
        if DATE_FOLDER_PATTERN.match(part) or part == "零散素材":
            return True

    return False


def get_unique_path(target: Path, reserved: set[Path]) -> Path:
    """生成不冲突的目标路径。"""
    if not target.exists() and target not in reserved:
        reserved.add(target)
        return target

    parent = target.parent
    stem = target.stem
    suffix = target.suffix
    i = 1

    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists() and candidate not in reserved:
            reserved.add(candidate)
            return candidate
        i += 1
