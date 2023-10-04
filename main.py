import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import sqlite3
from datetime import datetime
from translates import translations
import requests
import json

TOKEN = '6649677369:AAGLcrm5OUz31M8a5FNmKyaYHJjMw6iZ2b4'
bot = telebot.TeleBot(TOKEN)

# user related
user_ids = []
user_states = {}

# user input related
vol_input_dict = {}
user_sessions = {}
user_languages = {}

# car related + lang related
preferred_language = None
car_types = ["benzin", "dizel", "gibrid_be", "gibrid_de", "electr"]
translated_car_types = []

# channel username
channel_username = "@MusofirMotors"

# time to use in a query
time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the level to DEBUG to capture all log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Log to console
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# show info, debug-level messages in terminal
logger.info('INFO-level message')
logger.debug('DEBUG-level message')

# queries
type_query = "SELECT input FROM typeInput WHERE id in (SELECT MAX(id) FROM typeInput GROUP BY user_id) and user_id = ? GROUP BY user_id ORDER BY id DESC"
age_query = "SELECT input FROM ageInput WHERE id in (SELECT MAX(id) FROM ageInput GROUP BY user_id) AND user_id = ? GROUP BY user_id ORDER BY id DESC"
price_query = "SELECT input FROM priceInput WHERE id in (SELECT MAX(id) FROM priceInput GROUP BY user_id) AND user_id = ? GROUP BY user_id ORDER BY id DESC"
volume_query = "SELECT input FROM volumeInput WHERE id in (SELECT MAX(id) FROM volumeInput GROUP BY user_id) AND user_id = ? GROUP BY user_id ORDER BY id DESC"
lang_query = "SELECT input FROM langInput WHERE id in (SELECT MAX(id) FROM langInput GROUP BY user_id) AND user_id = ? GROUP BY user_id ORDER BY id DESC"
overall_query = """SELECT 
    a.user_id
    ,b.input type 
    ,c.input age
    ,d.input price 
    ,e.input volume
FROM
(SELECT user_id FROM users WHERE id in (SELECT MAX(id) FROM users GROUP BY user_id) GROUP BY user_id ORDER BY id DESC) AS a
JOIN (
    SELECT input, user_id FROM typeInput WHERE id in (SELECT MAX(id) FROM typeInput GROUP BY user_id) GROUP BY user_id ORDER BY id DESC
) AS b ON a.user_id = b.user_id
JOIN (
    SELECT input, user_id FROM ageInput WHERE id in (SELECT MAX(id) FROM ageInput GROUP BY user_id) GROUP BY user_id ORDER BY id DESC
) AS c on a.user_id = c.user_id
JOIN (
    SELECT input, user_id FROM priceInput WHERE id in (SELECT MAX(id) FROM priceInput GROUP BY user_id) GROUP BY user_id ORDER BY id DESC
) AS d ON a.user_id = d.user_id
JOIN (
    SELECT input, user_id FROM volumeInput WHERE id in (SELECT MAX(id) FROM volumeInput GROUP BY user_id) GROUP BY user_id ORDER BY id DESC
) AS e ON a.user_id = e.user_id
WHERE a.user_id = ?"""

# api for currency
url = "https://nbu.uz/en/exchange-rates/json/"
payload = {}
response = requests.request("GET", url, data=payload)
result = response.text
data_dict = json.loads(result)
USDUZS = float(data_dict[-1]['cb_price'])

# is_admin, check
def is_admin(user_id):
    return user_id == 1140808847

# is_member, check
def is_member(user_id):
    return bot.get_chat_member(channel_username, user_id).status == 'member' or bot.get_chat_member(channel_username, user_id).status == 'adminstrator' or bot.get_chat_member(channel_username, user_id).status == 'creator'


# for only admin, media send
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_admin(user_id):
        video_id = message.video.file_id
        announcement_text = message.caption if message.caption else ""
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM users WHERE is_bot = 'False'")
        for row in cursor.fetchall():
            user_ids.append(row[0])
        for user_id in user_ids:
            try:
                bot.send_video(user_id, video_id, caption=announcement_text)
            except Exception as e:
                print(f"Failed to send video announcement to user {user_id}: {str(e)}")
        cursor.close()
        connection.close()
    else:
        bot.send_message(chat_id, "Only administrators can use this command.")


