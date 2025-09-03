# 磁盘监控功能使用指南

## 功能总结

基于SPARC TDD方法成功实现了完整的磁盘告警监控系统，包含以下核心功能：

### 已实现功能

1. **自动磁盘空间监控**
   - 定期检查磁盘剩余空间（默认5分钟）
   - 可配置告警阈值（默认10GB）
   - 告警冷却机制避免频繁通知（默认1小时）

2. **交互式告警处理**
   - 清空下载目录释放空间
   - 调整Celery Worker频率降低磁盘压力
   - 查看详细磁盘使用信息
   - 忽略告警选项

3. **数据持久化**
   - 所有告警记录保存到MongoDB的monitor表
   - 记录处理动作和处理人信息
   - 支持查询历史告警记录

## 快速开始

### 1. 配置环境变量

在 `config.yaml` 中添加：

```yaml
DISK_ALERT_THRESHOLD: 10  # 告警阈值（GB）
DISK_ALERT_ENABLED: true  # 启用磁盘监控
```

或通过环境变量设置：
```bash
export DISK_ALERT_THRESHOLD=10
export DISK_ALERT_ENABLED=true
```

### 2. 启动监控

通过Telegram Bot命令启动监控：
```
/disk_start  # 启动磁盘监控
```

### 3. 管理命令

- `/disk_start` - 启动磁盘监控
- `/disk_stop` - 停止磁盘监控
- `/disk_status` - 查看当前磁盘状态
- `/disk_clean` - 手动清空下载目录
- `/disk_clean_old 7` - 清理7天前的旧文件
- `/disk_alerts` - 查看最近24小时告警
- `/disk_test_alert` - 发送测试告警

## 告警处理流程

1. **自动检测**：系统每5分钟检查一次磁盘空间
2. **触发告警**：剩余空间低于阈值时发送告警到管理员
3. **交互处理**：管理员通过按钮选择处理方式
4. **记录结果**：系统自动记录处理结果到数据库

## 代码复用说明

本实现充分复用了现有项目代码：

- 复用 `tool/mongo_client.py` 进行MongoDB连接
- 复用 `tool/telegram_client.py` 进行Bot消息发送
- 复用 `config/config.py` 配置管理
- 复用 `tool/utils.py` 工具函数
- 复用现有的Pyrogram框架和命令处理机制

## 技术实现亮点

1. **TDD开发**：完整的测试驱动开发流程，先写测试后实现
2. **模块化设计**：清晰的服务层、处理器层、模型层分离
3. **异步处理**：使用asyncio实现非阻塞监控
4. **交互式UI**：利用Telegram内联键盘实现交互
5. **持久化存储**：MongoDB记录所有告警历史

## 项目结构

```
module/disk/
├── services/          # 核心服务
│   ├── disk_monitor.py      # 磁盘监控
│   ├── cleanup_service.py   # 清理服务
│   └── celery_adjustment.py # Worker调整
├── handlers/          # 处理器
│   └── alert_handler.py     # 告警处理
├── models/            # 数据模型
│   └── disk_alert.py        # MongoDB模型
└── commands/          # Bot命令
    └── disk_monitor.py      # 命令处理
```

## 测试覆盖

- ✅ 磁盘空间检查测试
- ✅ 告警触发逻辑测试
- ✅ 清理服务测试
- ✅ Celery调整测试
- ✅ MongoDB持久化测试
- ✅ 集成测试

## 部署注意事项

1. 确保MongoDB服务正常运行
2. 设置合理的告警阈值（建议为总空间的10-20%）
3. 确保Bot有足够权限访问和操作下载目录
4. 建议在生产环境设置更长的检查间隔（如30分钟）

## 后续优化建议

1. 添加多路径监控支持
2. 实现告警升级机制（空间持续减少时增加告警频率）
3. 添加定时清理任务
4. 实现磁盘使用趋势分析
5. 支持自定义告警消息模板

## 总结

通过SPARC TDD方法成功实现了一个完整、可靠、可扩展的磁盘监控系统。代码结构清晰，测试覆盖完整，与现有系统无缝集成。该功能可以有效防止磁盘空间耗尽导致的服务中断。