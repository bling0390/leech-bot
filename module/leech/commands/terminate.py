from tool.utils import is_admin
from pyrogram import Client, filters
from celery.app.control import Control
from tool.celery_client import celery_client
from module.leech.beans.leech_task import LeechTask
from module.leech.utils.button import get_bottom_buttons
from module.leech.constants.task import TaskType, TaskStatus
from module.leech.utils.message import send_message_to_admin
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

COMMAND_PREFIX = 'leech_terminate_'
control_instance = Control(app=celery_client)


@Client.on_callback_query(filters.regex(f'^{COMMAND_PREFIX}'))
async def interact_callback(_, query):
    task_type = query.data.removeprefix(COMMAND_PREFIX)

    await query.message.delete()

    if task_type == 'both':
        terminate_specific_tasks(TaskType.DOWNLOAD)
        terminate_specific_tasks(TaskType.UPLOAD)
        message = '<b>All pending tasks has terminated!</b>'
    else:
        terminate_specific_tasks(task_type)
        message = f'<b>All pending {task_type.lower()} tasks has terminated!</b>'

    await send_message_to_admin(message)


def terminate_specific_tasks(task_type: TaskType, task_status: TaskStatus = TaskStatus.INITIAL):
    leech_tasks = LeechTask.objects(status=task_status, type__=task_type)

    if len(leech_tasks) == 0:
        return

    # for leech_task in leech_tasks:
    #     response = AsyncResult(id=leech_task.task_id, app=celery_client).revoke(terminate=True, wait=True, timeout=3, signal='QUIT')
    #     continue
    #
    # leech_tasks.update(
    #     status=TaskStatus.DONE,
    #     updated_at=datetime.datetime.utcnow()
    # )
    #
    # LeechFile.objects(id__in=list(map(lambda x: x.file_id, leech_tasks))).update(
    #     status=LeechFileStatus.TERMINATED,
    #     updated_at=datetime.datetime.utcnow()
    # )


@Client.on_message(filters.command('leech terminate') & filters.private & is_admin)
async def leech_terminate(_: Client, message: Message):
    await message.reply(
        text='\n\n'.join([
            '<b>Choose task type you wanna terminate.</b>'
        ]),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text='Only download tasks',
                    callback_data=f'{COMMAND_PREFIX}{TaskType.DOWNLOAD}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Only upload tasks',
                    callback_data=f'{COMMAND_PREFIX}{TaskType.UPLOAD}',
                )
            ],
            [
                InlineKeyboardButton(
                    text='Both',
                    callback_data=f'{COMMAND_PREFIX}both',
                )
            ],
            get_bottom_buttons('', should_have_return=False)
        ])
    )
