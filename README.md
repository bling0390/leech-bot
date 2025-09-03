# Alist-bot

[English](README.en.md) | 简体中文

一个基于Telegram的文件下载、转存机器人，支持多种资源下载和存储集成。

## 项目简介

Alist-bot是一个功能强大的Telegram机器人，能够从各种网络来源下载文件，并将其上传至Alist或通过Rclone转存到其他云存储服务。此机器人支持多种下载源，包括直接链接、YouTube、Mediafire等，并能与多种云存储集成。

## 功能特性

- **多种下载源支持**：支持直接链接、YouTube、Mediafire等资源的下载
- **云存储集成**：
  - Alist存储集成
  - Rclone云存储支持（115网盘、Mega等）
  - Telegram直传支持（发送至频道或私聊）
- **文件管理**：
  - 支持队列管理和并发任务
  - 任务状态监控
  - 失败任务重试机制
- **国际化支持**：内置多语言支持
- **Docker部署**：提供容器化部署方案

## 系统要求

- Python 3.8或更高版本
- Docker环境(可选，用于容器化部署)
- MongoDB数据库
- Redis服务
- Rclone (如需使用云存储功能)

## 安装指南

### 使用Docker部署(推荐)

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/Alist-bot.git
   cd Alist-bot
   ```

2. 配置`config.yaml`文件：
   ```yaml
   # 修改配置文件中的相关参数
   ALIST_HOST: "你的Alist地址"
   ALIST_WEB: "你的Alist网页地址"
   ALIST_TOKEN: "你的Alist Token"
   TELEGRAM_ADMIN_ID: 你的Telegram ID
   # 其他配置...
   ```

3. 使用Docker Compose启动服务：
   ```bash
   docker-compose up -d
   ```

### 手动安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/Alist-bot.git
   cd Alist-bot
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置`config.yaml`文件

4. 启动机器人：
   ```bash
   python bot.py
   ```

## 配置说明

### 基础配置

- `ALIST_HOST`: Alist服务器地址，如"http://192.168.1.100:5244"或域名
- `ALIST_WEB`: Alist网页访问地址
- `ALIST_TOKEN`: Alist授权Token
- `TELEGRAM_ADMIN_ID`: 管理员Telegram ID
- `TELEGRAM_MEMBER`: 允许使用bot的用户、群组、频道ID列表
- `TELEGRAM_BOT_TOKEN`: Telegram机器人Token
- `TELEGRAM_API_ID` & `TELEGRAM_API_HASH`: Telegram API凭证
- `TELEGRAM_CHANNEL_ID`: 通知频道ID

### 下载与存储配置

- `BOT_DOWNLOAD_LOCATION`: 下载文件存储路径
- `MAXIMUM_LEECH_WORKER`: 最大同时下载任务数
- `MAXIMUM_SYNC_WORKER`: 最大同时同步任务数
- `SHOULD_USE_DATETIME_CATEGORY`: 是否使用日期作为分类目录

### 数据库配置

- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis连接配置
- `MONGO_HOST`, `MONGO_PORT`, `MONGO_USERNAME`, `MONGO_PASSWORD`, `MONGO_DATABASE_NAME`: MongoDB连接配置

### 云存储配置

- `RCLONE_REMOTES`: 启用的Rclone远程存储列表
- `RCLONE_115_COOKIE`: 115网盘Cookie
- `MEGA_AUTHORIZATION_EMAIL` & `MEGA_AUTHORIZATION_PASSWORD`: Mega账号凭证
- `TELEGRAM_CHANNEL_ID`: 当使用Telegram上传选项时的默认频道ID

### 代理配置

- `BOT_PROXY_SCHEMAS`, `BOT_PROXY_HOST`, `BOT_PROXY_PORT`: 代理服务器配置

### 其他设置

- `SKIP_DUPLICATE_LINK_WITHIN_DAYS`: 跳过指定天数内重复链接
- `FAILED_TASK_EXPIRE_AFTER_DAYS`: 失败任务过期天数
- `MAXIMUM_QUEUE_SIZE`: 最大队列大小
- `WRITE_STREAM_CONNECT_TIMEOUT`: 写入流连接超时时间

## 使用指南

1. 在Telegram中启动机器人
2. 使用`/leech`命令开始下载任务
3. 按照提示选择下载源和目标存储
4. 等待任务完成并接收通知

## 常见问题

- **机器人无响应**：检查Telegram API配置和网络连接
- **下载失败**：确认源链接有效且有足够的存储空间
- **上传失败**：检查Alist配置和权限设置

## 贡献指南

欢迎提交问题报告、功能请求和贡献代码。请通过GitHub issue和pull request参与项目开发。

## 许可证

[项目许可证信息]

## 致谢

- [Pyrogram](https://github.com/pyrogram/pyrogram) - Telegram客户端库
- [Alist](https://github.com/alist-org/alist) - 文件列表程序
- [Rclone](https://github.com/rclone/rclone) - 云存储管理工具
