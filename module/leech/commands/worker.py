import time
import prettytable as pt
from beans.worker import Worker
from pyrogram import filters, Client
from constants.worker import Hostname
from celery.app.control import Control
from tool.celery_client import celery_client
from module.leech.utils.button import get_bottom_buttons
from constants.worker import Project, Queue, WorkerStatus
from tool.utils import is_admin, open_celery_worker_process
from module.leech.utils.message import send_message_to_admin
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from module.i18n import get_i18n_manager
from module.leech.constants.leech_file_tool import LeechFileTool, LeechFileSyncTool


class ConsumeInteractStep:
    SELECT_WORKER = 'SELECT_WORKER'
    SELECT_AMOUNT = 'SELECT_AMOUNT'
    SELECT_QUEUE = 'SELECT_QUEUE'


class ButtonCallbackPrefix:
    LEECH_CONSUME_WORKER = 'leech_worker_worker_'
    LEECH_CONSUME_AMOUNT = 'leech_worker_amount_'
    LEECH_CONSUME_QUEUE = 'leech_worker_queue_'


current_consume_step = ConsumeInteractStep.SELECT_WORKER

consume_steps = {
    ConsumeInteractStep.SELECT_WORKER: ConsumeInteractStep.SELECT_QUEUE,
    ConsumeInteractStep.SELECT_QUEUE: ConsumeInteractStep.SELECT_AMOUNT,
    ConsumeInteractStep.SELECT_AMOUNT: 'COMPLETED'
}

consume_react_value = {}

control = Control(app=celery_client)


async def get_queue_buttons(
    queue_name: str,
    tools: list[str],
    worker_name: str,
    worker_names: list[str],
    user_id: int
) -> list[list[InlineKeyboardButton]]:
    i18n = get_i18n_manager()
    buttons = []
    for x in tools:
        queue_for_text = await i18n.translate_for_user(user_id, "leech.worker.queue_for", tool=x.lower())
        running_text = await i18n.translate_for_user(user_id, "leech.worker.queue_running") if f"{worker_name}@{queue_name}@{x}" in worker_names else ""
        button_text = f'{queue_for_text} {running_text}'
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_QUEUE}{queue_name}@{x}',
            )
        ])
    
    buttons.append(get_bottom_buttons('', should_have_return=False))
    return buttons


def wait_expect_worker_status(hostname: str, status: WorkerStatus, timeout: float) -> bool:
    while time.time() < timeout:
        if Worker.objects(hostname=hostname, status=status).first():
            return True

        time.sleep(5)

    return False


async def construct_table_format_message(user_id: int, **kwargs) -> str:
    i18n = get_i18n_manager()
    item_col = await i18n.translate_for_user(user_id, 'leech.worker.table.item')
    current_col = await i18n.translate_for_user(user_id, 'leech.worker.table.current')
    table = pt.PrettyTable([item_col, current_col])
    table.border = True
    table.preserve_internal_border = False
    table.header = False
    table._max_width = {item_col: 18, current_col: 18}
    table.valign[item_col] = 'm'
    table.valign[current_col] = 'm'

    if kwargs.get('worker'):
        worker_name_label = await i18n.translate_for_user(user_id, 'leech.worker.table.worker_name')
        table.add_row([worker_name_label, kwargs.get('worker')], divider=True)

    if kwargs.get('queue'):
        queue_name_label = await i18n.translate_for_user(user_id, 'leech.worker.table.queue_name')
        table.add_row([queue_name_label, kwargs.get('queue')], divider=True)

    if kwargs.get('amount'):
        concurrency_label = await i18n.translate_for_user(user_id, 'leech.worker.table.concurrency')
        table.add_row([concurrency_label, kwargs.get('amount')], divider=True)

    if kwargs.get('status'):
        worker_status_label = await i18n.translate_for_user(user_id, 'leech.worker.table.worker_status')
        table.add_row([worker_status_label, kwargs.get('status')], divider=True)

    return f'<pre>| \n| {kwargs.get("title")}\n| \n{table.get_string()}</pre>'


