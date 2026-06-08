"""
主窗口 UI。

设计方向：
- 纯中文界面
- 深色模式
- 高信息密度
- 工具软件风格
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import (
    APP_EDITION,
    APP_NAME,
    APP_VERSION,
    PROJECTS_DIR,
    ensure_runtime_dirs,
)
from .models import DateCluster
from .project_io import (
    build_project_payload,
    get_last_project_file,
    load_project,
    make_project_path,
    payload_to_clusters,
    save_project,
    set_last_project_file,
)
from .utils import build_project_folder_name, sanitize_folder_name
from .workers import ApplyWorker, RestoreWorker, ScanWorker


class StatCard(QFrame):
    """总览页统计卡片。"""

    def __init__(self, title: str, value: str = "0"):
        super().__init__()
        self.setObjectName("StatCard")
        layout = QVBoxLayout(self)
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #8ab4f8;")
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #b8b8b8;")
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class MainWindow(QMainWindow):
    """Footage Organizer Free 主窗口。"""

    def __init__(self):
        super().__init__()
        ensure_runtime_dirs()

        self.setWindowTitle(f"{APP_NAME} {APP_EDITION} {APP_VERSION}")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1360, 860)
        self.setMinimumSize(1120, 720)

        self.source_dir: Path | None = None
        self.clusters: dict[str, DateCluster] = {}
        self.display_order: list[str] = []
        self.selected_date_key: str | None = None
        self.worker: QThread | None = None
        self.current_project_file: Path | None = None

        self.dirty = False
        self.has_meaningful_progress = False

        self.build_ui()
        self.load_current_project_on_startup()

    def build_ui(self):
        self.build_menus()

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)

        header = QHBoxLayout()

        title = QLabel("Footage Organizer")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #8ab4f8;")

        edition = QLabel("FREE")
        edition.setStyleSheet(
            "background-color: #315f9f; color: white; border-radius: 5px; "
            "padding: 3px 8px; font-size: 11px; font-weight: bold;"
        )

        beta = QLabel("BETA")
        beta.setStyleSheet(
            "background-color: #6b4fa3; color: white; border-radius: 5px; "
            "padding: 3px 8px; font-size: 11px; font-weight: bold;"
        )

        version = QLabel(APP_VERSION)
        version.setStyleSheet("color: #b8b8b8;")

        header.addWidget(title)
        header.addWidget(edition)
        header.addWidget(beta)
        header.addWidget(version)
        header.addStretch()
        root_layout.addLayout(header)

        subtitle = QLabel("一个用于快速整理视频素材的本地离线工具。")
        subtitle.setStyleSheet("font-size: 14px; color: #b8b8b8;")
        root_layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, stretch=1)

        self.dashboard_tab = QWidget()
        self.organize_tab = QWidget()
        self.help_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "总览")
        self.tabs.addTab(self.organize_tab, "整理")
        self.tabs.addTab(self.help_tab, "帮助")

        self.build_dashboard_tab()
        self.build_organize_tab()
        self.build_help_tab()

        self.progress = QProgressBar()
        root_layout.addWidget(self.progress)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("准备就绪")

    def build_menus(self):
        file_menu = self.menuBar().addMenu("文件")

        act_save = QAction("保存工程", self)
        act_save.triggered.connect(self.save_project_action)
        file_menu.addAction(act_save)

        act_save_as = QAction("工程另存为...", self)
        act_save_as.triggered.connect(self.save_project_as_action)
        file_menu.addAction(act_save_as)

        act_open = QAction("打开工程文件...", self)
        act_open.triggered.connect(self.open_project_action)
        file_menu.addAction(act_open)

        act_open_folder = QAction("打开工程文件夹", self)
        act_open_folder.triggered.connect(lambda: self.open_path(PROJECTS_DIR))
        file_menu.addAction(act_open_folder)

        file_menu.addSeparator()

        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        help_menu = self.menuBar().addMenu("帮助")

        act_github = QAction("打开 GitHub", self)
        act_github.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MichaelChen2025")))
        help_menu.addAction(act_github)

        act_site = QAction("打开网站", self)
        act_site.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://michaelchen.com.cn")))
        help_menu.addAction(act_site)

        act_email = QAction("联系作者", self)
        act_email.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("mailto:michael@mcslab.top")))
        help_menu.addAction(act_email)

    def build_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)

        dir_box = QGroupBox("素材根目录")
        dir_layout = QGridLayout(dir_box)

        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)

        btn_source = QPushButton("选择素材根目录")
        btn_source.clicked.connect(self.choose_source)

        self.btn_open_source = QPushButton("打开目录")
        self.btn_open_source.clicked.connect(lambda: self.open_path(self.source_dir))
        self.btn_open_source.setEnabled(False)

        dir_layout.addWidget(QLabel("目录："), 0, 0)
        dir_layout.addWidget(self.source_edit, 0, 1)
        dir_layout.addWidget(btn_source, 0, 2)
        dir_layout.addWidget(self.btn_open_source, 0, 3)
        dir_layout.setColumnStretch(1, 1)
        layout.addWidget(dir_box)

        option_box = QGroupBox("扫描与整理选项")
        option_layout = QVBoxLayout(option_box)

        self.strict_check = QTableWidgetItem  # 占位防静态误报

        from PySide6.QtWidgets import QCheckBox
        self.strict_check = QCheckBox("严格模式：校验文件名日期和元数据日期")
        self.skip_sorted_check = QCheckBox("跳过已经整理过的日期文件夹和零散素材文件夹")
        self.skip_sorted_check.setChecked(True)

        info_label = QLabel("整理方式：在素材根目录内移动文件。不复制素材，不上传素材。")
        info_label.setStyleSheet("color: #b8b8b8;")

        option_layout.addWidget(self.strict_check)
        option_layout.addWidget(self.skip_sorted_check)
        option_layout.addWidget(info_label)
        layout.addWidget(option_box)

        action_row = QHBoxLayout()

        self.btn_scan = QPushButton("扫描素材")
        self.btn_scan.setObjectName("PrimaryButton")
        self.btn_scan.clicked.connect(self.start_scan)

        self.btn_apply = QPushButton("应用整理")
        self.btn_apply.setObjectName("DangerButton")
        self.btn_apply.clicked.connect(self.start_apply)
        self.btn_apply.setEnabled(False)

        self.btn_restore = QPushButton("恢复上一次整理")
        self.btn_restore.clicked.connect(self.start_restore)

        self.btn_cancel = QPushButton("取消当前任务")
        self.btn_cancel.clicked.connect(self.cancel_task)
        self.btn_cancel.setEnabled(False)

        action_row.addWidget(self.btn_scan)
        action_row.addWidget(self.btn_apply)
        action_row.addWidget(self.btn_restore)
        action_row.addWidget(self.btn_cancel)
        layout.addLayout(action_row)

        cards = QHBoxLayout()
        self.card_total = StatCard("视频总数")
        self.card_groups = StatCard("日期组")
        self.card_named = StatCard("已命名 / 项目组")
        self.card_unnamed = StatCard("未命名")
        self.card_misc = StatCard("零散素材")
        self.card_skipped = StatCard("跳过")

        for card in [
            self.card_total, self.card_groups, self.card_named,
            self.card_unnamed, self.card_misc, self.card_skipped
        ]:
            cards.addWidget(card)
        layout.addLayout(cards)

        guide = QGroupBox("使用流程")
        guide_layout = QVBoxLayout(guide)
        guide_label = QLabel(
            "1. 选择素材根目录。\n"
            "2. 扫描视频素材，程序会按拍摄日期聚类。\n"
            "3. 进入“整理”页面：单击日期组查看素材，勾选多个日期组进行合并或归入零散素材。\n"
            "4. 双击右侧素材列表，可用系统默认播放器打开。\n"
            "5. 应用整理前会显示整理计划预览。\n"
            "6. 所有移动操作都会生成恢复日志。"
        )
        guide_label.setWordWrap(True)
        guide_layout.addWidget(guide_label)
        layout.addWidget(guide)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box, stretch=1)

    def build_organize_tab(self):
        layout = QVBoxLayout(self.organize_tab)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("排序依据："))

        self.sort_field_combo = QComboBox()
        self.sort_field_combo.addItems(["日期", "数量", "状态"])
        self.sort_field_combo.setCurrentText("日期")
        self.sort_field_combo.currentIndexChanged.connect(self.on_sort_field_changed)
        top_row.addWidget(self.sort_field_combo)

        self.sort_direction_label = QLabel("排序方向：")
        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["降序", "升序"])
        self.sort_direction_combo.setCurrentText("降序")
        self.sort_direction_combo.currentIndexChanged.connect(self.refresh_cluster_table)

        top_row.addWidget(self.sort_direction_label)
        top_row.addWidget(self.sort_direction_combo)

        self.btn_check_all = QPushButton("全选")
        self.btn_check_all.clicked.connect(lambda: self.set_all_checked(True))

        self.btn_uncheck_all = QPushButton("取消全选")
        self.btn_uncheck_all.clicked.connect(lambda: self.set_all_checked(False))

        self.btn_checked_misc = QPushButton("勾选项归入零散素材")
        self.btn_checked_misc.clicked.connect(self.mark_checked_misc)

        self.btn_checked_skip = QPushButton("勾选项跳过")
        self.btn_checked_skip.clicked.connect(self.mark_checked_skipped)

        top_row.addStretch()
        top_row.addWidget(self.btn_check_all)
        top_row.addWidget(self.btn_uncheck_all)
        top_row.addWidget(self.btn_checked_misc)
        top_row.addWidget(self.btn_checked_skip)
        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)

        note = QLabel("日期组表格：单击查看；勾选用于批量合并、跳过或归入零散素材。")
        note.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(note)

        self.cluster_table = QTableWidget(0, 6)
        self.cluster_table.setHorizontalHeaderLabels(["选择", "日期", "数量", "内容名称", "最终文件夹名", "状态"])
        self.cluster_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.cluster_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cluster_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cluster_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.cluster_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.cluster_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.cluster_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cluster_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cluster_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cluster_table.itemSelectionChanged.connect(self.on_cluster_selected)
        self.cluster_table.itemChanged.connect(self.on_table_item_changed)

        left_layout.addWidget(self.cluster_table)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.current_label = QLabel("当前日期组：未选择")
        self.current_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(self.current_label)

        self.clip_list = QListWidget()
        self.clip_list.itemDoubleClicked.connect(self.play_selected_clip)
        right_layout.addWidget(self.clip_list, stretch=1)

        clip_hint = QLabel("提示：双击素材可用系统默认播放器打开。")
        clip_hint.setStyleSheet("color: #b8b8b8;")
        right_layout.addWidget(clip_hint)

        self.btn_open_clip_folder = QPushButton("打开素材所在文件夹")
        self.btn_open_clip_folder.clicked.connect(self.open_selected_clip_folder)
        self.btn_open_clip_folder.setEnabled(False)
        right_layout.addWidget(self.btn_open_clip_folder)

        rename_box = QGroupBox("命名 / 项目操作")
        rename_layout = QVBoxLayout(rename_box)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称")
        self.name_edit.returnPressed.connect(self.apply_name_and_next)
        rename_layout.addWidget(self.name_edit)

        name_buttons = QHBoxLayout()
        self.btn_apply_name = QPushButton("单日命名")
        self.btn_apply_name.clicked.connect(self.apply_name)
        self.btn_apply_name.setEnabled(False)

        self.btn_apply_next = QPushButton("单日命名并下一组")
        self.btn_apply_next.clicked.connect(self.apply_name_and_next)
        self.btn_apply_next.setEnabled(False)

        name_buttons.addWidget(self.btn_apply_name)
        name_buttons.addWidget(self.btn_apply_next)
        rename_layout.addLayout(name_buttons)

        self.btn_project_group = QPushButton("勾选日期合并为同一项目")
        self.btn_project_group.clicked.connect(self.apply_project_group_name)

        self.btn_clear_project_group = QPushButton("取消勾选项的项目组 / 零散素材")
        self.btn_clear_project_group.clicked.connect(self.clear_group_flags_for_checked)

        self.btn_small_misc = QPushButton("5条及以下未命名组归入零散素材")
        self.btn_small_misc.clicked.connect(self.auto_name_small_groups)

        rename_layout.addWidget(self.btn_project_group)
        rename_layout.addWidget(self.btn_clear_project_group)
        rename_layout.addWidget(self.btn_small_misc)
        right_layout.addWidget(rename_box)

        splitter.addWidget(right)
        splitter.setSizes([820, 480])
        layout.addWidget(splitter)

    def build_help_tab(self):
        layout = QVBoxLayout(self.help_tab)

        about_box = QGroupBox("作者与反馈")
        about_layout = QVBoxLayout(about_box)
        about_label = QLabel(
            "作者：Michael Chen\n"
            "GitHub：https://github.com/MichaelChen2025\n"
            "网站：michaelchen.com.cn\n"
            "邮箱：michael@mcslab.top\n"
            "开源协议：MIT License"
        )
        about_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        about_layout.addWidget(about_label)
        layout.addWidget(about_box)

        safety_box = QGroupBox("安全声明")
        safety_layout = QVBoxLayout(safety_box)
        safety_label = QLabel(
            "Footage Organizer Free 是一个纯本地运行的软件。\n\n"
            "当前 Free / Beta 版本不会登录账号，不会连接云端，不会上传素材，不会同步文件，"
            "也不会把你的素材目录发送到任何服务器。\n\n"
            "软件只会在你选择的素材根目录内移动视频文件，并生成本地恢复日志。"
        )
        safety_label.setWordWrap(True)
        safety_layout.addWidget(safety_label)
        layout.addWidget(safety_box)

        license_box = QGroupBox("定位说明")
        license_layout = QVBoxLayout(license_box)
        license_label = QLabel(
            "本软件不是媒体库，也不是 Adobe Bridge / Lightroom 的替代品。\n"
            "它只是一个用于剪辑前快速整理视频素材的轻量工具。\n\n"
            "照片、RAW、缩略图墙等多媒体管理功能，未来可作为 Pro 版本方向。"
        )
        license_label.setWordWrap(True)
        license_layout.addWidget(license_label)
        layout.addWidget(license_box)
        layout.addStretch()

    # ---------------- 工程文件 ----------------

    def current_sort_state(self) -> tuple[str, bool]:
        field = self.sort_field_combo.currentText() if hasattr(self, "sort_field_combo") else "日期"
        desc = self.sort_direction_combo.currentText() == "降序" if hasattr(self, "sort_direction_combo") else True
        if field == "状态":
            desc = False
        return field, desc

    def build_project_payload(self) -> dict:
        field, desc = self.current_sort_state()
        return build_project_payload(self.source_dir, self.clusters, field, desc)

    def save_project_action(self):
        """
        保存工程。

        如果当前工程已有路径，则直接覆盖保存。
        如果当前工程没有路径，则要求用户输入工程名，并创建一个带时间戳的 JSON 工程文件。
        """
        if not self.clusters and not self.source_dir:
            QMessageBox.information(self, "提示", "当前没有可保存的工程。")
            return

        if self.current_project_file is None:
            name, ok = QInputDialog.getText(self, "保存工程", "工程名称：")
            if not ok:
                return

            self.current_project_file = make_project_path(name)

        save_project(self.current_project_file, self.build_project_payload())
        set_last_project_file(self.current_project_file)

        self.dirty = False
        self.log(f"已保存工程：{self.current_project_file.name}")
        self.statusBar().showMessage("工程已保存")

    def save_project_as_action(self):
        """
        工程另存为。

        无论当前工程是否已有路径，都会创建一个新的带时间戳 JSON 工程文件。
        """
        if not self.clusters and not self.source_dir:
            QMessageBox.information(self, "提示", "当前没有可保存的工程。")
            return

        name, ok = QInputDialog.getText(self, "工程另存为", "工程名称：")
        if not ok:
            return

        path = make_project_path(name)
        save_project(path, self.build_project_payload())
        set_last_project_file(path)

        self.current_project_file = path
        self.dirty = False

        abs_path = str(path.resolve())
        self.log(f"工程已另存为：{abs_path}")
        self.statusBar().showMessage(f"工程已另存为：{abs_path}")

    def open_project_action(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "打开工程文件",
            str(PROJECTS_DIR),
            "JSON 工程文件 (*.json);;所有文件 (*.*)"
        )
        if not file:
            return

        self.load_project_file(Path(file))

    def load_current_project_on_startup(self):
        """启动时自动加载最近一次保存或打开的工程。"""
        path = get_last_project_file()
        if not path:
            return

        try:
            payload = load_project(path)
            self.apply_project_payload(payload)
            self.current_project_file = path
            self.dirty = False
            self.log(f"已自动加载上次工程：{path.name}")
            self.statusBar().showMessage("已加载上次工程")
        except Exception as e:
            self.log(f"[工程加载失败] {e}")

    def load_project_file(self, path: Path):
        try:
            payload = load_project(path)
            self.apply_project_payload(payload)
            self.current_project_file = path
            set_last_project_file(path)
            self.dirty = False
            self.log(f"已打开工程：{path.name}")
            self.statusBar().showMessage("工程已打开")
        except Exception as e:
            QMessageBox.critical(self, "打开失败", str(e))

    def apply_project_payload(self, payload: dict):
        source = payload.get("source_dir", "")
        self.source_dir = Path(source) if source else None
        self.source_edit.setText(source)
        self.btn_open_source.setEnabled(bool(self.source_dir))

        self.clusters = payload_to_clusters(payload)
        self.has_meaningful_progress = bool(self.clusters)
        self.refresh_cluster_table()
        self.update_cards()
        self.btn_apply.setEnabled(bool(self.clusters))

        sort_field = payload.get("sort_field", "日期")
        sort_desc = bool(payload.get("sort_desc", True))
        if sort_field in ["日期", "数量", "状态"]:
            self.sort_field_combo.setCurrentText(sort_field)
        if sort_field != "状态":
            self.sort_direction_combo.setCurrentText("降序" if sort_desc else "升序")

    # ---------------- 通用 ----------------

    def log(self, message: str = ""):
        now = datetime.now().strftime("[%H:%M:%S]")
        self.log_box.append(f"{now} {message}")

    def mark_dirty(self, meaningful: bool = True):
        self.dirty = True
        if meaningful:
            self.has_meaningful_progress = True

    def open_path(self, path: Path | None):
        if not path:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def choose_source(self):
        folder = QFileDialog.getExistingDirectory(self, "选择素材根目录")
        if not folder:
            return

        self.source_dir = Path(folder)
        self.source_edit.setText(folder)
        self.btn_open_source.setEnabled(True)
        self.statusBar().showMessage("已选择素材根目录")

    def set_busy(self, busy: bool):
        self.btn_scan.setEnabled(not busy)
        self.btn_apply.setEnabled((not busy) and bool(self.clusters))
        self.btn_restore.setEnabled(not busy)
        self.btn_cancel.setEnabled(busy)

    def update_cards(self):
        total = sum(len(c.clips) for c in self.clusters.values())
        groups = len(self.clusters)
        named = sum(1 for c in self.clusters.values() if c.status in ["已命名", "项目组"])
        skipped = sum(1 for c in self.clusters.values() if c.skipped)
        unnamed = sum(1 for c in self.clusters.values() if c.status == "未命名")
        misc = sum(1 for c in self.clusters.values() if c.misc_group)

        self.card_total.set_value(total)
        self.card_groups.set_value(groups)
        self.card_named.set_value(named)
        self.card_unnamed.set_value(unnamed)
        self.card_misc.set_value(misc)
        self.card_skipped.set_value(skipped)

    # ---------------- 扫描 ----------------

    def start_scan(self):
        if not self.source_dir:
            QMessageBox.warning(self, "提示", "请先选择素材根目录。")
            return

        self.clusters.clear()
        self.display_order.clear()
        self.selected_date_key = None
        self.cluster_table.setRowCount(0)
        self.clip_list.clear()
        self.name_edit.clear()
        self.progress.setValue(0)
        self.log_box.clear()
        self.update_cards()

        self.tabs.setCurrentWidget(self.dashboard_tab)
        self.log("开始扫描并按日期分类。")

        self.worker = ScanWorker(
            source_dir=self.source_dir,
            strict=self.strict_check.isChecked(),
            skip_sorted=self.skip_sorted_check.isChecked()
        )

        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_ok.connect(self.on_scan_finished)
        self.worker.failed.connect(self.on_worker_failed)

        self.set_busy(True)
        self.worker.start()

    def on_scan_finished(self, payload: dict):
        self.set_busy(False)

        if not payload:
            self.log("未找到可处理的视频素材。")
            self.statusBar().showMessage("未找到视频素材")
            return

        self.clusters = payload["clusters"]
        stats = payload["stats"]
        self.refresh_cluster_table()
        self.update_cards()
        self.mark_dirty(meaningful=False)
        self.has_meaningful_progress = True

        self.log("")
        self.log("扫描完成。")
        self.log(f"日期组数量：{len(self.clusters)}")
        self.log(f"视频总数：{sum(len(c.clips) for c in self.clusters.values())}")
        self.log(f"文件名快速识别：{stats['filename_fast']}")
        self.log(f"严格校验通过：{stats['filename_verified']}")
        self.log(f"元数据识别：{stats['metadata']}")
        self.log(f"修改时间兜底：{stats['mtime']}")
        self.log(f"日期冲突跳过：{stats['conflict']}")
        self.log("请进入“整理”页面命名或合并日期组。")

        self.btn_apply.setEnabled(True)
        self.statusBar().showMessage("扫描完成，请进入整理页面")
        self.tabs.setCurrentWidget(self.organize_tab)

    # ---------------- 表格与排序 ----------------

    def on_sort_field_changed(self):
        field = self.sort_field_combo.currentText()

        if field == "状态":
            self.sort_direction_label.setVisible(False)
            self.sort_direction_combo.setVisible(False)
        else:
            self.sort_direction_label.setVisible(True)
            self.sort_direction_combo.setVisible(True)
            self.sort_direction_combo.setCurrentText("降序")

        self.refresh_cluster_table()

    def rebuild_display_order(self):
        keys = list(self.clusters.keys())
        field, desc = self.current_sort_state()

        if field == "日期":
            keys.sort(reverse=desc)
        elif field == "数量":
            keys.sort(key=lambda k: len(self.clusters[k].clips), reverse=desc)
        elif field == "状态":
            status_rank = {"未命名": 0, "已命名": 1, "项目组": 2, "零散素材": 3, "跳过": 4}
            keys.sort(key=lambda k: (status_rank.get(self.clusters[k].status, 9), k))

        self.display_order = keys

    def refresh_cluster_table(self):
        checked_keys = set(self.checked_date_keys()) if hasattr(self, "cluster_table") else set()
        self.cluster_table.blockSignals(True)
        self.rebuild_display_order()
        self.cluster_table.setRowCount(len(self.display_order))

        for row, date_key in enumerate(self.display_order):
            cluster = self.clusters[date_key]

            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            check_item.setCheckState(Qt.Checked if date_key in checked_keys else Qt.Unchecked)
            self.cluster_table.setItem(row, 0, check_item)

            values = [
                date_key,
                str(len(cluster.clips)),
                cluster.title,
                cluster.final_folder_name,
                cluster.status,
            ]

            for i, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                if i in [1, 2, 5]:
                    item.setTextAlignment(Qt.AlignCenter)
                self.cluster_table.setItem(row, i, item)

        self.cluster_table.blockSignals(False)
        self.update_cards()

    def on_table_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            return

    def checked_date_keys(self) -> list[str]:
        keys = []
        for row in range(self.cluster_table.rowCount()):
            item = self.cluster_table.item(row, 0)
            if item and item.checkState() == Qt.Checked and row < len(self.display_order):
                keys.append(self.display_order[row])
        return keys

    def set_all_checked(self, checked: bool):
        self.cluster_table.blockSignals(True)
        for row in range(self.cluster_table.rowCount()):
            item = self.cluster_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.cluster_table.blockSignals(False)

    def selected_date_keys_from_rows(self) -> list[str]:
        rows = sorted({item.row() for item in self.cluster_table.selectedItems()})
        keys = []
        for row in rows:
            if 0 <= row < len(self.display_order):
                keys.append(self.display_order[row])
        return keys

    def on_cluster_selected(self):
        date_keys = self.selected_date_keys_from_rows()
        if not date_keys:
            return

        self.selected_date_key = date_keys[0]
        cluster = self.clusters.get(self.selected_date_key)
        if not cluster:
            return

        self.current_label.setText(
            f"当前日期组：{cluster.date_key} | {len(cluster.clips)} 个视频 | {cluster.status}"
        )

        self.name_edit.setText(cluster.title)
        self.clip_list.clear()

        for clip in cluster.clips:
            self.clip_list.addItem(clip.path.name)

        self.btn_open_clip_folder.setEnabled(True)
        self.btn_apply_name.setEnabled(True)
        self.btn_apply_next.setEnabled(True)

    # ---------------- 素材预览 ----------------

    def selected_clip_path(self) -> Path | None:
        if not self.selected_date_key:
            return None

        cluster = self.clusters.get(self.selected_date_key)
        if not cluster:
            return None

        row = self.clip_list.currentRow()
        if row < 0 or row >= len(cluster.clips):
            return None

        return cluster.clips[row].path

    def play_selected_clip(self):
        clip = self.selected_clip_path()
        if not clip:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(clip)))

    def open_selected_clip_folder(self):
        clip = self.selected_clip_path()
        if not clip:
            QMessageBox.information(self, "提示", "请先选择一个素材。")
            return
        self.open_path(clip.parent)

    def reselect_date_key(self, date_key: str):
        for row, key in enumerate(self.display_order):
            if key == date_key:
                self.cluster_table.selectRow(row)
                break

    # ---------------- 命名和批量操作 ----------------

    def apply_name(self):
        if not self.selected_date_key:
            QMessageBox.information(self, "提示", "请先选择一个日期组。")
            return

        cluster = self.clusters.get(self.selected_date_key)
        if not cluster:
            return

        cluster.title = sanitize_folder_name(self.name_edit.text())
        cluster.project_folder_name = ""
        cluster.misc_group = False
        cluster.skipped = False

        self.refresh_cluster_table()
        self.reselect_date_key(self.selected_date_key)
        self.log(f"单日命名：{cluster.date_key} -> {cluster.final_folder_name}")
        self.mark_dirty()

    def apply_name_and_next(self):
        self.apply_name()
        if not self.selected_date_key or self.selected_date_key not in self.display_order:
            return

        idx = self.display_order.index(self.selected_date_key)
        if idx + 1 < len(self.display_order):
            self.reselect_date_key(self.display_order[idx + 1])

    def apply_project_group_name(self):
        date_keys = self.checked_date_keys()

        if len(date_keys) < 2:
            QMessageBox.information(self, "提示", "请先勾选两个或以上日期组。")
            return

        title = sanitize_folder_name(self.name_edit.text())
        if not title:
            QMessageBox.information(self, "提示", "请先输入项目名称。")
            return

        folder_name = build_project_folder_name(date_keys, title)

        for key in date_keys:
            cluster = self.clusters.get(key)
            if cluster:
                cluster.title = title
                cluster.project_folder_name = folder_name
                cluster.misc_group = False
                cluster.skipped = False

        self.refresh_cluster_table()
        self.log(f"项目组合并：{date_keys[0]} 至 {date_keys[-1]} -> {folder_name}")
        self.mark_dirty()

    def clear_group_flags_for_checked(self):
        date_keys = self.checked_date_keys()
        if not date_keys:
            QMessageBox.information(self, "提示", "请先勾选日期组。")
            return

        for key in date_keys:
            cluster = self.clusters.get(key)
            if cluster:
                cluster.project_folder_name = ""
                cluster.misc_group = False
                cluster.skipped = False

        self.refresh_cluster_table()
        self.log(f"已取消 {len(date_keys)} 个日期组的项目组 / 零散素材 / 跳过状态。")
        self.mark_dirty()

    def mark_checked_misc(self):
        date_keys = self.checked_date_keys()
        if not date_keys:
            QMessageBox.information(self, "提示", "请先勾选日期组。")
            return

        for key in date_keys:
            cluster = self.clusters.get(key)
            if cluster:
                cluster.title = ""
                cluster.project_folder_name = ""
                cluster.misc_group = True
                cluster.skipped = False

        self.refresh_cluster_table()
        self.log(f"已将 {len(date_keys)} 个日期组归入“零散素材”。")
        self.mark_dirty()

    def mark_checked_skipped(self):
        date_keys = self.checked_date_keys()
        if not date_keys:
            QMessageBox.information(self, "提示", "请先勾选日期组。")
            return

        for key in date_keys:
            cluster = self.clusters.get(key)
            if cluster:
                cluster.skipped = True

        self.refresh_cluster_table()
        self.log(f"已标记跳过：{len(date_keys)} 个日期组。")
        self.mark_dirty()

    def auto_name_small_groups(self):
        if not self.clusters:
            return

        count = 0
        for cluster in self.clusters.values():
            if (
                cluster.status == "未命名"
                and not cluster.skipped
                and len(cluster.clips) <= 5
            ):
                cluster.title = ""
                cluster.project_folder_name = ""
                cluster.misc_group = True
                count += 1

        self.refresh_cluster_table()
        self.log(f"已将 {count} 个 5 条及以下的未命名日期组归入“零散素材”。")
        self.mark_dirty()

    # ---------------- 应用整理与恢复 ----------------

    def show_apply_preview_dialog(self, preview_text: str) -> bool:
        """显示固定尺寸、可滚动的整理计划确认窗口。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("整理计划预览")
        dialog.setModal(True)
        dialog.setFixedSize(880, 600)

        layout = QVBoxLayout(dialog)

        title = QLabel("即将在素材根目录内移动整理文件。")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #8ab4f8;")
        layout.addWidget(title)

        hint = QLabel("请检查下面的整理计划。内容较多时，可以用鼠标滚轮上下查看。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #b8b8b8;")
        layout.addWidget(hint)

        preview_box = QPlainTextEdit()
        preview_box.setReadOnly(True)
        preview_box.setPlainText(preview_text)
        preview_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(preview_box, stretch=1)

        button_row = QHBoxLayout()
        button_row.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dialog.reject)

        btn_ok = QPushButton("继续整理")
        btn_ok.setObjectName("DangerButton")
        btn_ok.clicked.connect(dialog.accept)

        button_row.addWidget(btn_cancel)
        button_row.addWidget(btn_ok)
        layout.addLayout(button_row)

        btn_ok.setFocus()
        return dialog.exec() == QDialog.Accepted

    def build_apply_plan(self) -> list[tuple[Path, Path]]:
        if not self.source_dir:
            return []

        worker = ApplyWorker(self.clusters, self.source_dir)
        return worker.build_plan()

    def start_apply(self):
        if not self.clusters:
            QMessageBox.warning(self, "提示", "请先扫描分类。")
            return

        if not self.source_dir:
            QMessageBox.warning(self, "提示", "请先选择素材根目录。")
            return

        active_clusters = [c for c in self.clusters.values() if not c.skipped]
        unnamed = [c for c in active_clusters if c.status == "未命名"]

        if unnamed:
            ok = QMessageBox.question(
                self,
                "存在未命名日期组",
                f"还有 {len(unnamed)} 个未命名日期组。\n\n"
                "未命名日期组会只使用日期作为文件夹名。\n\n"
                "是否继续？"
            )
            if ok != QMessageBox.Yes:
                return

        plan = self.build_apply_plan()
        if not plan:
            QMessageBox.information(self, "提示", "没有需要移动的文件。")
            return

        preview_lines = []
        for src, dst in plan:
            preview_lines.append(f"{src.name}  ->  {dst.parent.name}/")

        preview_text = (
            f"计划移动文件数：{len(plan)}\n\n"
            + "\n".join(preview_lines)
            + "\n\n是否开始？"
        )

        if not self.show_apply_preview_dialog(preview_text):
            return

        self.tabs.setCurrentWidget(self.dashboard_tab)
        self.log("开始应用整理。")
        self.progress.setValue(0)

        self.worker = ApplyWorker(self.clusters, self.source_dir)
        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_ok.connect(self.on_apply_finished)
        self.worker.failed.connect(self.on_worker_failed)

        self.set_busy(True)
        self.worker.start()

    def on_apply_finished(self, result: dict):
        self.set_busy(False)
        self.log("")
        self.log("整理完成。")
        self.log(f"成功：{result.get('success', 0)}")
        self.log(f"失败：{result.get('failed', 0)}")

        if result.get("restore_log"):
            self.log(f"恢复记录：{result['restore_log']}")

        self.statusBar().showMessage("整理完成")

    def start_restore(self):
        if self.worker and self.worker.isRunning():
            return

        ok = QMessageBox.question(
            self,
            "确认恢复",
            "将读取最新 restore_log，把文件移回原位置，并尝试删除空文件夹。\n\n"
            "恢复不会覆盖原位置已存在的文件。\n\n"
            "是否继续？"
        )

        if ok != QMessageBox.Yes:
            return

        self.tabs.setCurrentWidget(self.dashboard_tab)
        self.progress.setValue(0)

        self.worker = RestoreWorker(self.source_dir)
        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished_ok.connect(self.on_restore_finished)
        self.worker.failed.connect(self.on_worker_failed)

        self.set_busy(True)
        self.worker.start()

    def on_restore_finished(self, result: dict):
        self.set_busy(False)
        self.log("")
        self.log("恢复完成。")
        self.log(f"恢复：{result.get('restored', 0)}")
        self.log(f"冲突：{result.get('conflict', 0)}")
        self.log(f"失败：{result.get('failed', 0)}")
        self.statusBar().showMessage("恢复完成")

    def on_worker_failed(self, error: str):
        self.set_busy(False)
        QMessageBox.critical(self, "错误", error)
        self.log(f"[错误] {error}")
        self.statusBar().showMessage("发生错误")

    def cancel_task(self):
        if self.worker and self.worker.isRunning() and hasattr(self.worker, "cancel"):
            self.worker.cancel()
            self.log("已请求取消当前任务。")
            self.btn_cancel.setEnabled(False)

    def closeEvent(self, event: QCloseEvent):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "提示", "当前任务正在运行，请先取消或等待完成。")
            event.ignore()
            return

        if self.dirty and self.has_meaningful_progress:
            msg = QMessageBox(self)
            msg.setWindowTitle("保存当前工程")
            msg.setText(
                "当前工程有未保存的整理进度。\n\n"
                "是否保存后退出？"
            )

            save_btn = msg.addButton("保存并退出", QMessageBox.AcceptRole)
            discard_btn = msg.addButton("不保存退出", QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton("取消", QMessageBox.RejectRole)

            msg.setDefaultButton(save_btn)
            msg.exec()

            clicked = msg.clickedButton()

            if clicked == save_btn:
                try:
                    if self.current_project_file is None:
                        name, ok = QInputDialog.getText(self, "保存工程", "工程名称：")
                        if not ok:
                            event.ignore()
                            return

                        self.current_project_file = make_project_path(name)

                    save_project(self.current_project_file, self.build_project_payload())
                    set_last_project_file(self.current_project_file)
                    event.accept()
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", str(e))
                    event.ignore()
                return

            if clicked == discard_btn:
                event.accept()
                return

            event.ignore()
            return

        event.accept()