from datetime import datetime, timedelta
from random import choice

import requests
import telebot
from dateutil.relativedelta import relativedelta
from telebot import types

link_cis = ''
link_world = ''
questions_registration = {0: 'Для регистрации введите ответ <b>10 / (3 * 2 + 4) = ?</b>.\n'
                             'Enter your answer to register <b>10 / (3 * 2 + 4) = ?</b>.',
                          1: 'Для регистрации введите ответ <b>1 + 1 * 0 = ?</b>.\n'
                             'Enter your answer to register <b>1 + 1 * 0 = ?</b>.',
                          5: 'Для регистрации введите ответ <b>12 * 2 / 4 - 1 = ?</b>.\n'
                             'Enter your answer to register <b>12 * 2 / 4 - 1 = ?</b>.',
                          6: 'Для регистрации введите ответ <b>8 / (2 + 2) * 3 = ?</b>.\n'
                             'Enter your answer to register <b>8 / (2 + 2) * 3 = ?</b>.',
                          8: 'Для регистрации введите ответ <b>4 / 2 + (2 * (1 + 2)) = ?</b>.\n'
                             'Enter your answer to register <b>4 / 2 + (2 * (1 + 2)) = ?</b>',
                          9: 'Для регистрации введите ответ <b>12 - 6 / 2 = ?</b>.\n'
                             'Enter your answer to register <b>12 - 6 / 2 = ?</b>.',
                          10: 'Для регистрации введите ответ <b>3 * 3 + 3 / 3 = ?</b>.\n'
                              'Enter your answer to register <b>3 * 3 + 3 / 3 = ?</b>.',
                          13: 'Для регистрации введите ответ <b>3 + 1 + 4 + 5 / 1 = ?</b>.\n'
                              'Enter your answer to register <b>3 + 1 + 4 + 5 / 1 = ?</b>.',
                          14: 'Для регистрации введите ответ <b>6 + 2 * 12 / 3 = ?</b>.\n'
                              'Enter your answer to register <b>6 + 2 * 12 / 3  = ?</b>.',
                          39: 'Для регистрации введите ответ <b>27 + (13 - 10) * 4 = ?</b>.\n'
                              'Enter your answer to register <b>27 + (13 - 10) * 4 = ?</b>.'
                          }

TOKEN = ''
tb = telebot.TeleBot(TOKEN, parse_mode='html')

keyboard = types.InlineKeyboardMarkup(row_width=2)
reg_button = types.InlineKeyboardButton(text='Регистрация/Registration', callback_data='reg_button')
status_button = types.InlineKeyboardButton(text='Статус/Status', callback_data='status_button')
payment_cis_button = types.InlineKeyboardButton(text='Покупка для СНГ', callback_data='payment_cis_button')
payment_world_button = types.InlineKeyboardButton(text='Payment not for CIS residents',
                                                  callback_data='payment_world_button')
keyboard.add(reg_button, status_button, payment_cis_button, payment_world_button)


def generate_payment_code(message):
    try:
        chars = '!@#$%^&*()+=?[]{};:<>qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
        _payment_code = ''
        for i in range(1, 11):
            _payment_code += choice(chars)

        subscriber = find_subscriber(message.chat.id)

        if message.chat.id == subscriber['telegram']:
            write = {'telegram': subscriber['telegram'], 'sub': subscriber['sub'], 'trial': subscriber['trial'],
                     'end_sub': subscriber['end_sub'], 'payment_code': _payment_code, 're_sub': subscriber['re_sub'],
                     'date_reg': subscriber['date_reg']}
            requests.put(f'http://127.0.0.1:5000/subscriber/:{message.chat.id}', json=write)
        tb.send_message(message.chat.id, f'Сгенерированный код для оплаты подписки - {_payment_code}')
        return _payment_code
    except requests.exceptions.ConnectionError:
        tb.send_message(message.chat.id, 'Ошибка генерации. Попробуйте позже, при повторной ошибке обратитесь к '
                                         'администратору.')


def get_subscribers():
    r = requests.get('http://127.0.0.1:5000/subscribers')
    return r.json()


def find_subscriber(telegram):
    r = requests.get(f'http://127.0.0.1:5000/subscriber/:{telegram}')
    return r.json()


