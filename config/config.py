import yaml
from os import environ, path, getcwd
from httpx._config import DEFAULT_TIMEOUT_CONFIG


def get_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = get_config(path.join(getcwd(), 'config.yaml'))

TELEGRAM_ADMIN_ID = int(environ.get('TELEGRAM_ADMIN_ID', config.get('TELEGRAM_ADMIN_ID', '-1')))
TELEGRAM_MEMBER = environ.get('TELEGRAM_MEMBER', config.get('TELEGRAM_MEMBER'))
TELEGRAM_BOT_TOKEN = str(environ.get('TELEGRAM_BOT_TOKEN', config.get('TELEGRAM_BOT_TOKEN', '')))
TELEGRAM_API_ID = str(environ.get('TELEGRAM_API_ID', config.get('TELEGRAM_API_ID', '')))
TELEGRAM_API_HASH = str(environ.get('TELEGRAM_API_HASH', config.get('TELEGRAM_API_HASH', '')))
TELEGRAM_CHANNEL_ID = str(environ.get('TELEGRAM_CHANNEL_ID', config.get('TELEGRAM_CHANNEL_ID', '')))
ALIST_HOST = environ.get('ALIST_HOST', config.get('ALIST_HOST', '')).rstrip('/')
ALIST_WEB = environ.get('ALIST_WEB', config.get('ALIST_WEB', '')).rstrip('/')
ALIST_TOKEN = str(environ.get('ALIST_TOKEN', config.get('ALIST_TOKEN', '')))
BOT_DOWNLOAD_LOCATION = str(environ.get('BOT_DOWNLOAD_LOCATION', config.get('BOT_DOWNLOAD_LOCATION', ''))).rstrip('/')
MAXIMUM_LEECH_WORKER = int(environ.get('MAXIMUM_LEECH_WORKER', config.get('MAXIMUM_LEECH_WORKER', '1')))
MAXIMUM_SYNC_WORKER = int(environ.get('MAXIMUM_SYNC_WORKER', config.get('MAXIMUM_SYNC_WORKER', '1')))
WRITE_STREAM_CONNECT_TIMEOUT = float(
    environ.get('WRITE_STREAM_CONNECT_TIMEOUT', config.get('WRITE_STREAM_CONNECT_TIMEOUT', DEFAULT_TIMEOUT_CONFIG))
)
SHOULD_USE_DATETIME_CATEGORY = bool(
    environ.get('SHOULD_USE_DATETIME_CATEGORY', config.get('SHOULD_USE_DATETIME_CATEGORY'))
)
BOT_LOGS_LOCATION = str(environ.get('BOT_LOGS_LOCATION', config.get('BOT_LOGS_LOCATION', ''))).rstrip('/')
REDIS_HOST = str(environ.get('REDIS_HOST', config.get('REDIS_HOST', '')))
REDIS_PORT = int(environ.get('REDIS_PORT', config.get('REDIS_PORT', '6379')))
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', config.get('REDIS_PASSWORD', None))
SKIP_DUPLICATE_LINK_WITHIN_DAYS = int(
    environ.get('SKIP_DUPLICATE_LINK_WITHIN_DAYS', config.get('SKIP_DUPLICATE_LINK_WITHIN_DAYS', '0'))
)
FAILED_TASK_EXPIRE_AFTER_DAYS = int(
    environ.get('FAILED_TASK_EXPIRE_AFTER_DAYS', config.get('FAILED_TASK_EXPIRE_AFTER_DAYS', '0'))
)
MAXIMUM_QUEUE_SIZE = int(environ.get('MAXIMUM_QUEUE_SIZE', config.get('MAXIMUM_QUEUE_SIZE', '0')))
MEGA_AUTHORIZATION_EMAIL = environ.get('MEGA_AUTHORIZATION_EMAIL', config.get('MEGA_AUTHORIZATION_EMAIL'))
MEGA_AUTHORIZATION_PASSWORD = environ.get('MEGA_AUTHORIZATION_PASSWORD', config.get('MEGA_AUTHORIZATION_PASSWORD'))
BUNKR_DOMAIN = environ.get('BUNKR_DOMAIN', config.get('BUNKR_DOMAIN'))
BOT_PROXY_SCHEMAS = environ.get('BOT_PROXY_SCHEMAS', config.get('BOT_PROXY_SCHEMAS'))
BOT_PROXY_HOST = environ.get('BOT_PROXY_HOST', config.get('BOT_PROXY_HOST'))
BOT_PROXY_PORT = int(environ.get('BOT_PROXY_PORT', config.get('BOT_PROXY_PORT', '0')))
RCLONE_REMOTES = environ.get('RCLONE_REMOTES', config.get('RCLONE_REMOTES', '')).split(',')
RCLONE_115_COOKIE = environ.get('RCLONE_115_COOKIE', config.get('RCLONE_115_COOKIE', ''))
MONGO_HOST = environ.get('MONGO_HOST', config.get('MONGO_HOST'))
MONGO_PORT = int(environ.get('MONGO_PORT', config.get('MONGO_PORT', '27017')))
MONGO_USERNAME = environ.get('MONGO_USERNAME', config.get('MONGO_USERNAME'))
MONGO_PASSWORD = environ.get('MONGO_PASSWORD', config.get('MONGO_PASSWORD'))
MONGO_DATABASE_NAME = environ.get('MONGO_DATABASE_NAME', config.get('MONGO_DATABASE_NAME'))
NODE_ENV = environ.get('NODE_ENV', config.get('NODE_ENV', 'PRODUCTION'))

# 磁盘监控配置
_disk_auto_start = environ.get('DISK_MONITOR_AUTO_START', config.get('DISK_MONITOR_AUTO_START', 'true'))
DISK_MONITOR_AUTO_START = str(_disk_auto_start).lower() == 'true'

DISK_ALERT_THRESHOLD = int(environ.get('DISK_ALERT_THRESHOLD', config.get('DISK_ALERT_THRESHOLD', '10')))

_disk_alert_enabled = environ.get('DISK_ALERT_ENABLED', config.get('DISK_ALERT_ENABLED', 'true'))
DISK_ALERT_ENABLED = str(_disk_alert_enabled).lower() == 'true'
