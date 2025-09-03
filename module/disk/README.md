# 磁盘监控模块

## 功能概述

磁盘监控模块提供了实时监控磁盘空间、自动告警和处理的完整解决方案。当磁盘空间不足时，通过Telegram Bot发送告警通知，并提供交互式按钮进行处理。

## 主要功能

1. **实时磁盘监控**
   - 定期检查磁盘剩余空间
   - 可配置的告警阈值
   - 告警冷却机制避免频繁通知

2. **交互式告警处理**
   - 清空下载目录
   - 调整Celery Worker执行频率
   - 查看详细磁盘信息
   - 忽略告警

3. **数据持久化**
   - 所有告警记录保存到MongoDB
   - 支持查询历史告警
   - 记录处理动作和结果

## 使用方法

### Bot命令

- `/disk_start` - 启动磁盘监控服务
- `/disk_stop` - 停止磁盘监控服务
- `/disk_status` - 查看当前磁盘状态
- `/disk_clean` - 手动清空下载目录
- `/disk_clean_old [天数]` - 清理指定天数前的旧文件
- `/disk_alerts` - 查看最近24小时的告警记录
- `/disk_test_alert` - 发送测试告警（用于测试）

### 环境变量配置

在 `config.yaml` 或环境变量中配置：

```yaml
DISK_ALERT_THRESHOLD: 10  # 磁盘剩余空间告警阈值（GB）
DISK_ALERT_ENABLED: true  # 是否启用磁盘监控
BOT_DOWNLOAD_LOCATION: "/downloads"  # 下载目录路径
```

### 告警处理流程

1. 系统检测到磁盘空间不足（低于阈值）
2. 发送告警消息到管理员，包含交互按钮
3. 管理员选择处理方式：
   - 清空下载目录：删除所有下载文件
   - 调整任务频率：降低Worker数量减少磁盘压力
   - 查看详情：显示详细磁盘和文件信息
   - 忽略：忽略本次告警

4. 系统记录处理结果到MongoDB

## 技术架构

### 模块结构

```
module/disk/
├── __init__.py
├── services/          # 核心服务
│   ├── disk_monitor.py      # 磁盘监控服务
│   ├── cleanup_service.py   # 清理服务
│   └── celery_adjustment.py # Celery调整服务
├── handlers/          # 处理器
│   └── alert_handler.py     # 告警处理器
├── models/            # 数据模型
│   └── disk_alert.py        # MongoDB模型
├── commands/          # Bot命令
│   └── disk_monitor.py      # 命令处理
└── utils/            # 工具函数
```

### 核心组件

1. **DiskMonitorService**
   - 负责定期检查磁盘空间
   - 管理告警冷却时间
   - 触发告警通知

2. **CleanupService**
   - 清理下载目录
   - 删除旧文件
   - 计算目录大小

3. **CeleryAdjustmentService**
   - 调整Worker执行频率
   - 暂停/恢复Worker
   - 获取Worker状态

4. **DiskAlertHandler**
   - 发送告警消息
   - 处理用户交互
   - 更新告警状态

## 测试

运行单元测试：
```bash
python3 -m pytest tests/unit/test_disk_monitor.py -v
```

## 注意事项

1. 确保Bot有足够的权限访问和操作下载目录
2. MongoDB必须正确配置和运行
3. 告警阈值应根据实际磁盘大小合理设置
4. 清理操作会永久删除文件，请谨慎使用