@bot.message_handler(content_types=['document'])
def handle_file(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_admin(user_id):
        file_id = message.document.file_id
        announcement_text = message.caption if message.caption else ""
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM users WHERE is_bot = 'False'")
        for row in cursor.fetchall():
            user_ids.append(row[0])
        for user_id in user_ids:
            try:
                bot.send_document(user_id, file_id, caption=announcement_text)
            except Exception as e:
                print(f"Failed to send announcement to user {user_id}: {str(e)}")
        cursor.close()
        connection.close()
    else:
        bot.send_message(chat_id, "Only administrators can use this command.")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_admin(user_id):
        announcement_text = ""
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM users WHERE is_bot = 'False'")
        for row in cursor.fetchall():
            user_ids.append(row[0])
        if message.caption:
            announcement_text = message.caption
        for user_id in user_ids:
            try:
                bot.send_photo(user_id, message.photo[-1].file_id, caption=announcement_text)
            except Exception as e:
                print(f"Failed to send announcement to user {user_id}: {str(e)}")
        cursor.close()
        connection.close()
    else:
        bot.send_message(chat_id, "Only administrators can use this command.")


@bot.message_handler(commands=['send_message'])
def send_message(message):
    if is_admin(message.from_user.id):
        announcement_text = message.text.replace('/send_message', '').strip()
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT user_id FROM users WHERE is_bot = 'False'")
        for user_id in user_ids:
            try:
                bot.send_message(user_id, announcement_text)
            except Exception as e:
                print(f"Failed to send announcement to user {user_id}: {str(e)}")
        cursor.close()
        connection.close()
    else:
        bot.reply_to(message, "Only administrators can use this command.")


# for only admin, users count
@bot.message_handler(commands=['user_count'])
def user_count(message):

    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users')
    for row in cursor.fetchall():
        count = row[0]
    if is_admin(message.from_user.id):
        bot.reply_to(message, f"There are {count} people!")
    else:
        bot.reply_to(message, "Only administrators can use this command.")
    cursor.close()
    connection.close()


def killer(message):
    inline_markup = InlineKeyboardMarkup()
    subscribe_btn = InlineKeyboardButton("Obuna bo'lish!", url=f"https://t.me/MusofirMotors")
    check_btn = InlineKeyboardButton("Tekshirish ✅", callback_data="check_membership")
    inline_markup.add(subscribe_btn, check_btn)
    bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(callback_query):
    user_id = callback_query.from_user.id
    if is_member(user_id):
        member(callback_query.message)
    else:
        start(callback_query.message)


@bot.message_handler(commands=['start'])
def start(message):
    if is_member(message.from_user.id):
        member(message)
    else:
        killer(message)


def member(message):
    user_states[message.chat.id] = 'main_menu'

    # initialize values to insert to the table
    first_name = message.from_user.first_name 
    last_name = message.from_user.last_name
    user_id = message.from_user.id
    user_name = message.from_user.username
    is_bot = message.from_user.is_bot

    # Create new table and insert values to it
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, first_name varchar(100), last_name varchar(100), username varchar(100), is_bot bool, date date)')
    cursor.execute("INSERT INTO users (user_id, first_name, last_name, username, is_bot, date) VALUES('%s', '%s', '%s', '%s', '%s', '%s')" % (user_id, first_name, last_name, user_name, is_bot, time))
    connection.commit()
    cursor.close()
    connection.close()

    # user session
    if user_id in user_sessions:
        session = user_sessions[user_id]
    else:
        session = {'state': 'type_menu', 'translated_car_types': None}
    user_sessions[user_id] = session

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("O'zbek 🇺🇿")
    button2 = KeyboardButton("Русский 🇷🇺")
    button3 = KeyboardButton("English 🇺🇸")
    keyboard.row(button1, button2, button3)
    bot.send_message(message.chat.id,
                         "Assalomu aleykum!\n Xizmat tilini tanlang 🇺🇿\n_______________________\n\nЗдравствуйте!\n Выберите язык обслуживания 🇷🇺\n_______________________\n\nHello!\n Choose the service language 🇺🇸\n"
                         ,reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text in [translations['lang']['uz'], translations['lang']['ru'], translations['lang']['en']])
