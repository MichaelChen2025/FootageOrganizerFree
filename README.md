# Footage Organizer Free

A lightweight local footage organization tool for video creators.

一个专为视频创作者设计的本地素材整理工具。

<img width="2042" height="1337" alt="image" src="https://github.com/user-attachments/assets/4ba79444-9a96-4e48-9454-47aa086cb69a" />


---

## 🌐 Language / 语言

* [简体中文](#简体中文)
* [English](#english)

---

# 简体中文

## 项目简介

Footage Organizer Free 是一个专为视频创作者设计的本地素材整理工具。

软件可以根据拍摄日期自动整理大量视频素材，帮助你在导入 Premiere Pro、Final Cut Pro 或 DaVinci Resolve 之前快速完成素材归档。

支持来自：

* 手机
* 相机
* 无人机
* 运动相机
* 录屏软件

的视频素材。

所有整理操作均在本地完成。

---

## 为什么开发这个软件？

很多创作者都会遇到类似的问题：

一次毕业旅行结束后，素材目录可能变成这样：

```text
DJI_0001.MP4
DJI_0002.MP4
DJI_0003.MP4

IMG_4582.MOV
IMG_4583.MOV

VID_20260712.mp4
VID_20260713.mp4
```

素材来自：

* 手机
* 相机
* 无人机

全部混在一起。

在正式开始剪辑之前，往往需要花费大量时间整理素材。

Footage Organizer Free 的目标很简单：

**让创作者把时间花在创作上，而不是整理素材上。**

---

## 软件定位

> 本软件不是媒体库（Media Library）

> 本软件不是 Adobe Bridge、Lightroom 或照片管理软件的替代品

> 本软件专注于剪辑前的视频素材整理

---

## 当前状态

当前版本：

```text
0.9.1-beta
```

项目目前处于 Beta 测试阶段。

---

## 下载与安装

如果你只是想使用软件，而不是参与开发：

请直接前往 GitHub Releases 页面下载最新安装包。

Release 版本已经包含：

* 主程序
* ExifTool
* 所有运行依赖

无需安装 Python。

无需额外配置 ExifTool。

下载安装即可使用。

---

## 主要功能

### 自动扫描素材

扫描指定目录下的视频文件。

### 自动识别拍摄日期

支持：

* 文件名日期识别
* ExifTool 元数据识别
* 文件修改时间兜底

### 日期聚类

自动将同一天拍摄的素材归为一个日期组。

例如：

```text
2026-07-12
```

包含：

```text
DJI_0001.MP4
DJI_0002.MP4
IMG_1023.MOV
```

### 单日命名

例如：

```text
2026-07-12 成都春熙路街拍
```

### 多日项目合并

例如：

```text
2026-07-12
2026-07-13
2026-07-14
```

合并为：

```text
2026-07-12 ~ 2026-07-14 云南毕业旅行
```

### 零散素材归档

适用于：

* 测试镜头
* 无人机试飞
* 延时摄影练习
* 设备测试素材

统一整理到：

```text
零散素材
```

文件夹。

### 整理计划预览

正式整理前：

软件会显示完整移动计划。

确认后才会执行。

### 工程文件

支持：

* 保存工程
* 加载工程
* 自动恢复上次进度

### 恢复功能

所有整理操作都会自动生成恢复日志。

支持：

```text
恢复上一次整理
```

避免误操作。

---

## 使用流程

```text
选择素材目录
        ↓
扫描素材
        ↓
自动按日期分类
        ↓
命名日期组
        ↓
合并项目组
        ↓
归档零散素材
        ↓
应用整理
        ↓
导入 Premiere / FCP / Resolve
```

---

## 支持格式

当前 Free 版本支持：

```text
.mp4
.mov
.mxf
.mts
.m2ts
.avi
.mkv
.mpg
.mpeg
.3gp
```

未来版本可能增加：

* JPG
* HEIC
* RAW
* DNG
* 缩略图管理
* 照片素材管理

---

## 数据安全

Footage Organizer Free 完全本地运行。

当前 Beta 版本：

* 不联网
* 不上传素材
* 不同步文件
* 不需要账号
* 不读取素材内容

软件仅会：

* 读取时间信息
* 创建文件夹
* 移动文件
* 生成恢复日志

所有数据均保留在本机。

---

## 开发环境

安装依赖：

```bash
pip install -r requirements.txt
```

运行：

```bash
python main.py
```

---

## 项目结构

```text
FootageOrganizerFree/
├─ src/
├─ exiftool/
├─ projects/
├─ requirements.txt
└─ README.md
```

---

## ExifTool

本项目使用 ExifTool 读取视频元数据。

为了方便用户使用：

* Release 版本已内置 ExifTool
* 仓库源码包含运行所需文件

无需额外下载和配置。

---

## Beta 测试反馈

当前版本仍处于 Beta 测试阶段。

如果你发现：

* Bug
* 崩溃问题
* 日期识别错误
* 界面显示问题
* 功能建议

欢迎反馈。

邮箱：

```text
michael@mcslab.top
```

建议附带：

* 软件版本号
* 问题截图
* 问题描述
* 示例素材（如方便提供）

你的反馈将帮助这个项目持续改进。

---

## License

MIT License

---

# English

## Overview

Footage Organizer Free is a lightweight local footage organization tool designed for video creators.

It automatically organizes large amounts of video footage by shooting date and helps creators prepare footage before importing into Premiere Pro, Final Cut Pro, or DaVinci Resolve.

Supported sources include:

* Smartphones
* Cameras
* Drones
* Action cameras
* Screen recordings

All operations are performed locally.

---

## Why This Project?

Many creators face the same problem.

After a trip or a large project, the footage folder may look like:

```text
DJI_0001.MP4
DJI_0002.MP4
DJI_0003.MP4

IMG_4582.MOV
IMG_4583.MOV

VID_20260712.mp4
VID_20260713.mp4
```

Footage comes from:

* Smartphones
* Cameras
* Drones

Everything is mixed together.

Before editing begins, a significant amount of time is often spent organizing files manually.

The goal of Footage Organizer Free is simple:

**Spend more time creating, and less time organizing footage.**

---

## Project Positioning

> This is not a media library.

> This is not a replacement for Adobe Bridge, Lightroom, or photo asset management software.

> It focuses on footage organization before editing.

---

## Current Status

Current version:

```text
0.9.1-beta
```

The project is currently in beta testing.

---

## Download & Installation

If you only want to use the software:

Download the latest installer from GitHub Releases.

The Release package already includes:

* Main application
* ExifTool
* Runtime dependencies

No Python installation required.

No additional ExifTool setup required.

Ready to use out of the box.

---

## Features

### Automatic Footage Scanning

Scan video files from a selected root folder.

### Automatic Date Detection

Supports:

* Filename date detection
* ExifTool metadata detection
* Modified-time fallback

### Date Clustering

Automatically groups footage shot on the same day.

Example:

```text
2026-07-12
```

Contains:

```text
DJI_0001.MP4
DJI_0002.MP4
IMG_1023.MOV
```

### Single-Day Naming

Example:

```text
2026-07-12 Chengdu Street Photography
```

### Multi-Day Project Grouping

Example:

```text
2026-07-12
2026-07-13
2026-07-14
```

Merged into:

```text
2026-07-12 ~ 2026-07-14 Yunnan Graduation Trip
```

### Misc Footage Organization

Useful for:

* Test clips
* Drone test flights
* Time-lapse practice
* Equipment tests

Grouped into:

```text
Misc Footage
```

### Move Plan Preview

Preview all file movements before applying changes.

### Project Files

Supports:

* Save project
* Load project
* Resume previous progress

### Restore Function

Every organization operation generates a restore log.

Supports:

```text
Restore Last Organization
```

to prevent accidental mistakes.

---

## Workflow

```text
Select Footage Folder
          ↓
Scan Footage
          ↓
Automatic Date Grouping
          ↓
Name Date Groups
          ↓
Merge Project Groups
          ↓
Organize Misc Footage
          ↓
Apply Changes
          ↓
Import into Premiere / FCP / Resolve
```

---

## Supported Formats

```text
.mp4
.mov
.mxf
.mts
.m2ts
.avi
.mkv
.mpg
.mpeg
.3gp
```

Future versions may include:

* JPG
* HEIC
* RAW
* DNG
* Thumbnail management
* Photo asset management

---

## Data Safety

Footage Organizer Free runs entirely locally.

The current Beta version:

* Does not connect to the internet
* Does not upload footage
* Does not sync files
* Does not require accounts
* Does not analyze footage content

The software only:

* Reads timestamp information
* Creates folders
* Moves files
* Generates restore logs

All data remains on the local machine.

---

## Development Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

---

## Project Structure

```text
FootageOrganizerFree/
├─ src/
├─ exiftool/
├─ projects/
├─ requirements.txt
└─ README.md
```

---

## ExifTool

This project uses ExifTool for video metadata extraction.

For convenience:

* ExifTool is included in Release packages
* The repository contains the required runtime files

No additional setup is required.

---

## Beta Feedback

This project is currently in beta testing.

Bug reports, feature requests, and feedback are welcome.

Email:

```text
michael@mcslab.top
```

Please include:

* Software version
* Screenshots
* Description of the issue
* Sample footage if available

Your feedback helps improve the project.

---

## License

MIT License
