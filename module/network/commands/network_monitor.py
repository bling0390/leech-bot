"""
网络监控命令处理器
提供网络状态查询和监控功能
"""

import asyncio
import prettytable as pt
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from loguru import logger
from tool.utils import is_admin
from module.network.services.network_monitor import NetworkMonitorService
from module.network.utils.format_utils import format_bandwidth, format_data_size, format_packet_count, format_uptime
from module.i18n.services.i18n_manager import I18nManager

# 初始化国际化管理器
i18n_manager = I18nManager()


# 全局监控服务实例
network_service = None


@Client.on_message(filters.command('network') & filters.private & is_admin)
async def network_command_handler(client: Client, message: Message):
    """网络管理主命令处理器"""
    try:
        import argparse
        user_lang = await i18n_manager.get_user_language(message.from_user.id)
        parser = argparse.ArgumentParser(description=i18n_manager.translate('network.monitor.main_command_desc', user_lang))
        parser.add_argument('subcommand', metavar='subcommand', type=str, nargs='?',
                          help=i18n_manager.translate('network.monitor.subcommand_help', user_lang))
        parser.add_argument('args', metavar='args', type=str, nargs='*',
                          help=i18n_manager.translate('network.monitor.args_help', user_lang))
        
        # 如果没有参数，显示帮助信息
        if len(message.command) == 1:
            await show_network_help(message)
            return
            
        args = parser.parse_args(message.command[1:])
        
        # 路由到相应的子命令处理器
        if args.subcommand == 'status':
            await handle_network_status(client, message)
        elif args.subcommand == 'interfaces':
            await handle_network_interfaces(client, message)
        elif args.subcommand == 'connections':
            await handle_network_connections(client, message)
        elif args.subcommand == 'start':
            await start_network_monitor(client, message)
        elif args.subcommand == 'stop':
            await stop_network_monitor(client, message)
        elif args.subcommand == 'reset':
            await reset_network_stats(client, message)
        else:
            await show_network_help(message)
            
    except (Exception, SystemExit):
        await show_network_help(message)