def reg_subscriber(message):
    try:
        if repeat_reg_subscriber(message):
            return
        subscriber_id = message.chat.id
        subscriber_text = message.text
        subscriber_sub = False
        subscriber_trial = 10
        subscriber_end_sub = str((datetime.utcnow() + timedelta(days=7)).strftime('%d.%m.%Y'))
        subscriber_payment_code = ''
        subscriber_re_sub = 0
        subscriber_date_reg = str(datetime.utcnow().strftime('%d.%m.%Y'))

        if int(subscriber_text) in questions_registration.keys():
            subscriber = {'telegram': subscriber_id, 'sub': subscriber_sub, 'trial': subscriber_trial,
                          'end_sub': subscriber_end_sub, 'payment_code': subscriber_payment_code,
                          're_sub': subscriber_re_sub, 'date_reg': subscriber_date_reg}
            requests.post('http://127.0.0.1:5000/registration', json=subscriber)  # write subscriber
            tb.send_message(subscriber_id, f'Регистрация завершена успешно. Ваш ID - <b>{subscriber_id}</b>.\n'
                                           f'Registration completed successfully. Your ID is - <b>{subscriber_id}</b>.')
            tb.send_message(subscriber_id,
                            'Чат поддержки.\nSupport chat.\nhttps://t.me/joinchat/AAAAAFeeHtA62cVhod47uQ')
            with open('id_telegram_subscribers.txt', 'a', encoding='utf-8') as f:
                f.write(str(subscriber_id) + '\n')
        else:
            tb.send_message(subscriber_id, 'Регистрация завершена неудачно.\nRegistration failed.')
    except requests.exceptions.ConnectionError:
        tb.send_message(message.chat.id, 'Ошибка регистрации. Попробуйте позже.\nRegistration error. Try later.')


def repeat_reg_subscriber(message):
    try:
        subscriber_id = message.chat.id
        subscriber_text = message.text

        if int(subscriber_text) in questions_registration.keys():
            subscriber = find_subscriber(subscriber_id)

            if len(subscriber) != 0:
                if subscriber_id == subscriber['telegram']:
                    tb.send_message(subscriber_id,
                                    f'Регистрация не возможна. Пользователь {message.from_user.first_name}'
                                    f' зарегистрирован.\n'
                                    f'Registration is not possible. User {message.from_user.first_name}'
                                    f' registered.')
                    return True
            else:
                return False
        else:
            return False
    except requests.exceptions.ConnectionError:
        tb.send_message(message.chat.id, 'Ошибка регистрации. Попробуйте позже.\nRegistration error. Try later.')


def status_subscriber(message):
    try:
        subscriber_id = message.chat.id
        subscriber = find_subscriber(subscriber_id)
        if len(subscriber) != 0:
            end_sub = subscriber['end_sub']
            trial = subscriber['trial']

            if subscriber['sub']:
                answer = f'Подписка активна до {end_sub}.\nSubscription active until {end_sub}.'
            else:
                answer = f'Подписка неактивна. Бесплатных заходов осталось - {trial}.\n' \
                         f'The subscription is inactive. Free calls left - {trial}.'
            tb.send_message(subscriber_id, answer)
        else:
            tb.send_message(subscriber_id, f'Проверка статуса невозможна, вы не зарегистрированы.\n'
                                           f'Status check is not possible, you are not registered.')
    except requests.exceptions.ConnectionError:
        tb.send_message(message.chat.id,
                        'Ошибка проверки статуса. Попробуйте позже.\nError checking status. Try later.')


