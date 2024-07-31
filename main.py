import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN
from db import *
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

user_data = {}
user_messages = {}

def main():
    create_tables()
    bot.polling(none_stop=True)

def create_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Добавить транзакцию", callback_data='add_transaction'))
    markup.add(InlineKeyboardButton("Посмотреть транзакции", callback_data='view_transactions'))
    return markup

def create_currency_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Рубли", callback_data='currency_rub'))
    markup.add(InlineKeyboardButton("Доллары", callback_data='currency_usd'))
    markup.add(InlineKeyboardButton("Евро", callback_data='currency_eur'))
    markup.add(InlineKeyboardButton("Отмена", callback_data='cancel_transaction'))
    return markup

def create_type_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🟢Прибыль", callback_data='type_income'))
    markup.add(InlineKeyboardButton("🔴Трата", callback_data='type_expense'))
    markup.add(InlineKeyboardButton("Отмена", callback_data='cancel_transaction'))
    return markup

def create_view_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("День", callback_data='view_day'))
    markup.add(InlineKeyboardButton("Неделя", callback_data='view_week'))
    markup.add(InlineKeyboardButton("Месяц", callback_data='view_month'))
    markup.add(InlineKeyboardButton("Год", callback_data='view_year'))
    markup.add(InlineKeyboardButton("Все", callback_data='view_all'))
    return markup

def create_back_to_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Вернуться в главное меню", callback_data='back_to_main'))
    return markup

