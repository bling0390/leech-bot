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


def get_queue_buttons(
    queue_name: str,
    tools: list[str],
    worker_name: str,
    worker_names: list[str]
) -> list[list[InlineKeyboardButton]]:
    return [
        *list(map(lambda x: [
            InlineKeyboardButton(
                text=f'For {x.lower()} {"(Running)" if f"{worker_name}@{queue_name}@{x}" in worker_names else ""}',
                callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_QUEUE}{queue_name}@{x}',
            )
        ], tools)),
        get_bottom_buttons('', should_have_return=False)
    ]


def wait_expect_worker_status(hostname: str, status: WorkerStatus, timeout: float) -> bool:
    while time.time() < timeout:
        if Worker.objects(hostname=hostname, status=status).first():
            return True

        time.sleep(5)

    return False


def construct_table_format_message(**kwargs) -> str:
    table = pt.PrettyTable(['Item', 'Current'])
    table.border = True
    table.preserve_internal_border = False
    table.header = False
    table._max_width = {'Item': 18, 'Current': 18}
    table.valign['Item'] = 'm'
    table.valign['Current'] = 'm'

    if kwargs.get('worker'):
        table.add_row(['Worker name', kwargs.get('worker')], divider=True)

    if kwargs.get('queue'):
        table.add_row(['Queue name', kwargs.get('queue')], divider=True)

    if kwargs.get('amount'):
        table.add_row(['Concurrency', kwargs.get('amount')], divider=True)

    if kwargs.get('status'):
        table.add_row(['Worker status', kwargs.get('status')], divider=True)

    return f'<pre>| \n| {kwargs.get("title")}\n| \n{table.get_string()}</pre>'


async def _next(message: Message, next_step: str):
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
                '<b>Worker</b>',
                'Bot will startup a new worker process for you if it does not exist.',
                'Be aware of the more worker you startup the more computer resource it will consume.'
            ]),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text=' '.join([
                            'For download',
                            f'({download_worker_count} running worker)' if download_worker_count > 0 else ''
                        ]),
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_WORKER}{Hostname.FILE_LEECH_WORKER}',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=' '.join([
                            'For upload',
                            f'({upload_worker_count} running worker)' if upload_worker_count > 0 else ''
                        ]),
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_WORKER}{Hostname.FILE_SYNC_WORKER}',
                    )
                ],
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif next_step == ConsumeInteractStep.SELECT_AMOUNT:
        return await message.reply(
            text='\n\n'.join([
                '<b>Amount</b>',
                'Amount of task will be processed at the same time.'
            ]),
            reply_markup=InlineKeyboardMarkup(list(filter(lambda x: x is not None, [
                [
                    InlineKeyboardButton(
                        text=f'Change to 0 (shutdown worker)',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_AMOUNT}{0}',
                    )
                ] if Worker.objects(hostname=hostname, status=WorkerStatus.READY).first() else None,
                *list(map(lambda x: [
                    InlineKeyboardButton(
                        text=f'Change to {x}',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_CONSUME_AMOUNT}{x}',
                    )
                ], range(1, 6))),
                get_bottom_buttons('', should_have_return=False)
            ])))
        )

    elif next_step == ConsumeInteractStep.SELECT_QUEUE:
        is_leech_worker_selected = consume_react_value.get('worker') == Hostname.FILE_LEECH_WORKER

        return await message.reply(
            text='\n\n'.join([
                '<b>Queue</b>'
            ]),
            reply_markup=InlineKeyboardMarkup(
                get_queue_buttons(
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
                    list(map(lambda x: x.hostname, Worker.objects(status=WorkerStatus.READY).only('hostname')))
                )
            )
        )

    elif next_step == 'COMPLETED':
        m: Message = await send_message_to_admin('Got it, please wait...', False)

        async def wait_until_worker_ready() -> bool:
            open_celery_worker_process(
                Project.LEECH_DOWNLOADER if worker == Hostname.FILE_LEECH_WORKER else Project.LEECH_UPLOADER,
                hostname,
                queue,
                amount
            )

            if not wait_expect_worker_status(hostname, WorkerStatus.READY, time.time() + 60):
                await m.delete()
                await send_message_to_admin(content='Failed to start worker, please try again later.')
                return False

            return True

        matched_worker: Worker = Worker.objects(hostname=hostname).first()

        if not matched_worker or matched_worker.status == WorkerStatus.SHUTDOWN:
            if not (await wait_until_worker_ready()):
                return

            await m.delete()
            await send_message_to_admin(
                content=construct_table_format_message(
                    title=f'🎉 Congratulations! Worker started!',
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
                content='Worker is not ready, please try again later.',
                should_auto_delete=False
            )
            return

        control.shutdown(destination=[hostname], reply=True)

        has_shutdown = wait_expect_worker_status(hostname, WorkerStatus.SHUTDOWN, time.time() + 60)

        await m.delete()
        if amount == 0 and has_shutdown:
            await send_message_to_admin(
                content=construct_table_format_message(
                    title='🎉 Worker has been shutdown!',
                    worker=hostname,
                    status=WorkerStatus.SHUTDOWN
                ),
                should_auto_delete=False
            )
        elif amount != 0 and has_shutdown:
            if not (await wait_until_worker_ready()):
                return

            await send_message_to_admin(
                content=construct_table_format_message(
                    title=f'🎉 Update number of concurrency to {amount}.',
                    worker=hostname,
                    amount=amount
                ),
                should_auto_delete=False
            )
        else:
            await send_message_to_admin(content='Fail to update worker concurrency, please try again later.')


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
