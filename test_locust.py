from locust import HttpUser, between, task

class WebsiteTest(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def index(self):
        self.client.get("/")