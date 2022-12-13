import telebot
import datetime
import requests
from bs4 import BeautifulSoup as bs
import re
import json

# Время
now = datetime.datetime.now()

# АПИ токен для бота
bot = telebot.TeleBot('5941613698:AAHIpnk-FaZXYAz9FT7T-Ba9-yWd0YZLi4I')
w_api = '5b901d1bfb125ca927feadf584d3df31'

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
                                               "/currency - курс валют от ЦБ РФ на сегодня\n"
                                               "/cw [город] - текущая погода в выбранном городе\n"
                                               "/pw [город] - прогноз погоды в выбраннном городе")
    elif message.text == "/currency":
        command_currency(message)
    elif message.text.__contains__("/cw"):
        get_coordinates(message)
    elif message.text.__contains__("/pw"):
        get_coordinates(message)
    else:
        currency_item_picked(message)


def currency_item_picked(message):
    temp = 0
    for item in currency_list:
        if message.text == "/" + item[0]:
            bot.send_message(message.from_user.id, "По данным ЦБ РФ на " + parse_day() + "." + parse_month() + "."
                             + str(now.year) + " " + str(item[1]) + " " + str(item[2]) + " = " + str(item[3]) + " руб.")
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
        count = f"{numbers[-3]}"

        # Добавляем в список списков
        currency_list.append([char_code, count, currency_name, price])


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
        message_to_user = message_to_user + "Для получения " + item[2] + " введите: /" + item[0] + "\n"
    bot.send_message(message.from_user.id, message_to_user)


def get_coordinates(message):
    city_name = message.text[4:]
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={w_api}"
    request = requests.get(url)

    js = json.loads(request.text)
    for item in js:
        if message.text[:3] == '/cw':
            get_current_weather(message, item["lat"], item["lon"])
        elif message.text[:3] == '/pw':
            get_predicted_weather(message, item["lat"], item["lon"])


def get_current_weather(message, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={w_api}"
    request = requests.get(url)

    js = json.loads(request.text)

    name = js["name"]
    sky = js["weather"][0]["description"]
    temp = int(js["main"]["temp"]) - 273
    feels_like = int(js["main"]["feels_like"]) - 273
    bot.send_message(message.from_user.id, f"Сейчас в {name} погода {sky}.\n"
                                           f"Температура сейчас: {temp}, ощущается как: {feels_like}.")


def get_predicted_weather(message, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={w_api}"
    request = requests.get(url)
    weather_list = []

    js = json.loads(request.text)

    name = js["city"]["name"]

    for item in js["list"]:
        temp = int(item["main"]["temp"]) - 273
        feels_list = int(item["main"]["feels_like"]) - 273
        sky = item["weather"][0]["description"]
        date = item["dt_txt"]
        date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        weather_list.append([name, temp, feels_list, sky, date_time_obj])

    answer_to_user = ""
    temp_date = datetime.datetime.strptime('2099-12-12 23:59:59', '%Y-%m-%d %H:%M:%S')
    bot.send_message(message.from_user.id, "Прогноз погоды на 5 дней:")
    for item in weather_list:
        if item[4].date() > temp_date.date():
            bot.send_message(message.from_user.id, answer_to_user)
            answer_to_user = ""
            temp_date = item[4]
        else:
            answer_to_user = answer_to_user + "На момент " + str(item[4]) + " в городе " + item[0] + " будет " + item[3] + ". " \
                                        "Ожидаемая температура: " + str(item[1]) + ", ощущается как: " + str(item[2]) + ".\n"
            temp_date = item[4]


bot.polling(none_stop=True, interval=0)