def create_network_help_buttons(user_lang: str = 'zh_CN'):
    """创建网络管理快捷按钮"""
    buttons = [
        [
            InlineKeyboardButton(i18n_manager.translate('network.buttons.status', user_lang), callback_data="network_cmd_status"),
            InlineKeyboardButton(i18n_manager.translate('network.buttons.interfaces', user_lang), callback_data="network_cmd_interfaces")
        ],
        [
            InlineKeyboardButton(i18n_manager.translate('network.buttons.connections', user_lang), callback_data="network_cmd_connections"),
            InlineKeyboardButton(i18n_manager.translate('network.buttons.start', user_lang), callback_data="network_cmd_start")
        ],
        [
            InlineKeyboardButton(i18n_manager.translate('network.buttons.stop', user_lang), callback_data="network_cmd_stop"),
            InlineKeyboardButton(i18n_manager.translate('network.buttons.reset', user_lang), callback_data="network_cmd_reset")
        ],
        [
            InlineKeyboardButton(i18n_manager.translate('network.buttons.close', user_lang), callback_data="network_cmd_close")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def show_network_help(message: Message):
    """显示网络管理命令帮助和交互按钮"""
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    help_text = i18n_manager.translate('network.commands.help', user_lang)
    
    await message.reply_text(
        help_text, 
        parse_mode=ParseMode.HTML,
        reply_markup=create_network_help_buttons(user_lang)
    )


async def handle_network_status(client: Client, message: Message):
    """处理网络状态查询子命令"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if not network_service:
        network_service = NetworkMonitorService()
    
    # 获取网络统计
    network_stats = network_service.get_network_stats()
    
    # 创建网络状态表格
    status_table = pt.PrettyTable([
        i18n_manager.translate('network.table.status_item', user_lang), 
        i18n_manager.translate('network.table.current_value', user_lang)
    ])
    status_table.border = True
    status_table.preserve_internal_border = False
    status_table.header = False
    status_table._max_width = {
        i18n_manager.translate('network.table.status_item', user_lang): 15, 
        i18n_manager.translate('network.table.current_value', user_lang): 12
    }
    status_table.valign[i18n_manager.translate('network.table.status_item', user_lang)] = 'm'
    status_table.valign[i18n_manager.translate('network.table.current_value', user_lang)] = 'm'
    
    if 'error' not in network_stats:
        status_table.add_row([
            i18n_manager.translate('network.data.upload_speed', user_lang), 
            format_bandwidth(network_stats.get('upload_speed', 0))
        ], divider=True)
        status_table.add_row([
            i18n_manager.translate('network.data.download_speed', user_lang), 
            format_bandwidth(network_stats.get('download_speed', 0))
        ], divider=True)
        status_table.add_row([
            i18n_manager.translate('network.data.total_bandwidth', user_lang), 
            format_bandwidth(network_stats.get('total_speed', 0))
        ], divider=True)
        status_table.add_row([
            i18n_manager.translate('network.data.total_sent', user_lang), 
            format_data_size(network_stats.get('bytes_sent', 0))
        ], divider=True)
        status_table.add_row([
            i18n_manager.translate('network.data.total_received', user_lang), 
            format_data_size(network_stats.get('bytes_recv', 0))
        ], divider=True)
    else:
        status_table.add_row([
            i18n_manager.translate('network.data.error', user_lang), 
            network_stats['error'][:10] + '..'
        ], divider=True)
    
    # 创建带宽统计表格
    bandwidth_avg = network_service.get_bandwidth_average(5)
    bandwidth_peak = network_service.get_peak_bandwidth()
    
    bandwidth_table = pt.PrettyTable([
        i18n_manager.translate('network.table.stats_type', user_lang), 
        i18n_manager.translate('network.table.upload', user_lang), 
        i18n_manager.translate('network.table.download', user_lang)
    ])
    bandwidth_table.border = True
    bandwidth_table.preserve_internal_border = False
    bandwidth_table.header = True
    bandwidth_table._max_width = {
        i18n_manager.translate('network.table.stats_type', user_lang): 10, 
        i18n_manager.translate('network.table.upload', user_lang): 8, 
        i18n_manager.translate('network.table.download', user_lang): 8
    }
    bandwidth_table.align[i18n_manager.translate('network.table.stats_type', user_lang)] = 'l'
    bandwidth_table.align[i18n_manager.translate('network.table.upload', user_lang)] = 'r'
    bandwidth_table.align[i18n_manager.translate('network.table.download', user_lang)] = 'r'
    
    bandwidth_table.add_row([
        i18n_manager.translate('network.data.five_min_avg', user_lang),
        format_bandwidth(bandwidth_avg.get('avg_upload', 0)),
        format_bandwidth(bandwidth_avg.get('avg_download', 0))
    ])
    
    bandwidth_table.add_row([
        i18n_manager.translate('network.data.peak_bandwidth', user_lang),
        format_bandwidth(bandwidth_peak.get('peak_upload', 0)),
        format_bandwidth(bandwidth_peak.get('peak_download', 0))
    ])
    
    # 创建监控状态表格
    monitor_table = pt.PrettyTable([
        i18n_manager.translate('network.table.monitor_item', user_lang), 
        i18n_manager.translate('network.table.status', user_lang)
    ])
    monitor_table.border = True
    monitor_table.preserve_internal_border = False
    monitor_table.header = False
    monitor_table._max_width = {
        i18n_manager.translate('network.table.monitor_item', user_lang): 15, 
        i18n_manager.translate('network.table.status', user_lang): 12
    }
    monitor_table.valign[i18n_manager.translate('network.table.monitor_item', user_lang)] = 'm'
    monitor_table.valign[i18n_manager.translate('network.table.status', user_lang)] = 'm'
    
    if network_service and network_service.running:
        monitor_status = i18n_manager.translate('network.data.service_running', user_lang)
    else:
        monitor_status = i18n_manager.translate('network.data.service_stopped', user_lang)
    monitor_table.add_row([
        i18n_manager.translate('network.data.monitor_service', user_lang), 
        monitor_status
    ], divider=True)
    monitor_table.add_row([
        i18n_manager.translate('network.data.data_points', user_lang), 
        str(len(network_service.bandwidth_history))
    ], divider=True)
    
    status_text = (
        f"<b>{i18n_manager.translate('network.status.title', user_lang)}</b>\n\n"
        f"<b>{i18n_manager.translate('network.status.realtime_status', user_lang)}</b>\n"
        f"<pre>{status_table.get_string()}</pre>\n\n"
        f"<b>{i18n_manager.translate('network.status.bandwidth_stats', user_lang)}</b>\n"
        f"<pre>{bandwidth_table.get_string()}</pre>\n\n"
        f"<b>{i18n_manager.translate('network.status.monitor_status', user_lang)}</b>\n"
        f"<pre>{monitor_table.get_string()}</pre>"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(status_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


async def handle_network_interfaces(client: Client, message: Message):
    """处理网络接口信息查询"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if not network_service:
        network_service = NetworkMonitorService()
    
    interfaces = network_service.get_network_interfaces()
    
    if not interfaces:
        sent_msg = await message.reply_text(i18n_manager.translate('network.status.get_info_failed', user_lang))
        await asyncio.sleep(5)
        await sent_msg.delete()
        return
    
    # 创建接口信息表格
    interface_table = pt.PrettyTable([
        i18n_manager.translate('network.table.interface_name', user_lang), 
        i18n_manager.translate('network.table.sent_data', user_lang), 
        i18n_manager.translate('network.table.received_data', user_lang)
    ])
    interface_table.border = True
    interface_table.preserve_internal_border = False
    interface_table.header = True
    interface_table._max_width = {
        i18n_manager.translate('network.table.interface_name', user_lang): 10, 
        i18n_manager.translate('network.table.sent_data', user_lang): 10, 
        i18n_manager.translate('network.table.received_data', user_lang): 10
    }
    interface_table.align[i18n_manager.translate('network.table.interface_name', user_lang)] = 'l'
    interface_table.align[i18n_manager.translate('network.table.sent_data', user_lang)] = 'r'
    interface_table.align[i18n_manager.translate('network.table.received_data', user_lang)] = 'r'
    
    for interface in interfaces[:10]:  # 限制显示前10个接口
        stats = network_service.get_network_stats(interface)
        if 'error' not in stats:
            interface_table.add_row([
                interface[:8] + '..' if len(interface) > 8 else interface,
                format_data_size(stats.get('bytes_sent', 0)),
                format_data_size(stats.get('bytes_recv', 0))
            ])
    
    interface_text = (
        f"<b>{i18n_manager.translate('network.interfaces.title', user_lang)}</b>\n\n"
        f"<b>{i18n_manager.translate('network.interfaces.traffic_stats', user_lang)}</b>\n"
        f"<pre>{interface_table.get_string()}</pre>\n\n"
        f"{i18n_manager.translate('network.interfaces.display_note', user_lang, count=min(len(interfaces), 10))}"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(interface_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


async def handle_network_connections(client: Client, message: Message):
    """处理网络连接统计查询"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if not network_service:
        network_service = NetworkMonitorService()
    
    conn_stats = network_service.get_connection_stats()
    
    if 'error' in conn_stats:
        # 发送消息并在5秒后自动删除
        sent_msg = await message.reply_text(
            i18n_manager.translate('network.status.get_connections_failed', user_lang, error=conn_stats['error'])
        )
        await asyncio.sleep(5)
        await sent_msg.delete()
        return
    
    # 创建连接统计表格
    conn_table = pt.PrettyTable([
        i18n_manager.translate('network.table.connection_type', user_lang), 
        i18n_manager.translate('network.table.count', user_lang)
    ])
    conn_table.border = True
    conn_table.preserve_internal_border = False
    conn_table.header = False
    conn_table._max_width = {
        i18n_manager.translate('network.table.connection_type', user_lang): 15, 
        i18n_manager.translate('network.table.count', user_lang): 12
    }
    conn_table.valign[i18n_manager.translate('network.table.connection_type', user_lang)] = 'm'
    conn_table.valign[i18n_manager.translate('network.table.count', user_lang)] = 'r'
    
    conn_table.add_row([
        i18n_manager.translate('network.connections.total_connections', user_lang), 
        str(conn_stats.get('total_connections', 0))
    ], divider=True)
    conn_table.add_row([
        i18n_manager.translate('network.connections.tcp_connections', user_lang), 
        str(conn_stats.get('tcp_connections', 0))
    ], divider=True)
    conn_table.add_row([
        i18n_manager.translate('network.connections.udp_connections', user_lang), 
        str(conn_stats.get('udp_connections', 0))
    ], divider=True)
    conn_table.add_row([
        i18n_manager.translate('network.connections.listening_ports', user_lang), 
        str(conn_stats.get('listening_ports', 0))
    ], divider=True)
    conn_table.add_row([
        i18n_manager.translate('network.connections.established_connections', user_lang), 
        str(conn_stats.get('established_connections', 0))
    ], divider=True)
    conn_table.add_row([
        i18n_manager.translate('network.connections.time_wait_connections', user_lang), 
        str(conn_stats.get('time_wait_connections', 0))
    ], divider=True)
    
    conn_text = (
        f"<b>{i18n_manager.translate('network.connections.title', user_lang)}</b>\n\n"
        f"<b>{i18n_manager.translate('network.connections.stats_title', user_lang)}</b>\n"
        f"<pre>{conn_table.get_string()}</pre>"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(conn_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


async def start_network_monitor(client: Client, message: Message):
    """启动网络监控"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if network_service and network_service.running:
        # 创建已运行状态表格
        running_table = pt.PrettyTable([
            i18n_manager.translate('network.table.status_info', user_lang), 
            i18n_manager.translate('network.table.current_status', user_lang)
        ])
        running_table.border = True
        running_table.preserve_internal_border = False
        running_table.header = False
        running_table._max_width = {
            i18n_manager.translate('network.table.status_info', user_lang): 15, 
            i18n_manager.translate('network.table.current_status', user_lang): 12
        }
        running_table.valign[i18n_manager.translate('network.table.status_info', user_lang)] = 'm'
        running_table.valign[i18n_manager.translate('network.table.current_status', user_lang)] = 'm'
        
        running_table.add_row([
            i18n_manager.translate('network.data.monitor_service', user_lang), 
            i18n_manager.translate('network.data.already_running_status', user_lang)
        ], divider=True)
        running_table.add_row([
            i18n_manager.translate('network.data.operation_result', user_lang), 
            i18n_manager.translate('network.data.already_running_text', user_lang)
        ], divider=True)
        
        running_text = (
            f"<b>{i18n_manager.translate('network.monitor.already_running', user_lang)}</b>\n\n"
            f"<pre>{running_table.get_string()}</pre>"
        )
        
        # 发送消息并在5秒后自动删除
        sent_msg = await message.reply_text(running_text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(5)
        await sent_msg.delete()
        return
    
    network_service = NetworkMonitorService()
    
    # 在后台启动监控
    asyncio.create_task(network_service.start_monitoring())
    
    # 创建网络监控启动信息表格
    start_table = pt.PrettyTable([
        i18n_manager.translate('network.table.config_item', user_lang), 
        i18n_manager.translate('network.table.setting_value', user_lang)
    ])
    start_table.border = True
    start_table.preserve_internal_border = False
    start_table.header = False
    start_table._max_width = {
        i18n_manager.translate('network.table.config_item', user_lang): 15, 
        i18n_manager.translate('network.table.setting_value', user_lang): 12
    }
    start_table.valign[i18n_manager.translate('network.table.config_item', user_lang)] = 'm'
    start_table.valign[i18n_manager.translate('network.table.setting_value', user_lang)] = 'm'
    
    start_table.add_row([
        i18n_manager.translate('network.control.check_interval', user_lang), 
        i18n_manager.translate('network.control.seconds', user_lang, seconds=network_service.check_interval)
    ], divider=True)
    start_table.add_row([
        i18n_manager.translate('network.control.history_records', user_lang), 
        i18n_manager.translate('network.control.data_points_unit', user_lang, size=network_service.max_history_size)
    ], divider=True)
    start_table.add_row([
        i18n_manager.translate('network.control.initial_points', user_lang), 
        '0'
    ], divider=True)
    start_table.add_row([
        i18n_manager.translate('network.control.service_status', user_lang), 
        i18n_manager.translate('network.control.started_status', user_lang)
    ], divider=True)
    
    start_text = (
        f"<b>{i18n_manager.translate('network.control.start_success', user_lang)}</b>\n\n"
        f"<b>{i18n_manager.translate('network.control.config_info', user_lang)}</b>\n"
        f"<pre>{start_table.get_string()}</pre>"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(start_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


async def stop_network_monitor(client: Client, message: Message):
    """停止网络监控"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if not network_service or not network_service.running:
        # 发送消息并在5秒后自动删除
        sent_msg = await message.reply_text(i18n_manager.translate('network.monitor.not_running', user_lang))
        await asyncio.sleep(5)
        await sent_msg.delete()
        return
    
    network_service.stop_monitoring()
    
    # 创建停止状态表格
    stop_table = pt.PrettyTable([
        i18n_manager.translate('network.table.status_info', user_lang), 
        i18n_manager.translate('network.table.result', user_lang)
    ])
    stop_table.border = True
    stop_table.preserve_internal_border = False
    stop_table.header = False
    stop_table._max_width = {
        i18n_manager.translate('network.table.status_info', user_lang): 15, 
        i18n_manager.translate('network.table.result', user_lang): 12
    }
    stop_table.valign[i18n_manager.translate('network.table.status_info', user_lang)] = 'm'
    stop_table.valign[i18n_manager.translate('network.table.result', user_lang)] = 'm'
    
    stop_table.add_row([
        i18n_manager.translate('network.data.monitor_service', user_lang), 
        i18n_manager.translate('network.data.service_stopped', user_lang)
    ], divider=True)
    stop_table.add_row([
        i18n_manager.translate('network.control.preserved_data', user_lang), 
        i18n_manager.translate('network.control.data_points_unit', user_lang, size=len(network_service.bandwidth_history))
    ], divider=True)
    
    stop_text = (
        f"<b>{i18n_manager.translate('network.control.stop_success', user_lang)}</b>\n\n"
        f"<pre>{stop_table.get_string()}</pre>"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(stop_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


async def reset_network_stats(client: Client, message: Message):
    """重置网络统计"""
    global network_service
    
    user_lang = await i18n_manager.get_user_language(message.from_user.id)
    
    if not network_service:
        # 发送消息并在5秒后自动删除
        sent_msg = await message.reply_text(i18n_manager.translate('network.monitor.service_not_initialized', user_lang))
        await asyncio.sleep(5)
        await sent_msg.delete()
        return
    
    old_data_points = len(network_service.bandwidth_history)
    network_service.reset_history()
    
    # 创建重置结果表格
    reset_table = pt.PrettyTable([
        i18n_manager.translate('network.table.reset_item', user_lang), 
        i18n_manager.translate('network.table.result', user_lang)
    ])
    reset_table.border = True
    reset_table.preserve_internal_border = False
    reset_table.header = False
    reset_table._max_width = {
        i18n_manager.translate('network.table.reset_item', user_lang): 15, 
        i18n_manager.translate('network.table.result', user_lang): 12
    }
    reset_table.valign[i18n_manager.translate('network.table.reset_item', user_lang)] = 'm'
    reset_table.valign[i18n_manager.translate('network.table.result', user_lang)] = 'm'
    
    reset_table.add_row([
        i18n_manager.translate('network.control.cleaned_data', user_lang), 
        i18n_manager.translate('network.control.data_points_unit', user_lang, size=old_data_points)
    ], divider=True)
    reset_table.add_row([
        i18n_manager.translate('network.control.reset_status', user_lang), 
        i18n_manager.translate('network.control.success_status', user_lang)
    ], divider=True)
    reset_table.add_row([
        i18n_manager.translate('network.control.current_data', user_lang), 
        i18n_manager.translate('network.control.zero_points', user_lang)
    ], divider=True)
    
    reset_text = (
        f"<b>{i18n_manager.translate('network.control.reset_success', user_lang)}</b>\n\n"
        f"<pre>{reset_table.get_string()}</pre>"
    )
    
    # 发送消息并在5秒后自动删除
    sent_msg = await message.reply_text(reset_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(5)
    await sent_msg.delete()


@Client.on_callback_query(filters.regex(r'^network_cmd_'))
async def handle_network_command_callback(client: Client, callback_query):
    """处理网络管理命令快捷按钮回调"""
    command = callback_query.data.replace('network_cmd_', '')
    
    # 删除原消息并执行对应的网络命令
    await callback_query.message.delete()
    
    # 创建模拟的消息对象来触发相应的命令处理逻辑
    if command == 'status':
        await handle_network_status(client, callback_query.message)
    elif command == 'interfaces':
        await handle_network_interfaces(client, callback_query.message)
    elif command == 'connections':
        await handle_network_connections(client, callback_query.message)
    elif command == 'start':
        await start_network_monitor(client, callback_query.message)
    elif command == 'stop':
        await stop_network_monitor(client, callback_query.message)
    elif command == 'reset':
        await reset_network_stats(client, callback_query.message)
    elif command == 'close':
        # 消息已删除，不需要额外操作
        pass
    
    # 回答回调查询
    await callback_query.answer()


# 保留原有的独立命令以维持向后兼容性
@Client.on_message(filters.command('network_status') & filters.private & is_admin)
async def network_status_legacy(client: Client, message: Message):
    """网络状态查询(兼容性保留)"""
    await handle_network_status(client, message)