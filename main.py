import json
import schedule
import time
import bs4
import datetime
import requests
from telegram import ReplyKeyboardMarkup, Update, KeyboardButton
from telegram.ext import MessageHandler, filters, Application, ContextTypes
from telegram.ext import CommandHandler
import threading

# Глобальные переменные и настройки
starti = True
bogdan_snils = '150-499-330-68'  #снилс 1
andr_snils = '150-862-479-69' # снилс 2
with open('vuz.json', encoding='UTF-32') as v:
    vuz = json.load(v)

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # Замените на ваш токен бота
markup0 = ReplyKeyboardMarkup([
    [KeyboardButton('Обновить'), KeyboardButton('Запросить')],
    [KeyboardButton('Общага')]
], one_time_keyboard=False, resize_keyboard=True)

last_t = 'Неизвестно'
it = 0
last = {}
ok = False


# Функция для проверки списков абитуриентов МИРЭА
def check_mirea(v, napr):
    global last_t, ok
    link = f'https://priem.mirea.ru/accepted-entrants-list/personal_code_rating.php?competition={vuz[v][napr][0]}'
    headers = {'User-Agent': ''}
    try:
        res2 = requests.get(link, headers=headers)
        beaLink = bs4.BeautifulSoup(res2.text, 'html.parser')
        last_time = beaLink.find('div', {'class': 'names'}).find('p', {'class': 'lastUpdate'}).get_text()
        if last_time == last_t and ok:
            return -1
        ok = False
        last_t = last_time
        data = beaLink.find('div', {'class': 'names'}).find('table', {'class': 'namesTable'}).findAll('tr', {})

        real_k, kon_all = 0, 0
        b_real_k, b_kon_all = -1, -1
        a_real_k, a_kon_all = -1, -1
        i = 0

        for inf in data[1:]:
            fio, d1, d2 = inf.contents[1].get_text(), inf.contents[3].get_text(), inf.contents[4].get_text()
            if d2 == 'да' or  fio in[bogdan_snils, andr_snils]:
                i += 1
            if fio == bogdan_snils:
                b_real_k = i
            if fio == andr_snils:
                a_real_k = i
                break

        return b_real_k, a_real_k, vuz[v][napr][1]
    except requests.HTTPError as http_error:
        print('Ошибка доступа')
        return -1


# Функция для отправки сообщения через Telegram
def sendMessage(id, text, token):
    zap = f'https://api.telegram.org/bot{token}/sendMessage'
    params = {'chat_id': id, 'text': text}
    return requests.get(zap, params=params).json()


# Функция для проверки претендентов на общежитие
def check_ob():
    text = [i.strip() for i in open('mi.txt').readlines()]
    cou = 0
    for q, w in enumerate(text):
        link = f'https://priem.mirea.ru/accepted-entrants-list/personal_code_rating.php?competition={w}'
        headers = {'User-Agent': ''}
        try:
            res2 = requests.get(link, headers=headers)
            beaLink = bs4.BeautifulSoup(res2.text, 'html.parser')
            data = beaLink.find('div', {'class': 'names'}).find('table', {'class': 'namesTable'}).findAll('tr', {})
        except Exception as e:
            print(e)
            continue
        for inf in data[1:]:
            if len(inf.contents) != 14:
                continue
            if (int(inf.contents[11].get_text()) == 0
            or int(inf.contents[11].get_text()) >= 259) and inf.contents[4].get_text() == 'да' and not ('отказано' in inf.contents[6].get_text() or 'не' in inf.contents[6].get_text()):
                cou += 1
            if int(inf.contents[11].get_text()) < 259:
                break
        print(q, cou)
    return cou


# Периодическая задача для проверки списков МИРЭА и уведомления пользователей
def job():
    date = datetime.datetime.today()
    date += datetime.timedelta(hours=3)
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

    global ok, last
    last = itog
    ok = True
    print(date)

    global it, starti
    if it != last_t and not starti:
        with open('settings.txt') as a:
            for k in a.readlines():
                sendMessage(k, 'Внимание, списки обновлены', TOKEN)

    it = last_t
    starti = False


job()


# Обработчик сообщений Telegram
async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'Обновить':
        await update.message.reply_text(f'Обработка, прошлый список\n{last_t}', reply_markup=markup0)
        job()
        await update.message.reply_text(f'Обработка завершена\n{last_t}', reply_markup=markup0)
    elif update.message.text == 'Запросить':
        for i in last[0][1:]:
            sendMessage(update.effective_user.id, f'Направление {i[0]} \nБогдан {i[1]}\nАндрей {i[2]}\n из {i[3]}!',
                        TOKEN)
    elif update.message.text == 'Общага':
        await update.message.reply_text(
            f'Обработка завершена\n Кол-во людей претендующих на общежитие с баллом >= 259 = {check_ob()}',
            reply_markup=markup0)


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('settings.txt', 'w') as a:
        a.write(str(update.effective_user.id))
    await update.message.reply_text(f'Регистрация пройдена', reply_markup=markup0)


# Функция для запуска периодической задачи в отдельном потоке
def threat():
    while True:
        schedule.run_pending()
        time.sleep(1000)


if __name__ == '__main__':
    schedule.every(20).minutes.do(job)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get))
    application.add_handler(CommandHandler("start", start))
    threading.Thread(target=threat).start()
    application.run_polling()
