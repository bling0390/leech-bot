# Alist-bot

English | [简体中文](README.md)

A Telegram-based file download and transfer bot that supports various resource downloads and storage integrations.

## Project Introduction

Alist-bot is a powerful Telegram bot capable of downloading files from various internet sources and uploading them to Alist or transferring them to other cloud storage services via Rclone. This bot supports multiple download sources, including direct links, YouTube, Mediafire, etc., and can integrate with various cloud storage services.

## Features

- **Multiple Download Sources**: Support for downloading from direct links, YouTube, Mediafire, and more
- **Cloud Storage Integration**:
  - Alist storage integration
  - Rclone cloud storage support (115 Netdisk, Mega, etc.)
  - Direct Telegram upload support (to channels or private chats)
- **File Management**:
  - Queue management and concurrent tasks
  - Task status monitoring
  - Failed task retry mechanism
- **Internationalization**: Built-in multi-language support
- **Docker Deployment**: Containerized deployment solution

## System Requirements

- Python 3.8 or higher
- Docker environment (optional, for containerized deployment)
- MongoDB database
- Redis service
- Rclone (if cloud storage functionality is needed)

## Installation Guide

### Using Docker Deployment (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Alist-bot.git
   cd Alist-bot
   ```

2. Configure the `config.yaml` file:
   ```yaml
   # Modify the relevant parameters in the configuration file
   ALIST_HOST: "Your Alist address"
   ALIST_WEB: "Your Alist web address"
   ALIST_TOKEN: "Your Alist Token"
   TELEGRAM_ADMIN_ID: Your Telegram ID
   # Other configurations...
   ```

3. Start the service using Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Alist-bot.git
   cd Alist-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the `config.yaml` file

4. Start the bot:
   ```bash
   python bot.py
   ```

## Configuration

### Basic Configuration

- `ALIST_HOST`: Alist server address, such as "http://192.168.1.100:5244" or domain name
- `ALIST_WEB`: Alist web access address
- `ALIST_TOKEN`: Alist authorization token
- `TELEGRAM_ADMIN_ID`: Administrator Telegram ID
- `TELEGRAM_MEMBER`: List of user, group, and channel IDs allowed to use the bot
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_API_ID` & `TELEGRAM_API_HASH`: Telegram API credentials
- `TELEGRAM_CHANNEL_ID`: Notification channel ID

### Download and Storage Configuration

- `BOT_DOWNLOAD_LOCATION`: Download file storage path
- `MAXIMUM_LEECH_WORKER`: Maximum number of simultaneous download tasks
- `MAXIMUM_SYNC_WORKER`: Maximum number of simultaneous synchronization tasks
- `SHOULD_USE_DATETIME_CATEGORY`: Whether to use date as category directory

### Database Configuration

- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis connection configuration
- `MONGO_HOST`, `MONGO_PORT`, `MONGO_USERNAME`, `MONGO_PASSWORD`, `MONGO_DATABASE_NAME`: MongoDB connection configuration

### Cloud Storage Configuration

- `RCLONE_REMOTES`: List of enabled Rclone remote storage
- `RCLONE_115_COOKIE`: 115 Netdisk Cookie
- `MEGA_AUTHORIZATION_EMAIL` & `MEGA_AUTHORIZATION_PASSWORD`: Mega account credentials
- `TELEGRAM_CHANNEL_ID`: Default channel ID when using Telegram upload option

### Proxy Configuration

- `BOT_PROXY_SCHEMAS`, `BOT_PROXY_HOST`, `BOT_PROXY_PORT`: Proxy server configuration

### Other Settings

- `SKIP_DUPLICATE_LINK_WITHIN_DAYS`: Skip duplicate links within specified days
- `FAILED_TASK_EXPIRE_AFTER_DAYS`: Failed task expiration days
- `MAXIMUM_QUEUE_SIZE`: Maximum queue size
- `WRITE_STREAM_CONNECT_TIMEOUT`: Write stream connection timeout

## Usage Guide

1. Start the bot in Telegram
2. Use the `/leech` command to begin a download task
3. Follow the prompts to select the download source and target storage
4. Wait for the task to complete and receive notifications

## Common Issues

- **Bot Not Responding**: Check Telegram API configuration and network connection
- **Download Failure**: Confirm that the source link is valid and there is enough storage space
- **Upload Failure**: Check Alist configuration and permission settings

## Contribution Guidelines

Bug reports, feature requests, and code contributions are welcome. Please participate in project development through GitHub issues and pull requests.

## License

[Project license information]

## Acknowledgements

- [Pyrogram](https://github.com/pyrogram/pyrogram) - Telegram client library
- [Alist](https://github.com/alist-org/alist) - File listing program
- [Rclone](https://github.com/rclone/rclone) - Cloud storage management tool 