def handle_member(message):
    global preferred_language
    user_id = message.from_user.id
    selected_language = {
        "O'zbek 🇺🇿": "uz",
        "Русский 🇷🇺": "ru",
        "English 🇺🇸": "en",
    }.get(message.text)

    if selected_language:
        user_languages[user_id] = selected_language
        if is_member(user_id):
            preferred_language = selected_language
            connection = sqlite3.connect('musofirmotors.db')
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS langInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
            cursor.execute("INSERT INTO langInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, selected_language, time))
            connection.commit()
            cursor.close()
            connection.close()
            type_menu(message)
        else:
            killer(message)
    else:
        bot.send_message(message.chat.id, "Please select a language from the provided options.")


def get_lang(message):
    user_id = message.from_user.id
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute(lang_query, (user_id,))
    for row in cursor.fetchall():
        lang = row[0]
    cursor.close()
    connection.close()
    return lang


@bot.message_handler(func=lambda message: message.text == translations[get_lang(message)]['home'])
def handle_menu_button(message):
    user_states[message.chat.id] = 'main_menu'
    member(message)



@bot.message_handler(func=lambda message: message.text in [translations['lang']['uz'], translations['lang']['ru'], translations['lang']['en']])
def type_menu(message):
    global translated_car_types
    user_id = message.from_user.id
    user_states[message.chat.id] = 'type_menu'

    session = user_sessions[user_id]
    session['state'] = 'type_menu'
    session['translated_car_types'] = [translations[get_lang(message)].get(car_type) for car_type in car_types]

    if is_member(user_id):
        type_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        type_menu_keyboard.row(session['translated_car_types'][0], session['translated_car_types'][1])
        type_menu_keyboard.row(session['translated_car_types'][2], session['translated_car_types'][3])
        type_menu_keyboard.row(session['translated_car_types'][4])
        type_menu_keyboard.row(translations[get_lang(message)]['back'])
        bot.send_message(message.chat.id, translations[get_lang(message)]['choose_type'], reply_markup=type_menu_keyboard)
    else:
        killer(message)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'type_menu')
def handle_type_menu(message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id, {})
    type_input = message.text

    if is_member(user_id):
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS typeInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
        cursor.execute("INSERT INTO typeInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, type_input, time))
        connection.commit()
        cursor.close()
        connection.close()
        if type_input == translations[get_lang(message)]['back']:
            session['state'] = 'main_menu'
            member(message)
        elif type_input == session['translated_car_types'][-1]:
            if message.chat.id in vol_input_dict and type_input == user_sessions[user_id]['translated_car_types'][-1]:
                del vol_input_dict[message.chat.id]
            age_menu(message)
        elif type_input != session['translated_car_types'][-1]:
            volume_menu(message)
    else:
        killer(message)


def get_type_input(message):
    user_id = message.from_user.id
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute(type_query, (user_id,))
    for row in cursor.fetchall():
        type_input = row[0]
    cursor.close()
    connection.close()
    return type_input


@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_numeric_input(message):
    user_id = message.from_user.id
    current_state = user_states.get(user_id)
    if current_state == 'volume_menu':
        if message.text.isdigit() and int(message.text) != 0:
            handle_volume_menu(message)
        else:
            bot.send_message(message.chat.id, translations[get_lang(message)]['wrong_volume'])
    elif current_state == 'price_menu':
        if message.text.isdigit() and int(message.text) != 0:
            handle_price_menu(message)
        else:
            bot.send_message(message.chat.id, translations[get_lang(message)]["wrong_price"])


@bot.message_handler(func=lambda message: message.text in 
                     [
                    translations[preferred_language][car_types[0]], 
                    translations[preferred_language][car_types[1]], 
                    translations[preferred_language][car_types[2]], 
                    translations[preferred_language][car_types[3]]
                    ])
def volume_menu(message):
    user_states[message.chat.id] = 'volume_menu'
    session = user_sessions[message.from_user.id]
    session['state'] = 'volume_menu'
    if is_member(message.from_user.id):
        volume_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        back_button = KeyboardButton(translations[get_lang(message)]['back'])
        home_button = KeyboardButton(translations[get_lang(message)]['home'])
        volume_menu_keyboard.row(back_button, home_button)
        bot.send_message(message.chat.id, translations[get_lang(message)]['choose_volume'], reply_markup=volume_menu_keyboard)
    else:
        killer(message)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'volume_menu')
