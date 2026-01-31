from ._login import usings
import sys
import time
import requests

def prints(text, times, size, ):
    sizes = 0
    ot = "-"
    tt = "-" * size
    while not sizes == size:
        sys.stdout.write(f"\r{ot}{text}{tt}")
        sys.stdout.flush()
        time.sleep(times)
        tt = tt[:-1]
        ot = ot + "-"
        sizes += 1

def idlogin(homeurl, error, title, code):
    print(f"{title}")
    data = {"username": "example", "password": "example"}
    data["username"] = input("Имя Пользователя: ")
    data["password"] = input("Пароль: ")
    usings(homeurld, data)
    if code in resp.text:
        print("Вход выполнен IDLogin")
        return IDLogin
    else:
        print(error)

def get(url):
    session = requests.Session()
    resp = session.post(url)
    return resp