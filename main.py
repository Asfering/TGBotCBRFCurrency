import telebot
import datetime
import requests
from bs4 import BeautifulSoup as bs
import re

# Время
now = datetime.datetime.now()

# АПИ токен для бота
bot = telebot.TeleBot('5941613698:AAHIpnk-FaZXYAz9FT7T-Ba9-yWd0YZLi4I')

# Регексы для парсинга ЦБ РФ
compiled_letters_pattern = re.compile(r"[а-яА-я]+")
compiled_charcode_pattern = re.compile(r"[A-Z]+")
compiled_numbers_pattern = re.compile(r"\d+")

# Лист всех валют
currency_list = []


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/start":
        bot.send_message(message.from_user.id, "Привет, напиши /help, чтобы узнать, что я умею!")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Вот что я могу: \n"
                                               "/currency - курс валют от ЦБ РФ на сегодня")
    elif message.text == "/currency":
        command_currency(message)
    else:
        currency_item_picked(message)


def currency_item_picked(message):
    temp = 0
    for item in currency_list:
        if message.text == "/" + item[0]:
            bot.send_message(message.from_user.id, "По данным ЦБ РФ на " + parse_day() + "." + parse_month() + "."
                             + str(now.year) + " 1 " + str(item[1]) + " = " + str(item[2]) + " руб.")
            temp = temp+1
            break
    if temp == 0:
        bot.send_message(message.from_user.id, "Я тебя не понимаю :(. Напиши /help.")


def parse_cb_rf():
    url = f"https://cbr.ru/scripts/XML_daily.asp?date_req={parse_day()}/{parse_month()}/{now.year}"
    request = requests.get(url)
    soup = bs(request.text, features="lxml")
    for tag in soup.findAll("valute"):
        result = tag.get_text(strip=True)
        # Получаем данные
        char_code = " ".join(compiled_charcode_pattern.findall(result))
        currency_name = " ".join(compiled_letters_pattern.findall(result))
        numbers = compiled_numbers_pattern.findall(result)

        # Парсим numbers, получаем price
        price = f"{numbers[-2]}.{numbers[-1]}"

        # Добавляем в список списков
        currency_list.append([char_code, currency_name, price])


def parse_day():
    if now.day < 10:
        return "0" + str(now.day)
    else:
        return str(now.day)


def parse_month():
    if now.month < 10:
        return "0" + str(now.month)
    else:
        return str(now.month)


def command_currency(message):
    parse_cb_rf()
    message_to_user = ""
    for item in currency_list:
        message_to_user = message_to_user + "Для получения " + item[1] + " введите: /" + item[0] + "\n"
    bot.send_message(message.from_user.id, message_to_user)


bot.polling(none_stop=True, interval=0)
