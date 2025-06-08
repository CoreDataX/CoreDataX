import requests
import json


def get_magnetic_data(reference, token):
    url = 'http://localhost:8000/read_magnetic_by_reference'
    body = {'reference': reference, 'token': token}

    x = requests.post(url, json=body)

    return json.loads(x.text)


def get_setup_data(reference, token):
    url = 'http://localhost:8000/read_setup_by_reference'
    body = {'reference': reference, 'token': token}

    x = requests.post(url, json=body)

    return json.loads(x.text)


def get_user_data(token):
    url = 'http://localhost:8000/get_user_data_by_token'
    body = {'token': token}

    x = requests.post(url, json=body)

    return x.text


def insert_data(data):
    url = 'http://localhost:8000/insert_data'
    body = {'data': data}

    x = requests.post(url, json=body)

    return x.text
