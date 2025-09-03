import prettytable as pt

from tool.utils import is_admin
from beans.setting import Setting
from pyrogram import filters, Client
from celery.app.control import Control
from constants.setting import SettingKey
from tool.celery_client import celery_client
from module.leech.utils.message import send_message_to_admin
from module.leech.constants.leech_file_tool import LeechFileSyncTool
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from module.leech.utils.button import get_upload_tool_buttons, get_alist_storage_buttons, \
    get_rclone_remote_buttons


class SettingInteractStep:
    SELECT_UPLOAD_TOOL = 'SELECT_UPLOAD_TOOL'
    SELECT_UPLOAD_DESTINATION = 'SELECT_UPLOAD_DESTINATION'
    COMPLETED = 'COMPLETED'


class ButtonCallbackPrefix:
    LEECH_SETTING_UPLOAD_TOOL = 'leech_setting_tool_'
    LEECH_SETTING_UPLOAD_DESTINATION = 'leech_setting_dest_'


current_setting_step = None

setting_steps = {
    SettingInteractStep.SELECT_UPLOAD_TOOL: SettingInteractStep.SELECT_UPLOAD_DESTINATION,
    SettingInteractStep.SELECT_UPLOAD_DESTINATION: SettingInteractStep.COMPLETED
}

alist_storages = []
setting_react_value = {}
current_upload_setting = {}
control = Control(app=celery_client)


async def _next(next_step: str):
    global current_setting_step, setting_react_value, current_upload_setting, alist_storages
    tool = setting_react_value.get('tool', '')
    dest = setting_react_value.get('dest', '')

    if next_step == SettingInteractStep.SELECT_UPLOAD_TOOL:
        tool_buttons: list[list[InlineKeyboardButton]] = \
            get_upload_tool_buttons(ButtonCallbackPrefix.LEECH_SETTING_UPLOAD_TOOL)

        if len(tool_buttons) == 0:
            return await send_message_to_admin('❌ <b>No sync tool available</b>', False)

        return await send_message_to_admin(
            content=f'Current upload tool: {current_upload_setting.get("tool") or "None"}',
            should_auto_delete=False,
            delete_after_seconds=-1,
            reply_markup=InlineKeyboardMarkup(tool_buttons)
        )

    elif next_step == SettingInteractStep.SELECT_UPLOAD_DESTINATION:
        if tool == LeechFileSyncTool.ALIST:
            global alist_storages

            storage_buttons, alist_storages = \
                await get_alist_storage_buttons(ButtonCallbackPrefix.LEECH_SETTING_UPLOAD_DESTINATION)

            return await send_message_to_admin(
                content=f'Current {LeechFileSyncTool.ALIST.lower()} storage: {current_upload_setting.get("dest") or "None"}',
                should_auto_delete=False,
                delete_after_seconds=-1,
                reply_markup=InlineKeyboardMarkup(storage_buttons)
            )

        elif tool == LeechFileSyncTool.RCLONE:
            return await send_message_to_admin(
                content=f'Current {LeechFileSyncTool.RCLONE.lower()} storage: {current_upload_setting.get("dest") or "None"}',
                should_auto_delete=False,
                delete_after_seconds=-1,
                reply_markup=InlineKeyboardMarkup(
                    get_rclone_remote_buttons(ButtonCallbackPrefix.LEECH_SETTING_UPLOAD_DESTINATION)
                )
            )

    elif next_step == SettingInteractStep.COMPLETED:
        m: Message = await send_message_to_admin('Got it, please wait...', False)

        alist_dest = \
            alist_storages[int(dest)].get('mount_path') if (tool == LeechFileSyncTool.ALIST and dest != '') else None

        Setting(
            key=SettingKey.FILE_UPLOAD_DESTINATION,
            value={
                'tool': tool,
                'dest': alist_dest or dest
            }
        ).save()

        await m.delete()

        table = pt.PrettyTable(
            field_names=['Item', 'Current'],
            border=True,
            preserve_internal_border=False,
            header=False,
            valign='m'
        )

        table._max_width = {'Item': 18, 'Current': 18}

        table.add_row(['Upload tool', tool], divider=True)

        table.add_row(['Upload destination', alist_dest or dest], divider=True)

        await send_message_to_admin(
            f'<pre>| \n| 🎉 Setting has been updated!\n| \n{table.get_string()}</pre>',
            False
        )


@Client.on_callback_query(filters.regex('^leech_setting_'))
async def consume_callback(_, query):
    global setting_react_value, setting_steps, current_setting_step

    [key, value] = query.data.removeprefix('leech_setting_').split('_', 1)
    setting_react_value[key] = value
    next_setting_step = setting_steps[current_setting_step]

    await query.message.delete()
    await _next(next_setting_step)
    current_setting_step = next_setting_step


@Client.on_message(filters.command('leech setting') & filters.private & is_admin)
async def leech_setting(_: Client, message: Message):
    global current_setting_step, current_upload_setting

    current_upload_setting = getattr(Setting.objects(key=SettingKey.FILE_UPLOAD_DESTINATION).first(), 'value', {})
    current_setting_step = SettingInteractStep.SELECT_UPLOAD_TOOL
    await _next(current_setting_step)
