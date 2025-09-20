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

from flask import Flask, render_template
from telebot import TeleBot, types

from cal import GoogleCalendar, CAL_ID, TZ_DELTA


app = Flask(__name__)

TG_BOT = True
TG_TOKEN = "YOUR_TOKEN_HERE"
PRINT_MSG = False
HOST = "127.0.0.1"
PORT = 5000
NOEVENT_MSG = "10:00–20:00", "No events today"

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
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


def get_cal_evnts():
    yandex_ctime = get_yandex_time()
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
            print(time_str, evnt["summary"])
            data.append((time_str, beautify(evnt["summary"])))
    return data, time_now.time()


def split_evnts(evnts):
    evnts_str = ""
    for evnt in evnts:
        evnts_str += f"{evnt[0]} {evnt[1]}\n"
    return evnts_str


def telegram_bot():
    bot = TeleBot(TG_TOKEN)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        MSG = "\n".join(("Hello and welcome to the daily scheduler bot.",
                         "Type <i>today</i> to display the daily schedule.",
                         ))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        today = types.KeyboardButton("Today")
        markup.row(today)
        bot.send_message(
            message.chat.id,
            MSG,
            reply_markup=markup,
            parse_mode='HTML',
            )

    @bot.message_handler()
    def send_text(message):
        if message.text.lower() == "today":
            events_arr, time_now = get_cal_evnts()
            events_str = split_evnts(events_arr)
            bot.send_message(
                message.chat.id,
                f"<u>Current time</u>: {time_now}\n\n{events_str}",
                parse_mode='HTML',
            )
        else:
            bot.send_message(message.chat.id, "Unknown command")

    bot.polling(none_stop=True)


@app.route("/")
def render_cal():
    yandex_ctime = get_yandex_time()
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
    return render_template("daily_with_hidden.html", data=data, today=today_dayweek, tim=time_now.time(), gdat=gdate)


@app.route("/tomorrow/")
def render_cal_tomorrow():
    # Yandex ctime increased by one day
    yandex_ctime = get_yandex_time() + 86400000
    time_now = datetime.strptime(ctime(yandex_ctime / 1000), "%c")
    gdate = time_now.date()
    start, end = get_time(time_now, dlt=TZ_DELTA)
    events = mk_req(start, end)
    locale.setlocale(locale.LC_ALL, "ru_RU")
    tomorrow = datetime.now() + timedelta(days=1)
    today_dayweek = tomorrow.strftime("%A")
    data = []
    for evnt in events["items"]:
        if today_dayweek == "вторник" and tomorrow.month != 1:
            data = [(NOEVENT_MSG)]
        else:
            time_str = get_times(evnt["start"]["dateTime"], evnt["end"]["dateTime"])
            if PRINT_MSG:
                print(time_str, evnt["summary"])
            data.append((time_str, beautify(evnt["summary"])))
    return render_template("daily_with_hidden.html", data=data, today=today_dayweek, tim=time_now.time(), gdat=gdate)


@app.route("/hidden/")
def render_hidden():
    return render_template("hidden.html")

if __name__ == "__main__":
    Gcal = GoogleCalendar()
    if TG_BOT:
        bot_thread = threading.Thread(target=telegram_bot)
        bot_thread.start()
    app.run(host=HOST, port=PORT)