async def _next(message: Message, next_step: str):
    user_id = message.from_user.id
    i18n = get_i18n_manager()
    global current_consume_step, consume_react_value
    worker = consume_react_value.get('worker', '')
    amount = int(consume_react_value.get('amount', '1'))
    queue = consume_react_value.get('queue', '')
    hostname = f'{worker}@{queue}'

    if next_step == ConsumeInteractStep.SELECT_WORKER:
        download_worker_count = Worker.objects(
            hostname__startswith=f'{Hostname.FILE_LEECH_WORKER}@{Queue.FILE_DOWNLOAD_QUEUE}@',
            status=WorkerStatus.READY
        ).count()

        upload_worker_count = Worker.objects(
            hostname__startswith=f'{Hostname.FILE_SYNC_WORKER}@{Queue.FILE_SYNC_QUEUE}@',
            status=WorkerStatus.READY
        ).count()

        return await message.reply(
            text='\n\n'.join([
                await i18n.translate_for_user(user_id, 'leech.worker.selection_title'),
                await i18n.translate_for_user(user_id, 'leech.worker.selection_description'),
                await i18n.translate_for_user(user_id, 'leech.worker.resource_warning')
            ]),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text=' '.join([
                            await i18n.translate_for_user(user_id, 'leech.worker.for_download'),
                            await i18n.translate_for_user(user_id, 'leech.worker.running_workers', count=download_worker_count) if download_worker_count > 0 else ''
                        ]),
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_WORKER}{Hostname.FILE_LEECH_WORKER}',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=' '.join([
                            await i18n.translate_for_user(user_id, 'leech.worker.for_upload'),
                            await i18n.translate_for_user(user_id, 'leech.worker.running_workers', count=upload_worker_count) if upload_worker_count > 0 else ''
                        ]),
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_WORKER}{Hostname.FILE_SYNC_WORKER}',
                    )
                ],
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif next_step == ConsumeInteractStep.SELECT_AMOUNT:
        amount_buttons = []
        
        # Add shutdown button if worker exists
        if Worker.objects(hostname=hostname, status=WorkerStatus.READY).first():
            shutdown_text = await i18n.translate_for_user(user_id, 'leech.worker.change_to_shutdown')
            amount_buttons.append([
                InlineKeyboardButton(
                    text=shutdown_text,
                    callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_AMOUNT}{0}',
                )
            ])
        
        # Add amount buttons 1-5
        for x in range(1, 6):
            change_text = await i18n.translate_for_user(user_id, 'leech.worker.change_to', amount=x)
            amount_buttons.append([
                InlineKeyboardButton(
                    text=change_text,
                    callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_AMOUNT}{x}',
                )
            ])
        
        # Add bottom buttons
        amount_buttons.append(get_bottom_buttons('', should_have_return=False))
        
        return await message.reply(
            text='\n\n'.join([
                await i18n.translate_for_user(user_id, 'leech.worker.amount_title'),
                await i18n.translate_for_user(user_id, 'leech.worker.amount_description')
            ]),
            reply_markup=InlineKeyboardMarkup(amount_buttons)
        )

    elif next_step == ConsumeInteractStep.SELECT_QUEUE:
        is_leech_worker_selected = consume_react_value.get('worker') == Hostname.FILE_LEECH_WORKER

        return await message.reply(
            text=await i18n.translate_for_user(user_id, 'leech.worker.queue_title'),
            reply_markup=InlineKeyboardMarkup(
                await get_queue_buttons(
                    Queue.FILE_DOWNLOAD_QUEUE if is_leech_worker_selected else Queue.FILE_SYNC_QUEUE,
                    list(
                        map(
                            lambda x: x[0],
                            filter(
                                lambda i: not i[0].startswith('_'),
                                vars(
                                    LeechFileTool if is_leech_worker_selected else LeechFileSyncTool
                                ).items()
                            )
                        )
                    ),
                    consume_react_value.get('worker'),
                    list(map(lambda x: x.hostname, Worker.objects(status=WorkerStatus.READY).only('hostname'))),
                    user_id
                )
            )
        )

    elif next_step == 'COMPLETED':
        waiting_msg = await i18n.translate_for_user(user_id, 'leech.worker.waiting')
        m: Message = await send_message_to_admin(waiting_msg, False)

        async def wait_until_worker_ready() -> bool:
            open_celery_worker_process(
                Project.LEECH_DOWNLOADER if worker == Hostname.FILE_LEECH_WORKER else Project.LEECH_UPLOADER,
                hostname,
                queue,
                amount
            )

            if not wait_expect_worker_status(hostname, WorkerStatus.READY, time.time() + 60):
                await m.delete()
                failed_msg = await i18n.translate_for_user(user_id, 'leech.worker.start_failed')
                await send_message_to_admin(content=failed_msg)
                return False

            return True

        matched_worker: Worker = Worker.objects(hostname=hostname).first()

        if not matched_worker or matched_worker.status == WorkerStatus.SHUTDOWN:
            if not (await wait_until_worker_ready()):
                return

            await m.delete()
            await send_message_to_admin(
                content=await construct_table_format_message(
                    user_id,
                    title=await i18n.translate_for_user(user_id, 'leech.worker.congratulations'),
                    worker=hostname,
                    queue=queue,
                    amount=amount,
                    status=WorkerStatus.READY
                ),
                should_auto_delete=False
            )

            return

        elif matched_worker.status != WorkerStatus.READY:
            await m.delete()
            await send_message_to_admin(
                content=await i18n.translate_for_user(user_id, 'leech.worker.worker_not_ready'),
                should_auto_delete=False
            )
            return

        control.shutdown(destination=[hostname], reply=True)

        has_shutdown = wait_expect_worker_status(hostname, WorkerStatus.SHUTDOWN, time.time() + 60)

        await m.delete()
        if amount == 0 and has_shutdown:
            await send_message_to_admin(
                content=await construct_table_format_message(
                    user_id,
                    title=await i18n.translate_for_user(user_id, 'leech.worker.worker_shutdown'),
                    worker=hostname,
                    status=WorkerStatus.SHUTDOWN
                ),
                should_auto_delete=False
            )
        elif amount != 0 and has_shutdown:
            if not (await wait_until_worker_ready()):
                return

            await send_message_to_admin(
                content=await construct_table_format_message(
                    user_id,
                    title=await i18n.translate_for_user(user_id, 'leech.worker.concurrency_updated', amount=amount),
                    worker=hostname,
                    amount=amount
                ),
                should_auto_delete=False
            )
        else:
            failed_update_msg = await i18n.translate_for_user(user_id, 'leech.worker.update_failed')
            await send_message_to_admin(content=failed_update_msg)


@Client.on_callback_query(filters.regex('^leech_worker_'))
async def consume_callback(_, query):
    global consume_react_value, consume_steps, current_consume_step

    [key, value] = query.data.removeprefix('leech_worker_').split('_', 1)
    consume_react_value[key] = value
    next_consume_step = consume_steps[current_consume_step]

    await query.message.delete()
    await _next(query.message, next_consume_step)
    current_consume_step = next_consume_step


@Client.on_message(filters.command('leech worker') & filters.private & is_admin)
async def leech_worker(_: Client, message: Message):
    global current_consume_step

    current_consume_step = ConsumeInteractStep.SELECT_WORKER
    await _next(message, current_consume_step)
