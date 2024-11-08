from django.test import Client


def test_can_runserver():
    Client().get('http://127.0.0.1:8000')
