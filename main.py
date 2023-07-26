import json

import schedule
import time
import xlsxwriter
import bs4
import datetime
from dop import keep_alive
import requests
import logging
from telegram import ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import MessageHandler, ConversationHandler, filters, Application, ContextTypes
from telegram.ext import CommandHandler
import threading

starti = False
w = open('settings.txt')
bogdan_snils = '150-499-330-68'
andr_snils = '150-862-479-69'
v = open('vuz.json', encoding='UTF-32')
vuz = json.load(v)

# TOKEN = '5342995443:AAEBqyRLrd5AmHEEhCNLyfHVy3td3Qvw-Ec'  # токен бота
TOKEN = '6380031031:AAFkhpubZvXUjRVFlWvn6RPugamNppbr4X8'
markup0 = ReplyKeyboardMarkup([[KeyboardButton('Обновить'), KeyboardButton('Запрос')]], one_time_keyboard=False, resize_keyboard=True)
last_t = 'Неизвестно'
it = 0
last = {}
ok = False


def check_mirea(v, napr):
    global last_t, ok
    link = f'https://priem.mirea.ru/accepted-entrants-list/personal_code_rating.php?competition={vuz[v][napr][0]}'
    headers = {'User-Agent': ''}
    res2 = requests.get(link, headers=headers)
    beaLink = bs4.BeautifulSoup(res2.text, 'html.parser')
    last_time = beaLink.find('div', {'class': 'names'}).find('p', {'class': 'lastUpdate'}).get_text()
    if last_time == last_t and ok:
        return last[napr]
    ok = False
    last_t = last_time
    data = beaLink.find('div', {'class': 'names'}).find('table', {'class': 'namesTable'}).findAll('tr', {})
    real_k, kon_all = 0, 0
    b_real_k, b_kon_all = -1, -1
    a_real_k, a_kon_all = -1, -1
    i = 0
    for inf in data[1:]:
        fio, d1, d2 = inf.contents[1].get_text(), inf.contents[3].get_text(), inf.contents[4].get_text()
        if d2 == 'да' or fio in [bogdan_snils, andr_snils]:
            i += 1
        if fio == bogdan_snils:
            b_real_k = i
        if fio == andr_snils:
            a_real_k = i
            break


    return b_real_k, a_real_k, vuz[v][napr][1]


def sendMessage(id, text, token):
    zap = f'''https://api.telegram.org/bot{token}/sendMessage'''
    params = {'chat_id': id, 'text': text}
    return requests.get(zap, params=params).json()


def job():
    date = datetime.datetime.today()
    date += datetime.timedelta(hours=3)
    # itog = [['Основные положения', ['Протокол ', 'сделан', date.strftime('%d/%m/%Y %H:%M:%S')], [
    #     'для всех направлений указанных в файле система выводит крайнее место. если человек вылетел из списка, то функция выводит кол-во бюджетных мест']]]
    itog = []
    i = 2
    for v, bibl in vuz.items():
        data = []
        for napr, dop in bibl.items():
            if napr == 'id':
                continue
            data.append([napr, *check_mirea(v, napr)])
            i += 1
        itog.append([v, *data])
    # workbook = xlsxwriter.Workbook('Таблица_Excel_БД.xlsx')
    # for sheet in itog:
    #     name, *stroki = sheet
    #
    #     worksheet = workbook.add_worksheet(name)
    #     for row, stroka in enumerate(stroki):
    #         for i in range(len(stroka)):
    #             worksheet.write(row, i, (stroka[i]))
    # workbook.close()
    global ok, last
    last = itog
    ok = True
    print(date)
    global it, starti
    if it != last_t and not starti:
        a = open('settings.txt')
        for k in a.readlines():
            sendMessage(k, 'Внимание, списки обновлены, это специальный фальц старт напиши "Запрос" тогда придёт вот такая шняга', TOKEN)
            for i in last[0][1:]:
                sendMessage(k, f'Направление {i[0]} \nБогдан {i[1]}\nАндрей {i[2]}\n из {i[3]}!',
                            TOKEN)

    it = last_t
    starti = False


job()


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'Обновить':
        await update.message.reply_text(f'Обработка, прошлый список\n{last_t}', reply_markup=markup0)
        job()
        await update.message.reply_text(f'Обработка завершена\n{last_t}', reply_markup=markup0)
    else:
        print(111, last)
        for i in last[0][1:]:
            sendMessage(update.effective_user.id, f'Направление {i[0]} \nБогдан {i[1]}\nАндрей {i[2]}\n из {i[3]}!', TOKEN)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a = open('settings.txt', 'w')
    a.write(str(update.effective_user.id))
    print(555)
    await update.message.reply_text(f'Регистрация пройдена', reply_markup=markup0)


def threat():
    while True:
        schedule.run_pending()
        time.sleep(1000)


if __name__ == '__main__':
    schedule.every(30).minutes.do(job)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get))
    application.add_handler(CommandHandler("start", start))
    keep_alive()
    threading.Thread(target=threat).start()
    application.run_polling()



