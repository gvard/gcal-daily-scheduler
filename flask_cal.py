"""Daily schedule data from Google Calendar taken by the list_event method and visualized using Flask
"""

import os
import ssl
from datetime import datetime, timedelta
from time import ctime
import locale
import json
import urllib.request
import threading
import time

from flask import Flask, render_template
from telebot import TeleBot, types
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from requests.exceptions import ConnectionError, ReadTimeout
from urllib3.exceptions import ReadTimeoutError, ProtocolError

from .cal import GoogleCalendar, CAL_ID, CAL_WRK_ID, TZ_DELTA


app = Flask(__name__)

TG_BOT = True
VK_BOT = False
TG_TOKEN = "YOUR_TOKEN_HERE"
VK_TOKEN = "YOUR_TOKEN_HERE"
PRINT_MSG = False
HOST = "127.0.0.1"
PORT = 5000
NOEVENT_MSG = "10:00–20:00", "No events today"

if (not os.environ.get("PYTHONHTTPSVERIFY", "") and
    getattr(ssl, "_create_unverified_context", None)):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_yandex_time(geo=213):
    """Get timestamp from time.yandex.ru for Moscow, return datetime object
    """
    locale.setlocale(locale.LC_ALL, "C")
    URL = f"https://yandex.com/time/sync.json?geo={geo}"
    time_data_json = json.load(urllib.request.urlopen(URL))
    yandex_time = time_data_json.get("time")
    return yandex_time


def get_time(time_now, dlt=3):
    start = (datetime(time_now.year, time_now.month, time_now.day,
                      9-dlt, 59)).isoformat() + "Z"
    end = (datetime(time_now.year, time_now.month, time_now.day,
                    21-dlt, 1)).isoformat() + "Z"
    return start, end


def get_times(strt, end):
    strt = strt.split("T")[1][:5]
    end = end.split("T")[1][:5]
    return "–".join((strt, end))


def mk_req(start, end):
    events = Gcal.list_event(CAL_ID, start, end)
    return events


beautify = lambda st: st.strip(".").replace("солнечн", "Солнечн").replace("вселенн", "Вселенн")


def get_cal_evnts(dt=0):
    yandex_ctime = get_yandex_time() + dt
    time_now = datetime.strptime(ctime(yandex_ctime / 1000), "%c")
    gdate = time_now.date()
    start, end = get_time(time_now, dlt=TZ_DELTA)
    events = mk_req(start, end)
    locale.setlocale(locale.LC_ALL, "ru_RU")
    today_dayweek = datetime.now().strftime("%A")
    data = []
    for evnt in events["items"]:
        if today_dayweek == "вторник" and datetime.now().month != 1:
            data = [(NOEVENT_MSG)]
        else:
            time_str = get_times(evnt["start"]["dateTime"], evnt["end"]["dateTime"])
            if PRINT_MSG:
                print(time_str, evnt["summary"])
            data.append((time_str, beautify(evnt["summary"])))
    return data, today_dayweek, time_now.time(), gdate


def split_evnts(evnts):
    evnts_str = ""
    for evnt in evnts:
        evnts_str += f"{evnt[0]} {evnt[1]}\n"
    return evnts_str


def vk_bot():
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    def sender(id, text):
        vk.messages.send(user_id=id, message=text, random_id=0)

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        msg = event.text.lower()
                        id = event.user_id
                        if msg in ['привет', 'start', '/start'] or not msg:
                            sender(id, "Приветствую! По команде today я могу показать расписание, who покажет, кто работает в БЗЗ сегодня.")
                        elif msg == "today":
                            events_arr, today_dayweek, time_now, gdate = get_cal_evnts()
                            events_str = split_evnts(events_arr)
                            sender(id, f"Current time: {time_now}\n\n{events_str}")
                        elif msg == "who":
                            sender(id, f"They are working today: {get_worker_today()}")
                        else:
                            sender(id, "Ничего не понимаю(")
        except (ConnectionError, ReadTimeout, ProtocolError, ReadTimeoutError) as e:
            print(f"Connection error occurred in VK bot: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def get_worker_today():
    workers_str = ""
    time_now = datetime.now()
    start = (datetime(
        time_now.year, time_now.month, time_now.day, time_now.hour, time_now.minute
        )).isoformat() + "Z"
    tomorrow = time_now + timedelta(days=1)
    end = (datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0)).isoformat() + "Z"
    events = Gcal.service.events().list(
        calendarId=CAL_WRK_ID, timeMin=start, timeMax=end, singleEvents=True, orderBy="startTime",
        maxResults=4, timeZone="UTC").execute()
    for event in events["items"]:
        workers_str += f"{event['summary'].strip('БЗЗ: ')}, "
    return workers_str.strip(", ")


def telegram_bot():
    bot = TeleBot(TG_TOKEN)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        MSG = "\n".join(("Hello and welcome to the daily scheduler bot.",
                         "Type <i>today</i> to display the daily schedule, <i>who</i> to display who is working today.",
                         ))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        today = types.KeyboardButton("Today")
        working_today = types.KeyboardButton("Who")
        markup.row(today, working_today)
        bot.send_message(
            message.chat.id,
            MSG,
            reply_markup=markup,
            parse_mode="HTML",
            )

    @bot.message_handler()
    def send_text(message):
        if message.text.lower() == "today":
            events_arr, today_dayweek, time_now, gdate = get_cal_evnts()
            events_str = split_evnts(events_arr)
            bot.send_message(
                message.chat.id,
                f"<u>Current time</u>: {time_now}\n\n{events_str}",
                parse_mode="HTML",
            )
        elif message.text.lower() == "who":
            bot.send_message(
                message.chat.id,
                f"They are working today: {get_worker_today()}"
            )
        else:
            bot.send_message(message.chat.id, "Unknown command")

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=15)
        except (ConnectionError, ReadTimeout, ProtocolError, ReadTimeoutError) as e:
            print(f"Connection error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)


@app.route("/")
def render_cal():
    data, today_dayweek, time_now, gdate = get_cal_evnts()
    return render_template("daily_with_hidden.html", data=data,
                           today=today_dayweek, tim=time_now, gdat=gdate)


@app.route("/tomorrow/")
def render_cal_tomorrow():
    # Yandex ctime increased by one day
    data, today_dayweek, time_now, gdate = get_cal_evnts(dt=86400000)
    tomorrow = datetime.now() + timedelta(days=1)
    today_dayweek = tomorrow.strftime("%A")
    return render_template("daily_with_hidden.html", data=data,
                           today=today_dayweek, tim=time_now, gdat=gdate)


@app.route("/hidden/")
def render_hidden():
    return render_template("hidden.html")

if __name__ == "__main__":
    Gcal = GoogleCalendar()
    if TG_BOT:
        bot_thread1 = threading.Thread(target=telegram_bot)
        bot_thread1.start()
    if VK_BOT:
        bot_thread2 = threading.Thread(target=vk_bot)
        bot_thread2.start()
    app.run(host=HOST, port=PORT)
