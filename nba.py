import requests
from bs4 import BeautifulSoup
import telnetlib
import time
import sys
from io import TextIOWrapper, BytesIO
import os

smth_username = os.getenv('smth_username')
smth_password = os.getenv('smth_password')


def login_bbs(tn, board):
    tn.set_debuglevel(0)
    user_required = '请输入代号:'
    tn.read_until(user_required.encode('GBK'))
    tn.write(smth_username.encode('GBK') + b'\n')
    password_required = '请输入密码:'
    tn.read_until(password_required.encode('GBK'))
    tn.write(smth_password.encode('GBK') + b'\n')
    time.sleep(2)

    for i in range(1, 6):
        tn.write(b'\n')
        time.sleep(2)
        tn.read_very_eager()

    tn.write(b's' + b'\n')
    time.sleep(2)
    tn.write(board.encode('GBK') + b'\n')

    for i in range(3):
        tn.write(b't')
        time.sleep(2)
        tn.read_very_eager()


def post(title, content, board='BasketballForum'):
    tn = telnetlib.Telnet("bbs.newsmth.net", port=23, timeout=100)
    for i in range(3):
        try:
            login_bbs(tn, board)
            time.sleep(5)
            tn.write(b'\x10') #Send CTRL + P
            time.sleep(2)
            tn.write(title.encode('GBK') + b"\n")
            time.sleep(2)
            tn.write(b'\n')
            time.sleep(2)
            tn.write(content.encode('GBK') + b"\n")
            time.sleep(2)
            tn.write(b'\x17')
            time.sleep(1)
            tn.write(b'\n')
            tn.read_very_eager()
            time.sleep(2)
            tn.close()
            return 1
        except Exception:
            tn.close()
            time.sleep(60)
            if i == 2:
                return -1


def post_standings():
    old_stdout = sys.stdout
    sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)

    nba_standings()
    sys.stdout.seek(0)
    content = sys.stdout.read()

    sys.stdout.close()
    sys.stdout = old_stdout

    title = "NBA Standings -- " + time.strftime("%Y-%m-%d")
    post(title, content)
    #print(title)
    #print(content)


def get_standings():
    url = 'https://sports.yahoo.com/nba/standings/?selectedTab=CONFERENCE'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,zh;q=0.8,zh-CN;q=0.7',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1'
    }

    east = []
    west = []

    try:
        r = requests.get(url, headers=headers)
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        return [east, west]

    soup = BeautifulSoup(r.text, 'lxml')

    table = soup.find_all('table', class_='W(100%)')

    # east
    table_body = table[0].find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        team = row.find_all('a')[0].get('title')
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        cols = [ele for ele in cols if ele]
        del cols[4:5]
        cols.insert(0, team)
        east.append(cols)

    # west
    table_body = table[1].find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        team = row.find_all('a')[0].get('title')
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        cols = [ele for ele in cols if ele]
        del cols[4:5]
        cols.insert(0, team)
        west.append(cols)

    return [east, west]


def print_standings(desc, info):
    template = '{:>2} {:<13} {:>2} {:>2} {:>5} {:3} {:4} {:3} {:4} {:4} {:>5} {:>5} {:>5} {:^6}'
    print('')
    print(template.format('', desc, 'W', 'L', 'Pct', 'CGB', 'Home', 'Div', 'Conf', 'L10', 'PF', 'PA', 'Diff', 'Streak'))
    for i, row in enumerate(info):
        print(template.format(i+1, *(row)))
        if i == 7:
            print('-' * 78)



def nba_standings():
    east, west = get_standings()
    if east == [] or west == []:
        print('Get NBA standings failed.')
        return

    print_standings('Eastern', east)
    print_standings('Western', west)


if __name__ == '__main__':
    post_standings()
