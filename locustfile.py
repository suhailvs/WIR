import re
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        response = self.client.get("/admin/login/")
        csrftoken = re.search(
            'name="csrfmiddlewaretoken" value="(.+?)"',
            response.text
        ).group(1)
        self.client.post(
            "/admin/login/",
            data={
                "username": "7356775981",
                "password": "a",
                "csrfmiddlewaretoken": csrftoken,
                "next": "/admin/"
            },
            headers={
                "Referer": f"{self.host}/admin/login/"
            }
        )        
    
    @task
    def make_txn(self):
        response = self.client.get("/")
        csrftoken = response.cookies.get('csrftoken')
        self.client.post("/", 
            data={"receiver":"8547622462", "amount":1,"csrfmiddlewaretoken":csrftoken},
            
        )