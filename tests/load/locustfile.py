from locust import HttpUser, between, task


class FpaPlatformUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def dashboard_apis(self):
        self.client.get("/health", name="health")
        self.client.get("/companies/", name="companies")
        self.client.get("/kpis/", name="kpis_all")

    @task(2)
    def forecast_endpoint(self):
        self.client.get("/financials/1/forecast", name="forecast")

    @task(2)
    def scenario_endpoint(self):
        self.client.get("/scenarios/?base_revenue=1000000&base_expense=700000", name="scenario")

    @task(1)
    def report_endpoint(self):
        self.client.get("/reports/board-pack/preview", name="report_preview")

    @task(1)
    def agent_cycle(self):
        self.client.post("/agents/run-cycle", json={"company_id": 1, "request_type": "load_test"}, name="agent_cycle")
