import os
import time
from loguru import logger
from api_google_bot.google_oath import authorizate
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext
from telegram.ext import CommandHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, Filters
# from telegram.ext import InlineQueryHandler

# The ID and range of a sample spreadsheet.
MAIN_SPREADSHEET_ID = os.getenv('READ_SPREADSHEET2')
BOT_TOKEN = os.getenv('BOT_TOKEN_TEST')
RANGE_NAME = 'Data!A2:J13'

logger.add('debug.log', encoding="utf8",
           format='TIME: {time} LEVEL: {level} MESSAGE: {message}', rotation='10 MB', compression='zip')


def read_data(sheets_service):
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=MAIN_SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    return values


def read_nps(sheet_data, chat_id):
    for row in sheet_data:
        if row[0] == str(chat_id):
            nps = row[9]
    if not nps:
        return 'NPS not found'
    return nps


def check_access(update, context):
    try:
        chat_member = context.bot.getChatMember(-520226574, update.message.chat_id)
        if chat_member.status in ['administrator', 'creator', 'member']:
            return True
        else:
            return False
    except BadRequest:
        return False


def send_nps(context):
    job = context.job
    context_data = job.context

    nps = read_nps(context.bot_data['sheet_data'], context_data)

    context.bot.send_message(context_data, text=nps)


def send_messages(context):
    job = context.job
    query = job.context
    message = context.bot.send_message(query.from_user.id, text='Начинаю отправлять сообщения')
    i = 0
    for row in context.bot_data['sheet_data']:
        if row[0]:
            context.bot.send_message(int(row[0]), text=row[9])
            i += 1
            message.edit_text(f'Отправил сообщений: {i}')
            time.sleep(0.1)
    message = context.bot.send_message(query.from_user.id, text='Рассылка завершена')


def button(update, context) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query.answer()
    if query.data == 'NPS':
        context.job_queue.run_once(send_nps, 0, context=query.from_user.id)
    if query.data == 'send messages':
        context.job_queue.run_once(send_messages, 0, context=query)


def text(update, context):
    print('ok')
    if update.message.text == 'text':
        context.bot.send_message(update.message.chat.id, 'dkfsdf')


def start_command(update, context):
    is_admin = check_access(update, context)

    keyboard_user = [
        [
            InlineKeyboardButton("NPS", callback_data='NPS'),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    keyboard_admin = [
        [
            InlineKeyboardButton("Разослать сообщения", callback_data='send messages'),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    keyboard_admin2 = [[KeyboardButton('text')]]

    reply_markup_user = InlineKeyboardMarkup(keyboard_user)
    reply_markup_admin = ReplyKeyboardMarkup(keyboard=keyboard_admin2, resize_keyboard=True, one_time_keyboard=True)

    if is_admin:
        update.message.reply_text('Выберите команду', reply_markup=reply_markup_admin)
    else:
        update.message.reply_text('Выберите команду', reply_markup=reply_markup_user)


def init_telegram():

    sheets_service = authorizate()
    sheet_data = read_data(sheets_service)

    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher
    CallbackContext(dispatcher).bot_data['sheet_data'] = sheet_data

    start_handler = CommandHandler('start', start_command)
    dispatcher.add_handler(start_handler)

    start_handler = CommandHandler('check_access', check_access)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(Filters.regex(r'text'), text)
    dispatcher.add_handler(echo_handler)

    dispatcher.add_handler(CallbackQueryHandler(button))

    logger.info('Bot start polling')
    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    init_telegram()
