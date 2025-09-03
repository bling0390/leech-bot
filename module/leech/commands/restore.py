import prettytable as pt

from tool.utils import is_admin
from beans.setting import Setting
from pyrogram import filters, Client
from celery.app.control import Control
from constants.setting import SettingKey
from tool.celery_client import celery_client
from module.leech.utils.message import send_message_to_admin
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


class RestoreInteractStep:
    SELECT_RESTORE_SETTING = 'SELECT_RESTORE_SETTING'
    COMPLETED = 'COMPLETED'


class ButtonCallbackPrefix:
    LEECH_RESTORE_SETTING = 'leech_restore_setting_'


current_restore_step = None

restore_steps = {
    RestoreInteractStep.SELECT_RESTORE_SETTING: RestoreInteractStep.COMPLETED
}

alist_storages = []
restore_react_value = {}
current_upload_restore = {}
control = Control(app=celery_client)


def get_restore_setting_buttons(callback_prefix: str) -> list[list[InlineKeyboardButton]]:
    return list(filter(lambda x: x is not None, [
        [
            InlineKeyboardButton(
                text=str(SettingKey.FILE_UPLOAD_DESTINATION),
                callback_data=f'{callback_prefix}{SettingKey.FILE_UPLOAD_DESTINATION}',
            )
        ]
    ]))


async def _next(next_step: str):
    global current_restore_step, restore_react_value, current_upload_restore, alist_storages
    setting_key = restore_react_value.get('setting', '')

    if next_step == RestoreInteractStep.SELECT_RESTORE_SETTING:
        buttons: list[list[InlineKeyboardButton]] = \
            get_restore_setting_buttons(ButtonCallbackPrefix.LEECH_RESTORE_SETTING)

        return await send_message_to_admin(
            content=f'Which setting you wanna restore?',
            should_auto_delete=False,
            delete_after_seconds=-1,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif next_step == RestoreInteractStep.COMPLETED:
        m: Message = await send_message_to_admin('Got it, please wait...', False)

        current_setting = Setting.objects(
            key=setting_key,
            value=None
        ).first()

        await m.delete()

        if current_setting is None or getattr(current_setting, 'value') is None:
            return await send_message_to_admin('❌ <b>Setting not found</b>', False)

        current_setting.value = None
        current_setting.save()

        table = pt.PrettyTable(
            field_names=['Item', 'Current'],
            border=True,
            preserve_internal_border=False,
            header=False,
            valign='m'
        )

        table._max_width = {'Item': 18, 'Current': 18}

        table.add_row(['key', setting_key], divider=True)

        table.add_row(['value', 'None'], divider=True)

        await send_message_to_admin(
            f'<pre>| \n| 🎉 Setting has been restored!\n| \n{table.get_string()}</pre>',
            False
        )


@Client.on_callback_query(filters.regex('^leech_restore_'))
async def consume_callback(_, query):
    global restore_react_value, restore_steps, current_restore_step

    [key, value] = query.data.removeprefix('leech_restore_').split('_', 1)
    restore_react_value[key] = value
    next_restore_step = restore_steps[current_restore_step]

    await query.message.delete()
    await _next(next_restore_step)
    current_restore_step = next_restore_step


@Client.on_message(filters.command('leech restore') & filters.private & is_admin)
async def leech_restore(_: Client, message: Message):
    global current_restore_step

    current_restore_step = RestoreInteractStep.SELECT_RESTORE_SETTING
    await _next(current_restore_step)
