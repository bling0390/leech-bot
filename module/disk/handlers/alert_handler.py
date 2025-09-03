from typing import Dict, Optional
from datetime import datetime
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.enums import ParseMode
from loguru import logger
from tool.telegram_client import get_telegram_client
from config.config import TELEGRAM_ADMIN_ID
from module.disk.models.disk_alert import DiskAlert
from module.disk.services.cleanup_service import CleanupService
from module.disk.services.celery_adjustment import CeleryAdjustmentService
from module.disk.services.disk_monitor import DiskMonitorService
from module.disk.utils.format_utils import format_file_count, format_directory_count, format_storage_size
from module.i18n import get_i18n_manager


class DiskAlertHandler:
    """磁盘告警处理器"""
    
    def __init__(self, bot: Client = None):
        """初始化告警处理器
        
        Args:
            bot: Telegram客户端
        """
        self.bot = bot or get_telegram_client()
        self.i18n = get_i18n_manager()
        self.cleanup_service = CleanupService()
        self.celery_service = CeleryAdjustmentService()
        self.monitor_service = DiskMonitorService()
        
    async def send_alert_with_buttons(self, chat_id: int, alert_info: Dict, user_id: int = None) -> Optional[Message]:
        """发送带交互按钮的告警消息
        
        Args:
            chat_id: 聊天ID
            alert_info: 告警信息
            user_id: 用户ID (用于i18n)
            
        Returns:
            发送的消息对象
        """
        try:
            # 如果没有提供user_id，使用chat_id
            if user_id is None:
                user_id = chat_id
                
            # 创建告警记录
            alert_record = DiskAlert(
                timestamp=datetime.now(),
                free_space_gb=alert_info.get('free_space_gb', 0),
                used_percent=alert_info.get('used_percent', 0),
                total_gb=alert_info.get('total_gb', 0),
                used_gb=alert_info.get('used_gb', 0),
                threshold_gb=alert_info.get('threshold_gb', 10),
                location=alert_info.get('location', '/downloads'),
                alert_message=self.monitor_service.format_alert_message(alert_info),
                alert_status='active'
            )
            alert_record.save()
            
            # 获取按钮文本翻译
            clear_btn = await self.i18n.translate_for_user(user_id, 'disk.buttons.clear_directory')
            adjust_btn = await self.i18n.translate_for_user(user_id, 'disk.buttons.adjust_task_frequency')
            details_btn = await self.i18n.translate_for_user(user_id, 'disk.buttons.view_details')
            ignore_btn = await self.i18n.translate_for_user(user_id, 'disk.buttons.ignore_alert')
            
            # 创建内联键盘
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        clear_btn,
                        callback_data=f"disk_cleanup_{alert_record.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        adjust_btn,
                        callback_data=f"disk_adjust_celery_{alert_record.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        details_btn,
                        callback_data=f"disk_info_{alert_record.id}"
                    ),
                    InlineKeyboardButton(
                        ignore_btn,
                        callback_data=f"disk_ignore_{alert_record.id}"
                    )
                ]
            ])
            
            # 发送消息
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=alert_record.alert_message,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
            success_msg = self.i18n.translate('disk.alerts.alert_sent', chat_id=chat_id)
            logger.info(success_msg)
            return message
            
        except Exception as e:
            error_msg = self.i18n.translate('disk.alerts.send_failed', error=str(e))
            logger.error(error_msg)
            return None
            
    async def handle_callback(self, callback_query: CallbackQuery):
        """处理回调查询
        
        Args:
            callback_query: 回调查询对象
        """
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            # 解析回调数据
            parts = data.split('_')
            if len(parts) < 3 or parts[0] != 'disk':
                return
                
            action = parts[1]
            alert_id = '_'.join(parts[2:]) if len(parts) > 2 else None
            
            # 获取告警记录
            alert = None
            if alert_id:
                try:
                    alert = DiskAlert.objects.get(id=alert_id)
                except:
                    await callback_query.answer("告警记录不存在", show_alert=True)
                    return
                    
            # 处理不同的动作
            if action == 'cleanup':
                await self._handle_cleanup(callback_query, alert, user_id)
            elif action == 'adjust':
                await self._handle_adjust_celery(callback_query, alert, user_id)
            elif action == 'info':
                await self._handle_show_info(callback_query, alert)
            elif action == 'ignore':
                await self._handle_ignore(callback_query, alert, user_id)
            else:
                await callback_query.answer("未知操作", show_alert=True)
                
        except Exception as e:
            logger.error(f"处理回调失败: {e}")
            await callback_query.answer(f"处理失败: {str(e)}", show_alert=True)
            
    async def _handle_cleanup(self, callback_query: CallbackQuery, alert: DiskAlert, user_id: int):
        """处理清理下载目录
        
        Args:
            callback_query: 回调查询
            alert: 告警记录
            user_id: 用户ID
        """
        await callback_query.answer("正在清理下载目录...")
        
        # 执行清理
        result = await self.cleanup_service.clean_download_directory()
        
        if result['success']:
            # 更新告警状态
            alert.resolve(
                action='cleaned_downloads',
                user_id=user_id,
                notes=f"释放空间: {result.get('freed_space_gb', 0)}GB"
            )
            if result.get('freed_space_gb'):
                alert.freed_space_gb = result['freed_space_gb']
                alert.save()
                
            # 重置告警冷却
            self.monitor_service.reset_alert_cooldown()
            
            # 更新消息
            new_text = self._format_resolution_message(
                "清空下载目录",
                callback_query.from_user.first_name,
                f"释放空间: {format_storage_size(result.get('freed_space_gb', 0))}"
            )
            
            await callback_query.message.edit_text(
                text=new_text,
                parse_mode=ParseMode.HTML
            )
            
            await callback_query.answer(
                f"✅ 清理完成，释放 {result.get('freed_space_gb', 0)}GB 空间",
                show_alert=True
            )
        else:
            await callback_query.answer(
                f"❌ 清理失败: {result.get('message', '未知错误')}",
                show_alert=True
            )
            
    async def _handle_adjust_celery(self, callback_query: CallbackQuery, alert: DiskAlert, user_id: int):
        """处理调整Celery频率
        
        Args:
            callback_query: 回调查询
            alert: 告警记录
            user_id: 用户ID
        """
        await callback_query.answer("正在调整任务频率...")
        
        # 调整频率
        result = self.celery_service.adjust_worker_frequency('reduce')
        
        if result['success']:
            # 更新告警状态
            alert.resolve(
                action='adjusted_celery',
                user_id=user_id,
                notes=result.get('message', '')
            )
            alert.celery_adjustment = str(result.get('details', {}))
            alert.save()
            
            # 重置告警冷却
            self.monitor_service.reset_alert_cooldown()
            
            # 更新消息  
            new_text = self._format_resolution_message(
                "降低任务频率",
                callback_query.from_user.first_name,
                f"详情: {result.get('message', '')}"
            )
            
            # 添加恢复按钮
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🔄 恢复任务频率",
                    callback_data=f"disk_restore_celery_{alert.id}"
                )
            ]])
            
            await callback_query.message.edit_text(
                text=new_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
            await callback_query.answer(
                "✅ 任务频率已降低",
                show_alert=True
            )
        else:
            await callback_query.answer(
                f"❌ 调整失败: {result.get('message', '未知错误')}",
                show_alert=True
            )
            
    async def _handle_show_info(self, callback_query: CallbackQuery, alert: DiskAlert):
        """显示详细信息
        
        Args:
            callback_query: 回调查询
            alert: 告警记录
        """
        # 获取目录信息
        dir_info = await self.cleanup_service.get_directory_info()
        
        info_text = (
            f"📊 <b>磁盘详细信息</b>\n\n"
            f"📍 位置: {alert.location}\n"
            f"💾 剩余空间: {format_storage_size(alert.free_space_gb)}\n"
            f"📈 使用率: {alert.used_percent}%\n"
            f"💿 总空间: {format_storage_size(alert.total_gb)}\n"
            f"📂 已使用: {format_storage_size(alert.used_gb)}\n\n"
            f"<b>下载目录信息:</b>\n"
            f"📁 {format_file_count(dir_info.get('file_count', 0))}\n"
            f"📂 {format_directory_count(dir_info.get('dir_count', 0))}\n"
            f"💾 占用空间: {format_storage_size(dir_info.get('total_size_gb', 0))}\n"
        )
        
        if dir_info.get('file_types'):
            info_text += "\n<b>文件类型分布:</b>\n"
            for ext, count in sorted(dir_info['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                info_text += f"  {ext}: {count} 个\n"
                
        await callback_query.answer(info_text[:200], show_alert=True)
        
    async def _handle_ignore(self, callback_query: CallbackQuery, alert: DiskAlert, user_id: int):
        """忽略告警
        
        Args:
            callback_query: 回调查询
            alert: 告警记录
            user_id: 用户ID
        """
        # 更新告警状态
        alert.alert_status = 'ignored'
        alert.action_taken = 'ignored'
        alert.resolved_at = datetime.now()
        alert.resolved_by = user_id
        alert.save()
        
        # 更新消息
        new_text = (
            f"⚠️ <b>告警已忽略</b>\n\n"
            f"👤 操作人: {callback_query.from_user.first_name}\n"
            f"🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await callback_query.message.edit_text(
            text=new_text,
            parse_mode=ParseMode.HTML
        )
        
        await callback_query.answer("告警已忽略", show_alert=False)
        
    async def _handle_restore_celery(self, callback_query: CallbackQuery):
        """恢复Celery频率
        
        Args:
            callback_query: 回调查询
        """
        await callback_query.answer("正在恢复任务频率...")
        
        # 恢复频率
        result = self.celery_service.adjust_worker_frequency('restore')
        
        if result['success']:
            # 更新消息
            new_text = (
                f"✅ <b>任务频率已恢复</b>\n\n"
                f"👤 操作人: {callback_query.from_user.first_name}\n"
                f"🕐 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await callback_query.message.edit_text(
                text=new_text,
                parse_mode=ParseMode.HTML
            )
            
            await callback_query.answer(
                "✅ 任务频率已恢复",
                show_alert=True
            )
        else:
            await callback_query.answer(
                f"❌ 恢复失败: {result.get('message', '未知错误')}",
                show_alert=True
            )
            
    def _format_resolution_message(self, action: str, user_name: str, details: str = "") -> str:
        """格式化告警解决消息
        
        Args:
            action: 执行的操作
            user_name: 操作人姓名
            details: 详细信息
            
        Returns:
            格式化的消息
        """
        message = (
            f"✅ <b>告警已处理</b>\n\n"
            f"📍 操作: {action}\n"
        )
        
        if details:
            message += f"💾 {details}\n"
            
        message += (
            f"👤 处理人: {user_name}\n"
            f"🕐 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return message