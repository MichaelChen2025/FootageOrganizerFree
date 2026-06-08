\
"""
后台任务线程。

耗时操作必须放到 QThread：
1. 扫描素材
2. 应用整理
3. 恢复整理
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .config import DATE_FORMAT, RESTORE_LOG_DIR
from .exif_reader import check_exiftool, read_metadata_batch
from .models import ClipItem, DateCluster
from .utils import (
    get_date_from_filename,
    get_file_mtime_date,
    get_unique_path,
    is_video_file,
    should_skip_sorted_folder,
)


class ScanWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, source_dir: Path, strict: bool, skip_sorted: bool):
        super().__init__()
        self.source_dir = source_dir
        self.strict = strict
        self.skip_sorted = skip_sorted
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            version = check_exiftool()
            self.log.emit(f"ExifTool Version: {version}")
            self.log.emit("开始扫描视频素材...")

            video_files: list[Path] = []
            for p in self.source_dir.rglob("*"):
                if self.cancelled:
                    self.log.emit("扫描已取消。")
                    return

                if not is_video_file(p):
                    continue

                if should_skip_sorted_folder(p, self.source_dir, self.skip_sorted):
                    continue

                video_files.append(p)

            if not video_files:
                self.finished_ok.emit({})
                return

            self.log.emit(f"扫描到视频：{len(video_files)} 个")
            self.progress.emit(10)

            filename_dates: dict[Path, object] = {}
            metadata_needed: list[Path] = []

            for i, file in enumerate(video_files, start=1):
                if self.cancelled:
                    self.log.emit("扫描已取消。")
                    return

                filename_date = get_date_from_filename(file.name)
                filename_dates[file] = filename_date

                if self.strict:
                    metadata_needed.append(file)
                elif filename_date is None:
                    metadata_needed.append(file)

                if i % 100 == 0 or i == len(video_files):
                    self.progress.emit(10 + int((i / len(video_files)) * 25))
                    self.log.emit(f"文件名日期分析：{i}/{len(video_files)}")

            metadata_dates = {}

            if metadata_needed:
                self.log.emit(f"需要读取元数据：{len(metadata_needed)} 个")
                metadata_dates = read_metadata_batch(metadata_needed)
                self.log.emit("元数据读取完成。")
            else:
                self.log.emit("所有视频均可通过文件名日期快速分类。")

            clusters: dict[str, DateCluster] = {}
            stats = {
                "total": len(video_files),
                "filename_fast": 0,
                "filename_verified": 0,
                "metadata": 0,
                "mtime": 0,
                "conflict": 0,
            }

            for i, file in enumerate(video_files, start=1):
                if self.cancelled:
                    self.log.emit("扫描已取消。")
                    return

                filename_date = filename_dates.get(file)
                metadata_date = metadata_dates.get(file)

                final_date = None
                source = ""

                if self.strict and filename_date and metadata_date:
                    delta = abs((filename_date.date() - metadata_date.date()).days)
                    if delta > 1:
                        stats["conflict"] += 1
                        self.log.emit(
                            f"[日期冲突] {file.name} | "
                            f"文件名 {filename_date.strftime(DATE_FORMAT)} | "
                            f"元数据 {metadata_date.strftime(DATE_FORMAT)} | 已跳过"
                        )
                        continue

                    final_date = filename_date
                    source = "filename_verified"
                    stats["filename_verified"] += 1

                elif filename_date:
                    final_date = filename_date
                    source = "filename_fast"
                    stats["filename_fast"] += 1

                elif metadata_date:
                    final_date = metadata_date
                    source = "metadata"
                    stats["metadata"] += 1

                else:
                    final_date = get_file_mtime_date(file)
                    source = "file_mtime"
                    stats["mtime"] += 1

                date_key = final_date.strftime(DATE_FORMAT)
                clusters.setdefault(date_key, DateCluster(date_key=date_key))
                clusters[date_key].clips.append(
                    ClipItem(path=file, date=final_date, source=source)
                )

                if i % 100 == 0 or i == len(video_files):
                    self.progress.emit(35 + int((i / len(video_files)) * 60))

            sorted_clusters = dict(sorted(clusters.items(), key=lambda x: x[0]))
            self.progress.emit(100)
            self.finished_ok.emit({"clusters": sorted_clusters, "stats": stats})

        except Exception as e:
            self.failed.emit(str(e))


class ApplyWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, clusters: dict[str, DateCluster], source_dir: Path):
        super().__init__()
        self.clusters = clusters
        self.source_dir = source_dir
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def build_plan(self) -> list[tuple[Path, Path]]:
        plan: list[tuple[Path, Path]] = []
        reserved: set[Path] = set()

        for cluster in self.clusters.values():
            if cluster.skipped:
                continue

            folder = self.source_dir / cluster.final_folder_name

            for clip in cluster.clips:
                target = folder / clip.path.name

                if clip.path.resolve() == target.resolve():
                    continue

                unique_target = get_unique_path(target, reserved)
                plan.append((clip.path, unique_target))

        return plan

    def run(self):
        try:
            plan = self.build_plan()

            if not plan:
                self.finished_ok.emit({"success": 0, "failed": 0, "restore_log": ""})
                return

            self.log.emit("开始应用整理。")
            self.log.emit("模式：在素材根目录内移动整理")
            self.log.emit(f"计划处理：{len(plan)} 个文件")

            restore_records = []
            success = 0
            failed = 0

            for i, (src, dst) in enumerate(plan, start=1):
                if self.cancelled:
                    self.log.emit("应用整理已取消。")
                    break

                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    restore_records.append(("MOVE", str(src), str(dst)))
                    success += 1

                except Exception as e:
                    failed += 1
                    self.log.emit(f"[失败] {src.name} -> {dst} | {e}")

                if i % 50 == 0 or i == len(plan):
                    self.progress.emit(int((i / len(plan)) * 100))
                    self.log.emit(f"应用进度：{i}/{len(plan)}")

            restore_log = ""

            if restore_records:
                RESTORE_LOG_DIR.mkdir(parents=True, exist_ok=True)
                log_path = RESTORE_LOG_DIR / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("# Footage Organizer Restore Log\n")
                    f.write(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("# Format: MODE | ORIGINAL_PATH | NEW_PATH\n\n")
                    for mode, old, new in restore_records:
                        f.write(f"{mode} | {old} | {new}\n")

                restore_log = str(log_path)

            self.progress.emit(100)
            self.finished_ok.emit({"success": success, "failed": failed, "restore_log": restore_log})

        except Exception as e:
            self.failed.emit(str(e))


class RestoreWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, source_dir: Path | None):
        super().__init__()
        self.source_dir = source_dir
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def latest_restore_log(self) -> Path | None:
        if not RESTORE_LOG_DIR.exists():
            return None

        logs = list(RESTORE_LOG_DIR.glob("restore_*.txt"))
        if not logs:
            return None

        return sorted(logs, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    def remove_empty_folders(self):
        if not self.source_dir or not self.source_dir.exists():
            return

        for folder in sorted(self.source_dir.rglob("*"), reverse=True):
            if folder.is_dir():
                try:
                    folder.rmdir()
                except OSError:
                    pass

    def run(self):
        try:
            log_path = self.latest_restore_log()
            if not log_path:
                self.failed.emit("没有找到 restore_log，无法恢复。")
                return

            self.log.emit(f"使用恢复记录：{log_path}")

            with open(log_path, "r", encoding="utf-8") as f:
                rows = [line.strip() for line in f.readlines()]

            records = []
            for row in rows:
                if not row or row.startswith("#"):
                    continue

                parts = row.split(" | ")
                if len(parts) == 3:
                    records.append(parts)

            restored = 0
            failed = 0
            conflict = 0
            total = len(records)

            for i, (_mode, old, new) in enumerate(records, start=1):
                if self.cancelled:
                    self.log.emit("恢复已取消。")
                    break

                old_path = Path(old)
                new_path = Path(new)

                try:
                    if not new_path.exists():
                        failed += 1
                        self.log.emit(f"[失败] 新位置不存在：{new_path}")
                        continue

                    if old_path.exists():
                        conflict += 1
                        self.log.emit(f"[冲突] 原位置已有同名文件：{old_path}")
                        continue

                    old_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(new_path), str(old_path))
                    restored += 1

                except Exception as e:
                    failed += 1
                    self.log.emit(f"[失败] {new_path} -> {old_path} | {e}")

                if i % 50 == 0 or i == total:
                    self.progress.emit(int((i / max(total, 1)) * 100))

            self.remove_empty_folders()

            self.progress.emit(100)
            self.finished_ok.emit({"restored": restored, "failed": failed, "conflict": conflict})

        except Exception as e:
            self.failed.emit(str(e))