def send_and_delete_message(chat_id, text, reply_markup=None, user_id=None, msg_to_delete=None):
    sent_message = bot.send_message(chat_id, text, reply_markup=reply_markup)
    if user_id is not None:
        if user_id not in user_messages:
            user_messages[user_id] = []
        if user_id in user_messages:
            for msg_id in user_messages[user_id]:
                try:
                    bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            user_messages[user_id] = []
        user_messages[user_id].append(sent_message.message_id)
    if msg_to_delete:
        try:
            bot.delete_message(chat_id, msg_to_delete)
        except Exception:
            pass
    return sent_message

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    username = message.from_user.username
    if register_user(user_id, username):
        send_and_delete_message(message.chat.id, "Вы успешно зарегистрированы! Выберите команду:", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)
    else:
        send_and_delete_message(message.chat.id, "Вы уже зарегистрированы. Выберите команду:", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    data = call.data

    if data == 'add_transaction':
        send_and_delete_message(call.message.chat.id, "Выберите валюту:", reply_markup=create_currency_keyboard(), user_id=user_id, msg_to_delete=call.message.message_id)
    elif data.startswith('currency_'):
        currency = data.split('_')[1]
        user_data[user_id] = {'currency': currency}
        send_and_delete_message(call.message.chat.id, f"Вы выбрали валюту: {currency}. Выберите тип транзакции:", reply_markup=create_type_keyboard(), user_id=user_id, msg_to_delete=call.message.message_id)
    elif data.startswith('type_'):
        transaction_type = '+' if data.split('_')[1] == 'income' else '-'
        user_data[user_id]['type'] = transaction_type
        sent_message = send_and_delete_message(call.message.chat.id, "Введите сумму транзакции:", user_id=user_id, msg_to_delete=call.message.message_id)
        bot.register_next_step_handler(sent_message, lambda msg: handle_transaction_amount(msg))
    elif data == 'view_transactions':
        send_and_delete_message(call.message.chat.id, "Выберите период для просмотра транзакций:", reply_markup=create_view_keyboard(), user_id=user_id, msg_to_delete=call.message.message_id)
    elif data.startswith('view_'):
        period = data.split('_')[1]
        handle_view_transactions(call.message, user_id, period)
    elif data.startswith('edit:'):
        transaction_id = data.split(':')[1]
        sent_message = send_and_delete_message(call.message.chat.id, "Введите новую сумму:", user_id=user_id, msg_to_delete=call.message.message_id)
        bot.register_next_step_handler(sent_message, lambda msg: handle_edit_amount(msg, transaction_id))
    elif data.startswith('delete:'):
        transaction_id = data.split(':')[1]
        delete_transaction(transaction_id)
        send_and_delete_message(call.message.chat.id, "Транзакция удалена", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=call.message.message_id)
    elif data == 'back_to_main':
        send_and_delete_message(call.message.chat.id, "Выберите команду:", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=call.message.message_id)
    elif data == 'cancel_transaction':
        cancel_transaction_process(call.message, user_id)
    elif data.startswith('transaction_'):
        transaction_id = data.split('_')[1]
        handle_transaction_selection(call.message, transaction_id, user_id)

def handle_transaction_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if user_id not in user_messages:
            user_messages[user_id] = []
        user_messages[user_id].append(message.message_id)
        sent_message = send_and_delete_message(message.chat.id, "Введите комментарий к транзакции:", user_id=user_id, msg_to_delete=message.message_id)
        bot.register_next_step_handler(sent_message, lambda msg: handle_transaction_comment(msg, amount))
    except ValueError:
        bot.reply_to(message, "Ошибка формата. Убедитесь, что сумма - число.")

def handle_transaction_comment(message, amount):
    user_id = message.from_user.id
    transaction_type = user_data[user_id].get('type', '-')
    currency = user_data[user_id].get('currency', 'рубли')
    comment = message.text
    add_transaction(user_id, amount, currency, transaction_type, comment)
    send_and_delete_message(message.chat.id, "Транзакция добавлена!", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

def handle_view_transactions(message, user_id, period):
    transactions = get_transactions(user_id, period)
    if transactions:
        text = "Вот ваши транзакции:\n"
        markup = InlineKeyboardMarkup()

        for index, transaction in enumerate(transactions, start=1):
            transaction_time = datetime.strptime(transaction[6], "%Y-%m-%d %H:%M:%S")
            formatted_time = transaction_time.strftime("%Y-%m-%d %H:%M:%S")
            circle = "🟢" if transaction[4] == '+' else "🔴" 
            text += f"{circle} Транзакция {index}:\n" \
                     f"💰 Сумма: {transaction[2]} {transaction[3]}\n" \
                     f"📈 Тип: {'Прибыль' if transaction[4] == '+' else 'Трата'}\n" \
                     f"📅 Время и дата: {formatted_time}\n" \
                     f"📝 Комментарий: {transaction[5]}\n" \
                     f"--------------------------\n"
            markup.add(InlineKeyboardButton(f"Выбрать транзакцию {index}", callback_data=f"transaction_{transaction[0]}"))

        markup.add(InlineKeyboardButton("Вернуться в главное меню", callback_data='back_to_main'))
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        send_and_delete_message(message.chat.id, "Нет транзакций за указанный период.", reply_markup=create_back_to_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

def handle_transaction_selection(message, transaction_id, user_id):
    transaction = get_transaction_by_id(transaction_id, user_id)
    if transaction:
        text = f"🟢 Вы выбрали транзакцию:\n" \
               f"💰 Сумма: {transaction[2]} {transaction[3]}\n" \
               f"📈 Тип: {'Прибыль (+)' if transaction[4] == '+' else 'Трата (-)'}\n" \
               f"📝 Комментарий: {transaction[5]}\n" \
               f"📅 Дата: {transaction[6]}\n" \
               f"--------------------------"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Редактировать", callback_data=f"edit:{transaction[0]}"))
        markup.add(InlineKeyboardButton("Удалить", callback_data=f"delete:{transaction[0]}"))
        markup.add(InlineKeyboardButton("Вернуться к списку транзакций", callback_data='back_to_main'))

        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        send_and_delete_message(message.chat.id, "Транзакция не найдена.", reply_markup=create_back_to_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

def get_transaction_by_id(transaction_id, user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
    transaction = cursor.fetchone()
    conn.close()
    return transaction

def handle_edit_amount(message, transaction_id):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if user_id not in user_messages:
            user_messages[user_id] = []
        user_messages[user_id].append(message.message_id)
        sent_message = send_and_delete_message(message.chat.id, "Введите новый комментарий:", user_id=user_id, msg_to_delete=message.message_id)
        bot.register_next_step_handler(sent_message, lambda msg: handle_edit_comment(msg, transaction_id, amount))
    except ValueError:
        bot.reply_to(message, "Ошибка формата. Убедитесь, что сумма - число.")

def handle_edit_comment(message, transaction_id, amount):
    user_id = message.from_user.id
    comment = message.text
    update_transaction(transaction_id, amount, comment)
    send_and_delete_message(message.chat.id, "Транзакция обновлена!", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

def cancel_transaction_process(message, user_id):
    if user_id in user_data:
        user_data.pop(user_id)
    send_and_delete_message(message.chat.id, "Создание транзакции отменено.", reply_markup=create_main_keyboard(), user_id=user_id, msg_to_delete=message.message_id)

if __name__ == '__main__':
    main()