@tb.message_handler(commands=['all'])
def send_message_all(message):
    if message.chat.id == '':  # insert self telegram id like 1234567890
        command = message.text
        with open('id_telegram_subscribers.txt', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                try:
                    tb.send_message(int(line.rstrip()), command[5:])
                except ValueError:
                    pass


@tb.message_handler(commands=['get'])
def get_info_subscribers(message):
    if message.chat.id == 'insert self telegram id like 1234567890':
        command = message.text.split()

        if command[1] == 'subscribers':
            subscribers = get_subscribers()
            count = len(subscribers)
            tb.send_message('insert self telegram id like 1234567890', f'Количество подписчиков {count}.')

        elif command[1] == 'sub':
            count_sub = 0
            subscribers = get_subscribers()

            for subscriber in subscribers:
                sub = subscriber['sub']

                if sub:
                    count_sub += 1
            tb.send_message('insert self telegram id like 1234567890', f'Количество активых подписок {count_sub}.')


@tb.message_handler(commands=['start'])
def welcome(message):
    pin_message = tb.send_message(message.chat.id, f'Добро пожаловать, {message.from_user.first_name}!\n'
                                                   f'Я - <b>{tb.get_me().first_name}</b>, помогу тебе управлять твоим '
                                                   f'ботом для игры Hustle Castle.\n'
                                                   f'Welcome, {message.from_user.first_name}!\n'
                                                   f'I - <b>{tb.get_me().first_name}</b>,will help you manage your '
                                                   f'bot for the game Hustle Castle.', reply_markup=keyboard)

    tb.pin_chat_message(message.chat.id, pin_message.message_id)


@tb.message_handler(commands=['update'])
def update_sub(message):
    if message.chat.id == 'insert self telegram id like 1234567890':
        command = message.text.split()
        subscriber_id = int(command[1])
        subscriber_payment_code = command[2]
        subscriber = find_subscriber(subscriber_id)
        if len(subscriber) != 0:
            if subscriber_payment_code == subscriber['payment_code']:
                subscriber_end_sub = (datetime.strptime(subscriber['end_sub'], '%d.%m.%Y') +
                                      relativedelta(months=1)).strftime('%d.%m.%Y')
                subscriber_re_sub = int(subscriber['re_sub'] + 1)
                write = {'telegram': subscriber_id,
                         'sub': True,
                         'trial': int(subscriber['trial']),
                         'end_sub': subscriber_end_sub,
                         'payment_code': subscriber['payment_code'],
                         're_sub': subscriber_re_sub,
                         'date_reg': subscriber['date_reg']
                         }
                requests.put(f'http://127.0.0.1:5000/subscriber/:{subscriber_id}', json=write)
                tb.send_message('insert self telegram id like 1234567890',
                                f'Подписчику {subscriber_id} обновлена подписка до {subscriber_end_sub}.')
                tb.send_message(subscriber_id, f'Вам обновлена подписка до {subscriber_end_sub}.')
            else:
                tb.send_message('insert self telegram id like 1234567890',
                                f'Ошибка в сгенерированном коде {subscriber_payment_code} не равен '
                                f"{subscriber['payment_code']}")
        else:
            tb.send_message('insert self telegram id like 1234567890', f'Не найден подписчик {subscriber_id}.')


@tb.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'reg_button':
        reg = tb.send_message(call.message.chat.id, choice(list(questions_registration.values())))
        tb.register_next_step_handler(reg, reg_subscriber)
    elif call.data == 'status_button':
        status_subscriber(call.message)
    elif call.data == 'payment_cis_button':
        payment_cis_board = types.InlineKeyboardMarkup(row_width=1)
        link_cis_button = types.InlineKeyboardButton(text='Ссылка на оплату', callback_data='link_cis')
        payment_cis_board.add(link_cis_button)
        tb.send_message(call.message.chat.id,
                        'Оплата подписки на <b>1 месяц</b> только для жителей стран СНГ (яндекс.деньги).\nФиксированная'
                        ' стоимость - 150р + комиссия за перевод.\nСрок активации подписки в течении суток.',
                        reply_markup=payment_cis_board)
    elif call.data == 'payment_world_button':
        payment_world_board = types.InlineKeyboardMarkup(row_width=1)
        link_world_button = types.InlineKeyboardButton(text='Link to payment', callback_data='link_world')
        payment_world_board.add(link_world_button)
        tb.send_message(call.message.chat.id, 'In developing.', reply_markup=payment_world_board)
    elif call.data == 'link_cis':
        tb.send_message(call.message.chat.id,
                        f'При платеже необходимо добавить сообщение получателю.\nВ сообщении указать ID полученный при '
                        f'регистрации и сгенерированный код разделенные пробелом.')
        generate_payment_code(call.message)
        try:
            example_payment = open('example_payment.png', 'rb')
            file_id = 'example_payment'
            tb.send_photo(call.message.chat.id, example_payment)
            tb.send_photo(call.message.chat.id, file_id)
            example_payment.close()
        except telebot.apihelper.ApiTelegramException:
            pass
        tb.send_message(call.message.chat.id, link_cis)
    elif call.data == 'link_world':
        tb.send_message(call.message.chat.id, 'In developing.')


tb.enable_save_next_step_handlers(delay=2)
tb.load_next_step_handlers()

if __name__ == '__main__':
    tb.polling(none_stop=True)
