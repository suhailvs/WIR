from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()



class TransactionTest(TestCase):
    fixtures = ["datas.json",]

    def setUp(self):
        self.client = Client()
        self.url = reverse("home")

    def test_login_and_make_transaction(self):
        response = self.client.get(self.url, follow=True)
        self.assertInHTML("<title>Log in | Django site admin</title>", response.content.decode())

        # login as suhail and pay 10$ to nusra
        response = self.client.post(
            f'{reverse("admin:login")}?next={self.url}',
            {"username": '7356775981', "password": "a"},
            follow=True,
        )

        self.assertInHTML('<h3 class="text-muted">Hi Suhail. Your balance: 0$</h3>', response.content.decode())

        response = self.client.post(
            self.url,
            {"receiver": "8921513696", "amount": 10, "description": "caring"},
            follow=True,
        )
        
        # check suhail has -10$ balance
        self.assertInHTML('<h3 class="text-muted">Hi Suhail. Your balance: -10$</h3>', response.content.decode())
        self.assertInHTML('<div class="fw-bold">Paid to Nusra</div>', response.content.decode())

        # prevent transaction to own account
        response = self.client.post(
            self.url,
            {"receiver": "7356775981", "amount": 10, "description": "caring"},
            follow=True,
        )
        self.assertInHTML('<h3 class="text-muted">Hi Suhail. Your balance: -10$</h3>', response.content.decode())

        
        # login as nusra. check she has 10$ balance
        response = self.client.post(
            f'{reverse("admin:login")}?next={self.url}',
            {"username": "8921513696", "password": "a"},
            follow=True,
        )
        self.assertInHTML('<h3 class="text-muted">Hi Nusra. Your balance: 10$</h3>', response.content.decode())
        self.assertInHTML('<div class="fw-bold">Received from Suhail</div>', response.content.decode())

    def todo_test_user_doesnt_exists(self):
        # send txn to user doesn't exists
        # login as suhail and pay 10$ to user doesnt exits
        self.client.post(
            f'{reverse("admin:login")}?next={self.url}',
            {"username": '7356775981', "password": "a"},
            follow=True,
        )
    
        self.client.post(
            self.url,
            {"receiver": "9000000000", "amount": 10, "description": "caring"},
            follow=True,
        )
