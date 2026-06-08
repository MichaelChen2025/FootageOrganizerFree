"""
工程文件读写。

工程文件使用 JSON。

新的保存逻辑：
- 每个工程都是一个独立 JSON 文件
- 文件名格式：时间戳_工程名.json
- projects/last_project.txt 记录最近一次保存或打开的工程
- 软件启动时自动加载最近工程
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import APP_NAME, APP_EDITION, APP_VERSION, PROJECTS_DIR, ensure_runtime_dirs
from .models import ClipItem, DateCluster
from .utils import sanitize_folder_name


def cluster_to_dict(cluster: DateCluster) -> dict:
    return {
        "date_key": cluster.date_key,
        "title": cluster.title,
        "project_folder_name": cluster.project_folder_name,
        "skipped": cluster.skipped,
        "misc_group": cluster.misc_group,
        "clips": [
            {
                "path": str(clip.path),
                "date": clip.date.strftime("%Y-%m-%d %H:%M:%S"),
                "source": clip.source,
            }
            for clip in cluster.clips
        ],
    }


def cluster_from_dict(data: dict) -> DateCluster:
    cluster = DateCluster(date_key=data["date_key"])
    cluster.title = data.get("title", "")
    cluster.project_folder_name = data.get("project_folder_name", "")
    cluster.skipped = bool(data.get("skipped", False))
    cluster.misc_group = bool(data.get("misc_group", False))

    for item in data.get("clips", []):
        try:
            dt = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            dt = datetime.now()

        cluster.clips.append(
            ClipItem(
                path=Path(item["path"]),
                date=dt,
                source=item.get("source", "unknown"),
            )
        )

    return cluster


def build_project_payload(source_dir: Path | None, clusters: dict[str, DateCluster], sort_field: str, sort_desc: bool) -> dict:
    return {
        "app": APP_NAME,
        "edition": APP_EDITION,
        "version": APP_VERSION,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_dir": str(source_dir) if source_dir else "",
        "sort_field": sort_field,
        "sort_desc": sort_desc,
        "clusters": [cluster_to_dict(c) for c in clusters.values()],
    }


def save_project(path: Path, payload: dict) -> None:
    ensure_runtime_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_project(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


LAST_PROJECT_NAME = "last_project.txt"


def make_project_path(project_name: str) -> Path:
    """
    根据用户输入的工程名生成工程文件路径。

    示例：
        projects/2026-06-07_21-35-18_毕业视频.json

    如果用户没有输入名称，则使用 project。
    """
    ensure_runtime_dirs()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    clean_name = sanitize_folder_name(project_name)

    if not clean_name:
        clean_name = "project"

    return PROJECTS_DIR / f"{timestamp}_{clean_name}.json"


def get_last_project_file() -> Path | None:
    """读取最近一次保存或打开的工程文件路径。"""
    path = PROJECTS_DIR / LAST_PROJECT_NAME

    if not path.exists():
        return None

    try:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return None

        project_path = Path(text)
        return project_path if project_path.exists() else None

    except Exception:
        return None


def set_last_project_file(project_path: Path) -> None:
    """记录最近一次保存或打开的工程文件路径。"""
    ensure_runtime_dirs()
    path = PROJECTS_DIR / LAST_PROJECT_NAME
    path.write_text(str(project_path), encoding="utf-8")


def payload_to_clusters(payload: dict) -> dict[str, DateCluster]:
    clusters: dict[str, DateCluster] = {}
    for item in payload.get("clusters", []):
        cluster = cluster_from_dict(item)
        clusters[cluster.date_key] = cluster
    return dict(sorted(clusters.items(), key=lambda x: x[0]))
