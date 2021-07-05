import os
import json
from loguru import logger
from api_google_bot.google_oath import authorizate
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler
from telegram.ext import CommandHandler
# from telegram.ext import MessageHandler, Filters
# from telegram.ext import InlineQueryHandler

# The ID and range of a sample spreadsheet.
MAIN_SPREADSHEET_ID = os.getenv('READ_SPREADSHEET2')
BOT_TOKEN = os.getenv('BOT_TOKEN_TEST')
RANGE_NAME = 'Data!A2:J13'

logger.add('debug.log', encoding="utf8",
           format='TIME: {time} LEVEL: {level} MESSAGE: {message}', rotation='10 MB', compression='zip')


def read_nps(sheets_service, chat_id):

    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=MAIN_SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        return 'No data found.'
    else:
        for row in values:
            if row[0] == str(chat_id):
                return row[9]


def send_nps(context):
    job = context.job
    context_data = job.context

    sheets_service = authorizate()
    print(context_data['chat_id'])
    nps = read_nps(sheets_service, context_data['chat_id'])
    print(nps)
    context.bot.send_message(context_data['chat_id'], text=nps)


def button(update, context) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query.answer()
    data = json.loads(query.data)
    if data['choise'] == 'NPS':
        context.job_queue.run_once(send_nps, 0, context=data)


def start_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Отправляйте любые проблемы, а сенсей на ближайшем созвоне поможет вам решить их!")
    chat_id = update.message.chat_id

    nps_data = {'chat_id': chat_id, 'choise': 'NPS'}
    nps_data_json = json.dumps(nps_data)
    keyboard = [
        [
            InlineKeyboardButton("NPS", callback_data=nps_data_json),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def init_telegram():

    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start_command)
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(CallbackQueryHandler(button))
    # echo_handler = MessageHandler(Filters.text, echo)
    # dispatcher.add_handler(echo_handler)

    logger.info('Bot start polling')
    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    init_telegram()
