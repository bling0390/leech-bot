import asyncio
import prettytable as pt
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from loguru import logger
from tool.utils import is_admin
from config.config import TELEGRAM_ADMIN_ID, BOT_DOWNLOAD_LOCATION
from module.disk.services.disk_monitor import DiskMonitorService
from module.disk.services.cleanup_service import CleanupService
from module.disk.handlers.alert_handler import DiskAlertHandler
from module.disk.models.disk_alert import DiskAlert
from module.disk.utils.format_utils import format_file_count, format_directory_count, format_storage_size
from module.disk.auto_start import get_global_monitor_service, is_monitor_service_running
from module.i18n import get_i18n_manager


# 全局监控服务实例
monitor_service = None
alert_handler = None


@Client.on_message(filters.command('disk_start') & filters.private & is_admin)
async def start_disk_monitor(client: Client, message: Message):
    """启动磁盘监控"""
    global monitor_service, alert_handler
    
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    # 检查是否已有监控服务在运行
    global_service = get_global_monitor_service()
    current_service = global_service or monitor_service
    
    if current_service and current_service.running:
        # 获取翻译文本
        status_header = await i18n.translate_for_user(user_id, 'disk.status.service_running')
        already_running = await i18n.translate_for_user(user_id, 'disk.monitor.already_running')
        
        # 获取表格标题翻译
        status_col = await i18n.translate_for_user(user_id, 'disk.table.status')
        value_col = await i18n.translate_for_user(user_id, 'disk.table.value')
        service_label = await i18n.translate_for_user(user_id, 'disk.status.service_running')
        
        # 创建已运行状态表格 - 使用翻译内容
        running_table = pt.PrettyTable([status_col, value_col])
        running_table.border = True
        running_table.preserve_internal_border = False
        running_table.header = False
        running_table._max_width = {status_col: 15, value_col: 12}
        running_table.valign[status_col] = 'm'
        running_table.valign[value_col] = 'm'
        
        running_table.add_row(['📊 Service', service_label], divider=True)
        running_table.add_row(['⚠️ Result', already_running], divider=True)
        
        status_title = await i18n.translate_for_user(user_id, 'disk.monitor.status')
        running_text = (
            f"⚠️ <b>{status_title}</b>\n\n"
            f"<pre>{running_table.get_string()}</pre>"
        )
        
        await message.reply_text(running_text, parse_mode=ParseMode.HTML)
        return
        
    monitor_service = DiskMonitorService()
    alert_handler = DiskAlertHandler(client)
    
    # 在后台启动监控
    asyncio.create_task(monitor_service.start_monitoring())
    
    # 获取翻译文本
    started_msg = await i18n.translate_for_user(user_id, 'disk.monitor.started')
    location_label = await i18n.translate_for_user(user_id, 'disk.status.location')
    config_info = await i18n.translate_for_user(user_id, 'disk.table.config_table')
    
    # 创建磁盘监控启动信息表格
    start_table = pt.PrettyTable(['Config', 'Value'])
    start_table.border = True
    start_table.preserve_internal_border = False
    start_table.header = False
    start_table._max_width = {'Config': 15, 'Value': 12}
    start_table.valign['Config'] = 'm'
    start_table.valign['Value'] = 'm'
    
    # 处理监控位置显示长度
    location = BOT_DOWNLOAD_LOCATION
    if len(location) > 12:
        location = location[:10] + ".."
    
    start_table.add_row([f'📍 {location_label}', location], divider=True)
    start_table.add_row(['🚨 Threshold', f"{monitor_service.threshold_gb}GB"], divider=True)
    start_table.add_row(['⏱ Interval', f"{monitor_service.check_interval}s"], divider=True)
    start_table.add_row(['📊 Status', '🟢 Started'], divider=True)
    
    start_text = (
        f"✅ <b>{started_msg}</b>\n\n"
        f"<b>{config_info}</b>\n"
        f"<pre>{start_table.get_string()}</pre>"
    )
    
    await message.reply_text(start_text, parse_mode=ParseMode.HTML)
    