def handle_volume_menu(message):
    volume_input = message.text
    if is_member(message.from_user.id):
        if volume_input == translations[get_lang(message)]['back']:
            user_states[message.chat.id] = 'type_menu'
            type_menu(message)
        else:
            if volume_input.isdigit() and int(volume_input) != 0:
                vol_input_dict[message.chat.id] = int(volume_input)
                user_id = message.from_user.id
                connection = sqlite3.connect('musofirmotors.db')
                cursor = connection.cursor()
                cursor.execute('CREATE TABLE IF NOT EXISTS volumeInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
                cursor.execute("INSERT INTO volumeInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, volume_input, time))
                connection.commit()
                cursor.close()
                connection.close()
                age_menu(message)
            else:
                bot.send_message(message.chat.id, translations[get_lang(message)]['wrong_volume'])
    else:
        killer(message)


def get_volume_input(message):
    user_id = message.from_user.id
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute(volume_query, (user_id,))
    for row in cursor.fetchall():
        volume_input = row[0]
    cursor.close()
    connection.close()
    return volume_input


@bot.message_handler(func=lambda message: message.text.isdigit())
def age_menu(message):
    user_states[message.chat.id] = 'age_menu'
    session = user_sessions[message.from_user.id]
    if is_member(message.from_user.id):
        age_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

        if get_type_input(message) == session['translated_car_types'][-1]:
            age_menu_button1 = KeyboardButton(translations[get_lang(message)]['one_three_year'])
            age_menu_button2 = KeyboardButton(translations[get_lang(message)]['three_plus_year'])
            age_menu_button_back = KeyboardButton(translations[get_lang(message)]['back'])
        elif get_type_input(message) != session['translated_car_types'][-1]:
            age_menu_button1 = KeyboardButton(translations[get_lang(message)]['one_year'])
            age_menu_button2 = KeyboardButton(translations[get_lang(message)]['two_plus_year'])
            age_menu_button_back = KeyboardButton(translations[get_lang(message)]['back'])
        age_menu_keyboard.row(age_menu_button1, age_menu_button2)
        age_menu_keyboard.row(age_menu_button_back)
        bot.send_message(message.chat.id, translations[get_lang(message)]['choose_age'], reply_markup=age_menu_keyboard)
    else:
        killer(message)


@bot.message_handler(func=lambda message: user_states[message.chat.id] == 'age_menu')
def handle_age_menu(message):
    age_input = message.text
    if is_member(message.from_user.id):
        user_id = message.from_user.id
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS ageInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
        cursor.execute("INSERT INTO ageInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, age_input, time))
        if get_type_input(message) == user_sessions[user_id]['translated_car_types'][-1]:
            cursor.execute('CREATE TABLE IF NOT EXISTS volumeInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
            cursor.execute("INSERT INTO volumeInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, '', time))
        connection.commit()
        cursor.close()
        connection.close()
        if (get_type_input(message) == user_sessions[user_id]['translated_car_types'][-1] and age_input == translations[get_lang(message)]['back']):
            user_states[message.chat.id] = 'type_menu'
            type_menu(message)
        elif (get_type_input(message) != user_sessions[user_id]['translated_car_types'][-1] and age_input == translations[get_lang(message)]['back']):
            user_states[message.chat.id] = 'volume_menu'
            volume_menu(message)
        elif get_type_input(message) in user_sessions[user_id]['translated_car_types']:
            price_menu(message)
    else:
        killer(message)


def get_age_input(message):
    user_id = message.from_user.id
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute(age_query, (user_id,))
    for row in cursor.fetchall():
        age_input = row[0]
    cursor.close()
    connection.close()
    return age_input


@bot.message_handler(func=lambda message: message.text in [translations[get_lang(message)]['one_year'], translations[get_lang(message)]['two_plus_year'], translations[get_lang(message)]['one_three_year'], translations[get_lang(message)]['three_plus_year']])
def price_menu(message):
    user_states[message.chat.id] = 'price_menu'
    if is_member(message.from_user.id):
        price_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        back_button = KeyboardButton(translations[get_lang(message)]['back'])
        home_button = KeyboardButton(translations[get_lang(message)]['home'])
        price_menu_keyboard.row(back_button, home_button)
        bot.send_message(message.chat.id, translations[get_lang(message)]['choose_price'], reply_markup=price_menu_keyboard)
    else:
        killer(message)


@bot.message_handler(func=lambda message: user_states[message.chat.id] == 'price_menu')
def handle_price_menu(message):
    price_input = message.text
    if is_member(message.from_user.id):
        if price_input.isdigit() and int(price_input) != 0:
            user_id = message.from_user.id
            connection = sqlite3.connect('musofirmotors.db')
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS priceInput (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int, input varchar(50), date date)')
            cursor.execute("INSERT INTO priceInput (user_id, input, date) VALUES('%s', '%s', '%s')" % (user_id, price_input, time))
            connection.commit()
            cursor.close()
            connection.close()
            confirmation_page(message)
        elif price_input == translations[get_lang(message)]['back']:
            user_states[message.chat.id] = 'age_menu'
            age_menu(message)
        else:
            bot.send_message(message.chat.id, translations[get_lang(message)]["wrong_price"])
    else:
        killer(message)
    

def get_price_input(message):
    user_id = message.from_user.id
    connection = sqlite3.connect('musofirmotors.db')
    cursor = connection.cursor()
    cursor.execute(price_query, (user_id,))
    for row in cursor.fetchall():
        price_input = row[0]
    cursor.close()
    connection.close()
    return price_input


@bot.message_handler(func=lambda message: message.text.isdigit())
def confirmation_page(message):
    user_states[message.chat.id] = 'confirmation_page'
    confirmation_page_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if is_member(message.from_user.id):
        back_button = KeyboardButton(translations[get_lang(message)]['back'])
        confirm_button = KeyboardButton(translations[get_lang(message)]['confirm'])
        cancel_button = KeyboardButton(translations[get_lang(message)]['cancel'])
        confirmation_page_keyboard.row(confirm_button, cancel_button)
        confirmation_page_keyboard.row(back_button)

        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute(overall_query, (message.from_user.id,))
        for row in cursor.fetchall():
            user_id = row[0]
            c_type = row[1]
            c_age = row[2]
            c_price = row[3]
            c_volume = row[4]
        if c_type == user_sessions[user_id]['translated_car_types'][-1]:
            c_volume = 0
        confirmation_message = (
            f"{translations[get_lang(message)]['confirm_data']} \n\n"
            f"{translations[get_lang(message)]['confirm_type']} {c_type}\n"
            f"{translations[get_lang(message)]['confirm_volume']} {c_volume} cm\u00b3\n"
            f"{translations[get_lang(message)]['confirm_age']} {c_age}\n"
            f"{translations[get_lang(message)]['confirm_price']} ${c_price}"
        )
        bot.send_message(message.chat.id, confirmation_message, reply_markup=confirmation_page_keyboard)
        cursor.close()
        connection.close()
    else:
        killer(message)


@bot.message_handler(func=lambda message: user_states[message.chat.id] == 'confirmation_page')
def handle_confirmation_page(message):
    confirm_input = message.text
    if is_member(message.from_user.id):
        if confirm_input == translations[get_lang(message)]['back']:
            user_states[message.chat.id] == 'price_menu'
            price_menu(message)
        elif confirm_input == translations[get_lang(message)]['cancel']:
            user_states[message.chat.id] == 'main_menu'
            member(message)
        elif confirm_input == translations[get_lang(message)]['confirm']:
            calculation_menu(message)
    else:
        killer(message)


@bot.message_handler(func=lambda message: message.text == translations[get_lang(message)]['confirm'])
def calculation_menu(message):
    user_states[message.chat.id] = 'calculation_menu'
    if is_member:
        
        bhm = 330000
        bojxona_boji = 0
        percent_boj = 0
        indicator_boj = 0
        connection = sqlite3.connect('musofirmotors.db')
        cursor = connection.cursor()
        cursor.execute(overall_query, (message.from_user.id,))
        for row in cursor.fetchall():
            user_id = row[0]
            c_type = row[1]
            c_age = row[2]
            c_price = row[3]
            c_volume = row[4]
        
        if c_type == user_sessions[user_id]['translated_car_types'][-1]:
            c_volume = 0
        

        # utilization cost for every car
        if c_type != user_sessions[user_id]['translated_car_types'][-1]:
            if int(c_volume) < 1000:
                utilization_cost = bhm * 30
                indicator_utilization = 30
            elif 1000 <= int(c_volume) < 2000:
                utilization_cost = bhm * 120
                indicator_utilization = 120
            elif 2000 <= int(c_volume) < 3500:
                utilization_cost = bhm * 180
                indicator_utilization = 180
            else:
                utilization_cost = bhm * 300
                indicator_utilization = 300
        elif c_type == user_sessions[user_id]['translated_car_types'][-1]:
            utilization_cost = bhm * 30
            indicator_utilization = 30
        else:
            utilization_cost = bhm * 90
            indicator_utilization = 90

        
        # bojxona boji
        # one year old
        if c_age == translations[get_lang(message)]['one_year']:
            bojxona_boji_percentage = int(c_price) * USDUZS * 0.15
            percent_boj = 15

            # for petrol
            if c_type == user_sessions[user_id]['translated_car_types'][0]:
                if int(c_volume) < 1000:
                    bojxona_boji_percentage = int(c_price) * USDUZS * 0
                    percent_boj = 0
                    bojxona_boji = bojxona_boji_percentage + int(c_price) * (USDUZS * 0)
                    indicator_boj = 0
                elif 1000 <= int(c_volume) < 1200:
                    bojxona_boji_percentage = int(c_price) * USDUZS * 0.05
                    percent_boj = 5
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0)
                    indicator_boj = 0
                elif 1200 <= int(c_volume) < 1500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0.6)
                    indicator_boj = 0.6
                elif 1500 <= int(c_volume) < 1800:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0.8)
                    indicator_boj = 0.8
                elif 1800 <= int(c_volume) < 3000:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 1.0)
                    indicator_boj = 1.0
                else:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 1.25)
                    indicator_boj = 1.25
            
            # for diesel
            elif c_type == user_sessions[user_id]['translated_car_types'][1]:
                if int(c_volume) < 1000:
                    bojxona_boji_percentage = int(c_volume) * USDUZS * 0
                    percent_boj = 0
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0)
                    indicator_boj = 0
                elif 1000 <= int(c_volume) < 1200:
                    bojxona_boji_percentage = int(c_volume) * USDUZS * 0.05
                    percent_boj = 5
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0)
                    indicator_boj = 0
                elif 1200 <= int(c_volume) <= 1500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0.6)
                    indicator_boj = 0.6
                elif 1500 < int(c_volume) <= 2500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0.8)
                    indicator_boj = 0.8
                else:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 1.25)
                    indicator_boj = 1.25
            
            # for hybrid
            else:
                bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0)
                indicator_boj = 0
        

        # 2-3 years old
        elif c_age == translations[get_lang(message)]['two_plus_year']:
            bojxona_boji_percentage = int(c_price) * USDUZS * 0.3
            percent_boj = 30

            # for petrol
            if c_type == user_sessions[user_id]['translated_car_types'][0]:
                if int(c_volume) <= 1000:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 1.8)
                    indicator_boj = 1.8
                elif 1000 < int(c_volume) <= 1500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 2.0)
                    indicator_boj = 2.0
                elif 1500 < int(c_volume) <= 3000:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 2.5)
                    indicator_boj = 2.5
                else:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 3.0)
                    indicator_boj = 3.0
            
            # for diesel
            elif c_type == user_sessions[user_id]['translated_car_types'][1]:
                if int(c_volume) <= 1500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 2.0)
                    indicator_boj = 2.0
                elif 1500 < int(c_volume) <= 2500:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 2.5)
                    indicator_boj = 2.5
                else:
                    bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 3.0)
                    indicator_boj = 3.0
            
            # for hybrid
            else:
                bojxona_boji = bojxona_boji_percentage + int(c_volume) * (USDUZS * 0)
                indicator_boj = 0

        # bojxona yig'imi
        if int(c_price) < 10000:
            bojxona_yigim = bhm * 1
            indicator_yigim = 1
        elif 10000 <= int(c_price) < 20000:
            bojxona_yigim = bhm * 1.5
            indicator_yigim = 1.5
        elif 20000 <= int(c_price) < 40000:
            bojxona_yigim = bhm * 2.5
            indicator_yigim = 2.5
        elif 40000 <= int(c_price) < 60000:
            bojxona_yigim = bhm * 4
            indicator_yigim = 4
        elif 60000 <= int(c_price) < 100000:
            bojxona_yigim = bhm * 8
            indicator_yigim = 8
        elif 100000 <= int(c_price) < 200000:
            bojxona_yigim = bhm * 15
            indicator_yigim = 15
        elif 200000 <= int(c_price) < 500000:
            bojxona_yigim = bhm * 30
            indicator_yigim = 30
        elif 500000 <= float(c_price) < 1000000:
            bojxona_yigim = bhm * 58
            indicator_yigim = 58
        else:
            bojxona_yigim = bhm * 75
            indicator_yigim = 75
        
        # in soum
        price_in_soum = int(c_price) * USDUZS

        # qqs
        if c_type == user_sessions[user_id]['translated_car_types'][1]:
            qqs = price_in_soum * 0.12
        else:
            qqs = (price_in_soum + bojxona_boji) * 0.12

        # formatting the zeros
        utilization_cost_formatted = "{:,}".format(int(round(utilization_cost))).replace(",", " ")
        qqs_formatted = "{:,}".format(int(round(qqs))).replace(",", " ")
        bojxona_boji_formatted = "{:,}".format(int(round(bojxona_boji))).replace(",", " ")
        bojxona_yigim_formatted = "{:,}".format(int(round(bojxona_yigim))).replace(",", " ")
        c_price_formatted = "{:,}".format(int(c_price)).replace(",", " ")

        overall_fee = utilization_cost + qqs + bojxona_boji + bojxona_yigim
        overall_fee_formatted = "{:,}".format(int(round(overall_fee))).replace(",", " ")

        calculation_page_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        home_button = KeyboardButton(translations[get_lang(message)]['home'])
        calculation_page_keyboard.row(home_button)
        overall_message = (
            f"<b>{translations[get_lang(message)]['price']}${c_price_formatted}</b>\n"
            f"{translations[get_lang(message)]['type']}{c_type}\n"
            f"{translations[get_lang(message)]['confirm_volume']} {c_volume} cm\u00b3\n"
            f"{translations[get_lang(message)]['age']}{c_age}\n"
            f"{translations[get_lang(message)]['usd']}{round(USDUZS, 2)}\n\n"
            f"<b>{translations[get_lang(message)]['overall']}\n {overall_fee_formatted} {translations[get_lang(message)]['currency']}</b>\n\n"
            f"{translations[get_lang(message)]['fees']}\n\n"
            f"- {translations[get_lang(message)]['qqs']}\n {qqs_formatted} {translations[get_lang(message)]['currency']}\n\n"
            f"- {translations[get_lang(message)]['boj']} ({percent_boj}% + ${indicator_boj}/cm\u00b3):\n {bojxona_boji_formatted} {translations[get_lang(message)]['currency']}\n\n"
            f"- {translations[get_lang(message)]['yigim']} ({indicator_yigim} {translations[get_lang(message)]['bhm']}):\n {bojxona_yigim_formatted} {translations[get_lang(message)]['currency']}\n\n"
            f"- {translations[get_lang(message)]['utilization']} ({indicator_utilization} {translations[get_lang(message)]['bhm']}):\n {utilization_cost_formatted} {translations[get_lang(message)]['currency']}\n\n"
        )
        bot.send_message(message.chat.id, overall_message, reply_markup=calculation_page_keyboard, parse_mode="HTML")

    else:
        killer(message)


if __name__ == '__main__':
    bot.infinity_polling()
