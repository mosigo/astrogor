import requests
import re
import time

from datetime import datetime


def load_chess_players_men():
    return __load_chess_players('data/chess_players_men.csv')


def load_chess_players_women():
    return __load_chess_players('data/chess_players_women.csv')


def __load_chess_players(file_name):
    result = []
    uniq = set()
    with open(file_name) as f:
        for line in f:
            row = line.split(';')
            if len(row) == 2 and row[0] not in uniq:
                dt = datetime.strptime(row[0], '%d.%m.%Y')
                result.append(dt)
                uniq.add(row[0])
    return result


if __name__ == '__main__':

    f = open('data/chess_players_men.csv', 'w', encoding='utf8')

    for i in range(1, 17):
        r = requests.get(f'https://www.chessbase.ru/player/?sex=M&country=RUS&PAGEN_1={i}')
        html = r.text
        print(html)

        print('Ищу карточки игроков')
        card_reg_exp = r'<div class="bx-newslist-other">(.*?)</div>'
        birthday_reg_exp = r'\d\d\.\d\d.\d\d\d\d'
        name_reg_exp = r'<a href="/player/.*?">(.*?)</a>'
        for res in re.findall(card_reg_exp, html, re.DOTALL):
            print('Игрок')
            print(res)

            birthdays = re.findall(birthday_reg_exp, res)
            if len(birthdays) > 0:
                print('день рождения =', birthdays[0])

            names = re.findall(name_reg_exp, res)
            if len(names) > 0:
                print('имя =', names[0])

            if len(birthdays) > 0 and len(names) > 0:
                f.write(f'{birthdays[0]};{names[0]}\n')
            print('=======')

        time.sleep(5)

    f.close()