@Client.on_message(filters.command('disk_stop') & filters.private & is_admin)
async def stop_disk_monitor(client: Client, message: Message):
    """停止磁盘监控"""
    global monitor_service
    
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    # 检查全局和局部监控服务
    global_service = get_global_monitor_service()
    current_service = global_service or monitor_service
    
    if not current_service or not current_service.running:
        not_running_msg = await i18n.translate_for_user(user_id, 'disk.monitor.not_running')
        await message.reply_text(f"⚠️ {not_running_msg}")
        return
    
    # 停止当前运行的服务
    current_service.stop_monitoring()
    
    # 如果停止的是全局服务，也要从全局状态中清除
    if current_service == global_service:
        from module.disk.auto_start import stop_global_monitor_service
        stop_global_monitor_service()
    
    stopped_msg = await i18n.translate_for_user(user_id, 'disk.monitor.stopped')
    await message.reply_text(f"✅ {stopped_msg}")
    

@Client.on_message(filters.command('disk') & filters.private & is_admin)
async def disk_command_handler(client: Client, message: Message):
    """磁盘管理主命令处理器"""
    try:
        import argparse
        parser = argparse.ArgumentParser(description='磁盘管理命令')
        parser.add_argument('subcommand', metavar='subcommand', type=str, nargs='?',
                          help='子命令: status, start, stop, clean, alerts 等')
        parser.add_argument('args', metavar='args', type=str, nargs='*',
                          help='子命令参数')
        
        # 如果没有参数，显示帮助信息
        if len(message.command) == 1:
            await show_disk_help(message)
            return
            
        args = parser.parse_args(message.command[1:])
        
        # 路由到相应的子命令处理器
        if args.subcommand == 'status':
            await handle_disk_status(client, message)
        elif args.subcommand == 'start':
            await start_disk_monitor(client, message)
        elif args.subcommand == 'stop':
            await stop_disk_monitor(client, message)
        elif args.subcommand == 'clean':
            # 支持可选的天数参数
            if args.args and args.args[0].isdigit():
                # 模拟 /disk clean 7 这样的命令
                temp_message = message
                temp_message.text = f"/disk_clean_old {args.args[0]}"
                temp_message.command = temp_message.text.split()
                await disk_clean_old(client, temp_message)
            else:
                await disk_clean(client, message)
        elif args.subcommand == 'alerts':
            await disk_alerts(client, message)
        else:
            await show_disk_help(message)
            
    except (Exception, SystemExit):
        await show_disk_help(message)


