import allure
from pages.ui import DashboardPage
from playwright.sync_api import expect

@allure.epic("dashboard pages")
class TestDashboard:
    @allure.story("Dashboard Load")
    def test_dashboard(self, page):
        dashboard_page = DashboardPage(page)
        assert dashboard_page.is_search_visible() is True

    