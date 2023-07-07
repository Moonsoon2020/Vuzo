import json

import schedule
import time
import xlsxwriter
import bs4
import datetime
import requests

w = open('settings.txt')
bogdan_snils = (w.readline().replace('\n', ''))
andr_snils = '150-862-479-69'
my = int(w.readline())
v = open('vuz.json', encoding='UTF-32')
vuz = json.load(v)

def check_mirea(v, napr):
    link = f'https://priem.mirea.ru/accepted-entrants-list/personal_code_rating.php?competition={vuz[v][napr][0]}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/100.0.4896.160 YaBrowser/22.5.2.615 Yowser/2.5 Safari/537.36'}
    res2 = requests.get(link, headers=headers)
    beaLink = bs4.BeautifulSoup(res2.text, 'html.parser')
    data = beaLink.find('div', {'class': 'names'}).find('table', {'class':'namesTable'}).findAll('tr', {})
    real_k, kon_all = 0, 0
    b_real_k, b_kon_all = 0, 0
    a_real_k, a_kon_all = 0, 0
    for inf in data[1:]:
        fio, d1, d2 = inf.contents[1].get_text(),inf.contents[3].get_text(),inf.contents[4].get_text()
        if d1 == 'да':
            kon_all += 1
            if d2 == 'да':
                real_k += 1
        if fio == bogdan_snils:
            b_real_k, b_kon_all = real_k, kon_all
        if fio == andr_snils:
            a_real_k, a_kon_all = real_k, kon_all
            break
    return b_real_k, b_kon_all, a_real_k, a_kon_all, vuz[v][napr][1]



def job():

    itog = [['Основные положения', ['Протокол ', 'сделан', str(datetime.datetime.now())], ['для всех направлений указанных в файле система выводит крайнее место. если человек вылетел из списка, то функция выводит кол-во бюджетных мест']]]
    i = 2
    for v, bibl in vuz.items():
        data = [['направление', 'Б>ориг', 'Б>', 'А>ориг', 'А>', 'кол-во мест', 'Бпрохориг', 'Бпрох', 'Апрохориг', 'Апрох']]
        for napr, dop in bibl.items():
            if napr == 'id':
                continue
            data.append([napr, *check_mirea(v, napr),f'=IF($F{i}>B{i},"+","-")', f'=IF($F{i}>C{i},"+","-")'
                            , f'=IF($F{i}>D{i},"+","-")', f'=IF($F{i}>E{i},"+","-")'])
            i += 1
        itog.append([v, *data])
    workbook = xlsxwriter.Workbook('Таблица_Excel_БД.xlsx')
    for sheet in itog:
        name, *stroki = sheet

        worksheet = workbook.add_worksheet(name)
        for row, stroka in enumerate(stroki):
            for i in range(len(stroka)):
                worksheet.write(row, i, (stroka[i]))
    workbook.close()
    print(str(datetime.datetime.now()))
job()
schedule.every(10).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(100)