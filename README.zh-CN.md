
# telert – 终端命令提醒工具

[English](README.md) | [हिन्दी](README.hi.md) | [中文 (简体)](README.zh-CN.md) | [Español](README.es.md)

<p align="center">
  <img src="https://github.com/navig-me/telert/raw/main/telert.png" alt="telert logo" width="150">
</p>

**版本 0.1.46**

[![GitHub Stars](https://img.shields.io/github/stars/navig-me/telert?style=social)](https://github.com/navig-me/telert/stargazers)
[![PyPI version](https://img.shields.io/pypi/v/telert)](https://pypi.org/project/telert/)
[![Downloads](https://static.pepy.tech/personalized-badge/telert?period=month&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/telert)
[![License](https://img.shields.io/github/license/navig-me/telert)](https://github.com/navig-me/telert/blob/main/docs/LICENSE)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Use%20this%20Action-blue?logo=github)](https://github.com/marketplace/actions/telert-run)
[![VS Code Marketplace](https://vsmarketplacebadges.dev/version/Navig.telert-vscode.svg?subject=VS%20Code%20Marketplace&style=flat-square)](https://marketplace.visualstudio.com/items?itemName=Navig.telert-vscode)

## 📱 概述

Telert 是一个轻量级工具，当你的终端命令或 Python 代码执行完毕时会发送通知。支持多个通知渠道：

- **消息应用**：Telegram、Microsoft Teams、Slack、Discord
- **电子邮件**：Email
- **移动设备**：Pushover（支持 Android 和 iOS）
- **本地通知**：桌面通知、音频提醒
- **自定义集成**：HTTP 接口，适配任意服务

非常适合长时间运行的任务、远程服务器、CI 流水线或关键代码的监控。

使用方式多样：
- Python 包：`pip install telert`
- Docker 镜像：`docker pull ghcr.io/navig-me/telert:latest`
- 云端托管 API：部署在 Replit、Railway、Render 或 Fly.io 上。

<img src="https://github.com/navig-me/telert/raw/main/docs/telert-demo.svg" alt="telert demo" width="600">

## 🚀 安装与快速开始

```bash
pip install telert
telert init
```

### 主要优势

- 📱 命令完成后立即获得通知，即使你不在电脑前
- ⏱️ 精准记录命令或代码的执行时长
- 🚦 捕获成功/失败状态码和异常信息
- 📃 在通知中直接查看命令输出片段
- 🔄 兼容 shell 命令、管道和 Python 代码

## 🤝 贡献与许可

欢迎提交 PR 和 issue！  
基于 MIT 协议开源许可 – 详见 `LICENSE` 文件。

## 👏 特别鸣谢

感谢所有为本项目提供反馈和功能建议的贡献者。如果你觉得此工具有用，可以通过 [Buy Me a Coffee](https://www.buymeacoffee.com/mihirk) 支持项目 ☕

### 需要 VPS？

推荐以下云平台（提供免费额度）：

- [Vultr](https://www.vultr.com/?ref=9752934-9J) — 免费赠送 $100
- [DigitalOcean](https://m.do.co/c/cdf2b5a182f2) — 免费赠送 $200
