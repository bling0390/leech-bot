import datetime

from loguru import logger
import prettytable as pt
from beans.worker import Worker
from tool.utils import is_admin
from pyrogram import filters, Client
from celery.app.control import Control
from tool.celery_client import celery_client
from module.leech.utils.button import get_bottom_buttons
from module.leech.utils.message import send_message_to_admin
from constants.worker import Hostname, Queue, WorkerStatus, Project
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


class RateInteractStep:
    SELECT_PHASE = 'SELECT_PHASE'
    SELECT_WORKER = 'SELECT_WORKER'
    SELECT_AMOUNT = 'SELECT_AMOUNT'
    SELECT_PERIOD = 'SELECT_PERIOD'
    COMPLETED = 'COMPLETED'


class ButtonCallbackPrefix:
    LEECH_RATE_PHASE = 'leech_rate_phase_'
    LEECH_RATE_WORKER = 'leech_rate_worker_'
    LEECH_RATE_AMOUNT = 'leech_rate_amount_'
    LEECH_RATE_PERIOD = 'leech_rate_period_'


current_rate_step = None

rate_steps = {
    RateInteractStep.SELECT_PHASE: RateInteractStep.SELECT_WORKER,
    RateInteractStep.SELECT_WORKER: RateInteractStep.SELECT_AMOUNT,
    RateInteractStep.SELECT_AMOUNT: RateInteractStep.SELECT_PERIOD,
    RateInteractStep.SELECT_PERIOD: RateInteractStep.COMPLETED
}

workers = []
rate_react_value = {}
control = Control(app=celery_client)


async def _next(message: Message, next_step: str):
    global current_rate_step, rate_react_value, workers
    phase = rate_react_value.get('phase', '')
    worker_index = int(rate_react_value.get('worker', '-1'))
    amount = int(rate_react_value.get('amount', '1'))
    period = rate_react_value.get('period', '1')

    if next_step == RateInteractStep.SELECT_PHASE:
        return await message.reply(
            text='\n\n'.join([
                '<b>Phase</b>'
            ]),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text='For download',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_PHASE}{Hostname.FILE_LEECH_WORKER}@{Queue.FILE_DOWNLOAD_QUEUE}',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='For upload',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_PHASE}{Hostname.FILE_SYNC_WORKER}@{Queue.FILE_SYNC_QUEUE}',
                    )
                ],
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif next_step == RateInteractStep.SELECT_WORKER:
        workers = Worker.objects(
            hostname__startswith=phase,
            status=WorkerStatus.READY
        )

        return await message.reply(
            text='\n\n'.join([
                '<b>Worker</b>'
            ]),
            reply_markup=InlineKeyboardMarkup([
                *list(map(lambda x: [
                    InlineKeyboardButton(
                        text=workers[x].hostname,
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_WORKER}{x}',
                    )
                ], range(0, len(workers)))),
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif next_step == RateInteractStep.SELECT_AMOUNT:
        return await message.reply(
            text='\n\n'.join([
                '<b>Amount</b>'
            ]),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text='One task',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_AMOUNT}1',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Five tasks',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_AMOUNT}5',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Ten tasks',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_AMOUNT}10',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='No limit',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_AMOUNT}-1',
                    )
                ],
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif next_step == RateInteractStep.SELECT_PERIOD and amount > 0:
        return await message.reply(
            text='\n\n'.join([
                '<b>Period</b>'
            ]),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text='Second',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_PERIOD}s',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Minute',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_PERIOD}m',
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Hour',
                        callback_data=f'{ButtonCallbackPrefix.LEECH_RATE_PERIOD}h',
                    )
                ],
                get_bottom_buttons('', should_have_return=False)
            ])
        )

    elif (next_step == RateInteractStep.SELECT_PERIOD and amount < 0) or next_step == RateInteractStep.COMPLETED:
        m: Message = await send_message_to_admin('Got it, please wait...', False)

        rate_limit = f'{amount}/{period}' if amount > 0 else 'No limit'
        hostname = workers[worker_index].hostname if worker_index >= 0 else None

        result = control.rate_limit(
            task_name=f'{Project.LEECH_DOWNLOADER}.process_download' if Hostname.FILE_LEECH_WORKER in phase else f'{Project.LEECH_UPLOADER}.process_upload',
            rate_limit=rate_limit,
            destination=[hostname] if hostname else None,
            reply=True
        )

        await m.delete()

        if len([item for item in result if item.get(hostname).get('ok')]) == 1:
            worker: Worker = workers[worker_index]
            worker.rate_limit = {'amount': amount, 'period': period} if amount > 0 else None
            worker.updated_at = datetime.datetime.utcnow()
            worker.save()

            table = pt.PrettyTable(
                field_names=['Item', 'Current'],
                border=True,
                preserve_internal_border=False,
                header=False,
                valign='m'
            )

            table._max_width = {'Item': 18, 'Current': 18}

            table.add_row(['Worker name', hostname], divider=True)

            table.add_row(['Rate limit', rate_limit], divider=True)

            await send_message_to_admin(f'<pre>| \n| 🎉 Rate limit has been set!\n| \n{table.get_string()}</pre>', False)
        else:
            await send_message_to_admin('Failed to set rate limit, please try again later.', False)


@Client.on_callback_query(filters.regex('^leech_rate_'))
async def consume_callback(_, query):
    global rate_react_value, rate_steps, current_rate_step

    [key, value] = query.data.removeprefix('leech_rate_').split('_', 1)
    rate_react_value[key] = value
    next_consume_step = rate_steps[current_rate_step]

    await query.message.delete()
    await _next(query.message, next_consume_step)
    current_rate_step = next_consume_step


@Client.on_message(filters.command('leech rate') & filters.private & is_admin)
async def leech_rate(_: Client, message: Message):
    global current_rate_step

    current_rate_step = RateInteractStep.SELECT_PHASE
    await _next(message, current_rate_step)