def create_disk_help_buttons():
    """创建磁盘管理快捷按钮"""
    buttons = [
        [
            InlineKeyboardButton("📊 查看状态", callback_data="disk_cmd_status"),
            InlineKeyboardButton("▶️ 启动监控", callback_data="disk_cmd_start")
        ],
        [
            InlineKeyboardButton("⏹️ 停止监控", callback_data="disk_cmd_stop"),
            InlineKeyboardButton("🗏️ 清理目录", callback_data="disk_cmd_clean")
        ],
        [
            InlineKeyboardButton("🚨 查看告警", callback_data="disk_cmd_alerts"),
            InlineKeyboardButton("🗑️ 清理7天", callback_data="disk_cmd_clean_7")
        ],
        [
            InlineKeyboardButton("❌ 关闭菜单", callback_data="disk_cmd_close")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def show_disk_help(message: Message):
    """显示磁盘管理命令帮助和交互按钮"""
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    # 获取翻译后的帮助文本
    help_text = await i18n.translate_for_user(user_id, 'disk.commands.help')
    
    await message.reply_text(
        help_text, 
        parse_mode=ParseMode.HTML,
        reply_markup=create_disk_help_buttons()
    )


async def handle_disk_status(client: Client, message: Message):
    """处理磁盘状态查询子命令"""
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    monitor = DiskMonitorService()
    disk_info = monitor.check_disk_space()
    
    cleanup = CleanupService()
    dir_info = await cleanup.get_directory_info()
    
    # 获取表格标题翻译
    item_col = await i18n.translate_for_user(user_id, 'disk.table.item')
    value_col = await i18n.translate_for_user(user_id, 'disk.table.value')
    
    # 创建磁盘状态表格 - 优化宽度
    disk_table = pt.PrettyTable([item_col, value_col])
    disk_table.border = True
    disk_table.preserve_internal_border = False
    disk_table.header = False
    disk_table._max_width = {item_col: 15, value_col: 12}
    disk_table.valign[item_col] = 'm'
    disk_table.valign[value_col] = 'm'
    
    # 获取磁盘状态标签翻译
    location_label = await i18n.translate_for_user(user_id, 'disk.status.location')
    free_space_label = await i18n.translate_for_user(user_id, 'disk.status.free_space')
    used_percent_label = await i18n.translate_for_user(user_id, 'disk.status.used_percent')
    total_space_label = await i18n.translate_for_user(user_id, 'disk.status.total_space')
    used_space_label = await i18n.translate_for_user(user_id, 'disk.status.used_space')
    
    # 添加磁盘信息
    location = disk_info.get('location', 'N/A')
    if len(location) > 12:
        location = location[:10] + ".."
    disk_table.add_row([location_label, location], divider=True)
    disk_table.add_row([free_space_label, format_storage_size(disk_info.get('free_space_gb', 0))], divider=True)
    disk_table.add_row([used_percent_label, f"{disk_info.get('used_percent', 0):.1f}%"], divider=True)
    disk_table.add_row([total_space_label, format_storage_size(disk_info.get('total_gb', 0))], divider=True)
    disk_table.add_row([used_space_label, format_storage_size(disk_info.get('used_gb', 0))], divider=True)
    
    # 创建目录信息表格 - 优化宽度
    dir_table = pt.PrettyTable([item_col, value_col])
    dir_table.border = True
    dir_table.preserve_internal_border = False
    dir_table.header = False
    dir_table._max_width = {item_col: 15, value_col: 12}
    dir_table.valign[item_col] = 'm'
    dir_table.valign[value_col] = 'm'
    
    # 获取目录信息标签翻译
    file_count_label = await i18n.translate_for_user(user_id, 'disk.status.file_count')
    dir_count_label = await i18n.translate_for_user(user_id, 'disk.status.dir_count')
    storage_label = await i18n.translate_for_user(user_id, 'disk.table.storage_space_item')
    
    dir_table.add_row([file_count_label, format_file_count(dir_info.get('file_count', 0))], divider=True)
    dir_table.add_row([dir_count_label, format_directory_count(dir_info.get('dir_count', 0))], divider=True)
    dir_table.add_row([storage_label, format_storage_size(dir_info.get('total_size_gb', 0))], divider=True)
    
    # 获取状态表格标题翻译
    status_col = await i18n.translate_for_user(user_id, 'disk.table.status')
    current_status_col = await i18n.translate_for_user(user_id, 'disk.table.current_status')
    
    # 创建系统状态表格 - 优化宽度
    status_table = pt.PrettyTable([status_col, current_status_col])
    status_table.border = True
    status_table.preserve_internal_border = False
    status_table.header = False
    status_table._max_width = {status_col: 15, current_status_col: 12}
    status_table.valign[status_col] = 'm'
    status_table.valign[current_status_col] = 'm'
    
    # 获取状态翻译
    if disk_info.get('alert_needed'):
        disk_status = await i18n.translate_for_user(user_id, 'disk.status.space_low')
    else:
        disk_status = await i18n.translate_for_user(user_id, 'disk.status.space_normal')
    
    disk_space_label = await i18n.translate_for_user(user_id, 'disk.status.free_space')
    status_table.add_row([disk_space_label, disk_status], divider=True)
    
    # 添加监控服务状态
    global_service = get_global_monitor_service()
    if global_service and global_service.running:
        monitor_status = await i18n.translate_for_user(user_id, 'disk.status.service_running')
    else:
        monitor_status = await i18n.translate_for_user(user_id, 'disk.status.service_stopped')
    
    monitor_service_label = await i18n.translate_for_user(user_id, 'disk.monitor.status')
    status_table.add_row([monitor_service_label, monitor_status], divider=True)
    
    # 获取状态报告翻译
    status_title = await i18n.translate_for_user(user_id, 'disk.status.title')
    disk_info_label = await i18n.translate_for_user(user_id, 'disk.table.disk_info')
    dir_info_label = await i18n.translate_for_user(user_id, 'disk.table.download_dir_info')
    system_status_label = await i18n.translate_for_user(user_id, 'disk.table.system_status')
    
    status_text = (
        f"{status_title}\n\n"
        f"<b>{disk_info_label}</b>\n"
        f"<pre>{disk_table.get_string()}</pre>\n\n"
        f"<b>{dir_info_label}</b>\n"
        f"<pre>{dir_table.get_string()}</pre>\n\n"
        f"<b>{system_status_label}</b>\n"
        f"<pre>{status_table.get_string()}</pre>"
    )
        
    await message.reply_text(status_text, parse_mode=ParseMode.HTML)


# 保留原有的独立命令以维持向后兼容性
@Client.on_message(filters.command('disk_status') & filters.private & is_admin)
async def disk_status_legacy(client: Client, message: Message):
    """磁盘状态查询(兼容性保留)"""
    await handle_disk_status(client, message)
    

@Client.on_message(filters.command('disk_clean') & filters.private & is_admin)
async def disk_clean(client: Client, message: Message):
    """手动清理磁盘"""
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    # 获取翻译后的清理开始消息
    clean_start_msg = await i18n.translate_for_user(user_id, 'disk.clean.start')
    await message.reply_text(clean_start_msg)
    
    cleanup = CleanupService()
    
    # 获取清理前状态
    before_info = await cleanup.get_directory_info()
    result = await cleanup.clean_download_directory()
    
    if result['success']:
        # 获取清理后状态
        after_info = await cleanup.get_directory_info()
        
        # 获取表格标题翻译
        item_col = await i18n.translate_for_user(user_id, 'disk.table.item')
        before_col = await i18n.translate_for_user(user_id, 'disk.table.clean_before')
        after_col = await i18n.translate_for_user(user_id, 'disk.table.clean_after')
        change_col = await i18n.translate_for_user(user_id, 'disk.table.change')
        
        # 创建清理结果表格 - 优化宽度
        clean_table = pt.PrettyTable([item_col, before_col, after_col, change_col])
        clean_table.border = True
        clean_table.preserve_internal_border = False
        clean_table.header = True
        clean_table._max_width = {item_col: 8, before_col: 9, after_col: 9, change_col: 9}
        clean_table.align[item_col] = 'l'
        clean_table.align[before_col] = 'r'
        clean_table.align[after_col] = 'r'
        clean_table.align[change_col] = 'r'
        
        files_removed = before_info.get('file_count', 0) - after_info.get('file_count', 0)
        space_freed = before_info.get('total_size_gb', 0) - after_info.get('total_size_gb', 0)
        
        # 获取表格行标签翻译
        file_count_label = await i18n.translate_for_user(user_id, 'disk.table.file_count_item')
        storage_space_label = await i18n.translate_for_user(user_id, 'disk.table.storage_space_item')
        
        clean_table.add_row([
            file_count_label,
            str(before_info.get('file_count', 0)),
            str(after_info.get('file_count', 0)),
            f"-{files_removed}"
        ])
        
        clean_table.add_row([
            storage_space_label,
            format_storage_size(before_info.get('total_size_gb', 0)),
            format_storage_size(after_info.get('total_size_gb', 0)),
            f"-{format_storage_size(space_freed)}"
        ])
        
        # 获取翻译后的完成消息
        clean_complete_msg = await i18n.translate_for_user(user_id, 'disk.clean.complete')
        freed_space_label = await i18n.translate_for_user(user_id, 'disk.clean.freed_space')
        
        await message.reply_text(
            f"✅ <b>{clean_complete_msg}</b>\n\n"
            f"<pre>{clean_table.get_string()}</pre>\n\n"
            f"🗑️ {freed_space_label}: <b>{format_storage_size(result.get('freed_space_gb', space_freed))}</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        # 获取翻译后的失败消息
        clean_failed_msg = await i18n.translate_for_user(user_id, 'disk.clean.failed')
        await message.reply_text(clean_failed_msg.format(reason=result.get('message', 'Unknown error')))
        

@Client.on_message(filters.command('disk_clean_old') & filters.private & is_admin)
async def disk_clean_old(client: Client, message: Message):
    """清理旧文件"""
    # 解析天数参数
    parts = message.text.split()
    days = 7  # 默认7天
    if len(parts) > 1:
        try:
            days = int(parts[1])
        except:
            pass
            
    await message.reply_text(f"🔄 正在清理 {days} 天前的文件...")
    
    cleanup = CleanupService()
    
    # 获取清理前状态
    before_info = await cleanup.get_directory_info()
    result = await cleanup.clean_old_files(days)
    
    if result['success']:
        # 获取清理后状态
        after_info = await cleanup.get_directory_info()
        
        # 创建旧文件清理结果表格 - 优化宽度
        old_clean_table = pt.PrettyTable(['清理统计', '数值'])
        old_clean_table.border = True
        old_clean_table.preserve_internal_border = False
        old_clean_table.header = False
        old_clean_table._max_width = {'清理统计': 12, '数值': 12}
        old_clean_table.valign['清理统计'] = 'm'
        old_clean_table.valign['数值'] = 'm'
        
        old_clean_table.add_row(['🗓️ 清理范围', f"{days} 天前文件"], divider=True)
        old_clean_table.add_row(['📁 删除文件', f"{result.get('removed_count', 0)} 个"], divider=True)
        old_clean_table.add_row(['💾 释放空间', format_storage_size(result.get('freed_space_gb', 0))], divider=True)
        
        files_remaining = after_info.get('file_count', 0)
        space_remaining = after_info.get('total_size_gb', 0)
        
        old_clean_table.add_row(['📁 剩余文件', f"{files_remaining} 个"], divider=True)
        old_clean_table.add_row(['💾 剩余空间', format_storage_size(space_remaining)], divider=True)
        
        await message.reply_text(
            f"✅ <b>旧文件清理完成</b>\n\n"
            f"<pre>{old_clean_table.get_string()}</pre>\n\n"
            f"🧹 清理了超过 {days} 天的旧文件",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            f"❌ 清理失败\n"
            f"原因: {result.get('message', '未知错误')}"
        )
        

@Client.on_message(filters.command('disk_alerts') & filters.private & is_admin)
async def disk_alerts(client: Client, message: Message):
    """查看最近的磁盘告警"""
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    # 获取最近24小时的告警
    alerts = DiskAlert.get_recent_alerts(24)
    
    if not alerts:
        no_alerts_msg = await i18n.translate_for_user(user_id, 'disk.alerts.no_alerts')
        await message.reply_text(no_alerts_msg)
        return
    
    # 获取表格列标题翻译
    time_col = await i18n.translate_for_user(user_id, 'disk.alerts.table.time_col')
    status_col = await i18n.translate_for_user(user_id, 'disk.alerts.table.status_col')
    space_usage_col = await i18n.translate_for_user(user_id, 'disk.alerts.table.space_usage_col')
    action_col = await i18n.translate_for_user(user_id, 'disk.alerts.table.action_col')
    
    # 创建告警历史表格 - 优化为适配小窗口
    alert_table = pt.PrettyTable([time_col, status_col, space_usage_col, action_col])
    alert_table.border = True
    alert_table.preserve_internal_border = False
    alert_table.header = True
    alert_table._max_width = {time_col: 10, status_col: 4, space_usage_col: 12, action_col: 10}
    alert_table.align[time_col] = 'l'
    alert_table.align[status_col] = 'c'
    alert_table.align[space_usage_col] = 'r'
    alert_table.align[action_col] = 'l'
    
    for i, alert in enumerate(alerts[:10]):  # 最多显示10条
        status_emoji = {
            'active': '🔴',
            'resolved': '✅',
            'ignored': '⚠️'
        }.get(alert.alert_status, '❓')
        
        # 缩短处理文本
        if alert.action_taken:
            if len(alert.action_taken) > 10:
                action_text = alert.action_taken[:8] + ".."
            else:
                action_text = alert.action_taken
        else:
            action_text = "-"
        
        # 合并空间和使用率信息
        space_usage = f"{alert.free_space_gb:.1f}G/{alert.used_percent:.0f}%"
        
        # 除了最后一行，其他行都添加分隔符
        add_divider = (i < len(alerts[:10]) - 1)
        
        alert_table.add_row([
            alert.timestamp.strftime('%m-%d %H:%M'),
            status_emoji,
            space_usage,
            action_text
        ], divider=add_divider)
    
    # 获取标题和总结文本翻译
    alerts_title = await i18n.translate_for_user(user_id, 'disk.alerts.title')
    summary_text = await i18n.translate_for_user(user_id, 'disk.alerts.summary_text', count=len(alerts[:10]))
    status_legend = await i18n.translate_for_user(user_id, 'disk.alerts.status_legend')
    
    alert_text = (
        f"{alerts_title}\n\n"
        f"<pre>{alert_table.get_string()}</pre>\n\n"
        f"{summary_text}\n"
        f"{status_legend}"
    )
        
    await message.reply_text(alert_text, parse_mode=ParseMode.HTML)
    

@Client.on_message(filters.command('disk_test_alert') & filters.private & is_admin)
async def test_alert(client: Client, message: Message):
    """测试磁盘告警（仅用于测试）"""
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    
    handler = DiskAlertHandler(client)
    
    # 模拟告警信息
    test_alert_info = {
        'free_space_gb': 5,
        'used_percent': 95.0,
        'total_gb': 100,
        'used_gb': 95,
        'threshold_gb': 10,
        'location': BOT_DOWNLOAD_LOCATION
    }
    
    await handler.send_alert_with_buttons(TELEGRAM_ADMIN_ID, test_alert_info)
    test_sent_msg = await i18n.translate_for_user(user_id, 'disk.alerts.send_test_alert')
    await message.reply_text(test_sent_msg)
    

# 处理回调查询
@Client.on_message(filters.command('disk_monitor') & filters.private & is_admin)
async def disk_monitor_toggle(client: Client, message: Message):
    """磁盘监控开关"""
    global monitor_service
    global_service = get_global_monitor_service()
    
    # 优先使用全局服务
    current_service = global_service or monitor_service
    
    if current_service and current_service.running:
        current_service.stop_monitoring()
        
        # 如果停止的是全局服务，也要从全局状态中清除
        if current_service == global_service:
            from module.disk.auto_start import stop_global_monitor_service
            stop_global_monitor_service()
            
        await message.reply_text("✅ 磁盘监控已停止")
    else:
        monitor_service = DiskMonitorService()
        # 在后台启动监控
        asyncio.create_task(monitor_service.start_monitoring())
        await message.reply_text(
            f"✅ 磁盘监控已启动\n"
            f"📍 监控位置: {BOT_DOWNLOAD_LOCATION}\n"
            f"🚨 告警阈值: {monitor_service.threshold_gb}GB"
        )


@Client.on_callback_query(filters.regex(r'^disk_cmd_'))
async def handle_disk_command_callback(client: Client, callback_query):
    """处理磁盘管理命令快捷按钮回调"""
    command = callback_query.data.replace('disk_cmd_', '')
    user_id = callback_query.from_user.id
    
    # 删除原消息并执行对应的磁盘命令
    await callback_query.message.delete()
    
    # 创建模拟的消息对象来触发相应的命令处理逻辑
    if command == 'status':
        await handle_disk_status(client, callback_query.message)
    elif command == 'start':
        await start_disk_monitor(client, callback_query.message)
    elif command == 'stop':
        await stop_disk_monitor(client, callback_query.message)
    elif command == 'clean':
        await disk_clean(client, callback_query.message)
    elif command == 'clean_7':
        # 模拟 /disk clean 7 命令
        temp_message = callback_query.message
        temp_message.text = "/disk_clean_old 7"
        temp_message.command = temp_message.text.split()
        await disk_clean_old(client, temp_message)
    elif command == 'alerts':
        await disk_alerts(client, callback_query.message)
    elif command == 'close':
        # 消息已删除，不需要额外操作
        pass
    
    # 回答回调查询
    await callback_query.answer()


@Client.on_callback_query(filters.regex(r'^disk_'))
async def handle_disk_callback(client: Client, callback_query):
    """处理磁盘相关的回调查询"""
    handler = DiskAlertHandler(client)
    await handler.handle_callback(callback_query)