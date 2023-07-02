import json

import schedule
import time
import xlsxwriter
import bs4
import datetime
import requests
w = open('settings.txt')
my_snils = (w.readline())
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
    count = 0
    rez = []
    for inf in data[1:]:
        b = (inf.get_text(';').replace('\n', ';')).replace(';;;', '^').replace(';;', '^').replace(';', '^')
        a = b.split('^')
        if count <= vuz[v][napr][1]:
            if len(a) == 9:
                rez.append([a[1], int(a[-1]),0 if a[3] == 'нет' else 1])
            else:
                rez.append([a[1], int(a[8]), 0 if a[3] == 'нет' else 1])
            if a[3] != 'нет':
                count += 1
    my_num, mini_b_at, cou_ball_bigvse, count_ball_big_at = 0, 10000, 0, 0
    i = 1
    my_ba = my + vuz[v]['id']
    for n, p, k in rez:
        if p >= my_ba:
            cou_ball_bigvse += 1
            if k == 1:
                count_ball_big_at += 1
        if n == my_snils:
            my_num = i
        if k == 1:
            mini_b_at = min(mini_b_at, p)
        i += 1

    print(my_num, mini_b_at, my_ba, cou_ball_bigvse, count_ball_big_at, vuz[v][napr][1])
    return my_num, mini_b_at, my_ba, cou_ball_bigvse, count_ball_big_at, vuz[v][napr][1]

def job():

    itog = [['Основные положения', ['Протокол ', 'сделан', str(datetime.datetime.now())], [3, 4]]]
    for v, bibl in vuz.items():
        data = [['направление', 'мойномер', 'проходбаллатт', 'мой', '>', '>+аттестат', 'мест']]
        for napr, dop in bibl.items():
            if napr == 'id':
                continue
            data.append([napr, *check_mirea(v, napr)])
        itog.append([v, *data])
    workbook = xlsxwriter.Workbook('Таблица_Excel_БД.xlsx')
    for sheet in itog:
        name, *stroki = sheet
        worksheet = workbook.add_worksheet(name)
        for row, stroka in enumerate(stroki):
            for i in range(len(stroka)):
                worksheet.write(row, i, stroka[i])
    workbook.close()
job()
schedule.every(10).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(100)