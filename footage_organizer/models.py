\
"""
数据模型。

当前 Free 版只处理视频文件，不做照片/RAW 管理。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class ClipItem:
    """单个视频素材。"""

    path: Path
    date: datetime
    source: str


@dataclass
class DateCluster:
    """按日期聚合后的一组视频素材。"""

    date_key: str
    clips: list[ClipItem] = field(default_factory=list)

    # 用户填写的项目名称，例如“毕业视频”
    title: str = ""

    # 多个日期合并为同一个项目时使用的统一文件夹名
    project_folder_name: str = ""

    # 是否跳过本日期组
    skipped: bool = False

    # 是否归入统一的“零散素材”文件夹
    misc_group: bool = False

    @property
    def final_folder_name(self) -> str:
        """
        计算最终文件夹名。

        注意：
        misc_group=True 时，文件直接进入：
            素材根目录/零散素材/xxx.mp4

        不会进入：
            素材根目录/2024-xx-xx_零散素材/xxx.mp4
        """
        if self.misc_group:
            return "零散素材"

        if self.project_folder_name.strip():
            return self.project_folder_name.strip()

        if self.title.strip():
            return f"{self.date_key}_{self.title.strip()}"

        return self.date_key

    @property
    def status(self) -> str:
        if self.skipped:
            return "跳过"
        if self.misc_group:
            return "零散素材"
        if self.project_folder_name.strip():
            return "项目组"
        return "已命名" if self.title.strip() else "未命名"
