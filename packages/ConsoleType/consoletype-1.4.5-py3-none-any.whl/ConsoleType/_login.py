import requests

def usings(homeurl, data):
    session = requests.Session()
    resp = session.post(homeurl, data=data)
    return resp
